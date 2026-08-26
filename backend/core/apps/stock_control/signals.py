import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    FuturePricing,
    PackBundleIngredient,
    SpecialDeal,
    StockItem,
    StockTransaction,
)

MARKUP_FIELD_LIMIT = Decimal(
    "9999.99"
)  # markup_1/2/3 are DecimalField(max_digits=6, decimal_places=2)


@receiver(pre_save, sender=StockItem)
def calculate_stock_item_markups(sender, instance, **kwargs):
    """
    Auto-calculate markup percentages when prices change. Clamped to the
    field's precision — a nominal cost_price (e.g. labour/service items
    costed at R1) against a much higher selling price would otherwise
    produce a markup in the tens of thousands of percent and overflow the
    DecimalField at save time.
    """
    if instance.cost_price > 0:
        for level in [1, 2, 3]:
            selling_price = getattr(instance, f"selling_price_{level}")
            if selling_price > 0:
                markup = (
                    (selling_price - instance.cost_price) / instance.cost_price
                ) * 100
                markup = max(-MARKUP_FIELD_LIMIT, min(MARKUP_FIELD_LIMIT, markup))
                setattr(instance, f"markup_{level}", markup)


@receiver(pre_save, sender=StockItem)
def validate_qty_allocation(sender, instance, **kwargs):
    """Validate that allocated + sale_order don't exceed QOH"""
    total_allocated = instance.quantity_allocated + instance.quantity_sale_order

    if total_allocated > instance.quantity_on_hand:
        raise ValidationError(
            f"Allocated quantity ({instance.quantity_allocated}) + "
            f"Sale Order quantity ({instance.quantity_sale_order}) "
            f"cannot exceed Quantity on Hand ({instance.quantity_on_hand})"
        )


@receiver(post_save, sender=PackBundleIngredient)
def update_pack_bundle_cost(sender, instance, **kwargs):
    """Update pack/bundle total cost when ingredients change"""
    instance.pack_bundle.calculate_total_cost()


def _as_date(value):
    """
    Safely coerce a value to datetime.date regardless of whether it is
    already a date, a datetime, or an ISO-format string.
    """
    if value is None:
        return None
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, datetime.date):
        return value  # already a date — do NOT call .date() again
    if isinstance(value, str):
        return datetime.date.fromisoformat(value)
    return value


@receiver(post_save, sender=StockTransaction)
def update_stock_item_after_transaction(sender, instance, created, **kwargs):
    """Update stock item data after a new transaction is created."""
    if not created:
        return

    stock_item = instance.stock_item
    update_fields = []

    transaction_date = _as_date(instance.transaction_date)

    # ── Incoming / Manufacture ────────────────────────────────────────────────
    if instance.transaction_type in ["INCOMING", "MANUFACTURE"]:
        current = _as_date(stock_item.date_last_purchased)
        if transaction_date and (current is None or transaction_date > current):
            stock_item.date_last_purchased = transaction_date
            update_fields.append("date_last_purchased")

        if instance.supplier:
            stock_item.last_supplier = instance.supplier
            update_fields.append("last_supplier")

    # ── Sales ─────────────────────────────────────────────────────────────────
    if instance.transaction_type in ["SALE", "SALE_RETURN"]:
        current = _as_date(stock_item.date_last_sold)
        if transaction_date and (current is None or transaction_date > current):
            stock_item.date_last_sold = transaction_date
            update_fields.append("date_last_sold")

    # ── Average cost ──────────────────────────────────────────────────────────
    if instance.transaction_type == "INCOMING" and instance.quantity_in > 0:
        stock_item.update_average_cost(instance.quantity_in, instance.unit_cost)
        update_fields.append("average_cost")

    if update_fields:
        stock_item.save(update_fields=update_fields)
