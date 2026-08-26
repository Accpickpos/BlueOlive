"""
CREDITORS APP - DJANGO ADMIN CONFIGURATION
Advanced admin interface with bulk actions, filters, and business logic
"""

from django.contrib import admin
from django.db.models import DecimalField, F, Q, Sum
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .models import (
    RFC,
    Creditor,
    CreditorCreditNote,
    CreditorCreditNoteLineItem,
    CreditorInvoice,
    CreditorInvoiceLineItem,
    CreditorJournal,
    CreditorOpenItem,
    CreditorPayment,
    CreditorTransactionLine,
    ExpenseCategoryMonthlyBalance,
    GoodsReceivedNote,
    GRNLineItem,
    OpenItemAllocation,
    OpenItemAudit,
    RFCLineItem,
)

# ============================================================================
# CUSTOM FILTERS
# ============================================================================


class BalanceRangeFilter(admin.SimpleListFilter):
    """Filter creditors by balance ranges"""

    title = _("Balance Range")
    parameter_name = "balance_range"

    def lookups(self, request, model_admin):
        return (
            ("0", _("Zero Balance")),
            ("1-1000", _("1 - 1,000")),
            ("1001-5000", _("1,001 - 5,000")),
            ("5001-10000", _("5,001 - 10,000")),
            ("10001+", _("Over 10,000")),
        )

    def queryset(self, request, queryset):
        if self.value() == "0":
            return queryset.filter(current_balance=0)
        elif self.value() == "1-1000":
            return queryset.filter(current_balance__gt=0, current_balance__lte=1000)
        elif self.value() == "1001-5000":
            return queryset.filter(current_balance__gt=1000, current_balance__lte=5000)
        elif self.value() == "5001-10000":
            return queryset.filter(current_balance__gt=5000, current_balance__lte=10000)
        elif self.value() == "10001+":
            return queryset.filter(current_balance__gt=10000)


class OverdueFilter(admin.SimpleListFilter):
    """Filter creditors by overdue status"""

    title = _("Overdue Status")
    parameter_name = "overdue"

    def lookups(self, request, model_admin):
        return (
            ("overdue_30", _("30+ Days Overdue")),
            ("overdue_60", _("60+ Days Overdue")),
            ("overdue_90", _("90+ Days Overdue")),
        )

    def queryset(self, request, queryset):
        if self.value() == "overdue_30":
            return queryset.filter(balance_30_days__gt=0)
        elif self.value() == "overdue_60":
            return queryset.filter(balance_60_days__gt=0)
        elif self.value() == "overdue_90":
            return queryset.filter(balance_90_days__gt=0)


# ============================================================================
# CREDITOR (SUPPLIER) ADMIN
# ============================================================================


@admin.register(Creditor)
class CreditorAdmin(admin.ModelAdmin):
    """Admin interface for creditors/suppliers with advanced features"""

    list_display = (
        "supplier_number",
        "name",
        "get_balance_color",
        "get_aging_summary",
        "credit_terms",
        "last_paid_date",
        "is_active",
    )
    list_filter = (
        "is_active",
        "account_category",
        BalanceRangeFilter,
        OverdueFilter,
        "credit_terms",
        "sales_area",
        "created_at",
    )
    search_fields = ("name", "email", "supplier_number", "contact_person", "telephone")
    readonly_fields = (
        "balance_current",
        "balance_30_days",
        "balance_60_days",
        "balance_90_days",
        "balance_120_days",
        "balance_150_days",
        "balance_180_days",
        "total_outstanding_balance",
        "last_paid_amount",
        "last_paid_date",
        "purchases_mtd",
        "purchases_ytd",
        "created_at",
        "updated_at",
        "balance_brought_forward",
        "get_aging_display",
    )

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "supplier_number",
                    "name",
                    "contact_person",
                    "sales_area",
                    "is_active",
                )
            },
        ),
        (_("Contact Details"), {"fields": ("telephone", "fax", "email")}),
        (
            _("Address Details"),
            {
                "fields": (
                    ("physical_address_line1", "physical_address_line2"),
                    ("physical_city", "physical_province", "physical_code"),
                    ("postal_address_line1", "postal_address_line2"),
                    ("postal_city", "postal_province", "postal_code"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Account Settings"),
            {
                "fields": (
                    "our_account_number",
                    "credit_terms",
                    "account_category",
                    "prompt_payment_discount_percent",
                    "update_selling_price_on_receipt",
                )
            },
        ),
        (
            _("Banking Details"),
            {
                "fields": ("bank_name", "branch_code", "account_number"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Opening Balance (BBF)"),
            {
                "fields": ("balance_brought_forward",),
                # Static string literal, no interpolated/user content.
                "description": mark_safe(  # nosec B308
                    "<strong>Set opening balance from previous period</strong>"
                ),
            },
        ),
        (
            _("Aged Balance Analysis"),
            {
                "fields": (
                    "get_aging_display",
                    ("balance_current", "balance_30_days", "balance_60_days"),
                    ("balance_90_days", "balance_120_days", "balance_150_days"),
                    ("balance_180_days", "total_outstanding_balance"),
                ),
                "classes": ("wide",),
                "description": "System-calculated aging balances (auto-updated)",
            },
        ),
        (
            _("Payment History"),
            {
                "fields": ("last_paid_amount", "last_paid_date"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Purchase Statistics"),
            {"fields": ("purchases_mtd", "purchases_ytd"), "classes": ("collapse",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    actions = [
        "activate_creditors",
        "deactivate_creditors",
        "recalculate_aged_balances",
    ]

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related("credit_terms", "sales_area")

    def get_balance_color(self, obj):
        """Display current balance with color coding"""
        balance = obj.current_balance
        if balance == 0:
            color = "gray"
            symbol = "✓"
        elif balance > 0:
            color = "red"
            symbol = "⚠"
        else:
            color = "green"
            symbol = "✓"

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {:.2f}</span>',
            color,
            symbol,
            balance,
        )

    get_balance_color.short_description = _("Current Balance")

    def get_aging_summary(self, obj):
        """Display aging summary tooltip"""
        if (
            obj.balance_30_days > 0
            or obj.balance_60_days > 0
            or obj.balance_90_days > 0
        ):
            aging = f"30D: {obj.balance_30_days:.0f} | 60D: {obj.balance_60_days:.0f} | 90D: {obj.balance_90_days:.0f}"
            return format_html('<span title="{}">{}</span>', aging, "📊")
        return "-"

    get_aging_summary.short_description = _("Aging")

    def get_aging_display(self, obj):
        """Display all aging buckets in table format"""
        html = """
        <table style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f0f0f0;">
                <td style="border: 1px solid #ccc; padding: 5px;"><strong>Current</strong></td>
                <td style="border: 1px solid #ccc; padding: 5px;"><strong>30 Days</strong></td>
                <td style="border: 1px solid #ccc; padding: 5px;"><strong>60 Days</strong></td>
                <td style="border: 1px solid #ccc; padding: 5px;"><strong>90 Days</strong></td>
                <td style="border: 1px solid #ccc; padding: 5px;"><strong>120 Days</strong></td>
                <td style="border: 1px solid #ccc; padding: 5px;"><strong>150 Days</strong></td>
                <td style="border: 1px solid #ccc; padding: 5px;"><strong>180 Days</strong></td>
            </tr>
            <tr>
                <td style="border: 1px solid #ccc; padding: 5px;">{:.2f}</td>
                <td style="border: 1px solid #ccc; padding: 5px;">{:.2f}</td>
                <td style="border: 1px solid #ccc; padding: 5px;">{:.2f}</td>
                <td style="border: 1px solid #ccc; padding: 5px;">{:.2f}</td>
                <td style="border: 1px solid #ccc; padding: 5px;">{:.2f}</td>
                <td style="border: 1px solid #ccc; padding: 5px;">{:.2f}</td>
                <td style="border: 1px solid #ccc; padding: 5px;">{:.2f}</td>
            </tr>
        </table>
        """.format(
            obj.balance_current,
            obj.balance_30_days,
            obj.balance_60_days,
            obj.balance_90_days,
            obj.balance_120_days,
            obj.balance_150_days,
            obj.balance_180_days,
        )
        # All interpolated values are DecimalField balances formatted with
        # {:.2f}, never free-text/user-supplied strings - no XSS vector.
        return mark_safe(html)  # nosec B308 B703

    get_aging_display.short_description = _("Aging Analysis")

    @admin.action(description=_("Activate selected creditors"))
    def activate_creditors(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} creditors activated.")

    @admin.action(description=_("Deactivate selected creditors"))
    def deactivate_creditors(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} creditors deactivated.")

    @admin.action(description=_("Recalculate aged balances"))
    def recalculate_aged_balances(self, request, queryset):
        count = 0
        for creditor in queryset:
            creditor.recalculate_aged_balances()
            count += 1
        self.message_user(request, f"Recalculated aged balances for {count} creditors.")


# ============================================================================
# GOODS RECEIVED NOTE (GRN) ADMIN
# ============================================================================


class GRNLineItemInline(admin.TabularInline):
    """Inline editor for GRN line items"""

    model = GRNLineItem
    extra = 1
    fields = (
        "line_number",
        "stock_item",
        "quantity_received",
        "unit_cost",
        "tax_code",
        "line_subtotal",
        "tax_amount",
        "line_total",
    )
    readonly_fields = ("line_subtotal", "tax_amount", "line_total")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("stock_item", "tax_code")


@admin.register(GoodsReceivedNote)
class GoodsReceivedNoteAdmin(admin.ModelAdmin):
    """Admin interface for Goods Received Notes"""

    list_display = (
        "transaction_number",
        "creditor",
        "transaction_date",
        "supplier_invoice_number",
        "get_total_display",
        "get_status_badge",
    )
    list_filter = ("is_posted", "transaction_date", "inclusive_exclusive", "created_at")
    search_fields = ("transaction_number", "creditor__name", "supplier_invoice_number")
    date_hierarchy = "transaction_date"

    readonly_fields = (
        "subtotal",
        "total_vat",
        "total_quantity",
        "transaction_type",
        "transaction_number",
        "posted_at",
        "posted_by",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            _("Document Information"),
            {"fields": ("transaction_number", "transaction_type", "transaction_date")},
        ),
        (
            _("Supplier Details"),
            {"fields": ("creditor", "supplier_invoice_number", "supplier_reference")},
        ),
        (_("Goods Information"), {"fields": ("inclusive_exclusive",)}),
        (
            _("Totals"),
            {
                "fields": ("total_quantity", "subtotal", "total_vat", "total_amount"),
                "classes": ("wide",),
            },
        ),
        (
            _("Posting"),
            {
                "fields": ("is_posted", "posted_date", "posted_by", "posted_at"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    inlines = [GRNLineItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("creditor", "posted_by")

    def get_total_display(self, obj):
        """Display total with currency formatting"""
        return format_html(
            '<span style="color: #1f77b4; font-weight: bold;">{:.2f}</span>',
            obj.total_amount or 0,
        )

    get_total_display.short_description = _("Total Amount")

    def get_status_badge(self, obj):
        """Display status as badge"""
        color = "green" if obj.is_posted else "orange"
        label = _("Posted") if obj.is_posted else _("Pending")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            label,
        )

    get_status_badge.short_description = _("Status")


# ============================================================================
# CREDITOR INVOICE ADMIN
# ============================================================================


class CreditorInvoiceLineItemInline(admin.TabularInline):
    """Inline editor for invoice line items"""

    model = CreditorInvoiceLineItem
    extra = 1
    fields = (
        "line_number",
        "expense_category",
        "amount",
        "tax_code",
        "tax_amount",
        "line_total",
    )
    readonly_fields = ("tax_amount", "line_total")

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("expense_category", "tax_code")
        )


@admin.register(CreditorInvoice)
class CreditorInvoiceAdmin(admin.ModelAdmin):
    """Admin interface for creditor invoices"""

    list_display = (
        "transaction_number",
        "creditor",
        "transaction_date",
        "supplier_invoice_number",
        "get_total_display",
        "get_status_badge",
    )
    list_filter = ("is_posted", "transaction_date", "inclusive_exclusive", "created_at")
    search_fields = ("transaction_number", "creditor__name", "supplier_invoice_number")
    date_hierarchy = "transaction_date"

    readonly_fields = (
        "subtotal",
        "total_vat",
        "transaction_type",
        "transaction_number",
        "posted_at",
        "posted_by",
        "due_date",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            _("Document Information"),
            {
                "fields": (
                    "transaction_number",
                    "transaction_type",
                    "transaction_date",
                    "due_date",
                )
            },
        ),
        (
            _("Supplier Details"),
            {"fields": ("creditor", "supplier_invoice_number", "supplier_reference")},
        ),
        (_("Invoice Settings"), {"fields": ("inclusive_exclusive",)}),
        (
            _("Totals"),
            {"fields": ("subtotal", "total_vat", "total_amount"), "classes": ("wide",)},
        ),
        (
            _("Posting"),
            {
                "fields": ("is_posted", "posted_date", "posted_by", "posted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [CreditorInvoiceLineItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("creditor", "posted_by")

    def get_total_display(self, obj):
        return format_html(
            '<span style="color: #1f77b4; font-weight: bold;">{:.2f}</span>',
            obj.total_amount or 0,
        )

    get_total_display.short_description = _("Total Amount")

    def get_status_badge(self, obj):
        color = "green" if obj.is_posted else "orange"
        label = _("Posted") if obj.is_posted else _("Pending")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            label,
        )

    get_status_badge.short_description = _("Status")


# ============================================================================
# CREDITOR CREDIT NOTE ADMIN
# ============================================================================


class CreditorCreditNoteLineItemInline(admin.TabularInline):
    """Inline editor for credit note line items"""

    model = CreditorCreditNoteLineItem
    extra = 1
    fields = (
        "line_number",
        "stock_item",
        "quantity_returned",
        "unit_cost",
        "tax_code",
        "line_subtotal",
        "tax_amount",
        "line_total",
    )
    readonly_fields = ("line_subtotal", "tax_amount", "line_total")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("stock_item", "tax_code")


@admin.register(CreditorCreditNote)
class CreditorCreditNoteAdmin(admin.ModelAdmin):
    """Admin interface for creditor credit notes"""

    list_display = (
        "transaction_number",
        "creditor",
        "transaction_date",
        "supplier_credit_note_number",
        "get_total_display",
        "get_status_badge",
    )
    list_filter = ("is_posted", "transaction_date", "inclusive_exclusive", "created_at")
    search_fields = (
        "transaction_number",
        "creditor__name",
        "supplier_credit_note_number",
    )
    date_hierarchy = "transaction_date"

    readonly_fields = (
        "subtotal",
        "total_vat",
        "transaction_type",
        "transaction_number",
        "posted_at",
        "posted_by",
        "due_date",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            _("Document Information"),
            {
                "fields": (
                    "transaction_number",
                    "transaction_type",
                    "transaction_date",
                    "due_date",
                )
            },
        ),
        (
            _("Supplier Details"),
            {
                "fields": (
                    "creditor",
                    "supplier_credit_note_number",
                    "supplier_reference",
                )
            },
        ),
        (_("Credit Note Settings"), {"fields": ("inclusive_exclusive",)}),
        (
            _("Totals"),
            {"fields": ("subtotal", "total_vat", "total_amount"), "classes": ("wide",)},
        ),
        (
            _("Posting"),
            {
                "fields": ("is_posted", "posted_date", "posted_by", "posted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    inlines = [CreditorCreditNoteLineItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("creditor", "posted_by")

    def get_total_display(self, obj):
        return format_html(
            '<span style="color: #2ca02c; font-weight: bold;">{:.2f}</span>',
            obj.total_amount or 0,
        )

    get_total_display.short_description = _("Total Amount")

    def get_status_badge(self, obj):
        color = "green" if obj.is_posted else "orange"
        label = _("Posted") if obj.is_posted else _("Pending")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            label,
        )

    get_status_badge.short_description = _("Status")


# ============================================================================
# CREDITOR PAYMENT ADMIN
# ============================================================================


@admin.register(CreditorPayment)
class CreditorPaymentAdmin(admin.ModelAdmin):
    """Admin interface for creditor payments"""

    list_display = (
        "transaction_number",
        "creditor",
        "transaction_date",
        "payment_method",
        "get_amount_display",
        "get_status_badge",
    )
    list_filter = ("is_posted", "payment_method", "transaction_date", "created_at")
    search_fields = (
        "transaction_number",
        "creditor__name",
        "cheque_number",
        "reference_number",
    )
    date_hierarchy = "transaction_date"

    readonly_fields = (
        "settlement_discount_amount",
        "settlement_discount_percent",
        "transaction_type",
        "transaction_number",
        "posted_at",
        "posted_by",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            _("Payment Information"),
            {"fields": ("transaction_number", "transaction_type", "transaction_date")},
        ),
        (_("Creditor Details"), {"fields": ("creditor",)}),
        (
            _("Payment Details"),
            {
                "fields": (
                    "payment_method",
                    "amount_paid",
                    "settlement_discount_percent",
                    "settlement_discount_amount",
                    "total_allocation",
                ),
                "classes": ("wide",),
            },
        ),
        (
            _("Payment Reference"),
            {
                "fields": ("cheque_number", "reference_number", "remarks"),
                "classes": ("collapse",),
            },
        ),
        (
            _("Posting"),
            {
                "fields": ("is_posted", "posted_date", "posted_by", "posted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("creditor", "posted_by", "payment_method")
        )

    def get_amount_display(self, obj):
        return format_html(
            '<span style="color: #d62728; font-weight: bold;">{:.2f}</span>',
            obj.amount_paid or 0,
        )

    get_amount_display.short_description = _("Amount Paid")

    def get_status_badge(self, obj):
        color = "green" if obj.is_posted else "orange"
        label = _("Posted") if obj.is_posted else _("Pending")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            label,
        )

    get_status_badge.short_description = _("Status")


# ============================================================================
# CREDITOR JOURNAL ADMIN
# ============================================================================


@admin.register(CreditorJournal)
class CreditorJournalAdmin(admin.ModelAdmin):
    """Admin interface for creditor journals"""

    list_display = (
        "transaction_number",
        "creditor",
        "transaction_date",
        "journal_type",
        "get_amount_display",
        "get_status_badge",
    )
    list_filter = ("is_posted", "journal_type", "transaction_date", "created_at")
    search_fields = ("transaction_number", "creditor__name", "remarks")
    date_hierarchy = "transaction_date"

    readonly_fields = (
        "transaction_type",
        "transaction_number",
        "total_amount",
        "posted_at",
        "posted_by",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            _("Journal Information"),
            {
                "fields": (
                    "transaction_number",
                    "transaction_type",
                    "transaction_date",
                    "journal_type",
                )
            },
        ),
        (_("Creditor Details"), {"fields": ("creditor",)}),
        (
            _("Journal Details"),
            {
                "fields": ("journal_amount", "narrative", "remarks"),
                "classes": ("wide",),
            },
        ),
        (
            _("Posting"),
            {
                "fields": ("is_posted", "posted_date", "posted_by", "posted_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("creditor", "posted_by")

    def get_amount_display(self, obj):
        color = "#ff7f0e" if obj.journal_amount > 0 else "#2ca02c"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            obj.journal_amount or 0,
        )

    get_amount_display.short_description = _("Amount")

    def get_status_badge(self, obj):
        color = "green" if obj.is_posted else "orange"
        label = _("Posted") if obj.is_posted else _("Pending")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            label,
        )

    get_status_badge.short_description = _("Status")


# ============================================================================
# CREDITOR OPEN ITEMS ADMIN
# ============================================================================


@admin.register(CreditorOpenItem)
class CreditorOpenItemAdmin(admin.ModelAdmin):
    """Admin interface for open items"""

    list_display = (
        "transaction_number",
        "creditor",
        "transaction_date",
        "original_amount",
        "get_balance_display",
        "get_allocation_badge",
    )
    list_filter = (
        "transaction_date",
        "transaction_type",
        "is_fully_allocated",
        "created_at",
    )
    search_fields = ("transaction_number", "creditor__name")
    date_hierarchy = "transaction_date"

    readonly_fields = (
        "transaction_type",
        "transaction_number",
        "original_amount",
        "balance_due",
        "is_fully_allocated",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            _("Item Information"),
            {"fields": ("transaction_number", "transaction_type", "transaction_date")},
        ),
        (_("Creditor Details"), {"fields": ("creditor",)}),
        (
            _("Amounts"),
            {"fields": ("original_amount", "balance_due"), "classes": ("wide",)},
        ),
        (
            _("Status"),
            {
                "fields": ("is_fully_allocated",),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("creditor")

    def get_balance_display(self, obj):
        color = "green" if obj.balance_due == 0 else "red"
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f}</span>',
            color,
            obj.balance_due or 0,
        )

    get_balance_display.short_description = _("Balance Due")

    def get_allocation_badge(self, obj):
        color = "green" if obj.is_fully_allocated else "orange"
        label = _("Fully Allocated") if obj.is_fully_allocated else _("Partial")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            label,
        )

    get_allocation_badge.short_description = _("Allocation Status")


# ============================================================================
# OPEN ITEM ALLOCATION ADMIN
# ============================================================================


@admin.register(OpenItemAllocation)
class OpenItemAllocationAdmin(admin.ModelAdmin):
    """Admin interface for open item allocations"""

    list_display = (
        "id",
        "get_creditor_display",
        "open_item",
        "payment",
        "get_amount_display",
        "allocated_at",
    )
    list_filter = ("allocated_at",)
    search_fields = (
        "payment__creditor__name",
        "open_item__transaction_number",
        "payment__transaction_number",
    )
    date_hierarchy = "allocated_at"

    readonly_fields = ("allocated_at",)

    fieldsets = (
        (_("Allocation Information"), {"fields": ("payment", "open_item")}),
        (
            _("Amount Details"),
            {
                "fields": ("amount_paid", "settlement_discount"),
            },
        ),
        (_("Audit"), {"fields": ("allocated_at",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("payment__creditor", "open_item")
        )

    def get_creditor_display(self, obj):
        return obj.payment.creditor.name

    get_creditor_display.short_description = _("Creditor")

    def get_amount_display(self, obj):
        return format_html(
            '<span style="color: #1f77b4; font-weight: bold;">{:.2f}</span>',
            obj.amount_paid or 0,
        )

    get_amount_display.short_description = _("Amount Allocated")


# ============================================================================
# REQUESTS FOR CREDIT (RFC) ADMIN
# ============================================================================


class RFCLineItemInline(admin.TabularInline):
    """Inline editor for RFC line items"""

    model = RFCLineItem
    extra = 1
    fields = (
        "line_number",
        "stock_item",
        "quantity_returned",
        "unit_cost",
        "tax_code",
        "reason",
        "line_value_exclusive",
        "tax_amount",
        "line_value_inclusive",
    )
    readonly_fields = (
        "unit_cost",
        "tax_amount",
        "line_value_exclusive",
        "line_value_inclusive",
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("stock_item", "tax_code")


@admin.register(RFC)
class RFCAdmin(admin.ModelAdmin):
    """Admin interface for Returns for Credit"""

    list_display = (
        "rfc_number",
        "creditor",
        "return_date",
        "get_status_badge",
        "get_total_display",
        "get_lifecycle_display",
    )
    list_filter = ("status", "return_date", "date_sent", "date_returned", "created_at")
    search_fields = ("rfc_number", "creditor__name", "purchase_order_number")
    date_hierarchy = "return_date"

    readonly_fields = (
        "total_value_exclusive",
        "total_value_inclusive",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (_("RFC Information"), {"fields": ("rfc_number", "return_date", "status")}),
        (
            _("Creditor Details"),
            {
                "fields": (
                    "creditor",
                    "purchase_order_number",
                    "purchase_order_line_number",
                )
            },
        ),
        (
            _("Return Details"),
            {
                "fields": ("reason_for_return", "remarks"),
            },
        ),
        (
            _("Lifecycle"),
            {
                "fields": (
                    "date_sent",
                    "date_returned",
                    "credited_date",
                    "replaced_date",
                    "replaced_rfc_number",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Totals"),
            {
                "fields": ("total_value_exclusive", "total_value_inclusive"),
                "classes": ("wide",),
            },
        ),
        (
            _("Audit"),
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    inlines = [RFCLineItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("creditor")

    def get_status_badge(self, obj):
        status_colors = {
            "pending": "orange",
            "credited": "green",
            "replaced": "blue",
            "cancelled": "red",
        }
        color = status_colors.get(obj.status, "gray")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display(),
        )

    get_status_badge.short_description = _("Status")

    def get_total_display(self, obj):
        return format_html(
            '<span style="color: #1f77b4; font-weight: bold;">{:.2f}</span>',
            obj.total_value_inclusive or 0,
        )

    get_total_display.short_description = _("Total Value")

    def get_lifecycle_display(self, obj):
        """Show lifecycle progress"""
        steps = []
        if obj.date_sent:
            steps.append("📤 Sent")
        if obj.date_returned:
            steps.append("📥 Returned")
        if obj.credited_date:
            steps.append("✓ Credited")
        if obj.replaced_date:
            steps.append("🔄 Replaced")
        return " → ".join(steps) if steps else "⏳ Pending"

    get_lifecycle_display.short_description = _("Lifecycle")
