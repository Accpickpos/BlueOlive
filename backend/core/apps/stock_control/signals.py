from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
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


@receiver(post_save, sender=PackBundleIngredient)
def update_pack_bundle_cost(sender, instance, **kwargs):
    """Update pack/bundle total cost when ingredients change"""
    instance.pack_bundle.calculate_total_cost()


@receiver(post_save, sender=StockTransaction)
def update_stock_item_dates(sender, instance, created, **kwargs):
    """Update last purchased/sold dates on stock item"""
    if not created:
        return
    
    stock_item = instance.stock_item
    
    # Update last purchased date for incoming transactions
    if instance.transaction_type in ['INCOMING', 'MANUFACTURE']:
        if not stock_item.date_last_purchased or instance.transaction_date.date() > stock_item.date_last_purchased:
            stock_item.date_last_purchased = instance.transaction_date.date()
            stock_item.save(update_fields=['date_last_purchased'])
    
    # Update last sold date for sales transactions
    if instance.transaction_type in ['SALE']:
        if not stock_item.date_last_sold or instance.transaction_date.date() > stock_item.date_last_sold:
            stock_item.date_last_sold = instance.transaction_date.date()
            stock_item.save(update_fields=['date_last_sold'])


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
