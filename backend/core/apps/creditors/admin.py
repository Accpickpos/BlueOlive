from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Creditor, GoodsReceivedNote, GRNLineItem, CreditorInvoice,
    CreditorInvoiceLineItem, CreditorCreditNote, CreditorCreditNoteLineItem,
    CreditorPayment, CreditorJournal, CreditorOpenItem, OpenItemAllocation,
    RFC, RFCLineItem, CreditorTransactionLine, SupplierMonthlyPurchase,
    ExpenseMonthlyTotal
)


@admin.register(Creditor)
class CreditorAdmin(admin.ModelAdmin):
    """Admin interface for creditors/suppliers"""
    
    list_display = (
        'supplier_number', 'name', 'email', 'telephone1',
        'get_current_balance', 'credit_terms', 'is_active'
    )
    list_filter = ('is_active', 'account_category', 'created_at', 'sales_area')
    search_fields = ('name', 'email', 'supplier_number', 'account_number')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('supplier_number', 'account_number', 'name', 'short_name', 'contact_person', 'sales_area')
        }),
        ('Contact Details', {
            'fields': ('telephone1', 'telephone2', 'fax', 'email')
        }),
        ('Physical Address', {
            'fields': (
                'physical_address_line1', 'physical_address_line2', 'physical_address_line3',
                'physical_city', 'physical_province', 'physical_postal_code'
            ),
            'classes': ('collapse',)
        }),
        ('Postal Address', {
            'fields': (
                'postal_address_line1', 'postal_address_line2', 'postal_address_line3',
                'postal_city', 'postal_province', 'postal_postal_code'
            ),
            'classes': ('collapse',)
        }),
        ('Account Settings', {
            'fields': (
                'our_account_number', 'account_type', 'credit_terms', 'account_category',
                'update_selling_price_on_receipt', 'prompt_payment_discount_percent', 'vat_number', 'is_active'
            )
        }),
        ('Banking Details', {
            'fields': (
                'bank_name', 'bank_branch_code', 'bank_account_number'
            ),
            'classes': ('collapse',)
        }),
        ('Balances', {
            'fields': (
                'balance_current', 'balance_30_days', 'balance_60_days',
                'balance_90_days', 'balance_120_days', 'balance_150_days',
                'balance_180_days', 'current_balance'
            ),
            'description': 'Age analysis balances'
        }),
        ('Statistics', {
            'fields': (
                'last_paid_amount', 'amount_last_paid', 'last_paid_date', 'date_last_paid',
                'purchases_mtd', 'purchases_ytd', 'rfc_outstanding_amount'
            ),
            'description': 'System-calculated statistics'
        }),
    )
    
    readonly_fields = (
        'balance_current', 'balance_30_days', 'balance_60_days',
        'balance_90_days', 'balance_120_days', 'balance_150_days',
        'balance_180_days', 'current_balance', 'last_paid_amount',
        'amount_last_paid', 'last_paid_date', 'date_last_paid',
        'purchases_mtd', 'purchases_ytd', 'rfc_outstanding_amount',
        'created_at', 'updated_at'
    )
    
    def get_current_balance(self, obj):
        """Display current balance with color coding"""
        balance = obj.current_balance
        color = 'red' if balance > 0 else 'green'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            f'{balance:,.2f}'
        )
    get_current_balance.short_description = 'Current Balance'


class GRNLineItemInline(admin.TabularInline):
    """Inline editor for GRN line items"""
    model = GRNLineItem
    extra = 1
    fields = ('line_number', 'stock_item', 'quantity_received', 'unit_cost', 'tax_code')
    readonly_fields = ('line_subtotal', 'tax_amount', 'line_total')


@admin.register(GoodsReceivedNote)
class GoodsReceivedNoteAdmin(admin.ModelAdmin):
    """Admin interface for GRN"""
    
    list_display = (
        'transaction_number', 'creditor', 'transaction_date',
        'supplier_invoice_number', 'total_amount', 'is_posted'
    )
    list_filter = ('transaction_date', 'is_posted', 'inclusive_exclusive')
    search_fields = ('transaction_number', 'creditor__name', 'supplier_invoice_number')
    date_hierarchy = 'transaction_date'
    
    readonly_fields = ('subtotal', 'total_vat', 'total_quantity', 'transaction_type',
                       'transaction_number', 'posted_at', 'posted_by')
    
    inlines = [GRNLineItemInline]


class CreditorInvoiceLineItemInline(admin.TabularInline):
    """Inline editor for invoice line items"""
    model = CreditorInvoiceLineItem
    extra = 1
    fields = ('line_number', 'expense_category', 'amount', 'tax_code')
    readonly_fields = ('tax_amount', 'line_total')


@admin.register(CreditorInvoice)
class CreditorInvoiceAdmin(admin.ModelAdmin):
    """Admin interface for creditor invoices"""
    
    list_display = (
        'transaction_number', 'creditor', 'transaction_date',
        'supplier_invoice_number', 'total_amount', 'is_posted'
    )
    list_filter = ('transaction_date', 'is_posted', 'inclusive_exclusive')
    search_fields = ('transaction_number', 'creditor__name', 'supplier_invoice_number')
    date_hierarchy = 'transaction_date'
    
    readonly_fields = ('subtotal', 'total_vat', 'transaction_type',
                       'transaction_number', 'posted_at', 'posted_by')
    
    inlines = [CreditorInvoiceLineItemInline]


class CreditorCreditNoteLineItemInline(admin.TabularInline):
    """Inline editor for credit note line items"""
    model = CreditorCreditNoteLineItem
    extra = 1
    fields = ('line_number', 'stock_item', 'quantity_returned', 'unit_cost', 'tax_code')
    readonly_fields = ('line_subtotal', 'tax_amount', 'line_total')


@admin.register(CreditorCreditNote)
class CreditorCreditNoteAdmin(admin.ModelAdmin):
    """Admin interface for credit notes"""
    
    list_display = (
        'transaction_number', 'creditor', 'transaction_date',
        'supplier_credit_note_number', 'total_amount', 'is_posted'
    )
    list_filter = ('transaction_date', 'is_posted', 'inclusive_exclusive')
    search_fields = ('transaction_number', 'creditor__name', 'supplier_credit_note_number')
    date_hierarchy = 'transaction_date'
    
    readonly_fields = ('subtotal', 'total_vat', 'transaction_type',
                       'transaction_number', 'posted_at', 'posted_by')
    
    inlines = [CreditorCreditNoteLineItemInline]


@admin.register(CreditorPayment)
class CreditorPaymentAdmin(admin.ModelAdmin):
    """Admin interface for creditor payments"""
    
    list_display = (
        'transaction_number', 'creditor', 'transaction_date',
        'payment_method', 'amount_paid', 'is_posted'
    )
    list_filter = ('transaction_date', 'payment_method', 'is_posted')
    search_fields = ('transaction_number', 'creditor__name')
    date_hierarchy = 'transaction_date'
    
    readonly_fields = ('settlement_discount_amount', 'settlement_discount_percent',
                       'transaction_type', 'transaction_number', 'posted_at', 'posted_by')


@admin.register(CreditorJournal)
class CreditorJournalAdmin(admin.ModelAdmin):
    """Admin interface for creditor journals"""
    
    list_display = (
        'transaction_number', 'creditor', 'transaction_date',
        'journal_type', 'journal_amount', 'is_posted'
    )
    list_filter = ('transaction_date', 'journal_type', 'is_posted')
    search_fields = ('transaction_number', 'creditor__name')
    date_hierarchy = 'transaction_date'
    
    readonly_fields = ('transaction_type', 'transaction_number', 'total_amount',
                       'posted_at', 'posted_by')


@admin.register(CreditorOpenItem)
class CreditorOpenItemAdmin(admin.ModelAdmin):
    """Admin interface for open items"""
    
    list_display = (
        'transaction_number', 'creditor', 'transaction_date',
        'original_amount', 'balance_due', 'is_fully_allocated'
    )
    list_filter = ('transaction_date', 'transaction_type', 'is_fully_allocated')
    search_fields = ('transaction_number', 'creditor__name')
    date_hierarchy = 'transaction_date'
    
    readonly_fields = ('transaction_type', 'transaction_number')


@admin.register(OpenItemAllocation)
class OpenItemAllocationAdmin(admin.ModelAdmin):
    """Admin interface for open item allocations"""
    
    list_display = (
        'payment', 'open_item', 'amount_paid',
        'settlement_discount', 'allocated_at'
    )
    list_filter = ('allocated_at',)
    search_fields = ('payment__creditor__name', 'open_item__transaction_number')
    date_hierarchy = 'allocated_at'
    
    readonly_fields = ('allocated_at',)


class RFCLineItemInline(admin.TabularInline):
    """Inline editor for RFC line items"""
    model = RFCLineItem
    extra = 1
    fields = ('line_number', 'stock_item', 'quantity_returned', 'unit_cost', 'tax_code', 'reason')
    readonly_fields = ('unit_cost', 'tax_amount', 'line_value_exclusive', 'line_value_inclusive')


@admin.register(RFC)
class RFCAdmin(admin.ModelAdmin):
    """Admin interface for Returns for Credit"""
    
    list_display = (
        'rfc_number', 'creditor', 'return_date', 'status',
        'total_value_inclusive'
    )
    list_filter = ('status', 'return_date', 'created_at')
    search_fields = ('rfc_number', 'creditor__name')
    date_hierarchy = 'return_date'
    
    inlines = [RFCLineItemInline]
    
    readonly_fields = (
        'total_value_exclusive', 'total_value_inclusive',
        'created_at', 'updated_at'
    )


@admin.register(CreditorTransactionLine)
class CreditorTransactionLineAdmin(admin.ModelAdmin):
    """Admin interface for transaction line items"""
    
    list_display = (
        'line_number', 'stock_item', 'expense_category', 'quantity',
        'amount_exclusive', 'amount_inclusive'
    )
    list_filter = ('line_number', 'created_at')
    search_fields = ('stock_item__stock_code', 'expense_category__category_name')
    date_hierarchy = 'created_at'
    
    readonly_fields = ('tax_amount', 'amount_inclusive', 'created_at')


@admin.register(SupplierMonthlyPurchase)
class SupplierMonthlyPurchaseAdmin(admin.ModelAdmin):
    """Admin interface for monthly purchase statistics"""
    
    list_display = (
        'supplier', 'year', 'month', 'total_purchases',
        'quantity_purchased', 'number_of_transactions'
    )
    list_filter = ('year', 'month', 'supplier')
    search_fields = ('supplier__name',)
    
    readonly_fields = ('total_purchases', 'quantity_purchased', 'number_of_transactions',
                       'created_at', 'updated_at')


@admin.register(ExpenseMonthlyTotal)
class ExpenseMonthlyTotalAdmin(admin.ModelAdmin):
    """Admin interface for monthly expense totals"""
    
    list_display = (
        'expense_category', 'year', 'month', 'total_amount',
        'total_vat', 'number_of_invoices'
    )
    list_filter = ('year', 'month', 'expense_category')
    search_fields = ('expense_category__category_name',)
    
    readonly_fields = ('total_amount', 'total_vat', 'number_of_invoices',
                       'created_at', 'updated_at')
