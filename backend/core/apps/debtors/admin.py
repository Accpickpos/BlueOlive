"""
Django admin configuration for debtors app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Debtor, DebtorTransaction, Debtopen, Dpdc, DebtorAudit, Darea


@admin.register(Debtor)
class DebtorAdmin(admin.ModelAdmin):
    """Admin interface for Debtor model (DMAST table)."""
    
    list_display = [
        'customer_number', 'name', 'balance_current', 
        'credit_limit', 'is_active'
    ]
    list_filter = [
        'block_flag', 'interest_flag', 'account_type', 'is_active', 'created_at'
    ]
    search_fields = ['customer_number', 'name', 'short_name', 'phone', 'email']
    readonly_fields = [
        'balance_current', 'balance_30_days', 'balance_60_days', 
        'balance_90_days', 'balance_120_days', 'balance_150_days', 
        'balance_180_days', 'last_payment_date', 'last_payment_amount',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Account Identification', {
            'fields': ('customer_number', 'name', 'short_name', 'contact_person', 'email')
        }),
        ('Contact Details', {
            'fields': ('phone', 'phone2', 'fax')
        }),
        ('Postal Address', {
            'fields': ('address_line1', 'address_line2', 'address_line3', 'postal_code'),
            'classes': ('collapse',)
        }),
        ('Business Details', {
            'fields': ('area_code', 'account_type', 'price_level', 'payment_terms')
        }),
        ('Discount & Credit', {
            'fields': (
                'discount_percentage', 'prompt_payment_discount',
                'credit_limit'
            )
        }),
        ('Account Control Flags', {
            'fields': (
                'block_flag', 'interest_flag', 'positive_balance_only'
            )
        }),
        ('Balance & Aging', {
            'fields': (
                'balance_current', 'balance_30_days', 'balance_60_days', 
                'balance_90_days', 'balance_120_days', 'balance_150_days', 
                'balance_180_days'
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'sales_month', 'sales_year', 
                'profit_month', 'profit_year',
                'last_payment_date', 'last_payment_amount'
            ),
            'classes': ('collapse',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['block_accounts', 'unblock_accounts']
    
    def status_display(self, obj):
        """Display color-coded block status."""
        if obj.is_blocked():
            color = 'red'
            status = 'BLOCKED'
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
        count = 0
        for debtor in queryset:
            debtor.set_blocked(True)
            count += 1
        self.message_user(request, f'{count} account(s) blocked.')
    block_accounts.short_description = "Block selected accounts"
    
    def unblock_accounts(self, request, queryset):
        """Admin action to unblock accounts."""
        count = 0
        for debtor in queryset:
            debtor.set_blocked(False)
            count += 1
        self.message_user(request, f'{count} account(s) unblocked.')
    unblock_accounts.short_description = "Unblock selected accounts"


@admin.register(DebtorTransaction)
class DebtorTransactionAdmin(admin.ModelAdmin):
    """Admin interface for DebtorTransaction (DEBTRAN table)."""
    
    list_display = ['debtor', 'transaction_number', 'transaction_type', 'transaction_date', 'total_amount', 'created_at']
    list_filter = ['transaction_type', 'transaction_date', 'vat_status', 'status', 'is_allocated', 'created_at']
    search_fields = ['transaction_number', 'debtor__name', 'order_number']
    readonly_fields = ['debtor', 'transaction_date', 'total_amount', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Header', {
            'fields': ('debtor', 'transaction_number', 'transaction_type', 'transaction_date', 'transaction_time')
        }),
        ('Financial Details', {
            'fields': ('subtotal', 'vat_amount', 'total_amount', 'vat_status')
        }),
        ('References', {
            'fields': ('source_type', 'source_reference', 'order_number', 'customer_reference'),
            'classes': ('collapse',)
        }),
        ('Delivery Information', {
            'fields': ('description_line1', 'description_line2', 'description_line3', 'description_line4'),
            'classes': ('collapse',)
        }),
        ('Status & Metadata', {
            'fields': ('status', 'is_allocated', 'created_by')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Debtopen)
class DebtOpenAdmin(admin.ModelAdmin):
    """Admin interface for Debtopen (DEBTOPEN table - Open Item Accounting)."""
    
    list_display = ['dno', 'dtrano', 'type', 'date', 'total', 'balancedue', 'ageflag']
    list_filter = ['type', 'date', 'ageflag', 'posted']
    search_fields = ['dtrano', 'dno__dname']
    readonly_fields = ['dno', 'date', 'total', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Open Item Details', {
            'fields': ('dno', 'dtrano', 'type', 'date')
        }),
        ('Amounts', {
            'fields': ('total', 'balancedue', 'ageflag')
        }),
        ('Status', {
            'fields': ('posted',)
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Dpdc)
class DpdcAdmin(admin.ModelAdmin):
    """Admin interface for Dpdc (DPDC table - Post Dated Cheques)."""
    
    list_display = ['dno', 'date', 'amount', 'status_display', 'created_at']
    list_filter = ['status', 'date', 'created_at']
    search_fields = ['dno__dname']
    readonly_fields = ['dno', 'date', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Cheque Details', {
            'fields': ('dno', 'date', 'amount', 'status')
        }),
        ('Audit', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display color-coded status."""
        colors = {'A': 'blue', 'I': 'orange', 'P': 'green', 'C': 'red'}
        status_text = {'A': 'Active', 'I': 'Inactive', 'P': 'Processed', 'C': 'Cancelled'}
        color = colors.get(obj.status, 'black')
        text = status_text.get(obj.status, obj.status)
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, text
        )
    status_display.short_description = 'Status'


@admin.register(DebtorAudit)
class DebtorAuditAdmin(admin.ModelAdmin):
    """Admin interface for DebtorAudit (DEBTORAUD table)."""
    
    list_display = ['dno', 'dtrano', 'type', 'date', 'amount']
    list_filter = ['type', 'date']
    search_fields = ['dtrano', 'dno__dname']
    readonly_fields = ['dno', 'dtrano', 'type', 'thistype', 'thistran', 'date', 'amount']
    
    fieldsets = (
        ('Audit Record', {
            'fields': ('dno', 'dtrano', 'type', 'date', 'amount')
        }),
        ('Details', {
            'fields': ('thistype', 'thistran'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Darea)
class DareaAdmin(admin.ModelAdmin):
    """Admin interface for Darea (DAREA table - Sales Areas)."""
    
    list_display = ['darea', 'dareaname', 'get_total_sales_display']
    search_fields = ['darea', 'dareaname']
    readonly_fields = ['get_total_sales_display']
    
    fieldsets = (
        ('Area Information', {
            'fields': ('darea', 'dareaname')
        }),
        ('Monthly Sales', {
            'fields': ('arsls1', 'arsls2', 'arsls3', 'arsls4', 'arsls5', 'arsls6',
                      'arsls7', 'arsls8', 'arsls9', 'arsls10', 'arsls11', 'arsls12',
                      'get_total_sales_display'),
            'classes': ('collapse',)
        }),
    )
    
    def get_total_sales_display(self, obj):
        """Display total sales."""
        return f"{obj.get_total_sales():.2f}"
    get_total_sales_display.short_description = 'Total Sales'



