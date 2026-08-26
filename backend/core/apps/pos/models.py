"""
Point of Sale models.
Based on the PointOfSale.pdf documentation.
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.settings.models import TimeStampedModel, SalesArea
from apps.debtors.models import Debtor
from apps.stock_control.models import StockItem
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date


class Invoice(TimeStampedModel):
    """
    Customer Invoice with State Machine Workflow
    
    Manages invoice lifecycle from draft → posted → paid/overdue
    """
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('POSTED', 'Posted'),
        ('PAID', 'Paid'),
        ('PARTIAL_PAID', 'Partially Paid'),
        ('OVERDUE', 'Overdue'),
        ('CANCELLED', 'Cancelled'),
        ('VOID', 'Void'),
    ]
    
    # ==========================================
    # IDENTIFICATION & DATES
    # ==========================================
    
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Invoice Number"
    )
    
    invoice_date = models.DateField(
        db_index=True,
        help_text="Invoice Date"
    )
    
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Payment Due Date"
    )
    
    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="Customer/Debtor"
    )
    
    # ==========================================
    # DELIVERY & ORDER INFORMATION
    # ==========================================
    
    delivery_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Delivery Name"
    )
    
    delivery_address_line1 = models.CharField(
        max_length=200,
        blank=True,
        help_text="Delivery Address Line 1"
    )
    
    delivery_address_line2 = models.CharField(
        max_length=200,
        blank=True,
        help_text="Delivery Address Line 2"
    )
    
    delivery_telephone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Delivery Telephone"
    )
    
    order_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Customer Order Number"
    )
    
    customer_reference = models.CharField(
        max_length=50,
        blank=True,
        help_text="Customer Reference"
    )
    
    job_card_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Job Card Number"
    )
    
    sales_area = models.CharField(
        max_length=2,
        blank=True,
        null=True,
        help_text="Sales Area Code"
    )
    
    # ==========================================
    # FINANCIAL TOTALS
    # ==========================================
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Subtotal (excl. VAT)"
    )
    
    discount_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total Discount Amount"
    )
    
    vat_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="VAT Amount (14%)"
    )
    
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total Amount (incl. VAT)"
    )
    
    # ==========================================
    # COST & PROFIT
    # ==========================================
    
    total_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total Cost Price"
    )
    
    gross_profit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Gross Profit (Total - Cost)"
    )
    
    # ==========================================
    # STATUS & WORKFLOW
    # ==========================================
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT',
        db_index=True,
        help_text="Invoice Status"
    )
    
    is_posted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Posted to accounts flag"
    )
    
    posted_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date posted to accounts"
    )
    
    # ==========================================
    # PAYMENT TRACKING
    # ==========================================
    
    amount_paid = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Amount Paid"
    )
    
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date Fully Paid"
    )
    
    # ==========================================
    # METADATA
    # ==========================================
    
    created_by = models.CharField(
        max_length=50,
        blank=True,
        help_text="User who created invoice"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Internal Notes"
    )
    
    class Meta:
        ordering = ['-invoice_date', '-invoice_number']
        verbose_name = 'Invoice'
        verbose_name_plural = 'Invoices'
        indexes = [
            models.Index(fields=['debtor', '-invoice_date'], name='idx_inv_deb_date'),
            models.Index(fields=['is_posted'], name='idx_inv_posted'),
            models.Index(fields=['status'], name='idx_inv_status'),
            models.Index(fields=['invoice_date'], name='idx_inv_date'),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.debtor.name}"
    
    def clean(self):
        """Validate invoice data and state transitions."""
        errors = {}
        
        # Cannot modify posted invoices (except status/payment)
        if self.pk and self.is_posted:
            original = Invoice.objects.get(pk=self.pk)
            if (original.is_posted and 
                any([
                    self.subtotal != original.subtotal,
                    self.total_amount != original.total_amount,
                    self.debtor_id != original.debtor_id
                ])):
                errors['is_posted'] = 'Cannot modify financial details of posted invoices.'
        
        # Amount paid cannot exceed total
        if self.amount_paid > self.total_amount:
            errors['amount_paid'] = 'Amount paid cannot exceed total invoice amount.'
        
        # Amounts must be non-negative
        if self.subtotal < 0:
            errors['subtotal'] = 'Subtotal cannot be negative.'
        
        if self.total_amount < 0:
            errors['total_amount'] = 'Total amount cannot be negative.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Auto-calculate due date if not set."""
        if not self.due_date and self.debtor and self.invoice_date:
            from datetime import timedelta
            # Use debtor.terms for payment terms (default 30 days if not set)
            payment_terms_days = getattr(self.debtor, 'terms', 30) or 30
            self.due_date = self.invoice_date + timedelta(days=payment_terms_days)
        
        # Skip Django validation for this save to avoid Decimal precision issues
        super(Invoice, self).save(*args, **kwargs)
    
    # ==========================================
    # PROPERTIES
    # ==========================================
    
    @property
    def balance_due(self):
        """Calculate outstanding balance."""
        return self.total_amount - self.amount_paid
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue."""
        if not self.due_date:
            return False
        return (self.due_date < date.today() and 
                self.balance_due > 0 and 
                self.status not in ['PAID', 'CANCELLED', 'VOID'])
    
    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days
    
    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.subtotal == 0:
            return Decimal('0.00')
        return (self.gross_profit / self.subtotal) * 100
    
    # ==========================================
    # STATE MACHINE METHODS
    # ==========================================
    
    def can_be_posted(self):
        """Check if invoice can be posted."""
        return (self.status == 'DRAFT' and 
                self.total_amount > 0 and 
                self.lines.exists())
    
    def can_be_cancelled(self):
        """Check if invoice can be cancelled."""
        return self.status in ['DRAFT', 'POSTED'] and self.amount_paid == 0
    
    def can_be_voided(self):
        """Check if invoice can be voided."""
        return self.is_posted and self.amount_paid == 0
    
    def post(self, posted_by=''):
        """
        Post invoice to accounts.
        
        Args:
            posted_by: Username of person posting
        
        Raises:
            ValidationError: If invoice cannot be posted
        """
        if not self.can_be_posted():
            raise ValidationError(
                f'Invoice cannot be posted (current status: {self.status})'
            )
        
        self.status = 'POSTED'
        self.is_posted = True
        self.posted_date = date.today()
        
        if posted_by:
            if not self.created_by:
                self.created_by = posted_by
        
        self.save()
        
        # Create debtor transaction. transaction_number is a 6-char field
        # (legacy DTRANO sequence) — invoice_number (e.g. "INV-20260729-00001")
        # doesn't fit it, so generate the same per-debtor sequence
        # DebtorService.post_debtran uses rather than truncating and risking
        # a collision.
        from apps.debtors.models import DebtorTransaction
        last_tran = DebtorTransaction.objects.filter(debtor=self.debtor).order_by('-transaction_number').first()
        try:
            new_dtrano = str(int(last_tran.transaction_number) + 1).zfill(6) if last_tran else '000001'
        except (ValueError, TypeError):
            new_dtrano = '000001'

        DebtorTransaction.objects.create(
            debtor=self.debtor,
            transaction_number=new_dtrano,
            transaction_type='IN',
            transaction_date=self.invoice_date,
            subtotal=self.subtotal,
            vat_amount=self.vat_amount,
            total_amount=self.total_amount,
            status='posted',
            created_by=posted_by
        )
    
    def mark_as_paid(self, payment_date=None, amount=None):
        """
        Mark invoice as fully paid.
        
        Args:
            payment_date: Date of payment (defaults to today)
            amount: Payment amount (defaults to balance due)
        """
        if self.status in ['CANCELLED', 'VOID']:
            raise ValidationError(f'Cannot mark {self.status} invoice as paid')
        
        self.amount_paid = amount or self.total_amount
        self.paid_date = payment_date or date.today()
        self.status = 'PAID'
        self.save()
    
    def apply_payment(self, amount, payment_date=None):
        """
        Apply a partial payment to invoice.
        
        Args:
            amount: Payment amount
            payment_date: Date of payment
        
        Returns:
            Decimal: Remaining balance
        """
        if amount <= 0:
            raise ValidationError('Payment amount must be positive')
        
        self.amount_paid += amount
        
        if self.amount_paid >= self.total_amount:
            # Fully paid
            self.mark_as_paid(payment_date, self.total_amount)
        else:
            # Partially paid
            self.status = 'PARTIAL_PAID'
            self.save()
        
        return self.balance_due
    
    def cancel(self, reason=''):
        """
        Cancel invoice.
        
        Args:
            reason: Cancellation reason
        
        Raises:
            ValidationError: If invoice cannot be cancelled
        """
        if not self.can_be_cancelled():
            raise ValidationError('Invoice cannot be cancelled')
        
        self.status = 'CANCELLED'
        if reason:
            self.notes = f"{self.notes}\nCancelled: {reason}".strip()
        self.save()
    
    def void(self, reason=''):
        """
        Void a posted invoice.
        
        Args:
            reason: Void reason
        
        Raises:
            ValidationError: If invoice cannot be voided
        """
        if not self.can_be_voided():
            raise ValidationError('Invoice cannot be voided')
        
        self.status = 'VOID'
        if reason:
            self.notes = f"{self.notes}\nVoided: {reason}".strip()
        self.save()
    
    def recalculate_totals(self):
        """Recalculate all totals from line items."""
        lines = self.lines.all()

        self.subtotal = sum(line.line_total for line in lines)
        self.discount_amount = sum(
            line.quantity * line.unit_price * (line.discount_percentage / 100)
            for line in lines
        )
        self.vat_amount = sum(line.vat_amount for line in lines)
        self.total_amount = self.subtotal + self.vat_amount
        self.total_cost = sum(line.line_cost for line in lines)
        self.gross_profit = self.subtotal - self.total_cost

        # Save without triggering full validation
        super(Invoice, self).save()

    @property
    def requires_cash_tender(self):
        """
        Manual §1 "1. Invoice - Cash Debtors": "Where the Debtor's Account
        Category is set to C in Debtor's File Maintenance and their payment
        terms are set to 0, the invoice transaction will end with a Tender
        Routine, as in a Cash Sale. An invoice plus a payment will be posted
        to the Cash Debtor's Account."
        """
        return bool(self.debtor_id) and self.debtor.acctype == 'C' and self.debtor.terms == 0

    def apply_subtotal_discount(self, percentage):
        """
        Manual §1 "1. Invoice - Subtotal Discount Facility": "Enter the
        Discount % which will automatically be applied to all the line
        items on the invoice. A minus (-) discount will automatically
        increase the unit price of all line items."

        Applied by scaling each line's unit_price directly (rather than
        folding into discount_percentage, which is capped 0-100 and can't
        represent the "minus discount increases price" case) — the whole
        operation is rejected up front if it would exceed a line's stock
        item's maximum_discount_percent; no partial apply.
        """
        from apps.stock_control.models import StockItem

        percentage = Decimal(str(percentage))
        factor = (Decimal(100) - percentage) / Decimal(100)
        if factor < 0:
            raise ValidationError('Subtotal discount cannot exceed 100%.')

        lines = list(self.lines.exclude(quantity=0))
        if not lines:
            raise ValidationError('Invoice has no line items to discount.')

        if percentage > 0:
            for line in lines:
                if not line.stock_code:
                    continue
                try:
                    stock_item = StockItem.objects.get(stock_code=line.stock_code)
                except StockItem.DoesNotExist:
                    continue
                if percentage > stock_item.maximum_discount_percent:
                    raise ValidationError(
                        f"Subtotal discount of {percentage}% exceeds the maximum discount "
                        f"of {stock_item.maximum_discount_percent}% allowed for line "
                        f"{line.line_number} ({line.stock_code})."
                    )

        for line in lines:
            line.unit_price = (line.unit_price * factor).quantize(Decimal('0.0001'))
            line.save()

        self.refresh_from_db()
        return self

    def apply_set_price(self, target_total):
        """
        Manual §1 "1. Invoice - Set Selling Price Facility": "Enter the
        revised inclusive Total Amount of the Invoice. The system
        automatically adjusts the prices of individual items in proportion
        to the new total price."
        """
        from .calculation_service import CalculationService

        target_total = Decimal(str(target_total))
        if target_total <= 0:
            raise ValidationError('Target total must be greater than zero.')

        lines = [l for l in self.lines.exclude(quantity=0) if (l.line_total + l.vat_amount) > 0]
        if not lines:
            raise ValidationError('Invoice has no priced line items to adjust.')

        current_total = self.total_amount
        if current_total <= 0:
            raise ValidationError('Invoice has no current total to scale from.')

        ratio = target_total / current_total
        largest_line_id = max(lines, key=lambda l: (l.line_total + l.vat_amount)).pk

        for line in lines:
            current_incl = line.line_total + line.vat_amount
            new_incl = (current_incl * ratio).quantize(Decimal('0.01'))

            is_taxable = line.tax_code in CalculationService.TAXABLE_TAX_CODES
            vat_factor = (Decimal(1) + line.vat_rate / Decimal(100)) if is_taxable else Decimal(1)
            new_excl = new_incl / vat_factor

            discount_factor = (Decimal(100) - line.discount_percentage) / Decimal(100)
            if discount_factor <= 0 or line.quantity <= 0:
                continue
            line.unit_price = (new_excl / (line.quantity * discount_factor)).quantize(Decimal('0.0001'))
            line.save()

        # Cent-rounding residual (proportional scaling across N lines rarely
        # divides evenly) goes onto the single largest line so the header
        # total matches the target exactly.
        self.refresh_from_db()
        residual = target_total - self.total_amount
        if residual != 0:
            largest_line = self.lines.get(pk=largest_line_id)
            is_taxable = largest_line.tax_code in CalculationService.TAXABLE_TAX_CODES
            vat_factor = (Decimal(1) + largest_line.vat_rate / Decimal(100)) if is_taxable else Decimal(1)
            discount_factor = (Decimal(100) - largest_line.discount_percentage) / Decimal(100)
            if discount_factor > 0 and largest_line.quantity > 0:
                unit_price_delta = residual / vat_factor / discount_factor / largest_line.quantity
                largest_line.unit_price = (largest_line.unit_price + unit_price_delta).quantize(Decimal('0.0001'))
                largest_line.save()

        self.refresh_from_db()
        return self


class InvoiceLine(TimeStampedModel):
    """
    Invoice Line Item
    
    Individual items/services on an invoice.
    """
    
    # ==========================================
    # FOREIGN KEYS
    # ==========================================
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='lines',
        help_text="Parent Invoice"
    )
    
    # ==========================================
    # LINE IDENTIFICATION
    # ==========================================
    
    line_number = models.PositiveIntegerField(
        help_text="Line Number (sequence)"
    )
    
    # ==========================================
    # STOCK INFORMATION
    # ==========================================
    
    stock_code = models.CharField(
        max_length=13,
        blank=True,
        help_text="Stock Code"
    )
    
    description = models.CharField(
        max_length=200,
        help_text="Item Description"
    )
    
    # ==========================================
    # QUANTITY & PRICING
    # ==========================================
    
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Quantity"
    )
    
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Unit Price (excl. VAT)"
    )
    
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100'))
        ],
        help_text="Discount %"
    )
    
    # ==========================================
    # TAX
    # ==========================================
    
    tax_code = models.PositiveIntegerField(
        default=1,
        help_text="Tax Code (1=Standard 15%)"
    )
    
    vat_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('14.00'),
        help_text="VAT Rate % (14% South African VAT)"
    )
    
    # ==========================================
    # CALCULATED FIELDS
    # ==========================================
    
    line_total = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="Line Total (excl. VAT, after discount)"
    )
    
    vat_amount = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        help_text="VAT Amount for this line"
    )
    
    # ==========================================
    # COST & PROFIT
    # ==========================================
    
    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        help_text="Cost Price per Unit"
    )
    
    line_cost = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.00'),
        help_text="Total Cost (quantity × cost_price)"
    )
    
    line_profit = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal('0.00'),
        help_text="Line Profit (line_total - line_cost)"
    )
    
    class Meta:
        ordering = ['line_number']
        unique_together = [['invoice', 'line_number']]
        verbose_name = 'Invoice Line'
        verbose_name_plural = 'Invoice Lines'
        indexes = [
            models.Index(fields=['stock_code'], name='idx_invline_stock'),
            models.Index(fields=['invoice', 'stock_code'], name='idx_invline_inv_stock'),
        ]
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - Line {self.line_number}: {self.description}"
    
    def clean(self):
        """Validate line item data."""
        errors = {}
        
        if self.quantity <= 0:
            errors['quantity'] = 'Quantity must be greater than zero.'
        
        if self.unit_price < 0:
            errors['unit_price'] = 'Unit price cannot be negative.'
        
        if not 0 <= self.discount_percentage <= 100:
            errors['discount_percentage'] = 'Discount must be between 0 and 100.'
        
        if self.cost_price < 0:
            errors['cost_price'] = 'Cost price cannot be negative.'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Auto-calculate line totals before saving."""
        from .calculation_service import CalculationService

        calc = CalculationService.calculate_line_totals(
            quantity=self.quantity,
            unit_price=self.unit_price,
            discount_percentage=self.discount_percentage,
            tax_code=self.tax_code,
            cost_price=self.cost_price,
            vat_rate=self.vat_rate,
            quantize_places=Decimal('0.0001'),  # preserve this model's 4dp fields
        )
        # NOTE: this model's `line_total` is excl-VAT ("before discount, after
        # VAT" per help_text) — map from the service's line_total_before_vat,
        # not its VAT-inclusive line_total key.
        self.line_total = calc['line_total_before_vat']
        self.vat_amount = calc['vat_amount']
        self.line_cost = calc['line_cost']
        self.line_profit = calc['line_profit']

        # Skip Django validation for this save to avoid Decimal precision issues
        # Validation is not skipped entirely - we just don't call full_clean()
        super(InvoiceLine, self).save(*args, **kwargs)

        # Update invoice totals
        if self.invoice_id:
            self.invoice.recalculate_totals()



class CashSale(TimeStampedModel):
    """Cash sale transaction."""
    sale_number = models.CharField(max_length=20, unique=True, db_index=True)
    sale_date = models.DateField(db_index=True)
    sale_time = models.TimeField(auto_now_add=True)
    
    # Header Information
    customer_name = models.CharField(max_length=200, blank=True)
    delivery_address = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    order_number = models.CharField(max_length=50, blank=True)
    job_card_number = models.CharField(max_length=50, blank=True)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_sales'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cost and Profit
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment
    cash_tendered = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_given = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # VAT
    vat_number = models.CharField(max_length=50, blank=True)
    
    # Status
    is_posted = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-sale_date', '-sale_time']
        indexes = [
            models.Index(fields=['sale_date', 'cashier']),
            models.Index(fields=['station_number', 'sale_date']),
        ]
    
    def __str__(self):
        return f"Cash Sale {self.sale_number}"


class CashSaleLine(TimeStampedModel):
    """Cash sale line item."""
    cash_sale = models.ForeignKey(
        CashSale,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_code = models.PositiveIntegerField(default=1)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    line_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['cash_sale', 'line_number']
    
    def __str__(self):
        return f"{self.cash_sale.sale_number} - Line {self.line_number}"


class Tender(TimeStampedModel):
    """Payment tender for cash sales and receipts."""
    
    TENDER_TYPE_CHOICES = [
        ('CASH', 'Cash'),
        ('CHEQUE', 'Cheque'),
        ('VOUCHER', 'Voucher'),
        ('SPEEDPOINT', 'Speedpoint/Card'),
        ('EFT', 'EFT'),
    ]
    
    # Link to transaction — exactly one of these must be set (see clean()/
    # the CheckConstraint below). Mirrors the typed-nullable-FK pattern
    # apps.creditors.CreditorOpenItem already uses for "one record, several
    # possible parent types" rather than a generic/contenttypes FK.
    cash_sale = models.ForeignKey(
        CashSale,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tenders'
    )
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tenders'
    )

    tender_type = models.CharField(max_length=15, choices=TENDER_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    # For cheques
    drawer_name = models.CharField(max_length=200, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=50, blank=True)
    id_number = models.CharField(max_length=50, blank=True)
    telephone = models.CharField(max_length=50, blank=True)

    # For speedpoint
    card_type = models.CharField(max_length=50, blank=True)
    authorization_code = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['tender_type']),
            models.Index(fields=['cash_sale', 'tender_type'], name='idx_receipt_tender'),
        ]
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(cash_sale__isnull=False, invoice__isnull=True) |
                    models.Q(cash_sale__isnull=True, invoice__isnull=False)
                ),
                name='tender_exactly_one_parent',
            ),
        ]

    def clean(self):
        linked = [pk for pk in (self.cash_sale_id, self.invoice_id) if pk]
        if len(linked) != 1:
            raise ValidationError('Tender must be linked to exactly one of cash_sale or invoice.')

    def __str__(self):
        return f"{self.tender_type} - {self.amount}"


class Laybye(TimeStampedModel):
    """Laybye (layaway) transaction (LBMAST equivalent)."""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CONVERTED_TO_INVOICE', 'Converted to Invoice'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    laybye_number = models.CharField(max_length=20, unique=True, db_index=True)
    
    # Customer details
    customer_name = models.CharField(max_length=40)
    address_line1 = models.CharField(max_length=25, blank=True)
    address_line2 = models.CharField(max_length=25, blank=True)
    address_line3 = models.CharField(max_length=25, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    
    # Debtor relationship
    debtor_account_number = models.IntegerField(null=True, blank=True, help_text="Customer account number (DNO)")
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Dates
    laybye_date = models.DateField()
    expiry_date = models.DateField()
    date_last_paid = models.DateField(null=True, blank=True)
    
    # Totals
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Comments
    comment1 = models.CharField(max_length=30, blank=True)
    comment2 = models.CharField(max_length=30, blank=True)
    
    # Status
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Cancellation
    retention_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Percentage retained on cancellation"
    )
    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-laybye_date']
        indexes = [
            models.Index(fields=['status', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"Laybye {self.laybye_number}"


class LaybyeLine(TimeStampedModel):
    """Laybye transaction (LBTRAN equivalent)."""
    
    TRANSACTION_TYPE_CHOICES = [
        ('SP', 'Sale'),
        ('PM', 'Payment'),
        ('AD', 'Adjustment'),
        ('RT', 'Return'),
        ('OT', 'Other'),
    ]
    
    laybye = models.ForeignKey(
        Laybye,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    
    # Stock details
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200, blank=True)
    
    # Prices and quantity
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_code = models.PositiveIntegerField(default=1)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    
    # Transaction info
    transaction_date = models.DateField()
    transaction_time = models.TimeField()
    transaction_type = models.CharField(max_length=2, choices=TRANSACTION_TYPE_CHOICES)
    
    # Operational
    station_number = models.PositiveIntegerField(null=True, blank=True)
    salesman_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Calculated
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['transaction_date', 'transaction_time']
    
    def __str__(self):
        return f"{self.laybye.laybye_number} - {self.transaction_type}"


class LaybyePayment(TimeStampedModel):
    """Payment on laybye."""
    laybye = models.ForeignKey(
        Laybye,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['payment_date']
    
    def __str__(self):
        return f"{self.laybye.laybye_number} - Payment {self.amount}"


class Quotation(TimeStampedModel):
    """Sales quotation."""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CONVERTED_TO_INVOICE', 'Converted to Invoice'),
        ('INVOICED', 'Invoiced'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
        ('JOB', 'Converted to Job'),
    ]
    
    PRICE_LEVEL_CHOICES = [
        (1, 'Selling Price 1'),
        (2, 'Selling Price 2'),
        (3, 'Selling Price 3'),
        ('COST', 'Cost Price'),
        ('MARKUP', 'Cost + Markup'),
        ('GP', 'Gross Profit %'),
    ]
    
    quotation_number = models.CharField(max_length=20, unique=True, db_index=True)
    quotation_date = models.DateField()
    expiry_date = models.DateField()
    
    # Customer details
    customer_name = models.CharField(max_length=200)
    address_line1 = models.CharField(max_length=25, blank=True)
    address_line2 = models.CharField(max_length=25, blank=True)
    address_line3 = models.CharField(max_length=25, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    
    # Debtor relationship
    debtor_account = models.ForeignKey(
        Debtor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotations'
    )
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    station_number = models.PositiveIntegerField(default=1)
    
    # Comments
    comment1 = models.CharField(max_length=30, blank=True)
    comment2 = models.CharField(max_length=30, blank=True)
    
    # Pricing basis
    price_level = models.CharField(max_length=10, choices=PRICE_LEVEL_CHOICES, default=1)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='ACTIVE')
    
    class Meta:
        ordering = ['-quotation_date']
        indexes = [
            models.Index(fields=['status', 'expiry_date']),
        ]
    
    def __str__(self):
        return f"Quotation {self.quotation_number}"


class QuotationLine(TimeStampedModel):
    """Quotation line item (QTRAN equivalent)."""
    quotation = models.ForeignKey(
        Quotation,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    # Stock details
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Tax and department
    tax_code = models.PositiveIntegerField(default=1)
    department = models.CharField(max_length=3, blank=True)
    
    # Comments
    comments = models.CharField(max_length=30, blank=True)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['quotation', 'line_number']
    
    def __str__(self):
        return f"{self.quotation.quotation_number} - Line {self.line_number}"


class Payout(TimeStampedModel):
    """Cash payout from till."""
    payout_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payee = models.CharField(max_length=200, help_text="To whom paid")
    description = models.TextField(help_text="Description of goods/service")
    reference = models.CharField(max_length=100, blank=True)
    
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='payouts'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['-payout_date']
    
    def __str__(self):
        return f"Payout {self.amount} to {self.payee}"


class Repair(TimeStampedModel):
    """Repair voucher (REPMAST equivalent)."""
    
    STATUS_CHOICES = [
        ('C', 'Created'),
        ('I', 'Issued to Supplier'),
        ('R', 'Received from Supplier'),
        ('V', 'Invoiced'),
        ('X', 'Cancelled'),
    ]
    
    repair_number = models.CharField(max_length=20, unique=True, db_index=True)

    # Debtor relationship — set when the repair is charged to an account
    # (manual §R "Charge for the Repair", Account option). Nullable because
    # most of a repair's lifecycle (created/issued/received) has no debtor
    # yet, and a Cash-charged repair never gets one at all.
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='repairs'
    )

    # Customer details
    customer_name = models.CharField(max_length=40)
    address_line1 = models.CharField(max_length=25, blank=True)
    address_line2 = models.CharField(max_length=25, blank=True)
    telephone = models.CharField(max_length=15, blank=True)
    contact_person = models.CharField(max_length=20, blank=True)
    customer_reference = models.CharField(max_length=10, blank=True)
    
    # Order details
    order_number = models.CharField(max_length=10, blank=True)
    date_received = models.DateField(null=True, blank=True)
    date_required = models.DateField()
    quoted_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Repair details (REP table equivalent)
    repair_details = models.TextField(blank=True)
    
    # Supplier details
    supplier_number = models.PositiveIntegerField(null=True, blank=True)
    date_sent = models.DateField(null=True, blank=True)
    date_returned = models.DateField(null=True, blank=True)
    
    # Repair costs
    repair_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Comments
    comment1 = models.CharField(max_length=30, blank=True)
    comment2 = models.CharField(max_length=30, blank=True)
    comment3 = models.CharField(max_length=30, blank=True)
    comment4 = models.CharField(max_length=30, blank=True)
    supplier_comment = models.CharField(max_length=25, blank=True)
    
    # Status
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='C')
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Repair {self.repair_number}"


class RepairLine(TimeStampedModel):
    """Repair transaction details (REPTRAN equivalent)."""
    
    TRANSACTION_TYPE_CHOICES = [
        ('IS', 'Issue'),
        ('RC', 'Receipt'),
        ('AD', 'Adjustment'),
        ('RT', 'Return'),
        ('OT', 'Other'),
    ]
    
    repair = models.ForeignKey(
        Repair,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=2, choices=TRANSACTION_TYPE_CHOICES)
    transaction_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Supplier reference
    supplier_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Additional info
    comment = models.CharField(max_length=25, blank=True)
    transport_mode = models.CharField(max_length=15, blank=True)
    station_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Captured info
    date_captured = models.DateField(auto_now_add=True)
    time_captured = models.TimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['transaction_date']
    
    def __str__(self):
        return f"{self.repair.repair_number} - {self.transaction_type}"


class JobCard(TimeStampedModel):
    """Job card for work orders."""
    
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('CONVERTED_TO_INVOICE', 'Converted to Invoice'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    job_number = models.CharField(max_length=20, unique=True, db_index=True)
    job_date = models.DateField()
    
    # Customer details
    customer_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    order_number = models.CharField(max_length=50, blank=True)
    
    # Debtor reference (optional - for converting to invoice)
    debtor_account_number = models.CharField(max_length=20, blank=True, db_index=True)
    
    # Job details
    registration_number = models.CharField(max_length=50, blank=True)
    job_description = models.TextField(blank=True)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    operator_number = models.PositiveIntegerField(null=True, blank=True)
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='ACTIVE')
    
    # Cancellation
    cancellation_reason = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-job_date']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Job {self.job_number}"

    def apply_subtotal_discount(self, percentage):
        """
        Manual §J "Job Costing", Update Transaction "S" option: same
        Subtotal Discount facility as Invoice — see Invoice.apply_subtotal_discount.
        """
        from apps.stock_control.models import StockItem

        percentage = Decimal(str(percentage))
        factor = (Decimal(100) - percentage) / Decimal(100)
        if factor < 0:
            raise ValidationError('Subtotal discount cannot exceed 100%.')

        lines = list(self.lines.exclude(quantity=0))
        if not lines:
            raise ValidationError('Job card has no line items to discount.')

        if percentage > 0:
            for line in lines:
                if not line.stock_code:
                    continue
                try:
                    stock_item = StockItem.objects.get(stock_code=line.stock_code)
                except StockItem.DoesNotExist:
                    continue
                if percentage > stock_item.maximum_discount_percent:
                    raise ValidationError(
                        f"Subtotal discount of {percentage}% exceeds the maximum discount "
                        f"of {stock_item.maximum_discount_percent}% allowed for line "
                        f"{line.line_number} ({line.stock_code})."
                    )

        for line in lines:
            line.unit_price = (line.unit_price * factor).quantize(Decimal('0.0001'))
            line.save()

        self.refresh_from_db()
        return self

    def apply_set_price(self, target_total):
        """
        Manual §J "Job Costing", Update Transaction "Set Price" option: same
        Set Selling Price facility as Invoice — see Invoice.apply_set_price.
        Note JobCardLine.line_total is VAT-inclusive (unlike InvoiceLine),
        so unlike Invoice this doesn't need to add a separate vat_amount.
        """
        from .calculation_service import CalculationService

        target_total = Decimal(str(target_total))
        if target_total <= 0:
            raise ValidationError('Target total must be greater than zero.')

        lines = [l for l in self.lines.exclude(quantity=0) if l.line_total > 0]
        if not lines:
            raise ValidationError('Job card has no priced line items to adjust.')

        current_total = self.total_amount
        if current_total <= 0:
            raise ValidationError('Job card has no current total to scale from.')

        ratio = target_total / current_total
        largest_line_id = max(lines, key=lambda l: l.line_total).pk

        for line in lines:
            new_incl = (line.line_total * ratio).quantize(Decimal('0.01'))
            is_taxable = line.tax_code in CalculationService.TAXABLE_TAX_CODES
            vat_factor = (Decimal(1) + CalculationService.VAT_RATE) if is_taxable else Decimal(1)
            new_excl = new_incl / vat_factor

            discount_factor = (Decimal(100) - line.discount_percentage) / Decimal(100)
            if discount_factor <= 0 or line.quantity <= 0:
                continue
            line.unit_price = (new_excl / (line.quantity * discount_factor)).quantize(Decimal('0.0001'))
            line.save()

        self.refresh_from_db()
        residual = target_total - self.total_amount
        if residual != 0:
            largest_line = self.lines.get(pk=largest_line_id)
            is_taxable = largest_line.tax_code in CalculationService.TAXABLE_TAX_CODES
            vat_factor = (Decimal(1) + CalculationService.VAT_RATE) if is_taxable else Decimal(1)
            discount_factor = (Decimal(100) - largest_line.discount_percentage) / Decimal(100)
            if discount_factor > 0 and largest_line.quantity > 0:
                unit_price_delta = residual / vat_factor / discount_factor / largest_line.quantity
                largest_line.unit_price = (largest_line.unit_price + unit_price_delta).quantize(Decimal('0.0001'))
                largest_line.save()

        self.refresh_from_db()
        return self


class JobCardLine(TimeStampedModel):
    """Job card line item."""
    job_card = models.ForeignKey(
        JobCard,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_code = models.PositiveIntegerField(default=1)
    
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    cost_price = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    line_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['job_card', 'line_number']
    
    def __str__(self):
        return f"{self.job_card.job_number} - Line {self.line_number}"


class ReceiptOnAccount(TimeStampedModel):
    """Receipt on account for debtor payments at POS."""
    receipt_number = models.CharField(max_length=20, unique=True, db_index=True)
    receipt_date = models.DateField(db_index=True)

    # Debtor details
    debtor_account = models.CharField(max_length=20, db_index=True)
    debtor_name = models.CharField(max_length=200)

    # Set by post_receipt() once posted — links back to the debtors-app
    # ledger record actually created (apps.debtors.DebtorService.post_receipt),
    # so this receipt can be reversed/cancelled correctly later.
    debtor_transaction = models.ForeignKey(
        'debtors.DebtorTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pos_receipts'
    )
    
    # Amounts
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    settlement_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Payment details
    tender_type = models.CharField(
        max_length=15,
        choices=[
            ('CASH', 'Cash'),
            ('CHEQUE', 'Cheque'),
            ('SPEEDPOINT', 'Speedpoint/Card'),
            ('EFT', 'EFT'),
        ]
    )
    
    # For cheques
    cheque_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    
    # For speedpoint
    card_type = models.CharField(max_length=50, blank=True)
    authorization_code = models.CharField(max_length=50, blank=True)
    
    reference = models.CharField(max_length=200, blank=True)
    
    # POS details
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='receipts_on_account'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Status
    is_posted = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    cancel_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-receipt_date']
        indexes = [
            models.Index(fields=['debtor_account', 'receipt_date']),
            models.Index(fields=['is_posted']),
        ]

    def __str__(self):
        return f"Receipt {self.receipt_number} - {self.debtor_name}"


class CreditNote(TimeStampedModel):
    """Credit note for returns."""
    credit_number = models.CharField(max_length=20, unique=True, db_index=True)
    credit_date = models.DateField(db_index=True)
    
    # Customer details (can be cash customer or debtor)
    customer_name = models.CharField(max_length=200, blank=True)
    debtor_account = models.CharField(max_length=20, blank=True, db_index=True)
    
    # Original sale reference
    original_sale_number = models.CharField(max_length=20, blank=True)
    reason = models.TextField(blank=True)
    
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Totals
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Refund method
    refund_type = models.CharField(
        max_length=15,
        choices=[
            ('CASH', 'Cash'),
            ('ACCOUNT', 'Credit to Account'),
            ('REPLACEMENT', 'Replacement'),
        ],
        default='CASH'
    )
    
    # POS details
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='credit_notes'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Status
    is_posted = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    cancel_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-credit_date']
        indexes = [
            models.Index(fields=['debtor_account', 'credit_date']),
            models.Index(fields=['is_posted']),
        ]

    def __str__(self):
        return f"Credit Note {self.credit_number}"


class CreditNoteLine(TimeStampedModel):
    """Credit note line item."""
    credit_note = models.ForeignKey(
        CreditNote,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    tax_code = models.PositiveIntegerField(default=1)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['credit_note', 'line_number']
    
    def __str__(self):
        return f"{self.credit_note.credit_number} - Line {self.line_number}"


class CashReturn(TimeStampedModel):
    """Cash return/refund for cash sales."""
    return_number = models.CharField(max_length=20, unique=True, db_index=True)
    return_date = models.DateField(db_index=True)
    
    # Original sale reference
    original_sale_number = models.CharField(max_length=20)
    customer_name = models.CharField(max_length=200, blank=True)
    reason = models.TextField()
    
    # Amounts
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # POS details
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_returns'
    )
    station_number = models.PositiveIntegerField(default=1)

    # Status
    is_posted = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    cancel_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-return_date']
        indexes = [
            models.Index(fields=['original_sale_number']),
        ]

    def __str__(self):
        return f"Cash Return {self.return_number}"


class CashReturnLine(TimeStampedModel):
    """Cash return line item."""
    cash_return = models.ForeignKey(
        CashReturn,
        on_delete=models.CASCADE,
        related_name='lines'
    )
    line_number = models.PositiveIntegerField()
    
    stock_code = models.CharField(max_length=13, blank=True)
    description = models.CharField(max_length=200)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    tax_code = models.PositiveIntegerField(default=1)
    
    # Calculated fields
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        ordering = ['line_number']
        unique_together = ['cash_return', 'line_number']
    
    def __str__(self):
        return f"{self.cash_return.return_number} - Line {self.line_number}"


class CashACheque(TimeStampedModel):
    """Cash a cheque transaction."""
    transaction_number = models.CharField(max_length=20, unique=True, db_index=True)
    transaction_date = models.DateField(db_index=True)
    
    # Customer details
    drawer_name = models.CharField(max_length=200)
    id_number = models.CharField(max_length=50)
    telephone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    # Cheque details
    cheque_number = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    branch_code = models.CharField(max_length=20, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    
    # Amounts
    cheque_amount = models.DecimalField(max_digits=12, decimal_places=2)
    commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_paid = models.DecimalField(max_digits=12, decimal_places=2)
    
    # POS details
    cashier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cashed_cheques'
    )
    station_number = models.PositiveIntegerField(default=1)
    
    # Status
    is_processed = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)
    cancel_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-transaction_date']
        indexes = [
            models.Index(fields=['drawer_name']),
            models.Index(fields=['cheque_number']),
        ]

    def __str__(self):
        return f"Cash Cheque {self.transaction_number} - {self.drawer_name}"


class TransactionQuery(TimeStampedModel):
    """Transaction query/enquiry system."""
    query_number = models.CharField(max_length=20, unique=True, db_index=True)
    query_date = models.DateField(db_index=True)
    
    # Query details
    transaction_type = models.CharField(
        max_length=20,
        choices=[
            ('CASH_SALE', 'Cash Sale'),
            ('INVOICE', 'Invoice'),
            ('RECEIPT', 'Receipt on Account'),
            ('CREDIT_NOTE', 'Credit Note'),
            ('LAYBYE', 'Laybye'),
            ('QUOTATION', 'Quotation'),
            ('JOB_CARD', 'Job Card'),
            ('REPAIR', 'Repair'),
            ('PAYOUT', 'Payout'),
        ]
    )
    transaction_number = models.CharField(max_length=20, db_index=True)
    
    # Query raised by
    customer_name = models.CharField(max_length=200, blank=True)
    contact_number = models.CharField(max_length=50, blank=True)
    
    # Query details
    query_description = models.TextField()
    query_status = models.CharField(
        max_length=20,
        choices=[
            ('OPEN', 'Open'),
            ('IN_PROGRESS', 'In Progress'),
            ('RESOLVED', 'Resolved'),
            ('CLOSED', 'Closed'),
        ],
        default='OPEN'
    )
    
    # Resolution
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_queries'
    )
    resolved_date = models.DateField(null=True, blank=True)
    
    # Assigned to
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_queries'
    )
    
    class Meta:
        ordering = ['-query_date']
        verbose_name_plural = 'Transaction Queries'
        indexes = [
            models.Index(fields=['query_status', 'query_date']),
            models.Index(fields=['transaction_number']),
        ]
    
    def __str__(self):
        return f"Query {self.query_number} - {self.transaction_type}"


class CashControl(TimeStampedModel):
    """Daily cash control totals per cashier."""
    control_date = models.DateField(db_index=True)
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    station_number = models.PositiveIntegerField(default=1)
    
    # Transactions
    cash_sales_count = models.PositiveIntegerField(default=0)
    cash_sales_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    cash_refunds_count = models.PositiveIntegerField(default=0)
    cash_refunds_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    invoices_count = models.PositiveIntegerField(default=0)
    invoices_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    credits_count = models.PositiveIntegerField(default=0)
    credits_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    receipts_count = models.PositiveIntegerField(default=0)
    receipts_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    settlement_discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Laybyes
    new_laybyes_count = models.PositiveIntegerField(default=0)
    new_laybyes_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    cancelled_laybyes_count = models.PositiveIntegerField(default=0)
    cancelled_laybyes_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    laybye_receipts_count = models.PositiveIntegerField(default=0)
    laybye_receipts_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    laybye_refunds_count = models.PositiveIntegerField(default=0)
    laybye_refunds_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    completed_laybyes_count = models.PositiveIntegerField(default=0)
    completed_laybyes_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payouts
    payouts_count = models.PositiveIntegerField(default=0)
    payouts_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cash a Cheque
    cashed_cheques_count = models.PositiveIntegerField(default=0)
    cashed_cheques_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Takings by type
    cash_takings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cheque_takings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    voucher_takings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    speedpoint_takings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Refunds by type
    cash_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cheque_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    voucher_refunds = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Rounding
    rounding_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Abandoned transactions
    abandoned_count = models.PositiveIntegerField(default=0)
    abandoned_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Cleared flag
    is_cleared = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-control_date', 'cashier']
        unique_together = ['control_date', 'cashier', 'station_number']
        indexes = [
            models.Index(fields=['control_date', 'is_cleared']),
        ]
    
    def __str__(self):
        return f"Cash Control {self.control_date} - {self.cashier.username}"