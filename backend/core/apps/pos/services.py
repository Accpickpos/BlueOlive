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
    CashSale, CashSaleLine, Laybye, LaybyeLine, LaybyelPayment,
    Quotation, QuotationLine, JobCard, JobCardLine, CashControl, Repair
)
from apps.stock_control.models import StockItem, StockTransaction
from .exceptions import (
    InvalidDocumentState, InsufficientStock, POSValidationException
)
from .calculation_service import CalculationService

logger = logging.getLogger(__name__)


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
                    
                    # Check stock availability
                    if stock_item.quantity_on_hand < line.quantity:
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
            cash_takings=Sum('cash_takings'),
            cheque_takings=Sum('cheque_takings'),
            speedpoint_takings=Sum('speedpoint_takings')
        )
        
        return {
            'control_date': control_date,
            'total_sales': summary['total_sales'] or Decimal('0.00'),
            'total_refunds': summary['total_refunds'] or Decimal('0.00'),
            'total_receipts': summary['total_receipts'] or Decimal('0.00'),
            'total_payouts': summary['total_payouts'] or Decimal('0.00'),
            'cash_expected': (summary['total_sales'] or Decimal('0.00')) - 
                           (summary['total_refunds'] or Decimal('0.00')) -
                           (summary['total_payouts'] or Decimal('0.00')),
            'cash_takings': summary['cash_takings'] or Decimal('0.00'),
            'cheque_takings': summary['cheque_takings'] or Decimal('0.00'),
            'speedpoint_takings': summary['speedpoint_takings'] or Decimal('0.00')
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
                
                line_data['line_total'] = line_calcs['line_total']
                line_data['vat_amount'] = line_calcs['vat_amount']
                
                LaybyeLine.objects.create(laybye=laybye, **line_data)
                total_amount += line_calcs['line_total']
                
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
            LaybyelPayment: Created payment record
        
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
        payment = LaybyelPayment.objects.create(
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
    
    @staticmethod
    @transaction.atomic
    def convert_to_invoice(quotation, debtor):
        """Convert quotation to invoice."""
        if quotation.status == 'INVOICED':
            raise ValueError("Quotation already converted to invoice")
        
        # This would create an invoice in the debtors app
        # Implementation depends on invoice creation logic
        
        quotation.status = 'INVOICED'
        quotation.save()
        
        return quotation
    
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
            address=quotation.address,
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


class RepairService:
    """Service class for repair voucher operations."""
    
    @staticmethod
    @transaction.atomic
    def issue_to_supplier(repair, supplier_account, transport_mode=''):
        """Issue repair to supplier."""
        if repair.status != 'CREATED':
            raise ValueError("Repair must be in CREATED status to issue")
        
        repair.supplier_account = supplier_account
        repair.date_sent = date.today()
        repair.transport_mode = transport_mode
        repair.status = 'ISSUED'
        repair.save()
        
        return repair
    
    @staticmethod
    @transaction.atomic
    def receive_from_supplier(repair, repair_cost, supplier_invoice=''):
        """Receive repaired item from supplier."""
        if repair.status != 'ISSUED':
            raise ValueError("Repair must be in ISSUED status to receive")
        
        repair.date_repaired = date.today()
        repair.repair_cost = repair_cost
        repair.supplier_invoice_number = supplier_invoice
        repair.status = 'RECEIVED'
        repair.save()
        
        return repair
    
    @staticmethod
    @transaction.atomic
    def invoice_customer(repair):
        """Mark repair as invoiced."""
        if repair.status != 'RECEIVED':
            raise ValueError("Repair must be RECEIVED before invoicing")
        
        # This would create an invoice for the customer
        # Implementation depends on invoice creation logic
        
        repair.status = 'INVOICED'
        repair.save()
        
        return repair