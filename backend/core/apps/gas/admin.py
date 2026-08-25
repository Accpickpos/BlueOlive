from django.contrib import admin

from .models import RentalSettings, RentalTransaction


@admin.register(RentalSettings)
class RentalSettingsAdmin(admin.ModelAdmin):
    list_display = ('overdue_threshold_days', 'deposits_held_accno', 'cash_accno')


@admin.register(RentalTransaction)
class RentalTransactionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'debtor', 'stock_item', 'quantity', 'deposit_amount',
        'status', 'checkout_date', 'due_date', 'reconciliation_state', 'is_overdue',
    )
    list_filter = ('status', 'reconciliation_state')
    search_fields = ('debtor__dname', 'stock_item__description')
    readonly_fields = ('gl_batchno_checkout', 'gl_batchno_return')
