"""
Shared business logic for Purchase Orders utilities.

Kept separate from views.py/management commands so the same recompute logic
can run from both the API (resync_on_order_quantities action, tenant-scoped
via the request's DB routing) and the resync_po_quantities CLI command
(explicit tenant/shop selection via --tenant/--shop, using self.db_alias).
"""

from apps.stock_control.models import StockItem
from django.db.models import Sum

from .models import PurchaseOrderLine


def resync_stock_on_order(db_alias=None):
    """
    Recompute StockItem.quantity_on_order from the sum of quantity_outstanding
    across all non-cancelled Purchase Order lines for each stock item.

    quantity_on_order is normally maintained incrementally (+= on PO create,
    -= on cancel/receive/back-order), so it can drift from reality after bugs,
    manual DB edits, or partial failures. This recomputes it from scratch.
    """
    po_lines = PurchaseOrderLine.objects
    stock_items = StockItem.objects
    if db_alias:
        po_lines = po_lines.using(db_alias)
        stock_items = stock_items.using(db_alias)

    outstanding_by_item = dict(
        po_lines.exclude(purchase_order__status="C")
        .exclude(stock_item__isnull=True)
        .values("stock_item")
        .annotate(total_outstanding=Sum("quantity_outstanding"))
        .values_list("stock_item", "total_outstanding")
    )

    changes = []
    for stock_item in stock_items.all():
        correct_qty = outstanding_by_item.get(stock_item.pk) or 0
        if stock_item.quantity_on_order != correct_qty:
            changes.append(
                {
                    "stock_code": stock_item.stock_code,
                    "previous_quantity_on_order": float(stock_item.quantity_on_order),
                    "corrected_quantity_on_order": float(correct_qty),
                }
            )
            stock_item.quantity_on_order = correct_qty
            stock_item.save(update_fields=["quantity_on_order"])

    return {"items_updated": len(changes), "changes": changes}
