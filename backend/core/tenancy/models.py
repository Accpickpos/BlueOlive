# tenancy/models.py
from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class EncryptedCharField(models.CharField):
    """
    A CharField that encrypts/decrypts values automatically.
    """

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return signing.loads(value)
        except signing.BadSignature:
            return value  # Return as-is if decryption fails

    def to_python(self, value):
        if value is None:
            return value
        return str(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        return signing.dumps(str(value))


# ============================================================================
# SUBSCRIPTION MODELS
# ============================================================================


class SubscriptionPlan(models.Model):
    """
    Pricing tiers for tenant subscriptions.
    Defines what features and limits each plan has.
    """

    BILLING_PERIOD_CHOICES = [
        (30, "Monthly"),
        (90, "Quarterly"),
        (365, "Yearly"),
    ]

    name = models.CharField(
        max_length=100, help_text="Plan name (e.g., Starter, Professional)"
    )
    slug = models.SlugField(unique=True, help_text="URL-friendly plan identifier")
    description = models.TextField(blank=True, help_text="Plan description")

    # Pricing
    price = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Price in ZAR"
    )
    currency = models.CharField(
        max_length=3, default="ZAR", help_text="Currency code (ISO 4217)"
    )
    setup_fee = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="One-time setup fee"
    )
    billing_period_days = models.PositiveIntegerField(
        choices=BILLING_PERIOD_CHOICES, default=30, help_text="Billing cycle in days"
    )

    # Limits
    max_shops = models.PositiveIntegerField(
        default=1, help_text="Maximum number of shops allowed"
    )
    max_users = models.PositiveIntegerField(
        default=5, help_text="Maximum number of users allowed"
    )
    max_invoices_per_month = models.PositiveIntegerField(
        default=100, help_text="Maximum invoices per month"
    )

    # Features (JSON field for feature flags)
    features = models.JSONField(
        default=dict,
        help_text='Feature flags as JSON (e.g., {"pos": true, "debtors": true})',
    )

    # Settings
    is_active = models.BooleanField(
        default=True, help_text="Whether this plan is available for new subscriptions"
    )
    is_trial = models.BooleanField(
        default=False, help_text="Is this a free trial plan?"
    )
    sort_order = models.PositiveIntegerField(
        default=0, help_text="Display order in pricing tables"
    )

    # Stripe Integration
    stripe_price_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Stripe price ID for this plan (cached after first use)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription_plans"
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        ordering = ["sort_order", "price"]

    def __str__(self):
        return f"{self.name} (R{self.price}/{self.get_billing_period_days_display()})"


class Subscription(models.Model):
    """
    Active subscription for a tenant.
    Tracks the subscription status, billing period, and limits.
    """

    STATUS_CHOICES = [
        ("TRIAL", "Trial"),
        ("ACTIVE", "Active"),
        ("PAST_DUE", "Past Due"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
        ("SUSPENDED", "Suspended"),
    ]

    tenant = models.OneToOneField(
        "Tenant", on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(
        SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="TRIAL")

    # Dates
    start_date = models.DateField(help_text="Subscription start date")
    end_date = models.DateField(
        help_text="Subscription end date (current billing period)"
    )
    trial_end_date = models.DateField(
        null=True, blank=True, help_text="Free trial end date"
    )
    cancelled_at = models.DateTimeField(
        null=True, blank=True, help_text="When subscription was cancelled"
    )

    # Auto-renewal
    auto_renew = models.BooleanField(
        default=True, help_text="Auto-renew subscription at end of period"
    )

    # Usage tracking
    current_period_start = models.DateField(null=True, blank=True)
    current_period_end = models.DateField(null=True, blank=True)
    invoices_this_period = models.PositiveIntegerField(default=0)

    # Gateway integration
    gateway_customer_id = models.CharField(
        max_length=200, blank=True, help_text="Payment gateway customer ID"
    )
    gateway_subscription_id = models.CharField(
        max_length=200, blank=True, help_text="Payment gateway subscription ID"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscriptions"
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name} ({self.get_status_display()})"

    @property
    def is_active(self):
        """Check if subscription is currently active (not expired, not cancelled)."""
        return self.status in ["TRIAL", "ACTIVE", "PAST_DUE"]

    @property
    def is_trial(self):
        """Check if subscription is in trial period."""
        if self.status == "TRIAL" and self.trial_end_date:
            return timezone.now().date() <= self.trial_end_date
        return False

    @property
    def is_expired(self):
        """Check if subscription has expired."""
        return timezone.now().date() > self.end_date

    @property
    def days_remaining(self):
        """Days remaining in current billing period."""
        if self.is_expired:
            return 0
        delta = self.end_date - timezone.now().date()
        return max(0, delta.days)

    @property
    def can_access(self):
        """Check if tenant can access the system based on subscription."""
        if self.status == "SUSPENDED":
            return False
        if self.status == "EXPIRED":
            return False
        return True


class SubscriptionPayment(models.Model):
    """
    Payment records for tenant subscriptions.
    Tracks all payment attempts and their status.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("SUCCEEDED", "Succeeded"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
        ("VOIDED", "Voided"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("CREDIT_CARD", "Credit Card"),
        ("DEBIT_CARD", "Debit Card"),
        ("EFT", "Electronic Funds Transfer"),
        ("PAYFAST", "PayFast"),
        ("STRIPE", "Stripe"),
        ("YOCO", "Yoco"),
        ("MANUAL", "Manual Payment"),
    ]

    subscription = models.ForeignKey(
        Subscription, on_delete=models.CASCADE, related_name="payments"
    )

    # Amount
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Payment amount in ZAR"
    )
    currency = models.CharField(max_length=3, default="ZAR")

    # Payment details
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    # Gateway reference
    gateway_payment_id = models.CharField(
        max_length=200, blank=True, help_text="Payment gateway transaction ID"
    )
    gateway_reference = models.CharField(
        max_length=200, blank=True, help_text="Payment gateway reference"
    )
    gateway_response = models.JSONField(
        default=dict, blank=True, help_text="Full gateway response"
    )

    # Dates
    paid_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)

    # Description
    description = models.CharField(max_length=500, blank=True)

    # Invoice
    invoice_number = models.CharField(
        max_length=50, blank=True, help_text="Invoice/receipt number"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subscription_payments"
        verbose_name = "Subscription Payment"
        verbose_name_plural = "Subscription Payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"R{self.amount} - {self.get_status_display()} - {self.subscription.tenant.name}"


class Tenant(models.Model):
    SETUP_STATUS_CHOICES = [
        ("pending", "Pending Setup"),
        ("db_ready", "Database Ready"),
        ("ready", "Ready for Use"),
        ("failed", "Setup Failed"),
    ]

    name = models.CharField(max_length=200, unique=True)  # Company name
    slug = models.SlugField(unique=True)
    subdomain = models.CharField(
        max_length=100,
        unique=True,
        default="default",
        help_text="Subdomain for tenant access, e.g., 'tenant1'",
    )

    # Company Information (tenant-level)
    company_name = models.CharField(
        max_length=200, blank=True, help_text="Company name for documents"
    )
    company_address = models.TextField(
        blank=True, help_text="Company address for documents"
    )
    phone = models.CharField(max_length=20, default="")
    email = models.EmailField(max_length=150, default="")
    vat_number = models.CharField(
        max_length=50, blank=True, help_text="VAT registration number"
    )
    registration_number = models.CharField(
        max_length=50, blank=True, help_text="Company registration number"
    )

    # Financial Settings (tenant-level)
    currency_symbol = models.CharField(
        max_length=10, default="R", help_text="Currency symbol"
    )
    currency_code = models.CharField(
        max_length=3, default="ZAR", help_text="Currency code (ISO 4217)"
    )
    decimal_places = models.PositiveIntegerField(
        default=2, help_text="Decimal places for currency"
    )
    default_interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text="Default interest rate (%)"
    )
    charge_interest_on_overdue = models.BooleanField(
        default=False, help_text="Charge interest on overdue accounts"
    )
    financial_year_start_month = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month the financial year starts (1-12)",
    )

    # Database settings
    db_name = models.CharField(max_length=200)
    db_user = models.CharField(max_length=200, default="postgres")
    db_password = EncryptedCharField(max_length=200)  # Encrypted field
    db_host = models.CharField(max_length=200, default="postgres")
    db_port = models.IntegerField(default=5432)
    is_active = models.BooleanField(
        default=True, help_text="Whether this tenant is active"
    )
    setup_status = models.CharField(
        max_length=20,
        choices=SETUP_STATUS_CHOICES,
        default="pending",
        help_text="Status of tenant database/signup provisioning",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    tenant_control = models.BooleanField(default=True)

    # Payment Gateway Settings
    preferred_gateway = models.CharField(
        max_length=20,
        blank=True,
        choices=[("payfast", "PayFast"), ("stripe", "Stripe")],
        help_text="Preferred payment gateway for this tenant",
    )
    country = models.CharField(
        max_length=2,
        blank=True,
        help_text="ISO 2-letter country code (e.g., ZA, US) - used for payment gateway selection",
    )
    stripe_customer_id = models.CharField(
        max_length=100, blank=True, help_text="Stripe customer ID for this tenant"
    )

    # Optional per-tenant addons (see settings.OPTIONAL_ADDON_APPS). Only a
    # subset of SHOP_APP_LABELS - everything else is mandatory core and always
    # migrated regardless of this list.
    enabled_addons = models.JSONField(
        default=list,
        blank=True,
        help_text="Subset of settings.OPTIONAL_ADDON_APPS enabled for this tenant",
    )

    # Stock Consolidation (inter-branch stock transfers, apps.stock_control
    # BranchTransfer/BranchTransferItem/BranchTransferInvoice) is a
    # sub-feature of the mandatory stock_control app, not a whole optional
    # app - so it gets its own flag rather than living in enabled_addons.
    enable_stock_consolidation = models.BooleanField(
        default=True,
        help_text="Allow inter-branch stock transfers (Stock Consolidation) for this tenant",
    )

    class Meta:
        verbose_name = "Tenant"

    @property
    def db_alias(self):
        return f"tenant_{self.id}"

    def clean(self):
        if not self.subdomain:
            raise ValidationError("Subdomain is required for tenant isolation.")

        from django.conf import settings as django_settings

        allowed = set(getattr(django_settings, "OPTIONAL_ADDON_APPS", []))
        enabled = set(self.enabled_addons or [])
        unknown = enabled - allowed
        if unknown:
            raise ValidationError(
                f"Unknown addon(s): {', '.join(sorted(unknown))}. "
                f"Must be a subset of {sorted(allowed)}."
            )

        dependencies = getattr(django_settings, "ADDON_DEPENDENCIES", {})
        for addon, required in dependencies.items():
            if addon in enabled:
                missing = [r for r in required if r not in enabled]
                if missing:
                    raise ValidationError(
                        f"Addon '{addon}' requires {missing} to also be enabled."
                    )

    def __str__(self):
        return self.name


class Shop(models.Model):
    """
    Represents a shop under a tenant.
    The actual shop data tables live in the tenant DB, in a schema named `schema_name`.
    """

    SETUP_STATUS_CHOICES = [
        ("pending", "Pending Setup"),
        ("ready", "Ready for Use"),
        ("failed", "Setup Failed"),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=200)
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Shop code (e.g., MS001)",
        null=True,
        blank=True,
    )
    address = models.TextField(
        blank=True, null=True, help_text="Physical address of the shop"
    )
    phone = models.CharField(
        max_length=20, blank=True, null=True, help_text="Shop phone number"
    )
    email = models.EmailField(
        blank=True, null=True, help_text="Shop email address for documents"
    )
    logo = models.ImageField(
        upload_to="shop_logos/",
        blank=True,
        null=True,
        help_text="Shop logo for invoices and PDFs",
    )
    schema_name = models.CharField(max_length=100, unique=True)
    subdomain = models.CharField(
        max_length=100,
        blank=True,
        help_text="Subdomain for shop access, e.g., 'downtown'",
    )
    description = models.TextField(blank=True, null=True)
    is_head_office = models.BooleanField(default=False)
    is_active = models.BooleanField(
        default=True, help_text="Whether this shop is active"
    )
    setup_status = models.CharField(
        max_length=20,
        choices=SETUP_STATUS_CHOICES,
        default="pending",
        help_text="Status of shop schema setup",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    tenant_control = True

    class Meta:
        verbose_name = "Shop"
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "is_head_office"],
                condition=models.Q(is_head_office=True),
                name="unique_head_office_per_tenant",
            ),
            models.UniqueConstraint(
                fields=["tenant", "subdomain"], name="unique_subdomain_per_tenant"
            ),
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"

    def save(self, *args, **kwargs):
        from django.utils.text import slugify

        # Ensure no other head office for this tenant
        if self.is_head_office:
            Shop.objects.filter(tenant=self.tenant, is_head_office=True).exclude(
                pk=self.pk
            ).update(is_head_office=False)

        # Auto-generate subdomain if not provided
        if not self.subdomain:
            subdomain = slugify(self.name)

            # Handle edge case: empty slug (shop name with only special characters)
            if not subdomain:
                subdomain = f"shop-{self.id if self.id else 'new'}"

            # Ensure uniqueness within tenant
            original_subdomain = subdomain
            counter = 1
            while (
                Shop.objects.filter(tenant=self.tenant, subdomain=subdomain)
                .exclude(pk=self.pk)
                .exists()
            ):
                subdomain = f"{original_subdomain}-{counter}"
                counter += 1

            self.subdomain = subdomain

        super().save(*args, **kwargs)


class ShopConfiguration(models.Model):
    """
    Per-shop configuration for period-end processes.
    Stored in the tenant database (public), not in shop schemas.
    """

    shop = models.OneToOneField(
        Shop, on_delete=models.CASCADE, related_name="configuration"
    )

    # === PERIOD END TRACKING ===
    last_day_end_date = models.DateField(
        null=True, blank=True, help_text="Date of last successful day-end process"
    )
    last_month_end_date = models.DateField(
        null=True, blank=True, help_text="Date of last successful month-end process"
    )
    last_year_end_date = models.DateField(
        null=True, blank=True, help_text="Date of last successful year-end process"
    )

    # === AUTOMATED SCHEDULING SETTINGS ===
    # Day-end scheduling
    enable_auto_day_end = models.BooleanField(
        default=False, help_text="Enable automatic day-end process"
    )
    day_end_time = models.TimeField(
        default="23:59", help_text="Time to run automatic day-end (HH:MM)"
    )
    day_end_day_of_week = models.JSONField(
        default=list, help_text="Days of week to run day-end [0=Mon, 6=Sun]"
    )

    # Month-end scheduling
    enable_auto_month_end = models.BooleanField(
        default=False, help_text="Enable automatic month-end process"
    )
    month_end_day = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of month to run month-end (1-28)",
    )
    month_end_time = models.TimeField(
        default="23:00", help_text="Time to run automatic month-end (HH:MM)"
    )

    # Year-end scheduling
    enable_auto_year_end = models.BooleanField(
        default=False, help_text="Enable automatic year-end process"
    )
    year_end_month = models.PositiveIntegerField(
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month to run year-end (1-12)",
    )
    year_end_day = models.PositiveIntegerField(
        default=31,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of month to run year-end",
    )
    year_end_time = models.TimeField(
        default="22:00", help_text="Time to run automatic year-end (HH:MM)"
    )

    # === ACCOUNTING PERIOD ===
    current_financial_year = models.PositiveIntegerField(
        default=2024, help_text="Current financial year (e.g., 2024)"
    )
    current_period = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Current accounting period (1-12)",
    )

    class Meta:
        db_table = "shop_configuration"
        verbose_name = "Shop Configuration"
        verbose_name_plural = "Shop Configurations"

    def __str__(self):
        return f"Config - {self.shop.name}"


# Import AuditLog from audit.py to make it accessible
from tenancy.audit import AuditLog  # noqa: E402, F401
