from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
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
    
    # Selling prices (3 price levels)
    selling_price_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    selling_price_2 = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    selling_price_3 = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    # Markup percentages for each price level
    markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Stock control
    quantity_on_hand = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    
    # Dates
    date_last_purchased = models.DateField(null=True, blank=True)
    date_last_sold = models.DateField(null=True, blank=True)
    
    # Bin location
    bin_number = models.CharField(max_length=50, blank=True, null=True)
    
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


class SpecialDeal(models.Model):
    """Special pricing for specific periods"""
    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='special_deals')
    special_cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    special_selling_price_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_selling_price_2 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_selling_price_3 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    special_markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    special_markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    special_markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    start_date = models.DateField()
    end_date = models.DateField()
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
    future_cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    future_selling_price_1 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    future_selling_price_2 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    future_selling_price_3 = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    future_markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    effective_date = models.DateField()
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'future_pricing'
        ordering = ['effective_date']

    def __str__(self):
        return f"Future Price: {self.stock_item.stock_code} (Effective: {self.effective_date})"


class ShrinkWrap(models.Model):
    """Shrink wrap relationships between bulk and individual items"""
    bulk_pack_code = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='shrink_bulks')
    shrink_pack_code = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='shrink_items')
    quantity_in_bulk = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shrink_wraps'
        unique_together = ['bulk_pack_code', 'shrink_pack_code']

    def __str__(self):
        return f"{self.shrink_pack_code.stock_code} -> {self.bulk_pack_code.stock_code} ({self.quantity_in_bulk})"


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
    """Ingredients that make up a pack/bundle"""
    pack_bundle = models.ForeignKey(PackBundle, on_delete=models.CASCADE, related_name='ingredients')
    ingredient_stock = models.ForeignKey(StockItem, on_delete=models.PROTECT, related_name='used_in_bundles')
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
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
    transaction_date = models.DateTimeField(default=timezone.now)
    transaction_number = models.CharField(max_length=50, blank=True, null=True)
    
    quantity_in = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_out = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    reference = models.CharField(max_length=255, blank=True, null=True)
    station_number = models.IntegerField(null=True, blank=True, help_text="Station number for stock take updates")
    
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
    
    # Fixed pricing flag
    is_fixed_pricing = models.BooleanField(default=False, help_text="Prevent POS from changing price")
    
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