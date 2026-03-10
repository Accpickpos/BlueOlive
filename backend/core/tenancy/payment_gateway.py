# tenancy/payment_gateway.py
"""
Payment Gateway Integration for Subscription Payments

Supports multiple payment gateways:
- PayFast (South African payment gateway)
- Stripe (International)

Gateway selection logic:
- Tenant country == 'ZA' → PayFast (default)
- Tenant country != 'ZA' → Stripe
- Can be overridden manually per tenant/subscription
"""

import hashlib
import hmac
import logging
import urllib.parse
from decimal import Decimal
from datetime import date, timedelta

import requests
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class PaymentGatewayError(Exception):
    """Base exception for payment gateway errors."""
    pass


class PaymentVerificationError(PaymentGatewayError):
    """Raised when payment verification fails."""
    pass


# ---------------------------------------------------------------------------
# Base Gateway
# ---------------------------------------------------------------------------

class PaymentGateway:
    """Abstract base payment gateway."""

    def create_payment(self, subscription, amount, description=''):
        """
        Create a payment session / hosted-checkout link.

        Returns:
            dict: {
                'payment_url': str,
                'payment_id':  str,   # our internal SubscriptionPayment.id
                'gateway':     str,
            }
        """
        raise NotImplementedError

    def verify_payment(self, payment_id, data):
        """
        Verify an inbound callback / webhook from the gateway.

        Returns:
            dict: { 'status': 'success' | 'failed' | 'pending', ... }
        """
        raise NotImplementedError

    def create_subscription(self, subscription, payment_token=None):
        """
        Register a recurring subscription with the gateway.

        Returns:
            dict: { 'subscription_id': str, ... }
        """
        raise NotImplementedError

    def cancel_subscription(self, gateway_subscription_id):
        """
        Cancel an active recurring subscription with the gateway.

        Returns:
            bool: True on success
        """
        raise NotImplementedError

    def refund_payment(self, gateway_payment_id, amount=None, reason=''):
        """
        Refund a completed payment (full or partial).

        Args:
            gateway_payment_id: The gateway's own payment / charge ID.
            amount: Decimal amount to refund; None means full refund.
            reason: Optional reason string.

        Returns:
            dict: { 'refund_id': str, 'status': str }
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# PayFast Gateway
# ---------------------------------------------------------------------------

class PayFastGateway(PaymentGateway):
    """
    PayFast Payment Gateway Integration (South Africa).
    Documentation: https://developers.payfast.co.za/
    """

    def __init__(self):
        self.merchant_id  = getattr(settings, 'PAYFAST_MERCHANT_ID',  '')
        self.merchant_key = getattr(settings, 'PAYFAST_MERCHANT_KEY', '')
        self.passphrase   = getattr(settings, 'PAYFAST_PASSPHRASE',   '')
        self.testing      = getattr(settings, 'PAYFAST_TESTING',      True)

        self.base_url = (
            'https://sandbox.payfast.co.za' if self.testing
            else 'https://www.payfast.co.za'
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _generate_signature(self, data: dict) -> str:
        """
        Build the MD5 signature PayFast expects.
        Keys are sorted alphabetically; 'signature' itself is excluded.
        The passphrase (if configured) is appended last.
        """
        filtered = {k: v for k, v in data.items() if k != 'signature' and v != ''}
        param_string = '&'.join(
            f"{k}={urllib.parse.quote_plus(str(v))}"
            for k in sorted(filtered.keys())
        )
        if self.passphrase:
            param_string += f"&passphrase={urllib.parse.quote_plus(self.passphrase)}"

        return hashlib.md5(param_string.encode('utf-8')).hexdigest()

    def _verify_itn_signature(self, data: dict) -> bool:
        """Return True when the ITN signature matches."""
        received  = data.get('signature', '')
        expected  = self._generate_signature(data)
        return hmac.compare_digest(received, expected)

    def _verify_itn_source_ip(self, source_ip: str) -> bool:
        """
        Confirm the ITN originated from a known PayFast IP range.
        PayFast publishes its valid IP ranges in their documentation.
        """
        valid_ips = getattr(
            settings,
            'PAYFAST_VALID_IPS',
            [
                '197.97.145.144/28',
                '41.74.179.192/27',
            ],
        )
        import ipaddress
        try:
            client = ipaddress.ip_address(source_ip)
            for cidr in valid_ips:
                if client in ipaddress.ip_network(cidr, strict=False):
                    return True
        except ValueError:
            pass

        # In sandbox / testing mode, allow localhost
        if self.testing and source_ip in ('127.0.0.1', '::1'):
            return True

        return False

    def _verify_amount(self, payment, gross_amount: str) -> bool:
        """Ensure the amount PayFast reports matches what we expect."""
        try:
            return abs(payment.amount - Decimal(gross_amount)) < Decimal('0.01')
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_payment(self, subscription, amount, description=''):
        """Create a PayFast once-off / ad-hoc payment link."""
        from tenancy.models import SubscriptionPayment

        payment = SubscriptionPayment.objects.create(
            subscription   = subscription,
            amount         = amount,
            currency       = 'ZAR',
            payment_method = 'PAYFAST',
            status         = 'PENDING',
            description    = description or f"Subscription payment for {subscription.tenant.name}",
        )

        data = {
            'merchant_id':   self.merchant_id,
            'merchant_key':  self.merchant_key,
            'return_url':    getattr(settings, 'PAYFAST_RETURN_URL',  ''),
            'cancel_url':    getattr(settings, 'PAYFAST_CANCEL_URL',  ''),
            'notify_url':    getattr(settings, 'PAYFAST_NOTIFY_URL',  ''),
            'm_payment_id':  str(payment.id),
            'amount':        f"{amount:.2f}",
            'item_name':     description or f"Subscription - {subscription.plan.name}",
            'item_description': f"Monthly subscription for {subscription.tenant.name}",
            'custom_int1':   str(subscription.id),
            'custom_str1':   str(subscription.tenant.id),
            # Enable tokenization so we can charge recurring payments later
            'subscription_type': '1',          # 1 = recurring
            'billing_date':  date.today().strftime('%Y-%m-%d'),
            'recurring_amount': f"{amount:.2f}",
            'frequency':     '3',              # 3 = monthly
            'cycles':        '0',              # 0 = indefinite
        }

        data['signature'] = self._generate_signature(data)

        qs = '&'.join(
            f"{k}={urllib.parse.quote_plus(str(v))}"
            for k, v in data.items()
        )
        payment_url = f"{self.base_url}/eng/process?{qs}"

        logger.info("Created PayFast payment %s, amount: %s", payment.id, amount)

        return {
            'payment_url': payment_url,
            'payment_id':  str(payment.id),
            'gateway':     'payfast',
        }

    def verify_payment(self, payment_id, data, source_ip=None):
        """
        Verify a PayFast ITN (Instant Transaction Notification).

        Steps (as per PayFast documentation):
          1. Verify the signature.
          2. Verify the source IP (production only).
          3. Verify the amount matches our record.
          4. POST back to PayFast to confirm the data is valid.
          5. Update payment + subscription records.
        """
        from tenancy.models import SubscriptionPayment

        # --- 1. Fetch our payment record -----------------------------------
        try:
            payment = SubscriptionPayment.objects.get(id=payment_id)
        except SubscriptionPayment.DoesNotExist:
            logger.error("PayFast ITN: payment %s not found", payment_id)
            return {'status': 'failed', 'error': 'Payment not found'}

        # --- 2. Signature check --------------------------------------------
        if not self._verify_itn_signature(data):
            logger.error("PayFast ITN: invalid signature for payment %s", payment_id)
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            return {'status': 'failed', 'error': 'Invalid signature'}

        # --- 3. Source-IP check (skip in testing) --------------------------
        if not self.testing and source_ip:
            if not self._verify_itn_source_ip(source_ip):
                logger.error("PayFast ITN: untrusted source IP %s", source_ip)
                return {'status': 'failed', 'error': 'Untrusted source IP'}

        # --- 4. Amount check -----------------------------------------------
        gross_amount = data.get('amount_gross', '0')
        if not self._verify_amount(payment, gross_amount):
            logger.error(
                "PayFast ITN: amount mismatch for payment %s (expected %s, got %s)",
                payment_id, payment.amount, gross_amount,
            )
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            return {'status': 'failed', 'error': 'Amount mismatch'}

        # --- 5. Server-side validation with PayFast ------------------------
        validation_data = {k: v for k, v in data.items() if k != 'signature'}
        try:
            resp = requests.post(
                f"{self.base_url}/eng/query/validate",
                data=validation_data,
                timeout=30,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("PayFast ITN: validation request failed: %s", exc)
            return {'status': 'error', 'error': str(exc)}

        if resp.text.strip() != 'VALID':
            logger.warning("PayFast ITN: server validation returned '%s' for payment %s", resp.text, payment_id)
            payment.status = 'FAILED'
            payment.failed_at = timezone.now()
            payment.save(update_fields=['status', 'failed_at'])
            return {'status': 'failed', 'error': 'PayFast validation failed'}

        # --- 6. Payment status from PayFast --------------------------------
        pf_payment_status = data.get('payment_status', '')

        if pf_payment_status == 'COMPLETE':
            payment.status             = 'SUCCEEDED'
            payment.paid_at            = timezone.now()
            payment.gateway_payment_id = data.get('pf_payment_id', '')
            payment.gateway_reference  = data.get('m_payment_id', '')
            # Store the recurring token for future charges
            token = data.get('token', '')
            if token:
                subscription = payment.subscription
                subscription.gateway_subscription_id = token
                subscription.save(update_fields=['gateway_subscription_id'])

            payment.save()
            self._extend_subscription(payment.subscription)

            logger.info("PayFast payment %s succeeded", payment.id)
            return {'status': 'success', 'payment': payment}

        elif pf_payment_status == 'FAILED':
            payment.status    = 'FAILED'
            payment.failed_at = timezone.now()
            payment.save(update_fields=['status', 'failed_at'])
            logger.warning("PayFast payment %s failed", payment.id)
            return {'status': 'failed', 'error': 'Payment failed'}

        else:
            # PENDING or other intermediate status
            logger.info("PayFast payment %s status: %s", payment.id, pf_payment_status)
            return {'status': 'pending'}

    def create_subscription(self, subscription, payment_token=None):
        """
        For PayFast, the recurring token is returned in the ITN callback
        ('token' field) after the first successful payment.  We store it
        in verify_payment(); nothing more to do here unless a token was
        passed in explicitly (e.g. after a manual first payment).
        """
        if payment_token:
            subscription.gateway_subscription_id = payment_token
            subscription.save(update_fields=['gateway_subscription_id'])
            logger.info("Stored PayFast token for subscription %s", subscription.id)

        return {'subscription_id': subscription.gateway_subscription_id or ''}

    def cancel_subscription(self, gateway_subscription_id):
        """
        Cancel a PayFast recurring subscription via the API.
        https://developers.payfast.co.za/api#cancel-subscription
        """
        if not gateway_subscription_id:
            logger.warning("PayFast cancel_subscription: no gateway_subscription_id provided")
            return False

        url = f"{self.base_url}/api/subscriptions/{gateway_subscription_id}/cancel"

        timestamp = timezone.now().strftime('%Y-%m-%dT%H:%M:%S%z') or timezone.now().isoformat()
        headers = {
            'merchant-id': self.merchant_id,
            'timestamp':   timestamp,
            'version':     'v1',
        }

        # Build signature for API call
        sig_string = (
            f"merchant-id={self.merchant_id}&"
            f"passphrase={self.passphrase}&"
            f"timestamp={timestamp}&"
            f"version=v1"
        )
        headers['signature'] = hashlib.md5(sig_string.encode()).hexdigest()

        try:
            resp = requests.put(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                logger.info("Cancelled PayFast subscription %s", gateway_subscription_id)
                return True
            else:
                logger.error(
                    "PayFast cancel subscription %s returned %s: %s",
                    gateway_subscription_id, resp.status_code, resp.text,
                )
                return False
        except requests.RequestException as exc:
            logger.error("PayFast cancel subscription request failed: %s", exc)
            return False

    def refund_payment(self, gateway_payment_id, amount=None, reason=''):
        """PayFast does not offer a programmatic refund API; refunds must be done via their merchant portal."""
        logger.warning(
            "PayFast does not support programmatic refunds. "
            "Please refund payment %s manually via the PayFast merchant portal.",
            gateway_payment_id,
        )
        raise PaymentGatewayError(
            "PayFast does not support programmatic refunds. "
            "Please process this refund via the PayFast merchant portal."
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extend_subscription(subscription):
        """Push the subscription end date forward by one billing period."""
        period_days = subscription.plan.billing_period_days
        new_end = (subscription.end_date or date.today()) + timedelta(days=period_days)
        subscription.end_date            = new_end
        subscription.current_period_end  = new_end
        subscription.status              = 'ACTIVE'
        subscription.save(update_fields=['end_date', 'current_period_end', 'status'])


# ---------------------------------------------------------------------------
# Stripe Gateway
# ---------------------------------------------------------------------------

class StripeGateway(PaymentGateway):
    """
    Stripe Payment Gateway Integration (International).
    Documentation: https://stripe.com/docs/api
    """

    def __init__(self):
        self.api_key        = getattr(settings, 'STRIPE_API_KEY',        '')
        self.webhook_secret = getattr(settings, 'STRIPE_WEBHOOK_SECRET', '')
        self._stripe        = None  # lazy-loaded

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def stripe(self):
        """Lazy-load the stripe SDK."""
        if self._stripe is None:
            try:
                import stripe as _stripe
                _stripe.api_key = self.api_key
                self._stripe = _stripe
            except ImportError:
                raise PaymentGatewayError(
                    "The 'stripe' package is not installed. "
                    "Run: pip install stripe"
                )
        return self._stripe

    def _verify_webhook_signature(self, payload: bytes, sig_header: str):
        """
        Verify the Stripe webhook signature.
        Raises stripe.error.SignatureVerificationError on failure.
        """
        return self.stripe.Webhook.construct_event(
            payload, sig_header, self.webhook_secret
        )

    def _interval_for_plan(self, plan):
        """Return ('month', 1) or ('year', 1) based on billing_period_days."""
        if plan.billing_period_days <= 31:
            return 'month', 1
        elif plan.billing_period_days <= 92:
            return 'month', 3
        elif plan.billing_period_days <= 184:
            return 'month', 6
        else:
            return 'year', 1

    def _get_or_create_price(self, plan):
        """
        Return a Stripe Price ID for the plan.
        Stores it on the plan to avoid creating duplicates.
        """
        # If the plan already has a Stripe price, reuse it
        stripe_price_id = getattr(plan, 'stripe_price_id', None)
        if stripe_price_id:
            return stripe_price_id

        interval, interval_count = self._interval_for_plan(plan)
        price = self.stripe.Price.create(
            currency            = 'zar',
            unit_amount         = int(plan.price * 100),
            recurring           = {'interval': interval, 'interval_count': interval_count},
            product_data        = {'name': plan.name},
            idempotency_key     = f"price-{plan.id}",
        )

        # Cache on the plan model if the field exists
        if hasattr(plan, 'stripe_price_id'):
            plan.stripe_price_id = price.id
            plan.save(update_fields=['stripe_price_id'])

        return price.id

    def _get_or_create_customer(self, tenant):
        """
        Return a Stripe Customer ID for the tenant.
        Stores it on the tenant to avoid creating duplicates.
        """
        stripe_customer_id = getattr(tenant, 'stripe_customer_id', None)
        if stripe_customer_id:
            return stripe_customer_id

        customer = self.stripe.Customer.create(
            email           = tenant.email,
            name            = tenant.name,
            metadata        = {'tenant_id': str(tenant.id)},
            idempotency_key = f"customer-{tenant.id}",
        )

        if hasattr(tenant, 'stripe_customer_id'):
            tenant.stripe_customer_id = customer.id
            tenant.save(update_fields=['stripe_customer_id'])

        return customer.id

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_payment(self, subscription, amount, description=''):
        """
        Create a Stripe Checkout Session (hosted checkout page).
        The session is in 'subscription' mode so Stripe manages
        recurring billing automatically.
        """
        from tenancy.models import SubscriptionPayment

        payment = SubscriptionPayment.objects.create(
            subscription   = subscription,
            amount         = amount,
            currency       = subscription.plan.currency or 'ZAR',
            payment_method = 'STRIPE',
            status         = 'PENDING',
            description    = description or f"Subscription payment for {subscription.tenant.name}",
        )

        price_id     = self._get_or_create_price(subscription.plan)
        customer_id  = self._get_or_create_customer(subscription.tenant)

        try:
            session = self.stripe.checkout.Session.create(
                customer             = customer_id,
                payment_method_types = ['card'],
                line_items           = [{'price': price_id, 'quantity': 1}],
                mode                 = 'subscription',
                success_url          = (
                    getattr(settings, 'STRIPE_SUCCESS_URL', '') +
                    '?session_id={CHECKOUT_SESSION_ID}'
                ),
                cancel_url           = getattr(settings, 'STRIPE_CANCEL_URL', ''),
                metadata             = {
                    'subscription_id': str(subscription.id),
                    'tenant_id':       str(subscription.tenant.id),
                    'payment_id':      str(payment.id),
                },
                idempotency_key      = f"checkout-{payment.id}",
            )

            payment.gateway_reference = session.id
            payment.save(update_fields=['gateway_reference'])

            logger.info("Created Stripe Checkout session %s for payment %s", session.id, payment.id)

            return {
                'payment_url': session.url,
                'payment_id':  str(payment.id),
                'gateway':     'stripe',
            }

        except self.stripe.error.StripeError as exc:
            logger.error("Stripe error creating checkout session: %s", exc)
            payment.status    = 'FAILED'
            payment.failed_at = timezone.now()
            payment.save(update_fields=['status', 'failed_at'])
            raise PaymentGatewayError(str(exc)) from exc

    def verify_payment(self, payment_id, data, raw_payload=None, sig_header=None):
        """
        Process a Stripe webhook event.

        Pass `raw_payload` (bytes) and `sig_header` to enable signature
        verification (strongly recommended in production).

        Handled events:
          - checkout.session.completed       → activate subscription
          - invoice.payment_succeeded        → renew subscription
          - invoice.payment_failed           → mark payment failed
          - customer.subscription.deleted    → cancel subscription
        """
        from tenancy.models import SubscriptionPayment

        # --- Optional webhook signature verification ----------------------
        if raw_payload and sig_header and self.webhook_secret:
            try:
                event = self._verify_webhook_signature(raw_payload, sig_header)
            except self.stripe.error.SignatureVerificationError as exc:
                logger.error("Stripe webhook signature verification failed: %s", exc)
                return {'status': 'failed', 'error': 'Invalid webhook signature'}
        else:
            event = data  # Pre-constructed event dict (e.g. in tests)

        event_type = event.get('type', '')
        obj        = event.get('data', {}).get('object', {})

        logger.info("Processing Stripe webhook event: %s", event_type)

        # ------------------------------------------------------------------
        if event_type == 'checkout.session.completed':
            internal_payment_id = obj.get('metadata', {}).get('payment_id')
            if not internal_payment_id:
                return {'status': 'error', 'error': 'No payment_id in metadata'}

            try:
                payment = SubscriptionPayment.objects.get(id=internal_payment_id)
            except SubscriptionPayment.DoesNotExist:
                return {'status': 'failed', 'error': 'Payment not found'}

            payment.status             = 'SUCCEEDED'
            payment.paid_at            = timezone.now()
            payment.gateway_payment_id = obj.get('payment_intent', '')
            payment.gateway_reference  = obj.get('id', '')
            payment.save()

            subscription = payment.subscription
            subscription.gateway_subscription_id = obj.get('subscription', '')
            subscription.gateway_customer_id     = obj.get('customer', '')
            subscription.save(update_fields=['gateway_subscription_id', 'gateway_customer_id'])

            self._extend_subscription(subscription)

            return {'status': 'success', 'payment': payment}

        # ------------------------------------------------------------------
        elif event_type == 'invoice.payment_succeeded':
            stripe_sub_id = obj.get('subscription')
            if not stripe_sub_id:
                return {'status': 'pending'}

            try:
                from tenancy.models import Subscription
                subscription = Subscription.objects.get(gateway_subscription_id=stripe_sub_id)
            except Exception:
                logger.warning("Stripe invoice.payment_succeeded: subscription %s not found", stripe_sub_id)
                return {'status': 'pending'}

            # Record the renewal payment
            amount_paid = Decimal(obj.get('amount_paid', 0)) / 100  # Stripe sends cents
            payment = SubscriptionPayment.objects.create(
                subscription       = subscription,
                amount             = amount_paid,
                currency           = obj.get('currency', 'zar').upper(),
                payment_method     = 'STRIPE',
                status             = 'SUCCEEDED',
                paid_at            = timezone.now(),
                gateway_payment_id = obj.get('payment_intent', ''),
                gateway_reference  = obj.get('id', ''),
                description        = 'Stripe automatic renewal',
            )

            self._extend_subscription(subscription)
            logger.info("Stripe renewal succeeded for subscription %s", stripe_sub_id)
            return {'status': 'success', 'payment': payment}

        # ------------------------------------------------------------------
        elif event_type == 'invoice.payment_failed':
            stripe_sub_id = obj.get('subscription')
            if stripe_sub_id:
                try:
                    from tenancy.models import Subscription
                    subscription = Subscription.objects.get(gateway_subscription_id=stripe_sub_id)
                    # Don't immediately cancel — Stripe will retry.
                    # Just flag as past_due.
                    subscription.status = 'PAST_DUE'
                    subscription.save(update_fields=['status'])
                    logger.warning("Stripe payment failed for subscription %s", stripe_sub_id)
                except Exception:
                    pass
            return {'status': 'failed', 'error': 'Invoice payment failed'}

        # ------------------------------------------------------------------
        elif event_type == 'customer.subscription.deleted':
            stripe_sub_id = obj.get('id')
            if stripe_sub_id:
                try:
                    from tenancy.models import Subscription
                    subscription = Subscription.objects.get(gateway_subscription_id=stripe_sub_id)
                    subscription.status = 'CANCELLED'
                    subscription.save(update_fields=['status'])
                    logger.info("Stripe subscription %s cancelled", stripe_sub_id)
                except Exception:
                    pass
            return {'status': 'success'}

        # ------------------------------------------------------------------
        else:
            logger.debug("Stripe webhook: unhandled event type '%s'", event_type)
            return {'status': 'pending'}

    def create_subscription(self, subscription, payment_token=None):
        """
        Directly create a Stripe subscription (without Checkout).
        Useful when a payment method token already exists.
        """
        customer_id = self._get_or_create_customer(subscription.tenant)
        price_id    = self._get_or_create_price(subscription.plan)

        if payment_token:
            # Attach the payment method to the customer
            self.stripe.PaymentMethod.attach(
                payment_token,
                customer=customer_id,
            )
            self.stripe.Customer.modify(
                customer_id,
                invoice_settings={'default_payment_method': payment_token},
            )

        try:
            stripe_sub = self.stripe.Subscription.create(
                customer        = customer_id,
                items           = [{'price': price_id}],
                metadata        = {
                    'subscription_id': str(subscription.id),
                    'tenant_id':       str(subscription.tenant.id),
                },
                idempotency_key = f"sub-{subscription.id}",
            )

            subscription.gateway_customer_id     = customer_id
            subscription.gateway_subscription_id = stripe_sub.id
            subscription.save(update_fields=['gateway_customer_id', 'gateway_subscription_id'])

            logger.info("Created Stripe subscription %s", stripe_sub.id)
            return {
                'subscription_id': stripe_sub.id,
                'customer_id':     customer_id,
            }

        except self.stripe.error.StripeError as exc:
            logger.error("Stripe error creating subscription: %s", exc)
            raise PaymentGatewayError(str(exc)) from exc

    def cancel_subscription(self, gateway_subscription_id):
        """Cancel a Stripe subscription immediately."""
        try:
            self.stripe.Subscription.delete(
                gateway_subscription_id,
                idempotency_key=f"cancel-{gateway_subscription_id}",
            )
            logger.info("Cancelled Stripe subscription %s", gateway_subscription_id)
            return True
        except self.stripe.error.StripeError as exc:
            logger.error("Stripe error cancelling subscription %s: %s", gateway_subscription_id, exc)
            return False

    def refund_payment(self, gateway_payment_id, amount=None, reason=''):
        """
        Issue a full or partial refund on a Stripe PaymentIntent.

        Args:
            gateway_payment_id: Stripe PaymentIntent ID (pi_xxx).
            amount: Decimal in major currency units (e.g. 50.00 ZAR).
                    None = full refund.
            reason: 'duplicate' | 'fraudulent' | 'requested_by_customer'
        """
        refund_kwargs = {
            'payment_intent':  gateway_payment_id,
            'idempotency_key': f"refund-{gateway_payment_id}",
        }
        if amount is not None:
            refund_kwargs['amount'] = int(amount * 100)  # Convert to cents
        if reason:
            refund_kwargs['reason'] = reason

        try:
            refund = self.stripe.Refund.create(**refund_kwargs)
            logger.info(
                "Stripe refund %s created for payment %s (status: %s)",
                refund.id, gateway_payment_id, refund.status,
            )
            return {'refund_id': refund.id, 'status': refund.status}
        except self.stripe.error.StripeError as exc:
            logger.error("Stripe error creating refund: %s", exc)
            raise PaymentGatewayError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extend_subscription(subscription):
        period_days = subscription.plan.billing_period_days
        new_end = (subscription.end_date or date.today()) + timedelta(days=period_days)
        subscription.end_date           = new_end
        subscription.current_period_end = new_end
        subscription.status             = 'ACTIVE'
        subscription.save(update_fields=['end_date', 'current_period_end', 'status'])


# ---------------------------------------------------------------------------
# Gateway selection / routing
# ---------------------------------------------------------------------------

def resolve_gateway_for_tenant(tenant) -> str:
    """
    Determine the appropriate gateway for a tenant based on:
      1. Explicit override stored on the tenant  (tenant.preferred_gateway)
      2. Tenant's registered country             (ZA → PayFast, else Stripe)
      3. Django settings default                 (DEFAULT_PAYMENT_GATEWAY)

    Returns:
        str: 'payfast' | 'stripe'
    """
    # 1. Explicit preference stored on tenant model
    preferred = getattr(tenant, 'preferred_gateway', None)
    if preferred:
        return preferred.lower()

    # 2. Country-based routing
    country = getattr(tenant, 'country', None) or ''
    if country.upper() == 'ZA':
        return 'payfast'
    elif country:
        return 'stripe'

    # 3. Fall back to settings default
    return getattr(settings, 'DEFAULT_PAYMENT_GATEWAY', 'payfast')


def get_payment_gateway(gateway_name: str = None, tenant=None) -> PaymentGateway:
    """
    Factory — return the correct PaymentGateway instance.

    Args:
        gateway_name: Explicit override ('payfast' | 'stripe').
                      If None, auto-resolved from `tenant` or settings.
        tenant:       Tenant object used for auto-resolution.

    Returns:
        PaymentGateway instance
    """
    if gateway_name is None:
        if tenant is not None:
            gateway_name = resolve_gateway_for_tenant(tenant)
        else:
            gateway_name = getattr(settings, 'DEFAULT_PAYMENT_GATEWAY', 'payfast')

    registry = {
        'payfast': PayFastGateway,
        'stripe':  StripeGateway,
    }

    gateway_class = registry.get(gateway_name.lower())
    if gateway_class is None:
        raise PaymentGatewayError(
            f"Unknown payment gateway: '{gateway_name}'. "
            f"Available: {', '.join(registry.keys())}"
        )

    return gateway_class()


# ---------------------------------------------------------------------------
# High-level helpers (called from views / tasks)
# ---------------------------------------------------------------------------

def create_subscription_payment(subscription, gateway_name=None):
    """
    Create a hosted-checkout payment link for a subscription.
    Gateway is auto-selected from the tenant's country if not specified.

    Returns:
        dict: { 'payment_url': str, 'payment_id': str, 'gateway': str }
    """
    gateway = get_payment_gateway(
        gateway_name=gateway_name,
        tenant=subscription.tenant,
    )
    amount      = subscription.plan.price
    description = f"{subscription.plan.name} - {subscription.tenant.name}"
    return gateway.create_payment(subscription, amount, description)


def process_payment_callback(gateway_name: str, data: dict, **kwargs):
    """
    Dispatch an inbound payment callback / webhook to the correct gateway.

    Extra kwargs are forwarded to verify_payment (e.g. raw_payload,
    sig_header for Stripe, or source_ip for PayFast).

    Returns:
        dict: { 'status': str, ... }
    """
    gateway = get_payment_gateway(gateway_name)

    if gateway_name.lower() == 'payfast':
        payment_id = data.get('m_payment_id')
        return gateway.verify_payment(payment_id, data, **kwargs)

    elif gateway_name.lower() == 'stripe':
        return gateway.verify_payment(None, data, **kwargs)

    return {'status': 'error', 'error': f"Unhandled gateway: {gateway_name}"}


def cancel_tenant_subscription(subscription):
    """
    Cancel a subscription on the correct gateway and mark it cancelled locally.

    Returns:
        bool: True if successfully cancelled on the gateway (or no gateway ID existed).
    """
    gw_sub_id    = getattr(subscription, 'gateway_subscription_id', None)
    gateway_name = getattr(subscription, 'gateway', None) or resolve_gateway_for_tenant(subscription.tenant)
    gateway      = get_payment_gateway(gateway_name)

    success = True
    if gw_sub_id:
        success = gateway.cancel_subscription(gw_sub_id)

    if success:
        subscription.status     = 'CANCELLED'
        subscription.cancelled_at = timezone.now()
        subscription.save(update_fields=['status', 'cancelled_at'])
        logger.info("Subscription %s cancelled", subscription.id)

    return success