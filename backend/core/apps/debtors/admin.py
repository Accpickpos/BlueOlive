"""
Django admin configuration for debtors app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Debtor, DebtorTransaction, Invoice, InvoiceLine, PostDatedCheque, AuditLog


@admin.register(Debtor)
class DebtorAdmin(admin.ModelAdmin):
    """Admin interface for Debtor model."""
    
    list_display = [
        'account_number', 'name', 'status_display', 'total_balance',
        'credit_limit', 'last_payment_date', 'is_active'
    ]
    list_filter = [
        'is_active', 'is_blocked', 'account_category', 'sales_area',
        'charge_interest', 'created_at'
    ]
    search_fields = ['account_number', 'name', 'email', 'telephone1']
    readonly_fields = [
        'current_balance', 'balance_30_days', 'balance_60_days',
        'balance_90_days', 'balance_120_days', 'balance_150_days',
        'balance_180_days', 'total_balance', 'sales_mtd', 'sales_ytd',
        'last_payment_date', 'last_payment_amount', 'created_at', 'updated_at',
        'blocked_by', 'blocked_date', 'unblocked_date'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('account_number', 'name', 'search_name', 'contact_person')
        }),
        ('Contact Details', {
            'fields': (
                'telephone1', 'telephone2', 'fax', 'email', 'additional_info'
            ),
            'classes': ('collapse',)
        }),
        ('Postal Address', {
            'fields': (
                'postal_address_line1', 'postal_address_line2',
                'postal_address_line3', 'postal_code'
            ),
            'classes': ('collapse',)
        }),
        ('Delivery Address', {
            'fields': (
                'delivery_address_line1', 'delivery_address_line2',
                'delivery_address_line3', 'delivery_code'
            ),
            'classes': ('collapse',)
        }),
        ('Business Details', {
            'fields': ('vat_number', 'sales_area')
        }),
        ('Account Settings', {
            'fields': (
                'account_category', 'trade_discount', 'credit_limit',
                'price_level', 'terms', 'prompt_discount_percentage',
                'print_discount_on_invoice', 'charge_interest',
                'print_balance_on_documents'
            )
        }),
        ('Block Status', {
            'fields': (
                'is_blocked', 'block_reason', 'block_invoicing',
                'block_receipts', 'blocked_by', 'blocked_date', 'unblocked_date'
            ),
            'classes': ('collapse',)
        }),
        ('Balances & Aging', {
            'fields': (
                'current_balance', 'balance_30_days', 'balance_60_days',
                'balance_90_days', 'balance_120_days', 'balance_150_days',
                'balance_180_days', 'total_balance'
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'last_payment_date', 'last_payment_amount',
                'sales_mtd', 'sales_ytd'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Audit', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['block_accounts', 'unblock_accounts', 'mark_inactive']
    
    def status_display(self, obj):
        """Display color-coded status."""
        if obj.is_blocked:
            color = 'red'
            status = 'BLOCKED'
        elif not obj.is_active:
            color = 'orange'
            status = 'INACTIVE'
        else:
            color = 'green'
            status = 'ACTIVE'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, status
        )
    status_display.short_description = 'Status'
    
    def block_accounts(self, request, queryset):
        """Admin action to block accounts."""
        count = queryset.update(is_blocked=True)
        self.message_user(request, f'{count} account(s) blocked.')
    block_accounts.short_description = "Block selected accounts"
    
    def unblock_accounts(self, request, queryset):
        """Admin action to unblock accounts."""
        count = queryset.update(is_blocked=False, block_reason='')
        self.message_user(request, f'{count} account(s) unblocked.')
    unblock_accounts.short_description = "Unblock selected accounts"
    
    def mark_inactive(self, request, queryset):
        """Admin action to mark as inactive."""
        count = queryset.update(is_active=False)
        self.message_user(request, f'{count} account(s) marked inactive.')
    mark_inactive.short_description = "Mark selected as inactive"


class InvoiceLineInline(admin.TabularInline):
    """Inline admin for invoice lines."""
    model = InvoiceLine
    extra = 0
    fields = ['line_number', 'description', 'quantity', 'unit_price', 'line_total']
    readonly_fields = ['line_total']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Admin interface for Invoice model."""
    
    list_display = [
        'invoice_number', 'debtor', 'invoice_date', 'total_amount',
        'status_display', 'is_posted'
    ]
    list_filter = ['status', 'is_posted', 'invoice_date', 'sales_area']
    search_fields = ['invoice_number', 'debtor__name', 'order_number']
    readonly_fields = [
        'subtotal', 'vat_amount', 'total_amount', 'gross_profit',
        'created_at', 'updated_at', 'amount_paid', 'paid_date'
    ]
    inlines = [InvoiceLineInline]
    
    fieldsets = (
        ('Invoice Header', {
            'fields': ('invoice_number', 'debtor', 'invoice_date', 'sales_area')
        }),
        ('Delivery Information', {
            'fields': (
                'delivery_name', 'delivery_address_line1',
                'delivery_address_line2', 'delivery_telephone'
            ),
            'classes': ('collapse',)
        }),
        ('References', {
            'fields': ('order_number', 'customer_reference', 'job_card_number')
        }),
        ('Financial Details', {
            'fields': (
                'subtotal', 'discount_amount', 'vat_amount', 'total_amount',
                'total_cost', 'gross_profit'
            )
        }),
        ('Payment', {
            'fields': ('amount_paid', 'paid_date')
        }),
        ('Status', {
            'fields': ('status', 'is_posted', 'is_cancelled')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display color-coded status."""
        colors = {
            'DRAFT': 'blue',
            'POSTED': 'orange',
            'PAID': 'green',
            'PARTIAL_PAID': 'yellow',
            'OVERDUE': 'red',
            'CANCELLED': 'gray'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.status
        )
    status_display.short_description = 'Status'


@admin.register(DebtorTransaction)
class DebtorTransactionAdmin(admin.ModelAdmin):
    """Admin interface for DebtorTransaction model."""
    
    list_display = [
        'transaction_number', 'debtor', 'transaction_type',
        'transaction_date', 'total_amount', 'is_allocated'
    ]
    list_filter = [
        'transaction_type', 'transaction_date', 'is_allocated'
    ]
    search_fields = [
        'transaction_number', 'debtor__name', 'reference'
    ]
    readonly_fields = [
        'debtor', 'transaction_type', 'transaction_number',
        'transaction_date', 'amount', 'vat_amount', 'total_amount',
        'created_at', 'updated_at'
    ]
    
    def has_add_permission(self, request):
        """Prevent manual creation - transactions created through services."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - transactions are immutable."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow viewing but not editing."""
        return request.method in ['GET', 'HEAD', 'OPTIONS']


@admin.register(PostDatedCheque)
class PostDatedChequeAdmin(admin.ModelAdmin):
    """Admin interface for PostDatedCheque model."""
    
    list_display = [
        'debtor', 'cheque_date', 'amount', 'is_processed', 'processed_date'
    ]
    list_filter = ['is_processed', 'cheque_date']
    search_fields = ['debtor__name', 'reference']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Cheque Details', {
            'fields': ('debtor', 'cheque_date', 'amount', 'reference')
        }),
        ('Processing', {
            'fields': ('is_processed', 'processed_date')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model - read-only."""
    
    list_display = [
        'debtor', 'change_type', 'changed_by', 'created_at'
    ]
    list_filter = ['change_type', 'created_at']
    search_fields = ['debtor__name', 'changed_by', 'description']
    readonly_fields = [
        'debtor', 'change_type', 'old_value', 'new_value',
        'changed_by', 'description', 'created_at', 'updated_at'
    ]
    
    def has_add_permission(self, request):
        """Prevent manual creation - created by system."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Read-only."""
        return True
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion - audit trail."""
        return False
