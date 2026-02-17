from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
from apps.creditors.models import Creditor
from apps.settings.models import TaxCode, SalesDepartment, SalesArea



class StockItem(models.Model):
    """Main Stock Item model"""
    
    stock_code = models.CharField(max_length=13, unique=True, primary_key=True)
    description = models.CharField(max_length=255)
    department = models.ForeignKey(SalesDepartment, on_delete=models.PROTECT, related_name='stock_items')
    supplier = models.ForeignKey(Creditor, on_delete=models.PROTECT, related_name='stock_items', null=True, blank=True)
    supplier_code = models.CharField(max_length=50, blank=True, null=True, help_text="Supplier's stock code")
    
    # Tax and pricing
    tax_code = models.ForeignKey(TaxCode, on_delete=models.PROTECT, related_name='stock_items', null=True, blank=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    average_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Selling prices (3 price levels) - SPRICE, SPRICE1, SPRICE2
    selling_price_1 = models.DecimalField(max_digits=12, decimal_places=4, default=0, validators=[MinValueValidator(0)], help_text="SPRICE - Selling Price 1")
    selling_price_2 = models.DecimalField(max_digits=12, decimal_places=4, default=0, validators=[MinValueValidator(0)], help_text="SPRICE1 - Selling Price 2")
    selling_price_3 = models.DecimalField(max_digits=12, decimal_places=4, default=0, validators=[MinValueValidator(0)], help_text="SPRICE2 - Selling Price 3")
    
    # Markup percentages for each price level
    markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Stock control - QOH (Quantity on Hand)
    quantity_on_hand = models.DecimalField(max_digits=14, decimal_places=4, default=0, help_text="QOH - Current stock quantity")
    quantity_allocated = models.DecimalField(
        max_digits=14, decimal_places=4, default=0,
        help_text="QTYBYSTOCK - Quantity allocated to batches/lots"
    )
    quantity_sale_order = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text="QTYSORD - Quantity reserved in sales orders"
    )
    quantity_counted = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Used during stock take")
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    quantity_on_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Settings
    default_selling_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    allow_negative_quantities = models.BooleanField(default=True)
    maximum_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Sales statistics
    sales_mtd_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sales_mtd_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sales_ytd_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sales_ytd_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit_mtd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gross_profit_ytd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Purchase statistics
    purchased_mtd_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    purchased_ytd_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Balance brought forward
    balance_bfwd_quantity = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    balance_bfwd_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    closing_stock_balance = models.DecimalField(max_digits=12, decimal_places=0, default=0)
    
    # Dates
    date_last_purchased = models.DateField(null=True, blank=True)
    date_last_sold = models.DateField(null=True, blank=True)
    last_supplier = models.ForeignKey(
        Creditor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='last_supplied_items',
        help_text="Last supplier used for this item"
    )
    
    # Bin location
    bin_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Weight
    weight = models.DecimalField(max_digits=8, decimal_places=2, default=0, blank=True, null=True, help_text="Weight of item")
    
    # Stock count flag
    stock_count_flag = models.CharField(max_length=1, blank=True, null=True, help_text="Stock count flag")
    
    # Flags
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'stock_items'
        ordering = ['stock_code']
        indexes = [
            models.Index(fields=['description']),
            models.Index(fields=['supplier', 'supplier_code']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f"{self.stock_code} - {self.description}"

    @property
    def available_quantity(self):
        """Calculate available quantity = QOH - allocated - sale_order"""
        return max(0, (self.quantity_on_hand - 
                      self.quantity_allocated - 
                      self.quantity_sale_order))

    def calculate_markup(self, price_level=1):
        """Calculate markup percentage for a given price level"""
        if self.cost_price > 0:
            selling_price = getattr(self, f'selling_price_{price_level}')
            return ((selling_price - self.cost_price) / self.cost_price) * 100
        return 0

    def calculate_gross_profit(self, price_level=1):
        """Calculate gross profit percentage"""
        selling_price = getattr(self, f'selling_price_{price_level}')
        if selling_price > 0:
            return ((selling_price - self.cost_price) / selling_price) * 100
        return 0

    def update_average_cost(self, new_quantity, new_cost):
        """
        Update average cost using weighted average cost method.
        Called when new stock is received.
        
        Args:
            new_quantity: Quantity of new stock received
            new_cost: Cost price of new stock
        """
        from decimal import Decimal
        
        new_quantity = Decimal(str(new_quantity))
        new_cost = Decimal(str(new_cost))
        current_qty = self.quantity_on_hand
        current_cost = self.average_cost
        
        if current_qty > 0:
            # Weighted average: (current_value + new_value) / (current_qty + new_qty)
            total_value = (current_qty * current_cost) + (new_quantity * new_cost)
            new_total_qty = current_qty + new_quantity
            self.average_cost = total_value / new_total_qty if new_total_qty > 0 else current_cost
        else:
            # First stock received
            self.average_cost = new_cost if new_quantity > 0 else 0
        
        self.save(update_fields=['average_cost'])

    def needs_reordering(self):
        """Check if available stock falls below reorder quantity"""
        return self.available_quantity <= self.reorder_quantity

    def is_overstocked(self):
        """Check if stock exceeds maximum level (if set)"""
        if hasattr(self, 'max_stock_level'):
            return self.quantity_on_hand > self.max_stock_level
        return False


class SpecialDeal(models.Model):
    """Special pricing for specific periods"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='special_deals')
    special_cost_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    special_selling_price_1 = models.DecimalField(max_digits=12, decimal_places=4, default=0, help_text="SPPRICE1")
    special_selling_price_2 = models.DecimalField(max_digits=12, decimal_places=4, default=0, help_text="SPPRICE2")
    special_selling_price_3 = models.DecimalField(max_digits=12, decimal_places=4, default=0, help_text="SPPRICE3")
    special_markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    special_markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    special_markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    start_date = models.DateField(help_text="SPECSTDATE - Special start date")
    end_date = models.DateField(help_text="SPECENDATE - Special end date")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'special_deals'
        ordering = ['-start_date']

    def __str__(self):
        return f"Special Deal: {self.stock_item.stock_code} ({self.start_date} to {self.end_date})"

    def is_valid_today(self):
        """Check if special deal is valid for today"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.is_active


class FuturePricing(models.Model):
    """Future pricing for stock items"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='future_prices')
    future_cost_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    future_selling_price_1 = models.DecimalField(max_digits=12, decimal_places=4, default=0, help_text="NEWPR - New price 1")
    future_selling_price_2 = models.DecimalField(max_digits=12, decimal_places=4, default=0, help_text="NEWPR1 - New price 2")
    future_selling_price_3 = models.DecimalField(max_digits=12, decimal_places=4, default=0, help_text="NEWPR2 - New price 3")
    future_markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    effective_date = models.DateField(help_text="NEWPRDATE - New price effective date")
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'future_pricing'
        ordering = ['effective_date']

    def __str__(self):
        return f"Future Price: {self.stock_item.stock_code} (Effective: {self.effective_date})"


class ShrinkWrap(models.Model):
    """Shrink wrap relationships between bulk and individual items (SHRINK table)"""
    shrink_pack_code = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='shrink_items',
        help_text="SCODE - Individual/shrink item code"
    )
    bulk_pack_code = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='shrink_bulks',
        help_text="BCODE - Bulk/main item code"
    )
    invoice_bulk_value = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=1.0,
        validators=[MinValueValidator(0.001)],
        help_text="SINBULK - Quantity/value in bulk"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shrink_wraps'
        unique_together = ['bulk_pack_code', 'shrink_pack_code']

    def __str__(self):
        return f"{self.shrink_pack_code.stock_code} -> {self.bulk_pack_code.stock_code} ({self.invoice_bulk_value})"


class PackBundle(models.Model):
    """Pack/Bundle finished products"""
    stock_item = models.OneToOneField(StockItem, on_delete=models.CASCADE, related_name='pack_bundle', primary_key=True)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pack_bundles'

    def __str__(self):
        return f"Pack/Bundle: {self.stock_item.stock_code}"

    def calculate_total_cost(self):
        """Calculate total cost from ingredients"""
        total = sum(
            ingredient.quantity * ingredient.ingredient_stock.cost_price
            for ingredient in self.ingredients.all()
        )
        self.total_cost = total
        self.save()
        return total


class PackBundleIngredient(models.Model):
    """Ingredients that make up a pack/bundle (BOM - Bill of Materials)"""
    pack_bundle = models.ForeignKey(PackBundle, on_delete=models.CASCADE, related_name='ingredients')
    ingredient_stock = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='used_in_bundles')
    quantity = models.DecimalField(max_digits=12, decimal_places=4, validators=[MinValueValidator(0.0001)], help_text="Quantity of ingredient in bundle")
    cost_at_creation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'pack_bundle_ingredients'
        unique_together = ['pack_bundle', 'ingredient_stock']

    def __str__(self):
        return f"{self.ingredient_stock.stock_code} in {self.pack_bundle.stock_item.stock_code}"

    def get_ingredient_value(self):
        """Calculate value of this ingredient"""
        return self.quantity * self.ingredient_stock.cost_price


class StockTransaction(models.Model):
    """Stock movement transactions"""
    
    TRANSACTION_TYPES = [
        ('INCOMING', 'Incoming Stock'),
        ('RETURN', 'Stock Return'),
        ('SALE', 'Sale'),
        ('SALE_RETURN', 'Sale Return'),
        ('ADJUSTMENT', 'Stock Adjustment'),
        ('STOCK_TAKE', 'Stock Take'),
        ('MANUFACTURE', 'Manufactured from Bundle'),
        ('BUNDLE_USE', 'Used in Bundle'),
        ('BULK_ISSUE', 'Issued from Bulk'),
        ('LAYBYE_IN', 'Laybye Issue'),
        ('LAYBYE_OUT', 'Laybye Return'),
        ('JOB_IN', 'Job Card Issue'),
        ('JOB_OUT', 'Job Card Return'),
        ('RFC_IN', 'RFC Issue'),
        ('RFC_OUT', 'RFC Return'),
    ]
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='transactions')
    transaction_date = models.DateField(default=timezone.now)
    transaction_time = models.TimeField(null=True, blank=True, help_text="Time of transaction (HH:MM)")
    transaction_number = models.CharField(max_length=50, blank=True, null=True)
    
    quantity_in = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_out = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    discount = models.DecimalField(max_digits=7, decimal_places=2, default=0, help_text="Discount applied")
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value = models.DecimalField(max_digits=14, decimal_places=4, default=0, help_text="Transaction value")
    
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_transactions',
        help_text="Department involved in transaction"
    )
    
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_transactions',
        help_text="Tax code for transaction"
    )
    
    debtor = models.ForeignKey(
        'debtors.Debtor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_transactions',
        help_text="Debtor account if applicable"
    )
    
    supplier = models.ForeignKey(
        Creditor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_transactions',
        help_text="Supplier account if applicable"
    )
    
    reference = models.CharField(max_length=255, blank=True, null=True)
    station_number = models.IntegerField(null=True, blank=True, help_text="Station/POS terminal number")
    comments = models.CharField(max_length=255, blank=True, null=True, help_text="Transaction comments")
    
    # Audit fields
    created_by = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock_transactions'
        ordering = ['-transaction_date', '-id']
        indexes = [
            models.Index(fields=['stock_item', 'transaction_date']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['transaction_date']),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.stock_item.stock_code} - {self.transaction_date}"


class StockTake(models.Model):
    """Stock take sessions"""
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('UPDATED', 'Updated'),
    ]
    
    stock_take_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    description = models.TextField(blank=True, null=True)
    
    # Update options
    reset_negatives_to_zero = models.BooleanField(default=False)
    set_uncounted_to_zero = models.BooleanField(default=False)
    
    # After trading options
    is_after_trading = models.BooleanField(default=False)
    trading_start_date = models.DateTimeField(null=True, blank=True)
    
    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'stock_takes'
        ordering = ['-stock_take_date']

    def __str__(self):
        return f"Stock Take - {self.stock_take_date} ({self.status})"


class StockTakeItem(models.Model):
    """Individual items counted in a stock take"""
    stock_take = models.ForeignKey(StockTake, on_delete=models.CASCADE, related_name='items')
    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='stock_take_items')
    
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, help_text="System quantity before count")
    quantity_counted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    variance_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    variance_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    cost_price_at_count = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    is_counted = models.BooleanField(default=False)
    count_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock_take_items'
        unique_together = ['stock_take', 'stock_item']
        indexes = [
            models.Index(fields=['stock_take', 'is_counted']),
        ]

    def __str__(self):
        return f"{self.stock_item.stock_code} - Count: {self.quantity_counted}"

    def calculate_variance(self):
        """Calculate variance between counted and system quantity"""
        self.variance_quantity = self.quantity_counted - self.quantity_on_hand
        self.variance_value = self.variance_quantity * self.cost_price_at_count
        self.save()


class ContractPricing(models.Model):
    """Contract pricing for specific debtors"""
    
    PRICING_METHOD_CHOICES = [
        ('ACTUAL', 'Actual Price'),
        ('COST_MARKUP', 'Cost + Markup%'),
    ]
    
    debtor = models.ForeignKey('debtors.Debtor', on_delete=models.CASCADE, related_name='contract_prices')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='contract_prices', null=True, blank=True)
    department = models.ForeignKey(SalesDepartment, on_delete=models.CASCADE, related_name='contract_prices', null=True, blank=True)
    supplier = models.ForeignKey(Creditor, on_delete=models.CASCADE, related_name='contract_prices', null=True, blank=True)
    
    pricing_method = models.CharField(max_length=20, choices=PRICING_METHOD_CHOICES)
    
    # For actual price method
    contract_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # For cost + markup method
    markup_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # For discount methods
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Last selling price
    last_selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="LSELL - Last transaction selling price"
    )
    last_updated_date = models.DateField(
        null=True,
        blank=True,
        help_text="LUPDATE - Last update date for contract"
    )
    
    # Fixed pricing flag
    is_fixed_pricing = models.BooleanField(default=False, help_text="FIXEDPRICE - Prevent POS from changing price")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'contract_pricing'
        indexes = [
            models.Index(fields=['debtor', 'stock_item']),
            models.Index(fields=['debtor', 'department']),
            models.Index(fields=['debtor', 'supplier']),
        ]

    def __str__(self):
        item_desc = self.stock_item.stock_code if self.stock_item else (
            self.department.department_name if self.department else 
            self.supplier.name if self.supplier else "General"
        )
        return f"Contract: {self.debtor.account_number} - {item_desc}"

    def get_price(self, stock_item=None):
        """Calculate contract price based on method"""
        if self.pricing_method == 'ACTUAL':
            return self.contract_price
        elif self.pricing_method == 'COST_MARKUP' and stock_item:
            return stock_item.cost_price * (1 + self.markup_percent / 100)
        return None


class OneTouchLookupKey(models.Model):
    """One-touch keyboard shortcuts for stock items at POS"""
    key_character = models.CharField(max_length=1, unique=True, help_text="Single uppercase letter")
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='lookup_keys')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'one_touch_lookup_keys'

    def __str__(self):
        return f"{self.key_character} -> {self.stock_item.stock_code}"


class StockMonthlyStatistic(models.Model):
    """Monthly sales statistics for stock items"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='monthly_stats')
    year = models.IntegerField()
    month = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    
    quantity_sold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_sold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'stock_monthly_statistics'
        unique_together = ['stock_item', 'year', 'month']
        ordering = ['-year', '-month']

    def __str__(self):
        return f"{self.stock_item.stock_code} - {self.year}/{self.month}"


# ============================================================================
# Phase 1: Branch Management Models
# ============================================================================

class Branch(models.Model):
    """Branch/Location model for multi-branch stock management"""
    
    BRANCH_TYPE_CHOICES = [
        ('RETAIL', 'Retail Store'),
        ('WAREHOUSE', 'Warehouse'),
        ('HQ', 'Headquarters'),
    ]
    
    branch_code = models.CharField(max_length=10, unique=True, primary_key=True, help_text="e.g., BR001, WH01")
    branch_name = models.CharField(max_length=100)
    branch_type = models.CharField(max_length=20, choices=BRANCH_TYPE_CHOICES)
    address = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text="Whether branch is operational")
    is_default = models.BooleanField(default=False, help_text="Default branch for the tenant")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = 'branches'
        ordering = ['branch_code']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['is_default']),
            models.Index(fields=['branch_type']),
        ]

    def __str__(self):
        return f"{self.branch_code} - {self.branch_name}"


class BranchStock(models.Model):
    """Stock quantity tracking per branch"""
    
    id = models.BigAutoField(primary_key=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='branch_stocks')
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='branch_stocks')
    
    quantity = models.DecimalField(max_digits=14, decimal_places=4, default=0, help_text="Current quantity at branch")
    quantity_allocated = models.DecimalField(max_digits=14, decimal_places=4, default=0, help_text="Reserved for transfers/orders")
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Per-branch reorder level")
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Per-branch reorder quantity")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branch_stocks'
        unique_together = ['branch', 'stock_item']
        ordering = ['branch', 'stock_item']
        indexes = [
            models.Index(fields=['branch', 'quantity']),
            models.Index(fields=['stock_item', 'branch']),
        ]

    def __str__(self):
        return f"{self.branch.branch_code} - {self.stock_item.stock_code} ({self.quantity})"

    @property
    def available_quantity(self):
        """Calculate available quantity = quantity - allocated"""
        return max(Decimal('0'), (self.quantity - self.quantity_allocated))


# ============================================================================
# Phase 3: Group Orders
# ============================================================================

class GroupOrder(models.Model):
    """Group order model for consolidating multiple orders"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    group_order_number = models.CharField(max_length=20, unique=True, help_text="e.g., GRP-2024-0001")
    order_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='group_orders')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_group_orders')
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_orders'
        ordering = ['-order_date', '-group_order_number']
        indexes = [
            models.Index(fields=['status', 'branch']),
            models.Index(fields=['order_date']),
        ]

    def __str__(self):
        return f"{self.group_order_number} - {self.status}"

    def calculate_total_amount(self):
        """Calculate total from items"""
        total = sum(item.line_total for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])
        return total


class GroupOrderItem(models.Model):
    """Individual items in a group order"""
    
    id = models.BigAutoField(primary_key=True)
    group_order = models.ForeignKey(GroupOrder, on_delete=models.CASCADE, related_name='items')
    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='group_order_items')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'group_order_items'
        unique_together = ['group_order', 'stock_item']
        ordering = ['stock_item']

    def __str__(self):
        return f"{self.group_order.group_order_number} - {self.stock_item.stock_code}"

    def save(self, *args, **kwargs):
        """Recalculate line total on save"""
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ============================================================================
# Phase 4: IBT - Inter-Branch Transfer
# ============================================================================

class BranchTransfer(models.Model):
    """Inter-branch transfer request"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('DISPATCHED', 'Dispatched'),
        ('IN_TRANSIT', 'In Transit'),
        ('RECEIVED', 'Received'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    TRANSFER_TYPE_CHOICES = [
        ('STANDARD', 'Standard Transfer'),
        ('URGENT', 'Urgent Transfer'),
        ('RETURN', 'Return Transfer'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    transfer_number = models.CharField(max_length=20, unique=True, help_text="e.g., IBT-2024-0001")
    from_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_out')
    to_branch = models.ForeignKey(Branch, on_delete=models.PROTECT, related_name='transfers_in')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPE_CHOICES, default='STANDARD')
    
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_requested')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_approved')
    dispatched_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_dispatched')
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_received')
    
    requested_date = models.DateTimeField(default=timezone.now)
    approved_date = models.DateTimeField(null=True, blank=True)
    dispatched_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branch_transfers'
        ordering = ['-requested_date', '-transfer_number']
        indexes = [
            models.Index(fields=['status', 'from_branch']),
            models.Index(fields=['status', 'to_branch']),
            models.Index(fields=['requested_date']),
            models.Index(fields=['transfer_type']),
        ]

    def __str__(self):
        return f"{self.transfer_number} - {self.from_branch.branch_code} → {self.to_branch.branch_code}: {self.status}"


class BranchTransferItem(models.Model):
    """Individual items in a branch transfer"""
    
    id = models.BigAutoField(primary_key=True)
    transfer = models.ForeignKey(BranchTransfer, on_delete=models.CASCADE, related_name='items')
    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='transfer_items')
    
    quantity_requested = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_dispatched = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Calculated on receive")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branch_transfer_items'
        unique_together = ['transfer', 'stock_item']
        ordering = ['stock_item']

    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.stock_item.stock_code}"

    def save(self, *args, **kwargs):
        """Calculate variance on save"""
        self.variance = self.quantity_received - self.quantity_requested
        super().save(*args, **kwargs)


# ============================================================================
# Phase 5: IBI - Inter-Branch Invoicing
# ============================================================================

class BranchTransferInvoice(models.Model):
    """Invoice for inter-branch transfers"""
    
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('ISSUED', 'Issued'),
        ('PAID', 'Paid'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    id = models.BigAutoField(primary_key=True)
    transfer = models.OneToOneField(BranchTransfer, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=20, unique=True, help_text="e.g., IBI-2024-0001")
    invoice_date = models.DateField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'branch_transfer_invoices'
        ordering = ['-invoice_date', '-invoice_number']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['invoice_date']),
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.status}"