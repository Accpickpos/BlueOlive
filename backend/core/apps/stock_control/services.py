"""
Stock control services.
Business logic for stock transactions that move quantity_on_hand.

Mirrors apps/debtors/services.py's service-class + tenant-alias-aware
locking pattern. QOH mutation lives ONLY here, never in signals.py:
signals.py's post_save handler fires for every StockTransaction (including
ones StockTakeViewSet.update_stock creates and mutates QOH for directly),
so a generic signal-based mutation would double-apply. Callers (views,
future callers) invoke these functions explicitly instead.
"""

from decimal import Decimal

from django.db import transaction

from .models import PackBundle, StockItem, StockTransaction


class StockTransactionService:
    """Service class for stock-moving transactions."""

    @staticmethod
    def adjust_quantity_on_hand(stock_item, delta):
        """
        Lock and adjust a stock item's QOH by `delta` (signed). Must be
        called inside an already-open transaction.atomic(using=<item's own
        db alias>) block — select_for_update() requires an active
        transaction on the connection the row is routed to, which for a
        shop-app model like StockItem is the tenant's own DB alias, never
        "default" (tenant connections run in true driver-level autocommit).

        Uses plain Python arithmetic on the locked row's already-fetched
        value rather than an F() expression: StockItem's pre_save signal
        (validate_qty_allocation) reads instance.quantity_on_hand to
        compare against allocated/sale-order quantities, and an unresolved
        F()-expression there fails with a TypeError since it isn't a
        concrete Decimal yet. select_for_update() already makes the
        read-then-write safe under concurrency.
        """
        locked = StockItem.objects.select_for_update().get(pk=stock_item.pk)
        locked.quantity_on_hand = locked.quantity_on_hand + delta
        locked.save(update_fields=["quantity_on_hand"])
        stock_item.refresh_from_db(fields=["quantity_on_hand"])
        return stock_item

    @staticmethod
    def create_incoming_transaction(
        stock_item,
        quantity,
        unit_cost=0,
        supplier=None,
        comments="",
        transaction_date=None,
        created_by=None,
        **extra_fields,
    ):
        """Receive stock: creates an INCOMING transaction and increases QOH."""
        quantity = Decimal(str(quantity))
        if quantity <= 0:
            raise ValueError("quantity must be positive.")

        alias = stock_item._state.db or "default"
        with transaction.atomic(using=alias):
            tx = StockTransaction.objects.create(
                transaction_type="INCOMING",
                stock_item=stock_item,
                quantity_in=quantity,
                unit_cost=unit_cost,
                supplier=supplier,
                comments=comments,
                created_by=created_by,
                **({"transaction_date": transaction_date} if transaction_date else {}),
                **extra_fields,
            )
            StockTransactionService.adjust_quantity_on_hand(stock_item, quantity)
        return tx

    @staticmethod
    def create_return_transaction(
        stock_item,
        quantity,
        unit_cost=0,
        supplier=None,
        comments="",
        transaction_date=None,
        created_by=None,
        **extra_fields,
    ):
        """Return stock to a supplier: creates a RETURN transaction and decreases QOH."""
        quantity = Decimal(str(quantity))
        if quantity <= 0:
            raise ValueError("quantity must be positive.")

        alias = stock_item._state.db or "default"
        with transaction.atomic(using=alias):
            tx = StockTransaction.objects.create(
                transaction_type="RETURN",
                stock_item=stock_item,
                quantity_out=quantity,
                unit_cost=unit_cost,
                supplier=supplier,
                comments=comments,
                created_by=created_by,
                **({"transaction_date": transaction_date} if transaction_date else {}),
                **extra_fields,
            )
            StockTransactionService.adjust_quantity_on_hand(stock_item, -quantity)
        return tx

    @staticmethod
    def create_manufacture_transaction(
        bundle_stock_item,
        quantity,
        unit_cost=None,
        comments="",
        transaction_date=None,
        created_by=None,
        **extra_fields,
    ):
        """
        Manufacture a pack/bundle: creates a MANUFACTURE transaction that
        increases QOH on the finished bundle item, then a BUNDLE_USE
        transaction per BOM ingredient that decreases QOH on each
        ingredient by (ingredient.quantity * quantity manufactured). All in
        one atomic block. Returns the MANUFACTURE transaction; ingredient
        BUNDLE_USE transactions are a side effect (not returned — callers
        that need them can query StockTransaction with
        transaction_type='BUNDLE_USE' and a matching transaction_date).
        """
        quantity = Decimal(str(quantity))
        if quantity <= 0:
            raise ValueError("quantity must be positive.")

        try:
            bundle = bundle_stock_item.pack_bundle
        except PackBundle.DoesNotExist:
            raise ValueError(
                f"{bundle_stock_item.stock_code} is not a pack/bundle item."
            )

        if unit_cost is None:
            unit_cost = bundle.total_cost

        alias = bundle_stock_item._state.db or "default"
        with transaction.atomic(using=alias):
            tx = StockTransaction.objects.create(
                transaction_type="MANUFACTURE",
                stock_item=bundle_stock_item,
                quantity_in=quantity,
                unit_cost=unit_cost,
                comments=comments,
                created_by=created_by,
                **({"transaction_date": transaction_date} if transaction_date else {}),
                **extra_fields,
            )
            StockTransactionService.adjust_quantity_on_hand(bundle_stock_item, quantity)

            for ingredient in bundle.ingredients.select_related("ingredient_stock"):
                used_qty = ingredient.quantity * quantity
                StockTransaction.objects.create(
                    transaction_type="BUNDLE_USE",
                    stock_item=ingredient.ingredient_stock,
                    quantity_out=used_qty,
                    unit_cost=ingredient.ingredient_stock.cost_price,
                    comments=f"Used in {bundle_stock_item.stock_code} manufacture"[:30],
                    created_by=created_by,
                    **(
                        {"transaction_date": transaction_date}
                        if transaction_date
                        else {}
                    ),
                )
                StockTransactionService.adjust_quantity_on_hand(
                    ingredient.ingredient_stock, -used_qty
                )
        return tx
