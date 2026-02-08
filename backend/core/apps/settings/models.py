"""
═══════════════════════════════════════════════════════════════════════════
SETTINGS APP - Django Models
Foundation models for the entire Accpick ERP system
(Renamed from 'core' to avoid conflict with project name)
═══════════════════════════════════════════════════════════════════════════

LOCATION: accpick_project/settings/models.py

PURPOSE: 
This app provides global reference data used by ALL other apps:
- Sales Departments (product categories)
- Sales Areas (salesmen/user creating sales transactions or debtors,creditors etc)
- Income Categories (cash book income types)
- Expense Categories (expense types)
- Tax Codes (VAT rates)
- Payment Methods
- Credit Terms
- System Configuration (global settings like address details, business's vat number, etc note These details appear on all Point-of-Sale documents where blank)
DEPENDS ON: Nothing - this is the foundation

Models in this file (11 + 2 abstract):
- TimeStampedModel (abstract)
- ActiveModel (abstract)
- SalesDepartment
- SalesArea
- IncomeCategory
- ExpenseCategory
- TaxCode
- CostingCategory
- PaymentMethod
- CreditTerms
- SystemConfiguration
- DepartmentMonthlyStats
- SalesAreaMonthlyStats
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()


# ═══════════════════════════════════════════════════════════════════════════
# ABSTRACT BASE MODELS
# ═══════════════════════════════════════════════════════════════════════════

class TimeStampedModel(models.Model):
    """
    Abstract base model that provides timestamp tracking
    All models that need audit trail inherit from this
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        editable=False
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        editable=False
    )
    
    class Meta:
        abstract = True


class ActiveModel(models.Model):
    """
    Abstract base model for soft delete functionality
    Instead of deleting records, we mark them as inactive
    """
    is_active = models.BooleanField(
        default=True,
        help_text="Active records are available for use"
    )
    deactivated_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False
    )
    deactivated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deactivated',
        editable=False
    )
    
    class Meta:
        abstract = True


# ═══════════════════════════════════════════════════════════════════════════
# VAT CALCULATION MIXIN
# ═══════════════════════════════════════════════════════════════════════════

class VATMixin(models.Model):
    """
    Abstract mixin for models that require VAT/Tax calculation fields
    Provides consistent VAT handling across all apps:
    - CashBookTransaction
    - CreditorInvoice and related models
    - DebtorTransaction
    - CashSale and POS models
    
    Ensures consistent: value_excl_vat + tax_amount = total_incl_vat
    """
    value_excl_vat = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Amount excluding VAT"
    )
    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="VAT/Tax amount"
    )
    total_incl_vat = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Total amount including VAT"
    )
    
    class Meta:
        abstract = True
    
    def validate_vat_integrity(self):
        """Verify VAT calculation is correct: value + tax = total"""
        from decimal import Decimal
        tolerance = Decimal('0.01')
        expected_total = self.value_excl_vat + self.tax_amount
        if abs(self.total_incl_vat - expected_total) > tolerance:
            return False, f"VAT mismatch: {self.value_excl_vat} + {self.tax_amount} ≠ {self.total_incl_vat}"
        return True, "VAT fields are valid"


# ═══════════════════════════════════════════════════════════════════════════
# POSTING STATUS MIXIN
# ═══════════════════════════════════════════════════════════════════════════

class PostingStatusMixin(models.Model):
    """
    Abstract mixin for models that track posting status to General Ledger
    Ensures consistent posting workflow across:
    - CreditorTransaction
    - DebtorTransaction
    - POS transactions
    
    Once posted, transactions become immutable for audit trail integrity
    """
    is_posted = models.BooleanField(
        default=False,
        help_text="Whether this transaction has been posted to GL"
    )
    posted_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        help_text="Timestamp when posted to GL"
    )
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_posted',
        editable=False,
        help_text="User who posted this transaction"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_posted']),
        ]


# ═══════════════════════════════════════════════════════════════════════════
# RECONCILIATION MIXIN
# ═══════════════════════════════════════════════════════════════════════════

class ReconciliationMixin(models.Model):
    """
    Abstract mixin for transactions that require reconciliation
    Tracks reconciliation status for:
    - CashBookTransaction (bank reconciliation)
    - Future: supplier statement reconciliation
    
    Once reconciled, transactions are locked to maintain audit trails
    """
    is_reconciled = models.BooleanField(
        default=False,
        help_text="Whether this transaction has been reconciled"
    )
    reconciled_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        help_text="Timestamp when reconciled"
    )
    reconciled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_reconciled',
        editable=False,
        help_text="User who reconciled this transaction"
    )
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_reconciled']),
        ]


# ═══════════════════════════════════════════════════════════════════════════
# SALES DEPARTMENT MODEL
# ═══════════════════════════════════════════════════════════════════════════

class SalesDepartment(TimeStampedModel, ActiveModel):
    """
    Sales departments - used to categorize stock items
    Examples: Electronics, Furniture, Clothing, etc.
    Numbered 1-999
    """
    
    # === USER INPUT FIELDS ===
    number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(999)],
        help_text="Department number (1-999)"
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Department name"
    )
    
    # === SYSTEM GENERATED FIELDS ===
    # Sales tracking
    sales_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales value Month-to-Date"
    )
    sales_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales value Year-to-Date"
    )
    
    # Profit tracking
    profit_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Gross profit Month-to-Date"
    )
    profit_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Gross profit Year-to-Date"
    )
    
    class Meta:
        db_table = 'sales_departments'
        ordering = ['number']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Sales Department'
        verbose_name_plural = 'Sales Departments'
    
    def __str__(self):
        return f"{self.number} - {self.name}"
    
    @property
    def gross_profit_percent_mtd(self):
        """Calculate gross profit percentage MTD"""
        if self.sales_mtd > 0:
            return (self.profit_mtd / self.sales_mtd) * 100
        return 0
    
    @property
    def gross_profit_percent_ytd(self):
        """Calculate gross profit percentage YTD"""
        if self.sales_ytd > 0:
            return (self.profit_ytd / self.sales_ytd) * 100
        return 0


# ═══════════════════════════════════════════════════════════════════════════
# SALES AREA MODEL (Salesmen/Territories)
# ═══════════════════════════════════════════════════════════════════════════

class SalesArea(TimeStampedModel, ActiveModel):
    """
    Sales areas / Salesmen
    Used to track sales by territory or salesperson
    Numbered 1-99
    """
    
    # === USER INPUT FIELDS ===
    number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        help_text="Sales area number (1-99)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Salesman name or area name"
    )
    
    # Commission settings
    commission_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Commission rate percentage"
    )
    
    # === SYSTEM GENERATED FIELDS ===
    # Sales tracking
    sales_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales value Month-to-Date"
    )
    sales_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales value Year-to-Date"
    )
    
    # Profit tracking
    profit_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Gross profit Month-to-Date"
    )
    profit_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Gross profit Year-to-Date"
    )
    
    # Commission tracking
    commission_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Commission earned Month-to-Date"
    )
    commission_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Commission earned Year-to-Date"
    )
    
    class Meta:
        db_table = 'sales_areas'
        ordering = ['number']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Sales Area'
        verbose_name_plural = 'Sales Areas'
    
    def __str__(self):
        return f"{self.number} - {self.name}"
    
    @property
    def gross_profit_percent_mtd(self):
        """Calculate gross profit percentage MTD"""
        if self.sales_mtd > 0:
            return (self.profit_mtd / self.sales_mtd) * 100
        return 0
    
    @property
    def gross_profit_percent_ytd(self):
        """Calculate gross profit percentage YTD"""
        if self.sales_ytd > 0:
            return (self.profit_ytd / self.sales_ytd) * 100
        return 0


# ═══════════════════════════════════════════════════════════════════════════
# INCOME CATEGORY MODEL
# ═══════════════════════════════════════════════════════════════════════════

class IncomeCategory(TimeStampedModel, ActiveModel):
    """
    Income categories for cash book
    Used to categorize non-debtor income
    Examples: Interest received, Rent received, Other income
    Numbered 1-99999999 (1-8 digits)
    """
    
    # === USER INPUT FIELDS ===
    number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(99999999)],
        help_text="Income category number (1-8 digits)"
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Income category name"
    )
    
    # === SYSTEM GENERATED FIELDS ===
    total_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total income Month-to-Date"
    )
    total_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total income Year-to-Date"
    )
    
    class Meta:
        db_table = 'income_categories'
        ordering = ['number']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Income Category'
        verbose_name_plural = 'Income Categories'
    
    def __str__(self):
        return f"{self.number} - {self.name}"


# ═══════════════════════════════════════════════════════════════════════════
# EXPENSE CATEGORY MODEL
# ═══════════════════════════════════════════════════════════════════════════

class ExpenseCategory(TimeStampedModel, ActiveModel):
    """
    Expense categories
    Used in both Cash Book and Creditors
    Examples: Electricity, Telephone, Salaries, etc.
    Numbered 1-99999999 (1-8 digits)
    """
    
    CATEGORY_TYPE_CHOICES = [
        ('BOTH', 'Both Cash Book & Creditors'),
        ('CASHBOOK', 'Cash Book Only'),
        ('CREDITORS', 'Creditors Only'),
    ]
    
    # === USER INPUT FIELDS ===
    number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(99999999)],
        help_text="Expense category number (1-8 digits)"
    )
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Expense category name"
    )
    category_type = models.CharField(
        max_length=10,
        choices=CATEGORY_TYPE_CHOICES,
        default='BOTH',
        help_text="Where this category can be used"
    )
    
    # === SYSTEM GENERATED FIELDS ===
    total_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total expenses Month-to-Date"
    )
    total_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Total expenses Year-to-Date"
    )
    
    class Meta:
        db_table = 'expense_categories'
        ordering = ['number']
        indexes = [
            models.Index(fields=['number']),
            models.Index(fields=['name']),
            models.Index(fields=['category_type']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Expense Category'
        verbose_name_plural = 'Expense Categories'
    
    def __str__(self):
        return f"{self.number} - {self.name}"


# ═══════════════════════════════════════════════════════════════════════════
# TAX CODE MODEL
# ═══════════════════════════════════════════════════════════════════════════

class TaxCode(TimeStampedModel, ActiveModel):
    """
    VAT/Tax codes
    Examples: 
    - Code 1: 14% VAT (South Africa standard rate)
    - Code 2: 0% Zero-rated
    """
    
    # === USER INPUT FIELDS ===
    code = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1)],
        help_text="Tax code number (1=14%, 2=0%, etc.)"
    )
    description = models.CharField(
        max_length=100,
        help_text="Tax description (e.g., '14% VAT', '0% Zero-rated')"
    )
    rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Tax rate percentage"
    )
    
    is_default = models.BooleanField(
        default=False,
        help_text="Default tax code for new items"
    )
    
    class Meta:
        db_table = 'tax_codes'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_default']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Tax Code'
        verbose_name_plural = 'Tax Codes'
    
    def __str__(self):
        return f"{self.code} - {self.description} ({self.rate}%)"
    
    def save(self, *args, **kwargs):
        # Ensure only one default tax code
        if self.is_default:
            TaxCode.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# COSTING CATEGORY MODEL
# ═══════════════════════════════════════════════════════════════════════════

class CostingCategory(TimeStampedModel, ActiveModel):
    """
    Costing categories for system costing method settings.
    
    Costing Method for Stock and Gross Profit Calculations:
        A = Average Cost
        L = Last Cost
    
    Pricing of Goods and Services:
        I = Inclusive of VAT
        E = Exclusive of VAT
    """
    # === COSTING METHOD ===
    COSTING_METHOD_CHOICES = [
        ('A', 'Average Cost'),
        ('L', 'Last Cost'),
    ]
    
    # === PRICING METHOD ===
    PRICING_METHOD_CHOICES = [
        ('I', 'Inclusive of VAT'),
        ('E', 'Exclusive of VAT'),
    ]
    
    # === FIELDS ===
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Descriptive name for the costing category"
    )
    costing_method = models.CharField(
        max_length=1,
        choices=COSTING_METHOD_CHOICES,
        default='A',
        help_text="Method for calculating stock cost and gross profit"
    )
    pricing_method = models.CharField(
        max_length=1,
        choices=PRICING_METHOD_CHOICES,
        default='E',
        help_text="VAT pricing method for goods and services"
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description of this costing category"
    )
    
    class Meta:
        db_table = 'costing_categories'
        verbose_name = "Costing Category"
        verbose_name_plural = "Costing Categories"
        ordering = ['name']
        indexes = [
            models.Index(fields=['costing_method']),
            models.Index(fields=['pricing_method']),
            models.Index(fields=['costing_method', 'pricing_method']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    # === PROPERTIES ===
    @property
    def uses_average_cost(self):
        """Returns True if using Average Cost method"""
        return self.costing_method == 'A'
    
    @property
    def uses_last_cost(self):
        """Returns True if using Last Cost method"""
        return self.costing_method == 'L'
    
    @property
    def is_vat_inclusive(self):
        """Returns True if pricing is VAT inclusive"""
        return self.pricing_method == 'I'
    
    @property
    def is_vat_exclusive(self):
        """Returns True if pricing is VAT exclusive"""
        return self.pricing_method == 'E'
    
    # === METHODS ===
    def get_methods_display(self):
        """Returns formatted display of both methods"""
        return f"{self.get_costing_method_display()} | {self.get_pricing_method_display()}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        # Validate costing method
        if self.costing_method not in dict(self.COSTING_METHOD_CHOICES):
            raise ValidationError({
                'costing_method': 'Invalid costing method selected.'
            })
        
        # Validate pricing method
        if self.pricing_method not in dict(self.PRICING_METHOD_CHOICES):
            raise ValidationError({
                'pricing_method': 'Invalid pricing method selected.'
            })
        
        # Validate name
        if self.name:
            self.name = self.name.strip()
            if not self.name:
                raise ValidationError({
                    'name': 'Name cannot be empty or only whitespace.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to ensure clean is called"""
        self.full_clean()
        super().save(*args, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════
# PAYMENT METHOD MODEL
# ═══════════════════════════════════════════════════════════════════════════

class PaymentMethod(TimeStampedModel, ActiveModel):
    """
    Payment methods for receipts and payments
    Examples: Cash, Cheque, EFT, Credit Card
    """
    
    # === USER INPUT FIELDS ===
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Payment method code (e.g., CASH, CHQ, EFT)"
    )
    name = models.CharField(
        max_length=100,
        help_text="Payment method name"
    )
    
    requires_reference = models.BooleanField(
        default=False,
        help_text="Requires reference number (e.g., cheque number)"
    )
    is_electronic = models.BooleanField(
        default=False,
        help_text="Electronic payment (EFT, card, etc.)"
    )
    
    class Meta:
        db_table = 'payment_methods'
        ordering = ['code']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Payment Method'
        verbose_name_plural = 'Payment Methods'
    
    def __str__(self):
        return f"{self.code} - {self.name}"


# ═══════════════════════════════════════════════════════════════════════════
# CREDIT TERMS MODEL
# ═══════════════════════════════════════════════════════════════════════════

class CreditTerms(TimeStampedModel, ActiveModel):
    """
    Credit terms for customers and suppliers
    Examples: 0 days (COD), 30 days, 60 days, 90 days
    """
    
    # === USER INPUT FIELDS ===
    days = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        help_text="Number of days credit (0 = Cash On Delivery)"
    )
    description = models.CharField(
        max_length=100,
        help_text="Description (e.g., 'COD', '30 Days', '60 Days')"
    )
    
    class Meta:
        db_table = 'credit_terms'
        ordering = ['days']
        indexes = [
            models.Index(fields=['days']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Credit Terms'
        verbose_name_plural = 'Credit Terms'
    
    def __str__(self):
        return f"{self.days} days - {self.description}"


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM CONFIGURATION MODEL
# ═══════════════════════════════════════════════════════════════════════════

class SystemConfiguration(TimeStampedModel):
    """
    Global system configuration
    Singleton model - only ONE record allowed
    Stores system-wide settings
    """
    
    # === COMPANY INFORMATION ===
    # Note: Tenant and Shop context are implicit in the schema; no FK references needed
    shop_address = models.TextField(blank=True, help_text="Shop address")
    shop_phone = models.CharField(max_length=20, blank=True)
    shop_email = models.EmailField(blank=True)
    shop_vat_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="VAT registration number"
    )
    shop_registration_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Company registration number"
    )
    
    # === SYSTEM SETTINGS ===
    default_tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        related_name='system_configs',
        null=True,
        blank=True,
        help_text="Default tax code for new items"
    )
    
    # Ageing periods (in days)
    ageing_periods = models.JSONField(
        default=list,
        help_text="Ageing periods in days [30, 60, 90, 120, 150, 180]"
    )
    
    # Financial year
    current_financial_year = models.PositiveIntegerField(
        default=2024,
        help_text="Current financial year (e.g., 2024)"
    )
    current_period = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Current accounting period (1-12)"
    )
    
    # === ACCOUNTING SETTINGS ===
    enable_negative_stock = models.BooleanField(
        default=False,
        help_text="Allow stock to go negative"
    )
    auto_post_transactions = models.BooleanField(
        default=False,
        help_text="Automatically post transactions"
    )
    
    # Debtor settings
    charge_interest_on_overdue = models.BooleanField(
        default=False,
        help_text="Charge interest on overdue debtor accounts"
    )
    default_interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Default interest rate percentage"
    )
    
    # === DISPLAY SETTINGS ===
    date_format = models.CharField(
        max_length=20,
        default='YYYY-MM-DD',
        help_text="Date display format"
    )
    currency_symbol = models.CharField(
        max_length=5,
        default='R',
        help_text="Currency symbol (e.g., R, $, €)"
    )
    decimal_places = models.PositiveIntegerField(
        default=2,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        help_text="Number of decimal places for currency"
    )
    
    class Meta:
        db_table = 'system_configuration'
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configuration'
    
    def __str__(self):
        return "System Configuration"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Get the singleton instance, creating with defaults if needed"""
        from django.utils import timezone
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'current_financial_year': timezone.now().year,
                'current_period': 1,
                'ageing_periods': [30, 60, 90, 120, 150, 180],
            }
        )
        return obj


# ═══════════════════════════════════════════════════════════════════════════
# MONTHLY STATISTICS MODELS (Historical Data)
# ═══════════════════════════════════════════════════════════════════════════

class DepartmentMonthlyStats(models.Model):
    """
    Historical monthly statistics for departments
    Created during month-end process
    """
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.CASCADE,
        related_name='monthly_stats'
    )
    
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    
    sales_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'department_monthly_stats'
        ordering = ['-year', '-month', 'department']
        unique_together = [['department', 'year', 'month']]
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['department']),
        ]
        verbose_name = 'Department Monthly Statistics'
        verbose_name_plural = 'Department Monthly Statistics'
    
    def __str__(self):
        return f"{self.department.name} - {self.year}/{self.month:02d}"


class SalesAreaMonthlyStats(models.Model):
    """
    Historical monthly statistics for sales areas
    Created during month-end process
    """
    sales_area = models.ForeignKey(
        SalesArea,
        on_delete=models.CASCADE,
        related_name='monthly_stats'
    )
    
    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    
    sales_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profit_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    commission_earned = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'sales_area_monthly_stats'
        ordering = ['-year', '-month', 'sales_area']
        unique_together = [['sales_area', 'year', 'month']]
        indexes = [
            models.Index(fields=['year', 'month']),
            models.Index(fields=['sales_area']),
        ]
        verbose_name = 'Sales Area Monthly Statistics'
        verbose_name_plural = 'Sales Area Monthly Statistics'
    
    def __str__(self):
        return f"{self.sales_area.name} - {self.year}/{self.month:02d}"