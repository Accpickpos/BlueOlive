"""
Point of Sale services.
Business logic for POS operations based on PointOfSale.pdf
"""
from django.db import transaction
from django.db.models import Sum, F, Q
from decimal import Decimal
from datetime import date, timedelta
import logging

from .models import (
    CashSale, CashSaleLine, Laybye, LaybyeLine, LaybyePayment,
    Quotation, QuotationLine, JobCard, JobCardLine, CashControl, Repair, Invoice, InvoiceLine
)
from apps.stock_control.models import StockItem, StockTransaction
from apps.debtors.models import Debtor
from .exceptions import (
    InvalidDocumentState, InsufficientStock, POSValidationException
)
from .calculation_service import CalculationService

logger = logging.getLogger(__name__)


class CashControlService:
    """
    Shared helper for updating the daily CashControl totals for a cashier.
    CashSaleService.update_cash_control() handles cash sales directly; every
    other till-affecting transaction (returns, receipts, credits, payouts,
    cashed cheques, laybyes) should post through here so the till reconciles.
    """

    @staticmethod
    def _get_or_create(control_date, cashier, station_number=1):
        control, _ = CashControl.objects.get_or_create(
            control_date=control_date, cashier=cashier, station_number=station_number
        )
        return control

    @staticmethod
    def record_cash_return(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(control_date, cashier, station_number)
        control.cash_refunds_count += 1
        control.cash_refunds_total += amount
        control.cash_refunds += amount
        control.save()
        return control

    @staticmethod
    def record_receipt(control_date, cashier, station_number, amount, tender_type='CASH'):
        control = CashControlService._get_or_create(control_date, cashier, station_number)
        control.receipts_count += 1
        control.receipts_total += amount
        if tender_type == 'CASH':
            control.cash_takings += amount
        elif tender_type == 'CHEQUE':
            control.cheque_takings += amount
        elif tender_type == 'SPEEDPOINT':
            control.speedpoint_takings += amount
        control.save()
        return control

    @staticmethod
    def record_credit_note(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(control_date, cashier, station_number)
        control.credits_count += 1
        control.credits_total += amount
        control.save()
        return control

    @staticmethod
    def record_payout(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(control_date, cashier, station_number)
        control.payouts_count += 1
        control.payouts_total += amount
        control.save()
        return control

    @staticmethod
    def record_cashed_cheque(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(control_date, cashier, station_number)
        control.cashed_cheques_count += 1
        control.cashed_cheques_total += amount
        control.save()
        return control

    @staticmethod
    def record_new_laybye(control_date, cashier, station_number, deposit_amount):
        control = CashControlService._get_or_create(control_date, cashier, station_number)
        control.new_laybyes_count += 1
        control.new_laybyes_total += deposit_amount
        control.cash_takings += deposit_amount
        control.save()
        return control

    @staticmethod
    def record_laybye_receipt(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(control_date, cashier, station_number)
        control.laybye_receipts_count += 1
        control.laybye_receipts_total += amount
        control.cash_takings += amount
        control.save()
        return control

    @staticmethod
    def record_laybye_cancel(control_date, cashier, station_number, refund_amount):
        control = CashControlService._get_or_create(control_date, cashier, station_number)
        control.cancelled_laybyes_count += 1
        control.cancelled_laybyes_total += refund_amount
        control.save()
        return control


class CashSaleService:
    """Service class for cash sale operations."""
    
    @staticmethod
    @transaction.atomic
    def post_cash_sale(cash_sale):
        """
        Post a cash sale - update stock and create movements.
        
        Args:
            cash_sale: CashSale instance
        
        Returns:
            CashSale: Updated cash sale
        
        Raises:
            InvalidDocumentState: If sale is already posted or cancelled
            InsufficientStock: If stock is insufficient
        """
        if cash_sale.is_posted:
            raise InvalidDocumentState(
                'Cash Sale', cash_sale.sale_number, 'POSTED', 'post'
            )
        
        if cash_sale.is_cancelled:
            raise InvalidDocumentState(
                'Cash Sale', cash_sale.sale_number, 'CANCELLED', 'post'
            )
        
        # Update stock for each line
        for line in cash_sale.lines.all():
            if line.stock_code:
                try:
                    stock_item = StockItem.objects.get(stock_code=line.stock_code)

                    # Check stock availability — manual §3.1 [311.htm]:
                    # "If No is selected [Allow Negative Quantities],
                    # Accpick will not allow a stock item with zero
                    # quantity on hand to be processed at Point of Sale."
                    # Previously this block ran unconditionally regardless
                    # of the per-item flag.
                    if not stock_item.allow_negative_quantities and stock_item.quantity_on_hand < line.quantity:
                        raise InsufficientStock(
                            stock_code=line.stock_code,
                            required=float(line.quantity),
                            available=float(stock_item.quantity_on_hand)
                        )

                    # Update quantity on hand
                    stock_item.quantity_on_hand -= line.quantity
                    
                    # Update sales statistics
                    stock_item.sales_mtd_quantity += line.quantity
                    stock_item.sales_mtd_value += line.line_total
                    stock_item.sales_ytd_quantity += line.quantity
                    stock_item.sales_ytd_value += line.line_total
                    stock_item.last_sale_date = cash_sale.sale_date
                    stock_item.save()
                    
                    # Create stock movement
                    StockTransaction.objects.create(
                        stock_item=stock_item,
                        transaction_type='SALE',
                        transaction_date=cash_sale.sale_date,
                        transaction_number=cash_sale.sale_number,
                        quantity_out=line.quantity,
                        quantity_balance=stock_item.quantity_on_hand,
                        unit_cost=line.cost_price,
                        unit_price=line.unit_price,
                        station_number=cash_sale.station_number
                    )
                    
                    logger.info(
                        f"Posted cash sale {cash_sale.sale_number}: "
                        f"stock {line.stock_code} reduced by {line.quantity}"
                    )
                    
                except StockItem.DoesNotExist:
                    logger.warning(
                        f"Stock item {line.stock_code} not found for sale {cash_sale.sale_number}"
                    )
                    # Non-stock item - continue without stock update
        
        # Mark as posted
        cash_sale.is_posted = True
        cash_sale.save()
        
        # Update cash control
        CashSaleService.update_cash_control(cash_sale)
        
        logger.info(f"Successfully posted cash sale {cash_sale.sale_number}")
        return cash_sale
    
    @staticmethod
    @transaction.atomic
    def cancel_cash_sale(cash_sale, reason=''):
        """
        Cancel a cash sale.
        
        Args:
            cash_sale: CashSale instance
            reason: Cancellation reason
        
        Returns:
            CashSale: Updated cash sale
        
        Raises:
            InvalidDocumentState: If already cancelled
        """
        if cash_sale.is_cancelled:
            raise InvalidDocumentState(
                'Cash Sale', cash_sale.sale_number, 'CANCELLED', 'cancel'
            )
        
        if cash_sale.is_posted:
            # Reverse stock movements
            for line in cash_sale.lines.all():
                if line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=line.stock_code)
                        
                        # Reverse quantity
                        stock_item.quantity_on_hand += line.quantity
                        stock_item.save()
                        
                        # Create reversing movement
                        StockTransaction.objects.create(
                            stock_item=stock_item,
                            transaction_type='RETURN',
                            transaction_date=date.today(),
                            transaction_number=f"CANC-{cash_sale.sale_number}",
                            reference=reason,
                            quantity_in=line.quantity,
                            quantity_balance=stock_item.quantity_on_hand,
                            unit_cost=line.cost_price,
                            unit_price=line.unit_price,
                            station_number=cash_sale.station_number
                        )
                        
                        logger.info(
                            f"Reversed stock for cancelled sale {cash_sale.sale_number}: "
                            f"{line.stock_code} increased by {line.quantity}"
                        )
                    except StockItem.DoesNotExist:
                        logger.warning(
                            f"Stock item {line.stock_code} not found for reversal"
                        )
        
        cash_sale.is_cancelled = True
        cash_sale.save()
        
        logger.info(f"Cancelled cash sale {cash_sale.sale_number}. Reason: {reason}")
        return cash_sale
    
    @staticmethod
    def update_cash_control(cash_sale):
        """Update daily cash control for cashier."""
        control, created = CashControl.objects.get_or_create(
            control_date=cash_sale.sale_date,
            cashier=cash_sale.cashier,
            station_number=cash_sale.station_number
        )
        
        control.cash_sales_count += 1
        control.cash_sales_total += cash_sale.total_amount
        
        # Update tender-specific totals
        for tender in cash_sale.tenders.all():
            if tender.tender_type == 'CASH':
                control.cash_takings += tender.amount
            elif tender.tender_type == 'CHEQUE':
                control.cheque_takings += tender.amount
            elif tender.tender_type == 'VOUCHER':
                control.voucher_takings += tender.amount
            elif tender.tender_type == 'SPEEDPOINT':
                control.speedpoint_takings += tender.amount
        
        control.save()
        return control
    
    @staticmethod
    def get_daily_summary(control_date, cashier=None, station_number=None):
        """Get daily sales summary."""
        filters = Q(control_date=control_date)
        if cashier:
            filters &= Q(cashier=cashier)
        if station_number:
            filters &= Q(station_number=station_number)
        
        controls = CashControl.objects.filter(filters)

        summary = controls.aggregate(
            total_sales=Sum('cash_sales_total'),
            total_refunds=Sum('cash_refunds_total'),
            total_receipts=Sum('receipts_total'),
            total_payouts=Sum('payouts_total'),
            total_credits=Sum('credits_total'),
            total_cashed_cheques=Sum('cashed_cheques_total'),
            total_new_laybyes=Sum('new_laybyes_total'),
            total_laybye_receipts=Sum('laybye_receipts_total'),
            total_cancelled_laybyes=Sum('cancelled_laybyes_total'),
            cash_takings=Sum('cash_takings'),
            cheque_takings=Sum('cheque_takings'),
            speedpoint_takings=Sum('speedpoint_takings')
        )

        zero = Decimal('0.00')
        return {
            'control_date': control_date,
            'total_sales': summary['total_sales'] or zero,
            'total_refunds': summary['total_refunds'] or zero,
            'total_receipts': summary['total_receipts'] or zero,
            'total_payouts': summary['total_payouts'] or zero,
            'total_credits': summary['total_credits'] or zero,
            'total_cashed_cheques': summary['total_cashed_cheques'] or zero,
            'total_new_laybyes': summary['total_new_laybyes'] or zero,
            'total_laybye_receipts': summary['total_laybye_receipts'] or zero,
            'total_cancelled_laybyes': summary['total_cancelled_laybyes'] or zero,
            'cash_expected': (
                (summary['total_sales'] or zero)
                + (summary['total_new_laybyes'] or zero)
                + (summary['total_laybye_receipts'] or zero)
                - (summary['total_refunds'] or zero)
                - (summary['total_payouts'] or zero)
                - (summary['total_cashed_cheques'] or zero)
            ),
            'cash_takings': summary['cash_takings'] or zero,
            'cheque_takings': summary['cheque_takings'] or zero,
            'speedpoint_takings': summary['speedpoint_takings'] or zero,
        }


class LaybyeService:
    """Service class for laybye operations."""
    
    @staticmethod
    @transaction.atomic
    def create_laybye(laybye_data, lines_data):
        """
        Create a new laybye with lines.
        
        Args:
            laybye_data: Dictionary with laybye header data
            lines_data: List of line item dictionaries
        
        Returns:
            Laybye: Created laybye instance
        
        Raises:
            POSValidationException: If validation fails
        """
        laybye = Laybye.objects.create(**laybye_data)
        
        total_amount = Decimal('0.00')
        
        for idx, line_data in enumerate(lines_data, start=1):
            line_data['line_number'] = idx
            
            # Calculate line totals using service
            try:
                line_calcs = CalculationService.calculate_line_totals(
                    quantity=line_data['quantity'],
                    unit_price=line_data['unit_price'],
                    discount_percentage=line_data.get('discount_percentage', Decimal('0.00')),
                    tax_code=line_data.get('tax_code', 1)
                )
                
                # line_total is excl-VAT here (LaybyeLine has its own separate
                # vat_amount field, same convention as InvoiceLine) — use
                # line_total_before_vat, not the VAT-inclusive line_total key.
                line_data['line_total'] = line_calcs['line_total_before_vat']
                line_data['vat_amount'] = line_calcs['vat_amount']

                LaybyeLine.objects.create(laybye=laybye, **line_data)
                total_amount += line_calcs['line_total']  # VAT-inclusive, correct for the laybye total
                
            except Exception as e:
                logger.error(f"Error creating laybye line {idx}: {str(e)}")
                raise POSValidationException(f"Error creating laybye line {idx}: {str(e)}")
        
        # Update laybye totals
        laybye.total_amount = total_amount
        laybye.balance_due = total_amount - laybye.deposit_amount
        laybye.amount_paid = laybye.deposit_amount
        laybye.save()
        
        logger.info(f"Created laybye {laybye.laybye_number} with {len(lines_data)} lines")
        return laybye
    
    @staticmethod
    @transaction.atomic
    def make_payment(laybye, amount, sales_area=None):
        """
        Make a payment on a laybye.
        
        Args:
            laybye: Laybye instance
            amount: Payment amount
            sales_area: Sales area (optional)
        
        Returns:
            LaybyePayment: Created payment record
        
        Raises:
            InvalidDocumentState: If laybye is not active
            POSValidationException: If payment amount is invalid
        """
        if laybye.status != 'ACTIVE':
            raise InvalidDocumentState(
                'Laybye', laybye.laybye_number, laybye.status, 'make_payment'
            )
        
        try:
            amount = Decimal(str(amount))
        except Exception:
            raise POSValidationException(f"Invalid payment amount: {amount}")
        
        if amount <= 0:
            raise POSValidationException("Payment amount must be positive")
        
        if amount > laybye.balance_due:
            raise POSValidationException(
                f"Payment amount {amount} exceeds balance due {laybye.balance_due}"
            )
        
        # Create payment record
        payment = LaybyePayment.objects.create(
            laybye=laybye,
            payment_date=date.today(),
            amount=amount,
            sales_area=sales_area
        )
        
        # Update laybye
        laybye.amount_paid += amount
        laybye.balance_due -= amount
        
        # Check if fully paid
        if laybye.balance_due <= 0:
            laybye.status = 'COMPLETED'
        
        laybye.save()
        
        logger.info(f"Payment of {amount} recorded on laybye {laybye.laybye_number}")
        return payment
    
    @staticmethod
    @transaction.atomic
    def cancel_laybye(laybye, retention_percentage=0):
        """
        Cancel a laybye and calculate refund.
        
        Args:
            laybye: Laybye instance
            retention_percentage: Percentage to retain (default 0%)
        
        Returns:
            Laybye: Updated laybye
        
        Raises:
            InvalidDocumentState: If already cancelled
            POSValidationException: If retention percentage is invalid
        """
        if laybye.status == 'CANCELLED':
            raise InvalidDocumentState(
                'Laybye', laybye.laybye_number, 'CANCELLED', 'cancel'
            )
        
        try:
            retention_percentage = Decimal(str(retention_percentage))
        except Exception:
            raise POSValidationException(f"Invalid retention percentage: {retention_percentage}")
        
        if not (0 <= retention_percentage <= 100):
            raise POSValidationException("Retention percentage must be between 0 and 100")
        
        # Calculate refund using service
        retention_amount = laybye.amount_paid * (retention_percentage / 100)
        refund_amount = laybye.amount_paid - retention_amount
        
        laybye.status = 'CANCELLED'
        laybye.retention_percentage = retention_percentage
        laybye.refund_amount = refund_amount
        laybye.save()
        
        logger.info(f"Cancelled laybye {laybye.laybye_number}. Refund: {refund_amount}")
        return laybye
    
    @staticmethod
    def check_expired_laybyes():
        """Check for and mark expired laybyes."""
        today = date.today()
        expired = Laybye.objects.filter(
            status='ACTIVE',
            expiry_date__lt=today
        )
        
        count = expired.update(status='EXPIRED')
        return count


class QuotationService:
    """Service class for quotation operations."""

    # NOTE: the real quotation->invoice conversion is convert_quotation_to_invoice
    # below (used by the API). A dead stub convert_to_invoice() previously lived
    # here too — same method name, different signature, never called anywhere
    # — removed to eliminate the two-competing-implementations trap.

    @staticmethod
    @transaction.atomic
    def convert_to_job_card(quotation):
        """Convert quotation to job card."""
        if quotation.status == 'JOB':
            raise ValueError("Quotation already converted to job card")
        
        # Create job card from quotation
        job_card = JobCard.objects.create(
            job_number=f"JOB-{quotation.quotation_number}",
            job_date=date.today(),
            customer_name=quotation.customer_name,
            address=quotation.address_line1,
            telephone=quotation.telephone,
            sales_area=quotation.sales_area
        )
        
        # Copy lines
        for q_line in quotation.lines.all():
            JobCardLine.objects.create(
                job_card=job_card,
                line_number=q_line.line_number,
                stock_code=q_line.stock_code,
                description=q_line.description,
                quantity=q_line.quantity,
                unit_price=q_line.unit_price,
                discount_percentage=q_line.discount_percentage,
                tax_code=q_line.tax_code,
                line_total=q_line.line_total,
                vat_amount=q_line.vat_amount,
                cost_price=q_line.cost_price
            )
        
        # Update quotation
        quotation.status = 'JOB'
        quotation.save()
        
        return job_card
    
    @staticmethod
    @transaction.atomic
    def convert_job_card_to_invoice(job_card, debtor):
        """
        Convert job card to customer invoice.
        
        Args:
            job_card: JobCard instance to convert
            debtor: Debtor instance (customer)
        
        Returns:
            Invoice: Created invoice
        
        Raises:
            ValueError: If job card cannot be converted
        """
        if job_card.status == 'CONVERTED_TO_INVOICE':
            raise ValueError("Job card already converted to invoice")
        
        if job_card.status == 'CANCELLED':
            raise ValueError("Cannot convert cancelled job card to invoice")
        
        if not debtor:
            raise ValueError("Debtor is required to create invoice. Please select a debtor.")
        
        # Generate invoice number (format: INV-YYYYMMDD-XXXXX)
        from django.utils import timezone
        today = timezone.now().date()
        invoice_count = Invoice.objects.filter(
            invoice_date=today
        ).count() + 1
        invoice_number = f"INV-{today.year}{today.month:02d}{today.day:02d}-{invoice_count:05d}"
        
        # Handle sales_area - get the code string (not the ForeignKey object)
        # Invoice.sales_area is a CharField(max_length=2), not a ForeignKey
        sales_area_code = '01'  # Default fallback
        if job_card.sales_area:
            # Convert the SalesArea number to a 2-digit string (e.g., 1 -> "01")
            sales_area_code = str(job_card.sales_area.number).zfill(2)
        else:
            # Try to get default sales area
            try:
                from apps.settings.models import SalesArea
                default_sales_area = SalesArea.objects.filter(is_active=True).first()
                if default_sales_area:
                    sales_area_code = str(default_sales_area.number).zfill(2)
            except Exception as e:
                logger.warning(f"Could not fetch default SalesArea: {e}")
        
        logger.debug(f"Using sales_area_code: {sales_area_code} for job card {job_card.job_number}")
        
        # Create invoice
        invoice = Invoice.objects.create(
            debtor=debtor,
            invoice_number=invoice_number,
            invoice_date=today,
            delivery_name=job_card.customer_name,
            delivery_address_line1=job_card.address,
            delivery_telephone=job_card.telephone,
            order_number=job_card.order_number,
            job_card_number=job_card.job_number,
            sales_area=sales_area_code,
            subtotal=round(job_card.subtotal, 2) if job_card.subtotal else Decimal('0.00'),
            vat_amount=round(job_card.vat_amount, 2) if job_card.vat_amount else Decimal('0.00'),
            total_amount=round(job_card.total_amount, 2) if job_card.total_amount else Decimal('0.00'),
            total_cost=round(job_card.total_cost, 2) if job_card.total_cost else Decimal('0.00'),
            gross_profit=round(job_card.gross_profit, 2) if job_card.gross_profit else Decimal('0.00'),
            status='DRAFT',
            is_posted=False
        )
        
        # Copy job card lines to invoice lines
        for job_line in job_card.lines.all():
            # Calculate line_cost from quantity * cost_price (if available)
            line_cost = (job_line.quantity * job_line.cost_price) if job_line.cost_price else Decimal('0.00')
            
            # Create invoice line - validation is now skipped in the model's save method
            InvoiceLine.objects.create(
                invoice=invoice,
                line_number=job_line.line_number,
                stock_code=job_line.stock_code,
                description=job_line.description,
                quantity=job_line.quantity,
                unit_price=job_line.unit_price,
                discount_percentage=job_line.discount_percentage,
                tax_code=job_line.tax_code,
                line_total=job_line.line_total,
                vat_amount=job_line.vat_amount,
                cost_price=job_line.cost_price,
                line_cost=line_cost,
                line_profit=job_line.line_profit
            )
        
        # Update job card status
        # Log all field lengths for debugging
        logger.debug(f"Job card field lengths before update:")
        logger.debug(f"  job_number: {len(job_card.job_number) if job_card.job_number else 0} (max 20)")
        logger.debug(f"  customer_name: {len(job_card.customer_name) if job_card.customer_name else 0} (max 200)")
        logger.debug(f"  address: {len(job_card.address) if job_card.address else 0} (max 1000)")
        logger.debug(f"  telephone: {len(job_card.telephone) if job_card.telephone else 0} (max 50)")
        logger.debug(f"  contact_person: {len(job_card.contact_person) if job_card.contact_person else 0} (max 100)")
        logger.debug(f"  order_number: {len(job_card.order_number) if job_card.order_number else 0} (max 50)")
        logger.debug(f"  registration_number: {len(job_card.registration_number) if job_card.registration_number else 0} (max 50)")
        logger.debug(f"  job_description: {len(job_card.job_description) if job_card.job_description else 0} (max ?)")
        logger.debug(f"  debtor_account_number: {len(job_card.debtor_account_number) if job_card.debtor_account_number else 0} (max 20)")
        logger.debug(f"  status: {len(job_card.status) if job_card.status else 0} (max 25)")
        logger.debug(f"  cancellation_reason: {len(job_card.cancellation_reason) if job_card.cancellation_reason else 0} (max ?)")
        
        # Truncate all string fields to their max_length to prevent database errors
        status_value = 'CONVERTED_TO_INVOICE'[:25]  # max_length is 25
        job_card.status = status_value
        
        # Truncate any potentially long string fields
        if job_card.job_number and len(job_card.job_number) > 20:
            job_card.job_number = job_card.job_number[:20]
        if job_card.customer_name and len(job_card.customer_name) > 200:
            job_card.customer_name = job_card.customer_name[:200]
        if job_card.address and len(job_card.address) > 1000:
            job_card.address = job_card.address[:1000]
        if job_card.telephone and len(job_card.telephone) > 50:
            job_card.telephone = job_card.telephone[:50]
        if job_card.contact_person and len(job_card.contact_person) > 100:
            job_card.contact_person = job_card.contact_person[:100]
        if job_card.order_number and len(job_card.order_number) > 50:
            job_card.order_number = job_card.order_number[:50]
        if job_card.registration_number and len(job_card.registration_number) > 50:
            job_card.registration_number = job_card.registration_number[:50]
        if job_card.job_description and len(job_card.job_description) > 2000:
            job_card.job_description = job_card.job_description[:2000]
        if job_card.debtor_account_number and len(job_card.debtor_account_number) > 20:
            job_card.debtor_account_number = job_card.debtor_account_number[:20]
        if job_card.cancellation_reason and len(job_card.cancellation_reason) > 500:
            job_card.cancellation_reason = job_card.cancellation_reason[:500]
        
        logger.debug(f"Updating job card {job_card.job_number} status to: {status_value}")
        
        try:
            # Use update_fields to avoid triggering full save signals that might cause issues
            job_card.save(update_fields=['status', 'updated_at'])
        except Exception as e:
            logger.error(f"Error updating job card status: {e}")
            logger.error(f"Job card fields: job_number={job_card.job_number}, status={job_card.status}")
            # Re-raise to maintain original error behavior
            raise
        
        logger.info(
            f"Converted job card {job_card.job_number} to invoice {invoice.invoice_number} "
            f"for debtor {debtor.dno}"
        )
        
        return invoice
    
    @transaction.atomic
    def convert_laybye_to_invoice(laybye, debtor):
        """
        Convert laybye to customer invoice.
        
        Args:
            laybye: Laybye instance to convert
            debtor: Debtor instance (customer)
        
        Returns:
            Invoice: Created invoice
        
        Raises:
            ValueError: If laybye cannot be converted
        """
        from apps.pos.models import LaybyeLine
        
        if laybye.status == 'CONVERTED_TO_INVOICE':
            raise ValueError("Laybye already converted to invoice")
        
        if laybye.status == 'CANCELLED':
            raise ValueError("Cannot convert cancelled laybye to invoice")
        
        if laybye.status == 'EXPIRED':
            raise ValueError("Cannot convert expired laybye to invoice")
        
        if not debtor:
            raise ValueError("Debtor is required to create invoice. Please select a debtor.")
        
        # Generate invoice number (format: INV-YYYYMMDD-XXXXX)
        from django.utils import timezone
        from apps.settings.models import SalesArea
        today = timezone.now().date()
        invoice_count = Invoice.objects.filter(
            invoice_date=today
        ).count() + 1
        invoice_number = f"INV-{today.year}{today.month:02d}{today.day:02d}-{invoice_count:05d}"
        
        # Handle sales_area - get the code string (not the ForeignKey object)
        # Invoice.sales_area is a CharField(max_length=2), not a ForeignKey
        sales_area_code = None
        if laybye.sales_area:
            sales_area_code = str(laybye.sales_area.number).zfill(2)
        else:
            default_sales_area = SalesArea.objects.filter(is_active=True).first()
            if default_sales_area:
                sales_area_code = str(default_sales_area.number).zfill(2)
        
        # Create invoice
        invoice = Invoice.objects.create(
            debtor=debtor,
            invoice_number=invoice_number,
            invoice_date=today,
            delivery_name=laybye.customer_name,
            delivery_address_line1=laybye.address_line1,
            delivery_address_line2=laybye.address_line2,
            delivery_address_line3=laybye.address_line3,
            delivery_telephone=laybye.telephone,
            sales_area=sales_area_code,
            subtotal=round(laybye.total_amount - laybye.vat_amount, 2) if laybye.total_amount else Decimal('0.00'),
            vat_amount=round(laybye.vat_amount, 2) if hasattr(laybye, 'vat_amount') and laybye.vat_amount else Decimal('0.00'),
            total_amount=round(laybye.total_amount, 2) if laybye.total_amount else Decimal('0.00'),
            total_cost=Decimal('0.00'),
            gross_profit=Decimal('0.00'),
            status='DRAFT',
            is_posted=False
        )
        
        # Copy laybye sale lines to invoice lines (only 'SP' = Sale type)
        laybye_lines = LaybyeLine.objects.filter(
            laybye=laybye, 
            transaction_type='SP'
        ).order_by('transaction_date', 'transaction_time')
        
        line_number = 1
        for laybye_line in laybye_lines:
            # Calculate line_cost from quantity * cost_price
            line_cost = (laybye_line.quantity * laybye_line.cost_price) if laybye_line.cost_price else Decimal('0.00')
            
            InvoiceLine.objects.create(
                invoice=invoice,
                line_number=line_number,
                stock_code=laybye_line.stock_code,
                description=laybye_line.description,
                quantity=laybye_line.quantity,
                unit_price=laybye_line.unit_price,
                discount_percentage=laybye_line.discount_percentage,
                tax_code=laybye_line.tax_code,
                line_total=laybye_line.line_total,
                vat_amount=laybye_line.vat_amount,
                cost_price=laybye_line.cost_price,
                line_cost=line_cost,
                line_profit=laybye_line.selling_price - laybye_line.cost_price if laybye_line.selling_price and laybye_line.cost_price else Decimal('0.00')
            )
            line_number += 1
        
        # Update laybye status
        laybye.status = 'CONVERTED_TO_INVOICE'
        laybye.save()
        
        logger.info(
            f"Converted laybye {laybye.laybye_number} to invoice {invoice.invoice_number} "
            f"for debtor {debtor.dno}"
        )
        
        return invoice
    
    @transaction.atomic
    def convert_quotation_to_invoice(quotation, debtor):
        """
        Convert quotation to customer invoice.
        
        Args:
            quotation: Quotation instance to convert
            debtor: Debtor instance (customer)
        
        Returns:
            Invoice: Created invoice
        
        Raises:
            ValueError: If quotation cannot be converted
        """
        if quotation.status == 'CONVERTED_TO_INVOICE':
            raise ValueError("Quotation already converted to invoice")
        
        if quotation.status == 'CANCELLED':
            raise ValueError("Cannot convert cancelled quotation to invoice")
        
        if quotation.status == 'EXPIRED':
            raise ValueError("Cannot convert expired quotation to invoice")
        
        if not debtor:
            raise ValueError("Debtor is required to create invoice. Please select a debtor.")
        
        # Generate invoice number (format: INV-YYYYMMDD-XXXXX)
        from django.utils import timezone
        from apps.settings.models import SalesArea
        today = timezone.now().date()
        invoice_count = Invoice.objects.filter(
            invoice_date=today
        ).count() + 1
        invoice_number = f"INV-{today.year}{today.month:02d}{today.day:02d}-{invoice_count:05d}"
        
        # Handle sales_area - get the code string (not the ForeignKey object)
        # Invoice.sales_area is a CharField(max_length=2), not a ForeignKey
        sales_area_code = None
        if quotation.sales_area:
            sales_area_code = str(quotation.sales_area.number).zfill(2)
        else:
            default_sales_area = SalesArea.objects.filter(is_active=True).first()
            if default_sales_area:
                sales_area_code = str(default_sales_area.number).zfill(2)
        
        # Create invoice
        invoice = Invoice.objects.create(
            debtor=debtor,
            invoice_number=invoice_number,
            invoice_date=today,
            delivery_name=quotation.customer_name,
            delivery_address_line1=quotation.address_line1,
            delivery_address_line2=quotation.address_line2,
            delivery_address_line3=quotation.address_line3,
            delivery_telephone=quotation.telephone,
            sales_area=sales_area_code,
            subtotal=round(quotation.subtotal, 2) if quotation.subtotal else Decimal('0.00'),
            vat_amount=round(quotation.vat_amount, 2) if quotation.vat_amount else Decimal('0.00'),
            total_amount=round(quotation.total_amount, 2) if quotation.total_amount else Decimal('0.00'),
            total_cost=Decimal('0.00'),
            gross_profit=round(quotation.gross_profit, 2) if quotation.gross_profit else Decimal('0.00'),
            status='DRAFT',
            is_posted=False
        )
        
        # Copy quotation lines to invoice lines
        for quote_line in quotation.lines.all():
            # Calculate line_cost from quantity * cost_price
            line_cost = (quote_line.quantity * quote_line.cost_price) if quote_line.cost_price else Decimal('0.00')
            
            InvoiceLine.objects.create(
                invoice=invoice,
                line_number=quote_line.line_number,
                stock_code=quote_line.stock_code,
                description=quote_line.description,
                quantity=quote_line.quantity,
                unit_price=quote_line.unit_price,
                discount_percentage=quote_line.discount_percentage,
                tax_code=quote_line.tax_code,
                line_total=quote_line.line_total,
                vat_amount=quote_line.vat_amount,
                cost_price=quote_line.cost_price,
                line_cost=line_cost,
                line_profit=(quote_line.unit_price - quote_line.cost_price) * quote_line.quantity if quote_line.unit_price and quote_line.cost_price else Decimal('0.00')
            )
        
        # Update quotation status
        quotation.status = 'CONVERTED_TO_INVOICE'
        quotation.save()
        
        logger.info(
            f"Converted quotation {quotation.quotation_number} to invoice {invoice.invoice_number} "
            f"for debtor {debtor.dno}"
        )
        
        return invoice


class RepairService:
    """Service class for repair voucher operations."""
    
    @staticmethod
    @transaction.atomic
    def issue_to_supplier(repair, supplier_account, transport_mode=''):
        """Issue repair to supplier."""
        if repair.status != 'C':
            raise ValueError("Repair must be in CREATED status to issue")
        
        repair.supplier_number = int(supplier_account) if str(supplier_account).isdigit() else None
        repair.date_sent = date.today()
        repair.status = 'I'
        repair.save()
        
        return repair
    
    @staticmethod
    @transaction.atomic
    def receive_from_supplier(repair, repair_cost, supplier_invoice=''):
        """Receive repaired item from supplier."""
        if repair.status != 'I':
            raise ValueError("Repair must be in ISSUED status to receive")
        
        repair.date_returned = date.today()
        repair.repair_cost = repair_cost
        repair.status = 'R'
        repair.save()
        
        return repair
    
    @staticmethod
    @transaction.atomic
    def invoice_customer(repair):
        """Mark repair as invoiced."""
        if repair.status != 'R':
            raise ValueError("Repair must be RECEIVED before invoicing")
        
        # This would create an invoice for the customer
        # Implementation depends on invoice creation logic
        
        repair.status = 'V'
        repair.save()
        
        return repair