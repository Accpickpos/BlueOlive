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

The recompute logic lives in services.resync_stock_on_order() so it can also
be run from the API (PurchaseOrderViewSet.resync_on_order_quantities), which
relies on the request's tenant-scoped DB routing instead of self.db_alias.
"""

from apps.purchase_orders.services import resync_stock_on_order
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand


class Command(TenantAwareLegacyImportCommand):
    help = "Resync StockItem.quantity_on_order against actual outstanding Purchase Order lines"

    def run(self, **options):
        result = resync_stock_on_order(db_alias=self.db_alias)
        for change in result["changes"]:
            self.stdout.write(
                f"  {change['stock_code']}: "
                f"{change['previous_quantity_on_order']} -> "
                f"{change['corrected_quantity_on_order']}"
            )
        self.updated += result["items_updated"]
