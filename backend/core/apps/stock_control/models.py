"""
STOCK APP - Django Models
Complete inventory/stock control models

LOCATION: accpick_project/stock/models.py

Models in this file:
- StockItem (main inventory item)
- StockMovement (all stock movements)
- StockTake (stock count sessions)
- StockTakeItem (individual items counted)
- StockAdjustment (manual adjustments)
- SpecialDeal (temporary pricing)
- FuturePrice (scheduled price changes)
- ContractPrice (customer-specific pricing)
- Bundle (pack/bundle/recipe)
- BundleIngredient (items in a bundle)
- ShrinkWrapRelationship (bulk to unit conversion)
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from decimal import Decimal
from apps.settings.models import (
    SalesDepartment,
    TaxCode,
    TimeStampedModel,
    ActiveModel
)

User = get_user_model()


# ============================================================================
# STOCK ITEM MODEL (Main Inventory)
# ============================================================================

class StockItem(TimeStampedModel, ActiveModel):
    """
    Main stock/inventory item
    Supports multiple price levels, bundles, and complex pricing
    """
    
    # === USER INPUT FIELDS ===
    
    # Identification
    stock_code = models.CharField(
        max_length=13,
        unique=True,
        help_text="Stock code (1-13 alphanumeric)"
    )
    description = models.CharField(max_length=200)
    
    # Categorization
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.PROTECT,
        related_name='stock_items',
        help_text="Sales department/category"
    )
    
    # Tax
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        related_name='stock_items',
        help_text="Default tax code (1=14%, 2=0%)"
    )
    
    # Supplier information
    supplier = models.ForeignKey(
        'creditors.Creditor',
        on_delete=models.PROTECT,
        related_name='supplied_items',
        help_text="Preferred supplier"
    )
    supplier_code = models.CharField(
        max_length=50,
        blank=True,
        help_text="Supplier's stock code"
    )
    
    # Stock control
    reorder_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Re-order level (below this = order more)"
    )
    default_selling_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=1,
        help_text="Default quantity for sales"
    )
    allow_negative_quantities = models.BooleanField(
        default=False,
        help_text="Allow stock to go negative"
    )
    
    # Pricing
    cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Current cost price (exclusive of VAT)"
    )
    
    # Multiple selling prices
    markup_percent_1 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Markup % for selling price 1"
    )
    selling_price_1 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Selling price level 1"
    )
    
    markup_percent_2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Markup % for selling price 2"
    )
    selling_price_2 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Selling price level 2"
    )
    
    markup_percent_3 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Markup % for selling price 3"
    )
    selling_price_3 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Selling price level 3"
    )
    
    # Discount control
    maximum_discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Maximum discount allowed at POS"
    )
    
    # === SYSTEM GENERATED FIELDS ===
    
    # Quantities
    quantity_on_hand = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Current stock on hand"
    )
    quantity_on_order = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Quantity on purchase orders"
    )
    quantity_on_sales_order = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Quantity on sales orders"
    )
    quantity_on_layby = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Quantity on laybys"
    )
    quantity_rfc = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Quantity on Returns For Credit"
    )
    
    # Cost tracking
    average_cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Weighted average cost"
    )
    last_cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Last purchase cost"
    )
    
    # Sales statistics
    sales_quantity_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales quantity Month-to-Date"
    )
    sales_quantity_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales quantity Year-to-Date"
    )
    sales_value_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales value Month-to-Date"
    )
    sales_value_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sales value Year-to-Date"
    )
    gross_profit_mtd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Gross profit Month-to-Date"
    )
    gross_profit_ytd = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Gross profit Year-to-Date"
    )
    
    # Dates
    date_last_purchased = models.DateField(null=True, blank=True, editable=False)
    date_last_sold = models.DateField(null=True, blank=True, editable=False)
    
    class Meta:
        db_table = 'stock_items'
        ordering = ['stock_code']
        indexes = [
            models.Index(fields=['stock_code']),
            models.Index(fields=['description']),
            models.Index(fields=['department']),
            models.Index(fields=['supplier']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = 'Stock Item'
        verbose_name_plural = 'Stock Items'
    
    def __str__(self):
        return f"{self.stock_code} - {self.description}"
    
    @property
    def available_quantity(self):
        """Calculate available quantity (on hand - committed)"""
        return self.quantity_on_hand - self.quantity_on_sales_order - self.quantity_on_layby
    
    @property
    def stock_value(self):
        """Current stock value at cost"""
        return self.quantity_on_hand * self.cost_price
    
    @property
    def needs_reorder(self):
        """Check if stock needs reordering"""
        return self.quantity_on_hand <= self.reorder_quantity
    
    @property
    def gross_profit_percent_mtd(self):
        """Calculate GP% for MTD"""
        if self.sales_value_mtd > 0:
            return (self.gross_profit_mtd / self.sales_value_mtd) * 100
        return 0
    
    @property
    def gross_profit_percent_ytd(self):
        """Calculate GP% for YTD"""
        if self.sales_value_ytd > 0:
            return (self.gross_profit_ytd / self.sales_value_ytd) * 100
        return 0


# ============================================================================
# STOCK MOVEMENT MODEL
# ============================================================================

class StockMovement(TimeStampedModel):
    """
    Tracks all stock movements (in and out)
    Complete audit trail of stock changes
    """
    
    MOVEMENT_TYPE_CHOICES = [
        ('RECEIPT', 'Stock Receipt'),
        ('RETURN', 'Stock Return to Supplier'),
        ('SALE', 'Sale'),
        ('SALE_RETURN', 'Sales Return'),
        ('ADJUSTMENT', 'Stock Adjustment'),
        ('STOCKTAKE', 'Stock Take Adjustment'),
        ('TRANSFER', 'Stock Transfer'),
        ('BUNDLE_MAKE', 'Bundle Created (ingredients out)'),
        ('BUNDLE_BREAK', 'Bundle Broken (ingredients in)'),
        ('SHRINK_ISSUE', 'Shrink Issued from Bulk'),
        ('LAYBY_IN', 'To Layby'),
        ('LAYBY_OUT', 'From Layby'),
        ('RFC_OUT', 'To Returns For Credit'),
        ('RFC_IN', 'From Returns For Credit'),
        ('JOB_OUT', 'To Job Card'),
        ('JOB_IN', 'From Job Card'),
    ]
    
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name='movements'
    )
    
    movement_type = models.CharField(
        max_length=20,
        choices=MOVEMENT_TYPE_CHOICES
    )
    movement_date = models.DateField()
    
    # Quantities
    quantity_in = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Quantity added to stock"
    )
    quantity_out = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Quantity removed from stock"
    )
    quantity_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Stock balance after this movement"
    )
    
    # Value
    unit_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Cost per unit at time of movement"
    )
    
    # Reference to source transaction
    transaction_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="E.g., Invoice, GRN, StockTake"
    )
    transaction_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Source transaction number"
    )
    
    # Additional details
    reference = models.CharField(
        max_length=200,
        blank=True,
        help_text="Additional reference"
    )
    
    # User who created this movement
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements_created'
    )
    
    class Meta:
        db_table = 'stock_movements'
        ordering = ['-movement_date', '-created_at']
        indexes = [
            models.Index(fields=['stock_item', 'movement_date']),
            models.Index(fields=['movement_type']),
            models.Index(fields=['transaction_number']),
        ]
        verbose_name = 'Stock Movement'
        verbose_name_plural = 'Stock Movements'
    
    def __str__(self):
        return f"{self.stock_item.stock_code} - {self.movement_type} - {self.movement_date}"


# ============================================================================
# STOCK TAKE MODELS
# ============================================================================

class StockTake(TimeStampedModel):
    """
    Stock take session (header)
    Groups all items counted in one stock take
    """
    
    stocktake_date = models.DateField()
    
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed (not updated)'),
        ('UPDATED', 'Updated to System'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='IN_PROGRESS'
    )
    
    # Update options
    reset_negative_to_zero = models.BooleanField(
        default=False,
        help_text="Set negative quantities to zero"
    )
    set_uncounted_to_zero = models.BooleanField(
        default=False,
        help_text="Set uncounted items to zero"
    )
    
    # For "after trading" update
    update_from_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="If updated after trading, from when?"
    )
    
    # Who performed the stock take
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stocktakes_performed'
    )
    
    # When updated to system
    updated_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stocktakes_updated'
    )
    
    class Meta:
        db_table = 'stock_takes'
        ordering = ['-stocktake_date']
        verbose_name = 'Stock Take'
        verbose_name_plural = 'Stock Takes'
    
    def __str__(self):
        return f"Stock Take {self.stocktake_date} - {self.status}"


class StockTakeItem(models.Model):
    """
    Individual item counted in stock take
    """
    stocktake = models.ForeignKey(
        StockTake,
        on_delete=models.CASCADE,
        related_name='items'
    )
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name='stocktake_items'
    )
    
    # System quantity before count
    quantity_system = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Quantity on system before count"
    )
    
    # Counted quantity
    quantity_counted = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Quantity counted"
    )
    
    # Variance
    quantity_variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False,
        help_text="Difference (counted - system)"
    )
    value_variance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False,
        help_text="Variance value"
    )
    
    class Meta:
        db_table = 'stock_take_items'
        unique_together = [['stocktake', 'stock_item']]
        verbose_name = 'Stock Take Item'
        verbose_name_plural = 'Stock Take Items'
    
    def save(self, *args, **kwargs):
        # Calculate variance
        self.quantity_variance = self.quantity_counted - self.quantity_system
        self.value_variance = self.quantity_variance * self.stock_item.cost_price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.stock_item.stock_code} - Counted: {self.quantity_counted}"


# ============================================================================
# STOCK ADJUSTMENT MODEL
# ============================================================================

class StockAdjustment(TimeStampedModel):
    """
    Manual stock adjustments (not from stock take)
    """
    
    ADJUSTMENT_TYPE_CHOICES = [
        ('INCREASE', 'Increase Stock'),
        ('DECREASE', 'Decrease Stock'),
        ('CORRECTION', 'Correction'),
    ]
    
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name='adjustments'
    )
    
    adjustment_date = models.DateField()
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    
    quantity_before = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    adjustment_quantity = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Quantity to add (+) or remove (-)"
    )
    quantity_after = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        editable=False
    )
    
    reason = models.TextField(help_text="Reason for adjustment")
    reference = models.CharField(max_length=100, blank=True)
    
    is_posted = models.BooleanField(default=False)
    posted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adjustments_posted'
    )
    
    class Meta:
        db_table = 'stock_adjustments'
        ordering = ['-adjustment_date']
        verbose_name = 'Stock Adjustment'
        verbose_name_plural = 'Stock Adjustments'
    
    def __str__(self):
        return f"{self.stock_item.stock_code} - {self.adjustment_type} - {self.adjustment_quantity}"


# ============================================================================
# SPECIAL DEAL MODEL (Temporary Pricing)
# ============================================================================

class SpecialDeal(TimeStampedModel):
    """
    Temporary special pricing for items or departments
    """
    
    DEAL_TYPE_CHOICES = [
        ('ITEM', 'Specific Item'),
        ('DEPARTMENT', 'Entire Department'),
    ]
    
    deal_type = models.CharField(max_length=20, choices=DEAL_TYPE_CHOICES)
    
    # Link to item or department
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='special_deals'
    )
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='special_deals'
    )
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Special pricing
    special_cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Special cost price"
    )
    
    special_markup_1 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    special_selling_price_1 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    special_markup_2 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    special_selling_price_2 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    special_markup_3 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    special_selling_price_3 = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    
    class Meta:
        db_table = 'special_deals'
        ordering = ['-start_date']
        verbose_name = 'Special Deal'
        verbose_name_plural = 'Special Deals'
    
    @property
    def is_active(self):
        """Check if deal is currently active"""
        from django.utils import timezone
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date
    
    def __str__(self):
        if self.stock_item:
            return f"Special: {self.stock_item.stock_code} ({self.start_date} to {self.end_date})"
        return f"Special: Dept {self.department.number} ({self.start_date} to {self.end_date})"


# ============================================================================
# FUTURE PRICE MODEL
# ============================================================================

class FuturePrice(TimeStampedModel):
    """
    Scheduled future price changes
    Auto-updates on specified date
    """
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='future_prices'
    )
    
    effective_date = models.DateField(help_text="Date from which prices are effective")
    
    future_cost_price = models.DecimalField(max_digits=15, decimal_places=2)
    
    future_markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_selling_price_1 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    future_markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_selling_price_2 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    future_markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_selling_price_3 = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    is_applied = models.BooleanField(
        default=False,
        help_text="Has been applied to stock item"
    )
    applied_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'future_prices'
        ordering = ['effective_date']
        verbose_name = 'Future Price'
        verbose_name_plural = 'Future Prices'
    
    def __str__(self):
        return f"{self.stock_item.stock_code} - Effective {self.effective_date}"


# ============================================================================
# CONTRACT PRICING MODELS
# ============================================================================

class ContractPrice(TimeStampedModel):
    """
    Customer-specific contract pricing
    """
    debtor = models.ForeignKey(
        'debtors.Debtor',
        on_delete=models.CASCADE,
        related_name='contract_prices'
    )
    
    fixed_pricing = models.BooleanField(
        default=False,
        help_text="Cannot override at POS"
    )
    
    class Meta:
        db_table = 'contract_prices'
        verbose_name = 'Contract Price'
        verbose_name_plural = 'Contract Prices'
    
    def __str__(self):
        return f"Contract for {self.debtor.name}"


class ContractPriceItem(models.Model):
    """
    Individual items/rules in contract
    """
    contract = models.ForeignKey(
        ContractPrice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    
    PRICING_TYPE_CHOICES = [
        ('FIXED', 'Fixed Price per Item'),
        ('DEPT_DISCOUNT', 'Department Discount %'),
        ('DEPT_MARKUP', 'Department Markup %'),
        ('SUPPLIER_DISCOUNT', 'Supplier Discount %'),
        ('SUPPLIER_MARKUP', 'Supplier Markup %'),
        ('SUPPLIER_DEPT_DISCOUNT', 'Supplier+Dept Discount %'),
    ]
    
    pricing_type = models.CharField(max_length=30, choices=PRICING_TYPE_CHOICES)
    
    # Links (depending on type)
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='contract_price_items'
    )
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    supplier = models.ForeignKey(
        'creditors.Creditor',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    
    # Pricing
    contract_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Fixed price (if FIXED type)"
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Discount % (if discount type)"
    )
    markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Markup % (if markup type)"
    )
    
    class Meta:
        db_table = 'contract_price_items'
        verbose_name = 'Contract Price Item'
        verbose_name_plural = 'Contract Price Items'


# ============================================================================
# BUNDLE (PACK) MODELS
# ============================================================================

class Bundle(TimeStampedModel):
    """
    Bundle/Pack/Recipe - Finished product made from ingredients
    """
    # The bundle IS a stock item
    stock_item = models.OneToOneField(
        StockItem,
        on_delete=models.CASCADE,
        related_name='bundle',
        primary_key=True
    )
    
    calculated_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        editable=False,
        help_text="Sum of ingredient costs"
    )
    
    class Meta:
        db_table = 'bundles'
        verbose_name = 'Bundle/Pack'
        verbose_name_plural = 'Bundles/Packs'
    
    def __str__(self):
        return f"Bundle: {self.stock_item.stock_code}"
    
    def calculate_cost(self):
        """Calculate total cost from ingredients"""
        total = sum(
            ingredient.quantity_required * ingredient.ingredient_item.cost_price
            for ingredient in self.ingredients.all()
        )
        self.calculated_cost = total
        self.save()
        return total


class BundleIngredient(models.Model):
    """
    Ingredients in a bundle
    """
    bundle = models.ForeignKey(
        Bundle,
        on_delete=models.CASCADE,
        related_name='ingredients'
    )
    ingredient_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name='used_in_bundles',
        help_text="Stock item used as ingredient"
    )
    quantity_required = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Quantity needed per bundle"
    )
    
    class Meta:
        db_table = 'bundle_ingredients'
        unique_together = [['bundle', 'ingredient_item']]
        verbose_name = 'Bundle Ingredient'
        verbose_name_plural = 'Bundle Ingredients'
    
    @property
    def ingredient_cost(self):
        """Cost of this ingredient"""
        return self.quantity_required * self.ingredient_item.cost_price
    
    def __str__(self):
        return f"{self.ingredient_item.stock_code} x {self.quantity_required}"


# ============================================================================
# SHRINK WRAP RELATIONSHIP MODEL
# ============================================================================

class ShrinkWrapRelationship(TimeStampedModel):
    """
    Relationship between bulk pack and shrink/unit
    E.g., 48-pack box → individual units
    """
    shrink_pack = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='as_shrink',
        help_text="The smaller unit/shrink"
    )
    bulk_pack = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name='as_bulk',
        help_text="The larger bulk pack"
    )
    
    quantity_in_bulk = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="How many shrinks in one bulk (e.g., 48)"
    )
    
    class Meta:
        db_table = 'shrink_wrap_relationships'
        unique_together = [['shrink_pack', 'bulk_pack']]
        verbose_name = 'Shrink Wrap Relationship'
        verbose_name_plural = 'Shrink Wrap Relationships'
    
    def __str__(self):
        return f"{self.bulk_pack.stock_code} → {self.quantity_in_bulk} x {self.shrink_pack.stock_code}"