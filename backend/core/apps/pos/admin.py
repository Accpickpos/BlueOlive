"""
Point of Sale admin configuration.
Django admin interface for POS models.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CashACheque,
    CashControl,
    CashReturn,
    CashReturnLine,
    CashSale,
    CashSaleLine,
    CreditNote,
    CreditNoteLine,
    JobCard,
    JobCardLine,
    Laybye,
    LaybyeLine,
    LaybyePayment,
    Payout,
    Quotation,
    QuotationLine,
    ReceiptOnAccount,
    Repair,
    Tender,
    TransactionQuery,
)


class CashSaleLineInline(admin.TabularInline):
    """Inline for cash sale lines."""

    model = CashSaleLine
    extra = 1
    fields = [
        "line_number",
        "stock_code",
        "description",
        "quantity",
        "unit_price",
        "discount_percentage",
        "tax_code",
        "line_total",
        "vat_amount",
        "line_profit",
    ]
    readonly_fields = ["line_total", "vat_amount", "line_profit"]


class TenderInline(admin.TabularInline):
    """Inline for payment tenders."""

    model = Tender
    extra = 1
    fields = ["tender_type", "amount", "drawer_name", "authorization_code"]


@admin.register(CashSale)
class CashSaleAdmin(admin.ModelAdmin):
    """Admin for CashSale model."""

    list_display = [
        "sale_number",
        "sale_date",
        "sale_time",
        "customer_name",
        "cashier",
        "station_number",
        "total_amount_display",
        "gross_profit_display",
        "is_posted",
        "is_cancelled",
    ]

    list_filter = [
        "is_posted",
        "is_cancelled",
        "sale_date",
        "cashier",
        "station_number",
        "sales_area",
    ]

    search_fields = [
        "sale_number",
        "customer_name",
        "telephone",
        "order_number",
        "job_card_number",
    ]

    readonly_fields = [
        "subtotal",
        "discount_amount",
        "vat_amount",
        "total_amount",
        "total_cost",
        "gross_profit",
        "change_given",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "sale_date"

    inlines = [CashSaleLineInline, TenderInline]

    fieldsets = (
        (
            "Sale Details",
            {
                "fields": (
                    "sale_number",
                    "sale_date",
                    "sale_time",
                    "is_posted",
                    "is_cancelled",
                )
            },
        ),
        (
            "Customer Information",
            {
                "fields": (
                    "customer_name",
                    "delivery_address",
                    "telephone",
                    "vat_number",
                    "order_number",
                    "job_card_number",
                )
            },
        ),
        ("POS Details", {"fields": ("cashier", "station_number", "sales_area")}),
        (
            "Totals",
            {"fields": ("subtotal", "discount_amount", "vat_amount", "total_amount")},
        ),
        ("Cost and Profit", {"fields": ("total_cost", "gross_profit")}),
        ("Payment", {"fields": ("cash_tendered", "change_given")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def total_amount_display(self, obj):
        """Display total amount."""
        return format_html("R {:,.2f}", obj.total_amount)

    total_amount_display.short_description = "Total"
    total_amount_display.admin_order_field = "total_amount"

    def gross_profit_display(self, obj):
        """Display gross profit."""
        if obj.total_amount > 0:
            percentage = (obj.gross_profit / obj.total_amount) * 100
            return format_html("R {:,.2f} ({:.1f}%)", obj.gross_profit, percentage)
        return format_html("R {:,.2f}", obj.gross_profit)

    gross_profit_display.short_description = "Gross Profit"

    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related("cashier", "sales_area")


class LaybyeLineInline(admin.TabularInline):
    """Inline for laybye lines."""

    model = LaybyeLine
    extra = 1
    fields = [
        "line_number",
        "stock_item",
        "quantity",
        "unit_price",
        "discount_percentage",
        "tax_code",
        "line_total",
    ]
    readonly_fields = ["line_total"]


class LaybyelPaymentInline(admin.TabularInline):
    """Inline for laybye payments."""

    model = LaybyePayment
    extra = 0
    fields = ["payment_date", "amount", "sales_area"]
    readonly_fields = ["payment_date", "amount"]


@admin.register(Laybye)
class LaybyeAdmin(admin.ModelAdmin):
    """Admin for Laybye model."""

    list_display = [
        "laybye_number",
        "customer_name",
        "telephone",
        "laybye_date",
        "expiry_date",
        "total_amount_display",
        "balance_due_display",
        "status",
    ]

    list_filter = ["status", "laybye_date", "expiry_date", "sales_area"]

    search_fields = ["laybye_number", "customer_name", "telephone"]

    readonly_fields = [
        "amount_paid",
        "balance_due",
        "refund_amount",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "laybye_date"

    inlines = [LaybyeLineInline, LaybyelPaymentInline]

    fieldsets = (
        (
            "Laybye Details",
            {"fields": ("laybye_number", "laybye_date", "expiry_date", "status")},
        ),
        (
            "Customer Information",
            {"fields": ("customer_name", "address", "telephone", "comments")},
        ),
        (
            "Amounts",
            {
                "fields": (
                    "total_amount",
                    "deposit_amount",
                    "amount_paid",
                    "balance_due",
                )
            },
        ),
        ("Cancellation", {"fields": ("retention_percentage", "refund_amount")}),
        ("Other", {"fields": ("sales_area",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def total_amount_display(self, obj):
        """Display total amount."""
        return format_html("R {:,.2f}", obj.total_amount)

    total_amount_display.short_description = "Total"
    total_amount_display.admin_order_field = "total_amount"

    def balance_due_display(self, obj):
        """Display balance due."""
        if obj.balance_due > 0:
            return format_html(
                '<span style="color: red;">R {:,.2f}</span>', obj.balance_due
            )
        return format_html("R {:,.2f}", obj.balance_due)

    balance_due_display.short_description = "Balance Due"


class QuotationLineInline(admin.TabularInline):
    """Inline for quotation lines."""

    model = QuotationLine
    extra = 1
    fields = [
        "line_number",
        "stock_code",
        "description",
        "quantity",
        "unit_price",
        "discount_percentage",
        "tax_code",
        "line_total",
        "vat_amount",
    ]
    readonly_fields = ["line_total", "vat_amount"]


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    """Admin for Quotation model."""

    list_display = [
        "quotation_number",
        "quotation_date",
        "expiry_date",
        "customer_name",
        "total_amount_display",
        "status",
    ]

    list_filter = ["status", "quotation_date", "expiry_date", "sales_area"]

    search_fields = ["quotation_number", "customer_name", "telephone"]

    readonly_fields = [
        "subtotal",
        "vat_amount",
        "total_amount",
        "gross_profit",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "quotation_date"

    inlines = [QuotationLineInline]

    def total_amount_display(self, obj):
        """Display total amount."""
        return format_html("R {:,.2f}", obj.total_amount)

    total_amount_display.short_description = "Total"
    total_amount_display.admin_order_field = "total_amount"


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    """Admin for Payout model."""

    list_display = [
        "payout_date",
        "payee",
        "amount_display",
        "cashier",
        "station_number",
    ]

    list_filter = ["payout_date", "cashier", "station_number"]

    search_fields = ["payee", "description", "reference"]

    readonly_fields = ["created_at", "updated_at"]

    date_hierarchy = "payout_date"

    def amount_display(self, obj):
        """Display amount."""
        return format_html("R {:,.2f}", obj.amount)

    amount_display.short_description = "Amount"
    amount_display.admin_order_field = "amount"


@admin.register(Repair)
class RepairAdmin(admin.ModelAdmin):
    """Admin for Repair model."""

    list_display = [
        "repair_number",
        "customer_name",
        "date_required",
        "quoted_value_display",
        "repair_cost_display",
        "status",
    ]

    list_filter = ["status", "date_required"]

    search_fields = ["repair_number", "customer_name", "supplier_account"]

    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Repair Details",
            {
                "fields": (
                    "repair_number",
                    "status",
                    "date_required",
                    "quoted_value",
                    "repair_details",
                )
            },
        ),
        (
            "Customer Information",
            {
                "fields": (
                    "customer_name",
                    "address",
                    "telephone",
                    "contact_person",
                    "order_number",
                )
            },
        ),
        (
            "Supplier Details (When Issued)",
            {
                "fields": (
                    "supplier_account",
                    "date_sent",
                    "transport_mode",
                    "issue_comments",
                    "company_contact",
                    "supplier_contact",
                )
            },
        ),
        (
            "Repair Costs (When Received)",
            {
                "fields": (
                    "date_repaired",
                    "supplier_invoice_number",
                    "repair_cost",
                    "supplier_comments",
                )
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def quoted_value_display(self, obj):
        """Display quoted value."""
        if obj.quoted_value:
            return format_html("R {:,.2f}", obj.quoted_value)
        return "-"

    quoted_value_display.short_description = "Quoted"

    def repair_cost_display(self, obj):
        """Display repair cost."""
        if obj.repair_cost:
            return format_html("R {:,.2f}", obj.repair_cost)
        return "-"

    repair_cost_display.short_description = "Cost"


class JobCardLineInline(admin.TabularInline):
    """Inline for job card lines."""

    model = JobCardLine
    extra = 1
    fields = [
        "line_number",
        "stock_code",
        "description",
        "quantity",
        "unit_price",
        "discount_percentage",
        "tax_code",
        "line_total",
        "vat_amount",
        "line_profit",
    ]
    readonly_fields = ["line_total", "vat_amount", "line_profit"]


@admin.register(JobCard)
class JobCardAdmin(admin.ModelAdmin):
    """Admin for JobCard model."""

    list_display = [
        "job_number",
        "job_date",
        "customer_name",
        "registration_number",
        "total_amount_display",
        "gross_profit_display",
        "status",
    ]

    list_filter = ["status", "job_date", "sales_area"]

    search_fields = [
        "job_number",
        "customer_name",
        "registration_number",
        "telephone",
        "order_number",
    ]

    readonly_fields = [
        "subtotal",
        "vat_amount",
        "total_amount",
        "total_cost",
        "gross_profit",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "job_date"

    inlines = [JobCardLineInline]

    def total_amount_display(self, obj):
        """Display total amount."""
        return format_html("R {:,.2f}", obj.total_amount)

    total_amount_display.short_description = "Total"
    total_amount_display.admin_order_field = "total_amount"

    def gross_profit_display(self, obj):
        """Display gross profit."""
        if obj.total_amount > 0:
            percentage = (obj.gross_profit / obj.total_amount) * 100
            return format_html("R {:,.2f} ({:.1f}%)", obj.gross_profit, percentage)
        return format_html("R {:,.2f}", obj.gross_profit)

    gross_profit_display.short_description = "Gross Profit"


@admin.register(CashControl)
class CashControlAdmin(admin.ModelAdmin):
    """Admin for CashControl model."""

    list_display = [
        "control_date",
        "cashier",
        "station_number",
        "cash_sales_total_display",
        "cash_takings_display",
        "is_cleared",
    ]

    list_filter = ["control_date", "cashier", "station_number", "is_cleared"]

    search_fields = ["cashier__username"]

    readonly_fields = ["created_at", "updated_at"]

    date_hierarchy = "control_date"

    fieldsets = (
        (
            "Control Details",
            {"fields": ("control_date", "cashier", "station_number", "is_cleared")},
        ),
        (
            "Cash Sales",
            {
                "fields": (
                    "cash_sales_count",
                    "cash_sales_total",
                    "cash_refunds_count",
                    "cash_refunds_total",
                )
            },
        ),
        (
            "Invoices and Credits",
            {
                "fields": (
                    "invoices_count",
                    "invoices_total",
                    "credits_count",
                    "credits_total",
                )
            },
        ),
        (
            "Receipts",
            {
                "fields": (
                    "receipts_count",
                    "receipts_total",
                    "settlement_discount_total",
                )
            },
        ),
        ("Cash Returns", {"fields": ("cash_returns_count", "cash_returns_total")}),
        (
            "Cash a Cheque",
            {
                "fields": (
                    "cashed_cheques_count",
                    "cashed_cheques_total",
                    "cashed_cheques_commission",
                )
            },
        ),
        (
            "Laybyes",
            {
                "fields": (
                    "new_laybyes_count",
                    "new_laybyes_total",
                    "cancelled_laybyes_count",
                    "cancelled_laybyes_total",
                    "laybye_receipts_count",
                    "laybye_receipts_total",
                    "laybye_refunds_count",
                    "laybye_refunds_total",
                    "completed_laybyes_count",
                    "completed_laybyes_total",
                ),
                "classes": ("collapse",),
            },
        ),
        ("Payouts", {"fields": ("payouts_count", "payouts_total")}),
        (
            "Takings by Type",
            {
                "fields": (
                    "cash_takings",
                    "cheque_takings",
                    "voucher_takings",
                    "speedpoint_takings",
                )
            },
        ),
        (
            "Refunds by Type",
            {
                "fields": ("cash_refunds", "cheque_refunds", "voucher_refunds"),
                "classes": ("collapse",),
            },
        ),
        (
            "Other",
            {
                "fields": ("rounding_total", "abandoned_count", "abandoned_total"),
                "classes": ("collapse",),
            },
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def cash_sales_total_display(self, obj):
        """Display cash sales total."""
        return format_html("R {:,.2f}", obj.cash_sales_total)

    cash_sales_total_display.short_description = "Sales Total"
    cash_sales_total_display.admin_order_field = "cash_sales_total"

    def cash_takings_display(self, obj):
        """Display cash takings."""
        return format_html("R {:,.2f}", obj.cash_takings)

    cash_takings_display.short_description = "Cash Takings"
    cash_takings_display.admin_order_field = "cash_takings"

    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related("cashier")


@admin.register(ReceiptOnAccount)
class ReceiptOnAccountAdmin(admin.ModelAdmin):
    """Admin for ReceiptOnAccount model."""

    list_display = [
        "receipt_number",
        "receipt_date",
        "debtor_account",
        "debtor_name",
        "amount_display",
        "settlement_discount_display",
        "total_amount_display",
        "tender_type",
        "is_posted",
    ]

    list_filter = [
        "receipt_date",
        "tender_type",
        "is_posted",
        "cashier",
        "station_number",
    ]

    search_fields = ["receipt_number", "debtor_account", "debtor_name"]

    readonly_fields = ["total_amount", "created_at", "updated_at"]

    date_hierarchy = "receipt_date"

    def amount_display(self, obj):
        return format_html("R {:,.2f}", obj.amount)

    amount_display.short_description = "Amount"

    def settlement_discount_display(self, obj):
        return format_html("R {:,.2f}", obj.settlement_discount)

    settlement_discount_display.short_description = "Discount"

    def total_amount_display(self, obj):
        return format_html("R {:,.2f}", obj.total_amount)

    total_amount_display.short_description = "Total"


class CreditNoteLineInline(admin.TabularInline):
    """Inline for credit note lines."""

    model = CreditNoteLine
    extra = 1
    fields = [
        "line_number",
        "stock_code",
        "description",
        "quantity",
        "unit_price",
        "tax_code",
        "line_total",
        "vat_amount",
    ]
    readonly_fields = ["line_total", "vat_amount"]


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    """Admin for CreditNote model."""

    list_display = [
        "credit_number",
        "credit_date",
        "customer_name",
        "total_amount_display",
        "refund_type",
        "is_posted",
    ]

    list_filter = [
        "credit_date",
        "refund_type",
        "is_posted",
        "cashier",
        "station_number",
    ]

    search_fields = ["credit_number", "customer_name", "debtor_account"]

    readonly_fields = [
        "subtotal",
        "vat_amount",
        "total_amount",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "credit_date"

    inlines = [CreditNoteLineInline]

    def total_amount_display(self, obj):
        return format_html("R {:,.2f}", obj.total_amount)

    total_amount_display.short_description = "Total"


class CashReturnLineInline(admin.TabularInline):
    """Inline for cash return lines."""

    model = CashReturnLine
    extra = 1
    fields = [
        "line_number",
        "stock_code",
        "description",
        "quantity",
        "unit_price",
        "tax_code",
        "line_total",
        "vat_amount",
    ]
    readonly_fields = ["line_total", "vat_amount"]


@admin.register(CashReturn)
class CashReturnAdmin(admin.ModelAdmin):
    """Admin for CashReturn model."""

    list_display = [
        "return_number",
        "return_date",
        "original_sale_number",
        "customer_name",
        "total_amount_display",
        "is_posted",
    ]

    list_filter = ["return_date", "is_posted", "cashier", "station_number"]

    search_fields = ["return_number", "original_sale_number", "customer_name"]

    readonly_fields = [
        "subtotal",
        "vat_amount",
        "total_amount",
        "created_at",
        "updated_at",
    ]

    date_hierarchy = "return_date"

    inlines = [CashReturnLineInline]

    def total_amount_display(self, obj):
        return format_html("R {:,.2f}", obj.total_amount)

    total_amount_display.short_description = "Total"


@admin.register(CashACheque)
class CashAChequeAdmin(admin.ModelAdmin):
    """Admin for CashACheque model."""

    list_display = [
        "transaction_number",
        "transaction_date",
        "drawer_name",
        "cheque_number",
        "bank_name",
        "cheque_amount_display",
        "commission_display",
        "cash_paid_display",
        "is_processed",
    ]

    list_filter = ["transaction_date", "is_processed", "cashier", "station_number"]

    search_fields = ["transaction_number", "drawer_name", "cheque_number", "id_number"]

    readonly_fields = ["cash_paid", "created_at", "updated_at"]

    date_hierarchy = "transaction_date"

    def cheque_amount_display(self, obj):
        return format_html("R {:,.2f}", obj.cheque_amount)

    cheque_amount_display.short_description = "Cheque Amount"

    def commission_display(self, obj):
        return format_html("R {:,.2f}", obj.commission)

    commission_display.short_description = "Commission"

    def cash_paid_display(self, obj):
        return format_html("R {:,.2f}", obj.cash_paid)

    cash_paid_display.short_description = "Cash Paid"


@admin.register(TransactionQuery)
class TransactionQueryAdmin(admin.ModelAdmin):
    """Admin for TransactionQuery model."""

    list_display = [
        "query_number",
        "query_date",
        "transaction_type",
        "transaction_number",
        "customer_name",
        "query_status",
        "assigned_to",
        "resolved_by",
    ]

    list_filter = ["query_date", "transaction_type", "query_status"]

    search_fields = ["query_number", "transaction_number", "customer_name"]

    readonly_fields = ["created_at", "updated_at"]

    date_hierarchy = "query_date"

    fieldsets = (
        (
            "Query Details",
            {
                "fields": (
                    "query_number",
                    "query_date",
                    "transaction_type",
                    "transaction_number",
                    "query_status",
                )
            },
        ),
        ("Customer Information", {"fields": ("customer_name", "contact_number")}),
        ("Query Description", {"fields": ("query_description",)}),
        ("Assignment", {"fields": ("assigned_to",)}),
        (
            "Resolution",
            {"fields": ("resolution_notes", "resolved_by", "resolved_date")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )
