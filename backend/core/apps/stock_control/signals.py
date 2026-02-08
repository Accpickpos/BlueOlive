from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import (
    StockItem, StockTransaction, PackBundleIngredient,
    SpecialDeal, FuturePricing
)


@receiver(pre_save, sender=StockItem)
def calculate_stock_item_markups(sender, instance, **kwargs):
    """Auto-calculate markup percentages when prices change"""
    if instance.cost_price > 0:
        # Calculate markup for each price level
        for level in [1, 2, 3]:
            selling_price = getattr(instance, f'selling_price_{level}')
            if selling_price > 0:
                markup = ((selling_price - instance.cost_price) / instance.cost_price) * 100
                setattr(instance, f'markup_{level}', markup)


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


@receiver(post_save, sender=StockTransaction)
def update_stock_item_after_transaction(sender, instance, created, **kwargs):
    """Update stock item data after transaction is created"""
    if not created:
        return
    
    stock_item = instance.stock_item
    
    # Update last purchased date for incoming transactions
    if instance.transaction_type in ['INCOMING', 'MANUFACTURE']:
        if not stock_item.date_last_purchased or instance.transaction_date.date() > stock_item.date_last_purchased:
            stock_item.date_last_purchased = instance.transaction_date.date()
        
        # Update last supplier for incoming
        if instance.supplier:
            stock_item.last_supplier = instance.supplier
    
    # Update last sold date for sales transactions
    if instance.transaction_type in ['SALE', 'SALE_RETURN']:
        if not stock_item.date_last_sold or instance.transaction_date.date() > stock_item.date_last_sold:
            stock_item.date_last_sold = instance.transaction_date.date()
    
    # Auto-update average cost for incoming stock
    if instance.transaction_type == 'INCOMING' and instance.quantity_in > 0:
        stock_item.update_average_cost(instance.quantity_in, instance.unit_cost)
    
    # Save only if there were updates
    if (instance.supplier or instance.transaction_type in ['SALE', 'SALE_RETURN']) and not instance._state.adding:
        stock_item.save(update_fields=['date_last_purchased', 'date_last_sold', 'last_supplier'])


@receiver(pre_save, sender=SpecialDeal)
def calculate_special_deal_markups(sender, instance, **kwargs):
    """Auto-calculate markup percentages for special deals"""
    if instance.special_cost_price > 0:
        for level in [1, 2, 3]:
            selling_price = getattr(instance, f'special_selling_price_{level}')
            if selling_price > 0:
                markup = ((selling_price - instance.special_cost_price) / instance.special_cost_price) * 100
                setattr(instance, f'special_markup_{level}', markup)


@receiver(pre_save, sender=FuturePricing)
def calculate_future_pricing_markups(sender, instance, **kwargs):
    """Auto-calculate markup percentages for future pricing"""
    if instance.future_cost_price > 0:
        for level in [1, 2, 3]:
            selling_price = getattr(instance, f'future_selling_price_{level}')
            if selling_price > 0:
                markup = ((selling_price - instance.future_cost_price) / instance.future_cost_price) * 100
                setattr(instance, f'future_markup_{level}', markup)

