from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from decimal import Decimal
from .models import (
    CreditorTransaction, OpenItemAllocation, RFC, RFCLineItem
)
from apps.settings.models import TaxCode


@receiver(post_save, sender=CreditorTransaction)
def update_supplier_balances(sender, instance, created, **kwargs):
    """Update supplier balances when transaction is created"""
    if not created:
        return
    
    supplier = instance.supplier
    amount = instance.amount_inclusive
    
    # Update last paid info for payments
    if instance.transaction_type == 'PAYMENT':
        supplier.amount_last_paid = amount
        supplier.date_last_paid = instance.transaction_date
    
    # Update balance brought forward balances
    if supplier.account_type == '':
        if instance.transaction_type in ['INVOICE_STOCK', 'INVOICE_EXPENSE', 'DEBIT_JOURNAL']:
            # Increase balance
            supplier.balance_current += instance.age_current
            supplier.balance_30_days += instance.age_30
            supplier.balance_60_days += instance.age_60
            supplier.balance_90_days += instance.age_90
            supplier.balance_120_days += instance.age_120
            supplier.balance_150_days += instance.age_150
            supplier.balance_180_days += instance.age_180
        
        elif instance.transaction_type in ['CREDIT_STOCK', 'CREDIT_EXPENSE', 'PAYMENT', 'CREDIT_JOURNAL']:
            # Decrease balance
            supplier.balance_current -= instance.age_current
            supplier.balance_30_days -= instance.age_30
            supplier.balance_60_days -= instance.age_60
            supplier.balance_90_days -= instance.age_90
            supplier.balance_120_days -= instance.age_120
            supplier.balance_150_days -= instance.age_150
            supplier.balance_180_days -= instance.age_180
    
    supplier.save()


@receiver(post_save, sender=OpenItemAllocation)
def update_open_item_balances(sender, instance, created, **kwargs):
    """Update open item transaction balances when allocation is made"""
    if not created:
        return
    
    invoice = instance.invoice_transaction
    
    # Reduce balance due
    invoice.balance_due -= instance.amount_allocated
    
    # Mark as fully allocated if balance is zero
    if invoice.balance_due <= 0:
        invoice.is_allocated = True
        invoice.balance_due = 0
    
    invoice.save()


@receiver(post_save, sender=RFCLineItem)
def update_rfc_totals(sender, instance, created, **kwargs):
    """Update RFC totals when line items are added/updated"""
    instance.rfc.calculate_totals()


@receiver(pre_save, sender=RFCLineItem)
def calculate_rfc_line_totals(sender, instance, **kwargs):
    """Calculate line item totals before saving"""
    # Calculate amounts
    instance.amount_exclusive = instance.quantity * instance.unit_cost_exclusive
    
    # Get tax rate from tax code
    if instance.tax_code:
        instance.tax_amount = instance.amount_exclusive * (instance.tax_code.rate / 100)
    else:
        # Get default tax code if not provided
        default_tax = TaxCode.objects.filter(is_default=True, is_active=True).first()
        if default_tax:
            instance.tax_code = default_tax
            instance.tax_amount = instance.amount_exclusive * (default_tax.rate / 100)
        else:
            instance.tax_amount = Decimal('0')
    
    instance.amount_inclusive = instance.amount_exclusive + instance.tax_amount


@receiver(pre_save, sender=CreditorTransaction)
def set_transaction_number(sender, instance, **kwargs):
    """Auto-generate transaction numbers if not provided"""
    if not instance.transaction_number and instance.pk is None:
        # Generate transaction number based on type
        from django.utils import timezone
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        
        type_prefix = {
            'INVOICE_STOCK': 'INV',
            'INVOICE_EXPENSE': 'EXP',
            'CREDIT_STOCK': 'CR',
            'CREDIT_EXPENSE': 'CRE',
            'PAYMENT': 'PAY',
            'DEBIT_JOURNAL': 'DJ',
            'CREDIT_JOURNAL': 'CJ',
        }.get(instance.transaction_type, 'TXN')
        
        instance.transaction_number = f"{type_prefix}-{timestamp}"