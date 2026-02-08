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
        'dno', 'dname', 'status_display', 'dcrnt', 'dclimit',
        'ddatlpd', 'blockflag'
    ]
    list_filter = [
        'blockflag', 'dintflag', 'acctype', 'darea', 'created_at'
    ]
    search_fields = ['dno', 'dname', 'dsname', 'dtel', 'dtaxno']
    readonly_fields = [
        'dcrnt', 'd30', 'd60', 'd90', 'd120', 'd150', 'd180',
        'dsalesm', 'dsalesy', 'dprofitm', 'dprofity',
        'ddatlpd', 'damtlpd', 'created_at', 'updated_at',
        'get_total_balance', 'get_overdue_balance'
    ]
    
    fieldsets = (
        ('Account Identification', {
            'fields': ('dno', 'dname', 'dsname', 'dcontact', 'dtaxno')
        }),
        ('Contact Details', {
            'fields': ('dtel', 'dfax')
        }),
        ('Postal Address', {
            'fields': ('dadd1', 'dadd2', 'dadd3', 'dadd4', 'dpcode'),
            'classes': ('collapse',)
        }),
        ('Delivery Address', {
            'fields': ('delad1', 'delad2', 'delad3', 'delad4'),
            'classes': ('collapse',)
        }),
        ('Business Details', {
            'fields': ('darea', 'acctype', 'price', 'terms')
        }),
        ('Discount & Credit', {
            'fields': (
                'ddiscper', 'pdisc', 'discprn',
                'dclimit'
            )
        }),
        ('Account Control Flags', {
            'fields': (
                'blockflag', 'dintflag', 'dposbal'
            )
        }),
        ('Balance & Aging', {
            'fields': (
                'dcrnt', 'd30', 'd60', 'd90', 'd120', 'd150', 'd180',
                'get_total_balance', 'get_overdue_balance'
            ),
            'classes': ('collapse',)
        }),
        ('Statistics', {
            'fields': (
                'dsalesm', 'dsalesy', 'dprofitm', 'dprofity',
                'ddatlpd', 'damtlpd'
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
        if obj.blockflag == 'Y':
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
    
    list_display = ['dno', 'dtrano', 'dtype', 'dtdate', 'dttot', 'created_at']
    list_filter = ['dtype', 'dtdate', 'dtaxstat', 'created_at']
    search_fields = ['dtrano', 'dno__dname', 'ordno']
    readonly_fields = ['dno', 'dtdate', 'dttot', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Header', {
            'fields': ('dno', 'dtrano', 'dtype', 'dtdate')
        }),
        ('Financial Details', {
            'fields': ('dtsub', 'dtgst', 'dttot', 'dtaxstat')
        }),
        ('References', {
            'fields': ('source', 'ordno', 'custref'),
            'classes': ('collapse',)
        }),
        ('Delivery Information', {
            'fields': ('del1', 'del2', 'del3', 'del4'),
            'classes': ('collapse',)
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



