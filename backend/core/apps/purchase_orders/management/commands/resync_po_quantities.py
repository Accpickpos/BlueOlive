"""
Reset Purchase Order Quantities utility (manual §6, Utilities: "Reset
Purchase Order Quantities" — "resyncs 'quantity on order' values in the
Stock Master against the actual outstanding Purchase Orders").

StockItem.quantity_on_order is maintained incrementally (+= on PO create,
-= on cancel/receive/back-order — see purchase_orders/views.py and
PurchaseOrder.cancel()) rather than derived, so it can drift from reality
after bugs, manual DB edits, or partial failures. This command recomputes
it from scratch as the sum of quantity_outstanding across all non-cancelled
PO lines for each stock item, matching the legacy utility's purpose.
"""
from django.db.models import Sum

from apps.purchase_orders.models import PurchaseOrderLine
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.stock_control.models import StockItem


class Command(TenantAwareLegacyImportCommand):
    help = "Resync StockItem.quantity_on_order against actual outstanding Purchase Order lines"

    def run(self, **options):
        outstanding_by_item = dict(
            PurchaseOrderLine.objects
            .using(self.db_alias)
            .exclude(purchase_order__status='C')
            .exclude(stock_item__isnull=True)
            .values('stock_item')
            .annotate(total_outstanding=Sum('quantity_outstanding'))
            .values_list('stock_item', 'total_outstanding')
        )

        stock_items = StockItem.objects.using(self.db_alias).all()
        for stock_item in stock_items:
            correct_qty = outstanding_by_item.get(stock_item.pk) or 0
            if stock_item.quantity_on_order != correct_qty:
                self.stdout.write(
                    f"  {stock_item.stock_code}: {stock_item.quantity_on_order} -> {correct_qty}"
                )
                stock_item.quantity_on_order = correct_qty
                stock_item.save(update_fields=['quantity_on_order'])
                self.updated += 1
