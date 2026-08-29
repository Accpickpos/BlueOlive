from decimal import Decimal

from apps.creditors.models import Creditor
from apps.settings.models import SalesArea, SalesDepartment, TaxCode
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class StockItem(models.Model):
    """Main Stock Item model - mapped from smast.dbf"""

    # CODE C 13
    stock_code = models.CharField(max_length=13, unique=True, primary_key=True)
    # DESCRIP C 30
    description = models.CharField(max_length=30)
    # DEPT C 3
    department = models.ForeignKey(
        SalesDepartment, on_delete=models.PROTECT, related_name="stock_items"
    )
    # SUPNO N 4
    supplier = models.ForeignKey(
        Creditor,
        on_delete=models.PROTECT,
        related_name="stock_items",
        null=True,
        blank=True,
    )
    # SUPCODE C 20
    supplier_code = models.CharField(
        max_length=20, blank=True, null=True, help_text="Supplier's stock code"
    )

    # Tax and pricing
    # TAXIND N 1
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.PROTECT,
        related_name="stock_items",
        null=True,
        blank=True,
    )
    # CPRICE N 12,2
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    # AVECOST N 12,2
    average_cost = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    # Selling prices (3 price levels) - SPRICE, SPRICE1, SPRICE2
    # SPRICE N 12,4
    selling_price_1 = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="SPRICE - Selling Price 1",
    )
    # SPRICE1 N 12,4
    selling_price_2 = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="SPRICE1 - Selling Price 2",
    )
    # SPRICE2 N 12,4
    selling_price_3 = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="SPRICE2 - Selling Price 3",
    )

    # Markup percentages for each price level
    # MUP N 6,2
    markup_1 = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    # MUP1 N 6,2
    markup_2 = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    # MUP2 N 6,2
    markup_3 = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    # Stock control
    # QOH N 14,4
    quantity_on_hand = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
        help_text="QOH - Current stock quantity",
    )
    # QTYBYSTOCK N 12,2
    quantity_allocated = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="QTYBYSTOCK - Quantity allocated to batches/lots",
    )
    # QTYSORD N 10,2
    quantity_sale_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="QTYSORD - Quantity reserved in sales orders",
    )
    # QTYPORD N 10,2
    quantity_on_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="QTYPORD - Quantity on purchase order",
    )
    quantity_counted = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, help_text="Used during stock take"
    )
    # REORD N 10,2
    reorder_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    # Settings
    # SELLQTY N 10,2
    default_selling_quantity = models.DecimalField(
        max_digits=10, decimal_places=2, default=1
    )
    # ALLOWNEGSL C 1
    allow_negative_quantities = models.BooleanField(default=True)
    # MAXDISC N 6,2
    maximum_discount_percent = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    # Sales statistics
    # QSOLDM N 10,2
    sales_mtd_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # VSOLDM N 12,2
    sales_mtd_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # QSOLDY N 10,2
    sales_ytd_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # VSOLDY N 12,2
    sales_ytd_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # GPM N 12,2
    gross_profit_mtd = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # GPY N 12,2
    gross_profit_ytd = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Purchase statistics
    # QTYPURCHM N 12,2
    purchased_mtd_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )
    # QTYPURCHY N 12,2
    purchased_ytd_quantity = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    # Balance brought forward
    # BFWDQTY N 14,4
    balance_bfwd_quantity = models.DecimalField(
        max_digits=14, decimal_places=4, default=0
    )
    # BFWDVAL N 10,2
    balance_bfwd_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # CLOSTOCK N 12,0
    closing_stock_balance = models.DecimalField(
        max_digits=12, decimal_places=0, default=0
    )

    # Brought-forward values for sub-ledgers
    # JCBFWDVAL N 14,2
    job_card_bfwd_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="JCBFWDVAL - Job card brought-forward value",
    )
    # LBBFWDVAL N 14,2
    laybye_bfwd_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="LBBFWDVAL - Laybye brought-forward value",
    )
    # RFBFWDVAL N 14,2
    rfc_bfwd_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="RFBFWDVAL - RFC (Repair/Field Call) brought-forward value",
    )

    # Dates
    # DATELPURCH D 8
    date_last_purchased = models.DateField(null=True, blank=True)
    # DATELSOLD D 8
    date_last_sold = models.DateField(null=True, blank=True)
    # LASTSUP N 4
    last_supplier = models.ForeignKey(
        Creditor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="last_supplied_items",
        help_text="Last supplier used for this item",
    )

    # Bin location - BIN N 4 (numeric in DBF)
    bin_number = models.IntegerField(
        blank=True, null=True, help_text="BIN - Bin/shelf location number"
    )

    # Weight - WEIGHT N 8,2
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        blank=True,
        null=True,
        help_text="Weight of item",
    )

    # Stock count flag - SCOUNTFLAG C 1
    stock_count_flag = models.CharField(
        max_length=1, blank=True, null=True, help_text="Stock count flag"
    )

    # Pack/bundle code - PACK C 10
    pack_code = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="PACK - Pack or bundle group code",
    )

    # KVI flag - KVI C 1
    kvi_flag = models.CharField(
        max_length=1, blank=True, null=True, help_text="KVI - Known Value Item flag"
    )

    # Barcode - no legacy DBF equivalent, not unique (real-world barcode data
    # is messy: duplicates, reused codes across suppliers) - stock_code
    # already carries uniqueness as the primary key.
    barcode = models.CharField(
        max_length=20, blank=True, null=True, help_text="Barcode/EAN for scanner lookup"
    )

    # Flags
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "stock_items"
        ordering = ["stock_code"]
        indexes = [
            models.Index(fields=["description"]),
            models.Index(fields=["supplier", "supplier_code"]),
            models.Index(fields=["department"]),
            models.Index(fields=["is_active"]),
            models.Index(fields=["bin_number"]),
            models.Index(
                fields=["is_active", "department"], name="idx_stock_active_dept"
            ),
            models.Index(fields=["barcode"], name="idx_stockitem_barcode"),
        ]

    def __str__(self):
        return f"{self.stock_code} - {self.description}"

    @property
    def available_quantity(self):
        """Calculate available quantity = QOH - allocated - sale_order"""
        return max(
            0,
            (
                self.quantity_on_hand
                - self.quantity_allocated
                - self.quantity_sale_order
            ),
        )

    def calculate_markup(self, price_level=1):
        """Calculate markup percentage for a given price level"""
        if self.cost_price > 0:
            selling_price = getattr(self, f"selling_price_{price_level}")
            return ((selling_price - self.cost_price) / self.cost_price) * 100
        return 0

    def apply_markups(self):
        """
        Recompute selling_price_1/2/3 from cost_price and the stored markup
        percentages. Inverse of calculate_markup(). Called when a supplier is
        flagged to auto-update selling prices on goods receipt.
        """
        from decimal import Decimal

        for level in (1, 2, 3):
            markup = getattr(self, f"markup_{level}")
            setattr(
                self,
                f"selling_price_{level}",
                self.cost_price * (1 + markup / Decimal("100")),
            )
        self.save(
            update_fields=["selling_price_1", "selling_price_2", "selling_price_3"]
        )

    def calculate_gross_profit(self, price_level=1):
        """Calculate gross profit percentage"""
        selling_price = getattr(self, f"selling_price_{price_level}")
        if selling_price > 0:
            return ((selling_price - self.cost_price) / selling_price) * 100
        return 0

    def update_average_cost(self, new_quantity, new_cost):
        """
        Update average cost using weighted average cost method.
        Called when new stock is received.
        """
        from decimal import Decimal

        new_quantity = Decimal(str(new_quantity))
        new_cost = Decimal(str(new_cost))
        current_qty = self.quantity_on_hand
        current_cost = self.average_cost

        if current_qty > 0:
            total_value = (current_qty * current_cost) + (new_quantity * new_cost)
            new_total_qty = current_qty + new_quantity
            self.average_cost = (
                total_value / new_total_qty if new_total_qty > 0 else current_cost
            )
        else:
            self.average_cost = new_cost if new_quantity > 0 else 0

        self.save(update_fields=["average_cost"])

    def needs_reordering(self):
        """Check if available stock falls below reorder quantity"""
        return self.available_quantity <= self.reorder_quantity

    def is_overstocked(self):
        """Check if stock exceeds maximum level (if set)"""
        if hasattr(self, "max_stock_level"):
            return self.quantity_on_hand > self.max_stock_level
        return False


class SpecialDeal(models.Model):
    """
    Special pricing for specific periods.
    Dates and prices sourced from smast.dbf: SPECSTDATE, SPECENDATE, SPPRICE1/2/3.
    special_cost_price and special_markup_1/2/3 are application-managed fields
    (not present in the legacy DBF) to support cost-aware special pricing.
    """

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="special_deals"
    )
    # Application-managed: cost price applicable during the special period
    special_cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cost price applicable during the special period (app-managed, not in legacy DBF)",
    )
    # SPPRICE1 N 12,4
    special_selling_price_1 = models.DecimalField(
        max_digits=12, decimal_places=4, default=0, help_text="SPPRICE1"
    )
    # SPPRICE2 N 12,4
    special_selling_price_2 = models.DecimalField(
        max_digits=12, decimal_places=4, default=0, help_text="SPPRICE2"
    )
    # SPPRICE3 N 12,4
    special_selling_price_3 = models.DecimalField(
        max_digits=12, decimal_places=4, default=0, help_text="SPPRICE3"
    )
    # Application-managed markup fields (not in legacy DBF)
    special_markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    special_markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    special_markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # SPECSTDATE D 8
    start_date = models.DateField(help_text="SPECSTDATE - Special start date")
    # SPECENDATE D 8
    end_date = models.DateField(help_text="SPECENDATE - Special end date")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "special_deals"
        ordering = ["-start_date"]

    def __str__(self):
        return f"Special Deal: {self.stock_item.stock_code} ({self.start_date} to {self.end_date})"

    def is_valid_today(self):
        """Check if special deal is valid for today"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.is_active


class FuturePricing(models.Model):
    """
    Future pricing for stock items.
    Prices sourced from smast.dbf: NEWPR, NEWPR1, NEWPR2, NEWPRDATE.
    future_cost_price and future_markup_1/2/3 are application-managed fields
    (not present in the legacy DBF) to support cost-aware future pricing.
    """

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="future_prices"
    )
    # Application-managed: anticipated cost price when future pricing takes effect
    future_cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Anticipated cost price at effective date (app-managed, not in legacy DBF)",
    )
    # NEWPR N 12,4
    future_selling_price_1 = models.DecimalField(
        max_digits=12, decimal_places=4, default=0, help_text="NEWPR - New price 1"
    )
    # NEWPR1 N 12,4
    future_selling_price_2 = models.DecimalField(
        max_digits=12, decimal_places=4, default=0, help_text="NEWPR1 - New price 2"
    )
    # NEWPR2 N 12,4
    future_selling_price_3 = models.DecimalField(
        max_digits=12, decimal_places=4, default=0, help_text="NEWPR2 - New price 3"
    )
    # Application-managed markup fields (not in legacy DBF)
    future_markup_1 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_markup_2 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    future_markup_3 = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    # NEWPRDATE D 8
    effective_date = models.DateField(help_text="NEWPRDATE - New price effective date")
    is_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "future_pricing"
        ordering = ["effective_date"]

    def __str__(self):
        return f"Future Price: {self.stock_item.stock_code} (Effective: {self.effective_date})"

    def apply(self):
        """
        Apply this future pricing to the parent stock item. Manual (§3.1
        [313.htm]): "Accpick automatically updates the future prices for
        the following day when Day End procedures are run" — see
        DayEndService._apply_future_pricing in
        apps/settings/period_end_services.py for the batch caller. Also
        used directly by FuturePricingViewSet.apply for manual/immediate
        application ("Where Day End is not normally processed, use the
        Update facility").
        """
        if self.is_applied:
            return False
        item = self.stock_item
        item.selling_price_1 = self.future_selling_price_1
        item.selling_price_2 = self.future_selling_price_2
        item.selling_price_3 = self.future_selling_price_3
        item.markup_1 = self.future_markup_1
        item.markup_2 = self.future_markup_2
        item.markup_3 = self.future_markup_3
        if self.future_cost_price:
            item.cost_price = self.future_cost_price
        item.save()
        self.is_applied = True
        self.save(update_fields=["is_applied"])
        return True


class ShrinkWrap(models.Model):
    """Shrink wrap relationships between bulk and individual items (SHRINK table)"""

    shrink_pack_code = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name="shrink_items",
        help_text="SCODE - Individual/shrink item code",
    )
    bulk_pack_code = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name="shrink_bulks",
        help_text="BCODE - Bulk/main item code",
    )
    invoice_bulk_value = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=1.0,
        validators=[MinValueValidator(0.001)],
        help_text="SINBULK - Quantity/value in bulk",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "shrink_wraps"
        unique_together = ["bulk_pack_code", "shrink_pack_code"]

    def __str__(self):
        return f"{self.shrink_pack_code.stock_code} -> {self.bulk_pack_code.stock_code} ({self.invoice_bulk_value})"


class PackBundle(models.Model):
    """Pack/Bundle finished products"""

    stock_item = models.OneToOneField(
        StockItem,
        on_delete=models.CASCADE,
        related_name="pack_bundle",
        primary_key=True,
    )
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pack_bundles"

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

    pack_bundle = models.ForeignKey(
        PackBundle, on_delete=models.CASCADE, related_name="ingredients"
    )
    ingredient_stock = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="used_in_bundles"
    )
    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0.0001)],
        help_text="Quantity of ingredient in bundle",
    )
    cost_at_creation = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pack_bundle_ingredients"
        unique_together = ["pack_bundle", "ingredient_stock"]

    def __str__(self):
        return f"{self.ingredient_stock.stock_code} in {self.pack_bundle.stock_item.stock_code}"

    def get_ingredient_value(self):
        """Calculate value of this ingredient"""
        return self.quantity * self.ingredient_stock.cost_price


class StockTransaction(models.Model):
    """
    Stock movement transactions - mapped from stran.dbf.
    The QTY field from stran.dbf is split into quantity_in/quantity_out based on transaction type.
    The running balance (BALANCE) is maintained in StockMovementLedger.
    """

    TRANSACTION_TYPES = [
        ("INCOMING", "Incoming Stock"),
        ("RETURN", "Stock Return"),
        ("SALE", "Sale"),
        ("SALE_RETURN", "Sale Return"),
        ("ADJUSTMENT", "Stock Adjustment"),
        ("STOCK_TAKE", "Stock Take"),
        ("MANUFACTURE", "Manufactured from Bundle"),
        ("BUNDLE_USE", "Used in Bundle"),
        ("BULK_ISSUE", "Issued from Bulk"),
        ("LAYBYE_IN", "Laybye Issue"),
        ("LAYBYE_OUT", "Laybye Return"),
        ("JOB_IN", "Job Card Issue"),
        ("JOB_OUT", "Job Card Return"),
        ("RFC_IN", "RFC Issue"),
        ("RFC_OUT", "RFC Return"),
    ]

    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    # CODE C 13
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="transactions"
    )
    # DATE D 8
    # default=timezone.localdate, not timezone.now: this is a DateField, and
    # timezone.now() returns a full datetime. When a caller omits
    # transaction_date, DRF injects the model field's raw default into
    # validated_data unconverted, so a stray datetime here reaches
    # DateField.to_representation() on the response and fails its
    # assert-not-a-datetime check.
    transaction_date = models.DateField(default=timezone.localdate)
    # TIME C 5
    transaction_time = models.TimeField(
        null=True, blank=True, help_text="Time of transaction (HH:MM)"
    )
    # TRANO N 6
    transaction_number = models.IntegerField(
        blank=True, null=True, help_text="TRANO - Transaction reference number"
    )

    # QTY N 14,4 - split into in/out based on TYPE
    quantity_in = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    quantity_out = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    quantity_balance = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    # DISCOUNT N 7,2
    discount = models.DecimalField(
        max_digits=7, decimal_places=2, default=0, help_text="Discount applied"
    )
    # COST N 10,2
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # STDPRICE N 12,2
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # VAL N 14,4
    value = models.DecimalField(
        max_digits=14, decimal_places=4, default=0, help_text="Transaction value"
    )

    # DEPT C 3
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_transactions",
    )

    # TAXIND C 1
    tax_code = models.ForeignKey(
        TaxCode,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_transactions",
    )

    # DNO N 5
    debtor = models.ForeignKey(
        "debtors.Debtor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_transactions",
    )

    # SUPNO N 4
    supplier = models.ForeignKey(
        Creditor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_transactions",
    )

    # SOURCE N 2 - station/source terminal number
    station_number = models.IntegerField(
        null=True,
        blank=True,
        help_text="SOURCE - Station/POS terminal or source number",
    )
    # COMMENTS C 30
    comments = models.CharField(max_length=30, blank=True, null=True)

    # Audit fields
    created_by = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock_transactions"
        ordering = ["-transaction_date", "-id"]
        indexes = [
            models.Index(fields=["stock_item", "transaction_date"]),
            models.Index(fields=["transaction_type"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["transaction_number"]),
            models.Index(
                fields=["debtor", "transaction_date"], name="idx_stock_debtor_date"
            ),
            models.Index(
                fields=["supplier", "transaction_date"], name="idx_stock_supplier_date"
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.stock_item.stock_code} - {self.transaction_date}"


class StockMovementLedger(models.Model):
    """
    Running balance ledger per stock item - mapped from stmove{CODE}.dbf files.
    Each stock item has its own stmove DBF (e.g. stmove41200.dbf for item 41200).
    This consolidates all per-item movement files into a single table.
    Fields: DATE, TIME, TYPE, TRANO, DETAILS, QTYIN, QTYOUT, BALANCE, BFWD, PERUNIT, SUPDETAILS, RECORD
    """

    # DATE C 10 (stored as string "YYYY/MM/DD" in DBF)
    movement_date = models.DateField(help_text="DATE - Date of movement")
    # TIME C 8
    movement_time = models.TimeField(
        null=True, blank=True, help_text="TIME - Time of movement"
    )
    # TYPE C 2
    movement_type = models.CharField(
        max_length=2, help_text="TYPE - Movement type code (e.g. SI, SO, SR)"
    )
    # TRANO N 6
    transaction_number = models.IntegerField(
        null=True, blank=True, help_text="TRANO - Linked transaction number"
    )
    # DETAILS C 30
    details = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="DETAILS - Description or reference",
    )
    # QTYIN C 14 (stored as formatted string in DBF)
    quantity_in = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
        help_text="QTYIN - Quantity received",
    )
    # QTYOUT C 14
    quantity_out = models.DecimalField(
        max_digits=14, decimal_places=4, default=0, help_text="QTYOUT - Quantity issued"
    )
    # BALANCE C 14
    balance = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
        help_text="BALANCE - Running stock balance",
    )
    # BFWD N 12,2
    brought_forward = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="BFWD - Brought-forward value",
    )
    # PERUNIT N 12,2
    per_unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="PERUNIT - Cost per unit at time of movement",
    )
    # SUPDETAILS C 25
    supplier_details = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        help_text="SUPDETAILS - Supplier reference or details",
    )
    # RECORD C 15
    record_reference = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        help_text="RECORD - Source record reference",
    )

    # FK to link back to the stock item (derived from filename e.g. stmove41200)
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name="movement_ledger",
        help_text="Stock item this ledger entry belongs to",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "stock_movement_ledger"
        ordering = ["stock_item", "movement_date", "movement_time"]
        indexes = [
            models.Index(fields=["stock_item", "movement_date"]),
            models.Index(fields=["movement_type"]),
            models.Index(fields=["transaction_number"]),
        ]

    def __str__(self):
        return f"{self.stock_item_id} | {self.movement_date} | {self.movement_type} | in={self.quantity_in} out={self.quantity_out} bal={self.balance}"


class StockTake(models.Model):
    """Stock take sessions"""

    STATUS_CHOICES = [
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("UPDATED", "Updated"),
    ]

    stock_take_date = models.DateField(default=timezone.localdate)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="IN_PROGRESS"
    )
    description = models.TextField(blank=True, null=True)

    reset_negatives_to_zero = models.BooleanField(default=False)
    set_uncounted_to_zero = models.BooleanField(default=False)

    is_after_trading = models.BooleanField(default=False)
    trading_start_date = models.DateTimeField(null=True, blank=True)

    created_by = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "stock_takes"
        ordering = ["-stock_take_date"]

    def __str__(self):
        return f"Stock Take - {self.stock_take_date} ({self.status})"


class StockTakeItem(models.Model):
    """Individual items counted in a stock take"""

    stock_take = models.ForeignKey(
        StockTake, on_delete=models.CASCADE, related_name="items"
    )
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="stock_take_items"
    )

    quantity_on_hand = models.DecimalField(
        max_digits=14, decimal_places=4, help_text="System quantity before count"
    )
    quantity_counted = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    variance_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    variance_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    cost_price_at_count = models.DecimalField(
        max_digits=12, decimal_places=2, default=0
    )

    is_counted = models.BooleanField(default=False)
    count_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock_take_items"
        unique_together = ["stock_take", "stock_item"]
        indexes = [
            models.Index(fields=["stock_take", "is_counted"]),
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
        ("ACTUAL", "Actual Price"),
        ("COST_MARKUP", "Cost + Markup%"),
    ]

    debtor = models.ForeignKey(
        "debtors.Debtor", on_delete=models.CASCADE, related_name="contract_prices"
    )
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name="contract_prices",
        null=True,
        blank=True,
    )
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.CASCADE,
        related_name="contract_prices",
        null=True,
        blank=True,
    )
    supplier = models.ForeignKey(
        Creditor,
        on_delete=models.CASCADE,
        related_name="contract_prices",
        null=True,
        blank=True,
    )

    pricing_method = models.CharField(max_length=20, choices=PRICING_METHOD_CHOICES)
    contract_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    markup_percent = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    last_selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="LSELL - Last transaction selling price",
    )
    last_updated_date = models.DateField(
        null=True, blank=True, help_text="LUPDATE - Last update date for contract"
    )
    valid_from = models.DateField(
        null=True, blank=True, help_text="Contract price valid from (unbounded if blank)"
    )
    valid_until = models.DateField(
        null=True, blank=True, help_text="Contract price valid until (unbounded if blank)"
    )
    is_fixed_pricing = models.BooleanField(
        default=False, help_text="FIXEDPRICE - Prevent POS from changing price"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "contract_pricing"
        indexes = [
            models.Index(fields=["debtor", "stock_item"]),
            models.Index(fields=["debtor", "department"]),
            models.Index(fields=["debtor", "supplier"]),
        ]

    def __str__(self):
        item_desc = (
            self.stock_item.stock_code
            if self.stock_item
            else (
                self.department.department_name
                if self.department
                else self.supplier.name if self.supplier else "General"
            )
        )
        return f"Contract: {self.debtor.account_number} - {item_desc}"

    def is_valid_today(self):
        today = timezone.now().date()
        if self.valid_from and today < self.valid_from:
            return False
        if self.valid_until and today > self.valid_until:
            return False
        return True

    def get_price(self, stock_item=None):
        """Calculate contract price based on method, honoring valid_from/valid_until."""
        if not self.is_valid_today():
            return None
        if self.pricing_method == "ACTUAL":
            return self.contract_price
        elif self.pricing_method == "COST_MARKUP" and stock_item:
            return stock_item.cost_price * (1 + self.markup_percent / 100)
        return None


class OneTouchLookupKey(models.Model):
    """One-touch keyboard shortcuts for stock items at POS"""

    key_character = models.CharField(
        max_length=1, unique=True, help_text="Single uppercase letter"
    )
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="lookup_keys"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "one_touch_lookup_keys"

    def __str__(self):
        return f"{self.key_character} -> {self.stock_item.stock_code}"


class StockMonthlyStatistic(models.Model):
    """Monthly sales statistics for stock items"""

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="monthly_stats"
    )
    year = models.IntegerField()
    month = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

    quantity_sold = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    value_sold = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock_monthly_statistics"
        unique_together = ["stock_item", "year", "month"]
        ordering = ["-year", "-month"]

    def __str__(self):
        return f"{self.stock_item.stock_code} - {self.year}/{self.month}"


# ============================================================================
# Phase 1: Branch Management Models
# ============================================================================


class Branch(models.Model):
    """Branch/Location model for multi-branch stock management"""

    BRANCH_TYPE_CHOICES = [
        ("RETAIL", "Retail Store"),
        ("WAREHOUSE", "Warehouse"),
        ("HQ", "Headquarters"),
    ]

    branch_code = models.CharField(max_length=10, unique=True, primary_key=True)
    branch_name = models.CharField(max_length=100)
    branch_type = models.CharField(max_length=20, choices=BRANCH_TYPE_CHOICES)
    address = models.TextField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=255, null=True, blank=True)
    updated_by = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "branches"
        ordering = ["branch_code"]
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["is_default"]),
            models.Index(fields=["branch_type"]),
        ]

    def __str__(self):
        return f"{self.branch_code} - {self.branch_name}"


class BranchStock(models.Model):
    """Stock quantity tracking per branch"""

    id = models.BigAutoField(primary_key=True)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="branch_stocks"
    )
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="branch_stocks"
    )

    quantity = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    quantity_allocated = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "branch_stocks"
        unique_together = ["branch", "stock_item"]
        ordering = ["branch", "stock_item"]
        indexes = [
            models.Index(fields=["branch", "quantity"]),
            models.Index(fields=["stock_item", "branch"]),
        ]

    def __str__(self):
        return f"{self.branch.branch_code} - {self.stock_item.stock_code} ({self.quantity})"

    @property
    def available_quantity(self):
        return max(Decimal("0"), (self.quantity - self.quantity_allocated))


# ============================================================================
# Phase 3: Group Orders
# ============================================================================


class GroupOrder(models.Model):
    """Group order model for consolidating multiple orders"""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.BigAutoField(primary_key=True)
    group_order_number = models.CharField(max_length=20, unique=True)
    order_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    branch = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name="group_orders"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_group_orders",
    )
    notes = models.TextField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "group_orders"
        ordering = ["-order_date", "-group_order_number"]
        indexes = [
            models.Index(fields=["status", "branch"]),
            models.Index(fields=["order_date"]),
        ]

    def __str__(self):
        return f"{self.group_order_number} - {self.status}"

    def calculate_total_amount(self):
        total = sum(item.line_total for item in self.items.all())
        self.total_amount = total
        self.save(update_fields=["total_amount"])
        return total


class GroupOrderItem(models.Model):
    """Individual items in a group order"""

    id = models.BigAutoField(primary_key=True)
    group_order = models.ForeignKey(
        GroupOrder, on_delete=models.CASCADE, related_name="items"
    )
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="group_order_items"
    )
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=4)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "group_order_items"
        unique_together = ["group_order", "stock_item"]
        ordering = ["stock_item"]

    def __str__(self):
        return f"{self.group_order.group_order_number} - {self.stock_item.stock_code}"

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ============================================================================
# Phase 4: IBT - Inter-Branch Transfer
# ============================================================================


class BranchTransfer(models.Model):
    """Inter-branch transfer request"""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("PENDING", "Pending Approval"),
        ("APPROVED", "Approved"),
        ("DISPATCHED", "Dispatched"),
        ("IN_TRANSIT", "In Transit"),
        ("RECEIVED", "Received"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    TRANSFER_TYPE_CHOICES = [
        ("STANDARD", "Standard Transfer"),
        ("URGENT", "Urgent Transfer"),
        ("RETURN", "Return Transfer"),
    ]

    id = models.BigAutoField(primary_key=True)
    transfer_number = models.CharField(max_length=20, unique=True)
    from_branch = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name="transfers_out"
    )
    to_branch = models.ForeignKey(
        Branch, on_delete=models.PROTECT, related_name="transfers_in"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    transfer_type = models.CharField(
        max_length=20, choices=TRANSFER_TYPE_CHOICES, default="STANDARD"
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_requested",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_approved",
    )
    dispatched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_dispatched",
    )
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transfers_received",
    )

    requested_date = models.DateTimeField(default=timezone.now)
    approved_date = models.DateTimeField(null=True, blank=True)
    dispatched_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "branch_transfers"
        ordering = ["-requested_date", "-transfer_number"]
        indexes = [
            models.Index(fields=["status", "from_branch"]),
            models.Index(fields=["status", "to_branch"]),
            models.Index(fields=["requested_date"]),
            models.Index(fields=["transfer_type"]),
        ]

    def __str__(self):
        return f"{self.transfer_number} - {self.from_branch.branch_code} → {self.to_branch.branch_code}: {self.status}"


class BranchTransferItem(models.Model):
    """Individual items in a branch transfer"""

    id = models.BigAutoField(primary_key=True)
    transfer = models.ForeignKey(
        BranchTransfer, on_delete=models.CASCADE, related_name="items"
    )
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="transfer_items"
    )

    quantity_requested = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_dispatched = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    variance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "branch_transfer_items"
        unique_together = ["transfer", "stock_item"]
        ordering = ["stock_item"]

    def __str__(self):
        return f"{self.transfer.transfer_number} - {self.stock_item.stock_code}"

    def save(self, *args, **kwargs):
        self.variance = self.quantity_received - self.quantity_requested
        super().save(*args, **kwargs)


# ============================================================================
# Phase 5: IBI - Inter-Branch Invoicing
# ============================================================================


class BranchTransferInvoice(models.Model):
    """Invoice for inter-branch transfers"""

    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("ISSUED", "Issued"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.BigAutoField(primary_key=True)
    transfer = models.OneToOneField(
        BranchTransfer, on_delete=models.CASCADE, related_name="invoice"
    )
    invoice_number = models.CharField(max_length=20, unique=True)
    invoice_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "branch_transfer_invoices"
        ordering = ["-invoice_date", "-invoice_number"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["invoice_date"]),
        ]


# ============================================================================
# Legacy DBF imports with no prior model home (serial_number.dbf,
# prupdate.dbf, stock_promo.dbf, smast_discounts.dbf)
# ============================================================================


class SerializedStockItem(models.Model):
    """Serial-number tracked stock item, mapped from serial_number.dbf"""

    # SERIALNO C 20
    serial_number = models.CharField(max_length=20, unique=True, help_text="SERIALNO")
    # CODE C 13 - stock item this serial belongs to
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="serial_numbers",
        help_text="CODE",
    )
    # ITEMDETAIL C 30
    item_detail = models.CharField(max_length=30, blank=True, help_text="ITEMDETAIL")
    # DATE D 8
    transaction_date = models.DateField(null=True, blank=True, help_text="DATE")
    # TRANSTYPE C 2
    transaction_type = models.CharField(max_length=2, blank=True, help_text="TRANSTYPE")
    # TRANSNO N 6
    transaction_number = models.PositiveIntegerField(
        null=True, blank=True, help_text="TRANSNO"
    )
    # VALUE N 12,2
    value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="VALUE"
    )
    # WARRANTPER N 3
    warranty_period_months = models.PositiveIntegerField(
        null=True, blank=True, help_text="WARRANTPER"
    )
    # COMMENT1-4 C 30 each
    comment1 = models.CharField(max_length=30, blank=True, help_text="COMMENT1")
    comment2 = models.CharField(max_length=30, blank=True, help_text="COMMENT2")
    comment3 = models.CharField(max_length=30, blank=True, help_text="COMMENT3")
    comment4 = models.CharField(max_length=30, blank=True, help_text="COMMENT4")
    # NAME C 40
    customer_name = models.CharField(max_length=40, blank=True, help_text="NAME")
    # ADD1-3 C 25 each
    address_line1 = models.CharField(max_length=25, blank=True, help_text="ADD1")
    address_line2 = models.CharField(max_length=25, blank=True, help_text="ADD2")
    address_line3 = models.CharField(max_length=25, blank=True, help_text="ADD3")
    # TEL C 15
    telephone = models.CharField(max_length=15, blank=True, help_text="TEL")
    # EMAIL C 50
    email = models.CharField(max_length=50, blank=True, help_text="EMAIL")
    # STOLEN L 1
    is_stolen = models.BooleanField(default=False, help_text="STOLEN")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "serialized_stock_items"
        ordering = ["serial_number"]

    def __str__(self):
        return f"Serial {self.serial_number}"


class StagedPriceUpdate(models.Model):
    """Pending/staged price update, mapped from prupdate.dbf"""

    # STOCKCODE C 13 — raw code, kept even when it doesn't resolve to a
    # current StockItem (many legacy entries reference discontinued codes),
    # so (stock_code, effective_date) is always a usable natural key on import.
    stock_code = models.CharField(
        max_length=13, blank=True, help_text="STOCKCODE (raw)"
    )
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staged_price_updates",
        help_text="STOCKCODE",
    )
    # SUPNAME C 30 - no reliable FK key in this file, kept as plain text
    supplier_name = models.CharField(max_length=30, blank=True, help_text="SUPNAME")
    # DEPARTMENT C 20 - plain text, no reliable department code in this file
    department_name = models.CharField(
        max_length=20, blank=True, help_text="DEPARTMENT"
    )
    # DESCRIP C 30
    description = models.CharField(max_length=30, blank=True, help_text="DESCRIP")
    # UNITOFMEAS C 10
    unit_of_measure = models.CharField(
        max_length=10, blank=True, help_text="UNITOFMEAS"
    )
    # COST N 12,2
    cost_price = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="COST"
    )
    # SELL1-3 N 12,2
    sell_price_1 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="SELL1"
    )
    sell_price_2 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="SELL2"
    )
    sell_price_3 = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="SELL3"
    )
    # EFFECTDATE D 8
    effective_date = models.DateField(null=True, blank=True, help_text="EFFECTDATE")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "staged_price_updates"
        ordering = ["effective_date"]

    def __str__(self):
        return f"Price update: {self.stock_item_id} ({self.effective_date})"


class StockPromotion(models.Model):
    """Promotional pricing/messaging, mapped from stock_promo.dbf"""

    # CODE C 13
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, related_name="promotions", help_text="CODE"
    )
    # DEPT C 3
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_promotions",
        help_text="DEPT",
    )
    # STARTDATE D 8
    start_date = models.DateField(help_text="STARTDATE")
    # ENDDATE D 8
    end_date = models.DateField(help_text="ENDDATE")
    # BASIS C 1
    basis = models.CharField(max_length=1, blank=True, help_text="BASIS")
    # AMOUNT N 12,2
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="AMOUNT"
    )
    # MESSAGE1-2 C 40 each
    message_line1 = models.CharField(max_length=40, blank=True, help_text="MESSAGE1")
    message_line2 = models.CharField(max_length=40, blank=True, help_text="MESSAGE2")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stock_promotions"
        ordering = ["-start_date"]

    def __str__(self):
        return f"Promo: {self.stock_item.stock_code} ({self.start_date} to {self.end_date})"


class DepartmentTimeDiscount(models.Model):
    """Day-of-week/time-window department discount, mapped from smast_discounts.dbf"""

    # DEPT C 3
    department = models.ForeignKey(
        SalesDepartment,
        on_delete=models.CASCADE,
        related_name="time_discounts",
        help_text="DEPT",
    )
    # DEPTNAME C 20 - denormalised cache from the legacy file
    department_name_legacy = models.CharField(
        max_length=20, blank=True, help_text="DEPTNAME"
    )
    # DAYOFWEEK N 1
    day_of_week = models.PositiveSmallIntegerField(help_text="DAYOFWEEK")
    # START_TIME C/N (time)
    start_time = models.TimeField(help_text="START_TIME")
    # END_TIME C/N (time)
    end_time = models.TimeField(help_text="END_TIME")
    # DISCOUNT N 5,2
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, help_text="DISCOUNT"
    )
    # TYPE C 1
    discount_type = models.CharField(max_length=1, blank=True, help_text="TYPE")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "department_time_discounts"
        ordering = ["department", "day_of_week", "start_time"]

    def __str__(self):
        return f"{self.department_id} discount day {self.day_of_week} {self.start_time}-{self.end_time}"
