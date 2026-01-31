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
- Sales Areas (salesmen/territories)
- Income Categories (cash book income types)
- Expense Categories (expense types)
- Tax Codes (VAT rates)
- Payment Methods
- Credit Terms
- System Configuration (global settings)

DEPENDS ON: Nothing - this is the foundation

Models in this file (10 + 2 abstract):
- TimeStampedModel (abstract)
- ActiveModel (abstract)
- SalesDepartment
- SalesArea
- IncomeCategory
- ExpenseCategory
- TaxCode
- PaymentMethod
- CreditTerms
- SystemConfiguration
- DepartmentMonthlyStats
- SalesAreaMonthlyStats
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
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
        unique=True,
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
    company_name = models.CharField(
        max_length=200,
        help_text="Company name"
    )
    company_address = models.TextField(blank=True)
    company_phone = models.CharField(max_length=20, blank=True)
    company_email = models.EmailField(blank=True)
    company_vat_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="VAT registration number"
    )
    company_registration_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Company registration number"
    )
    
    # === SYSTEM SETTINGS ===
    default_tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        related_name='system_configs',
        help_text="Default tax code for new items"
    )
    
    # Ageing periods (in days)
    ageing_periods = models.JSONField(
        default=list,
        help_text="Ageing periods in days [30, 60, 90, 120, 150, 180]"
    )
    
    # Financial year
    current_financial_year = models.PositiveIntegerField(
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
        return f"System Config - {self.company_name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        """Get the singleton instance"""
        obj, created = cls.objects.get_or_create(pk=1)
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