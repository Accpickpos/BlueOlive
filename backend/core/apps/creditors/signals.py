"""
Enterprise-grade signals for Creditors module
Handles balance updates, validations, audit trails, and business logic
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Sum, F, DecimalField
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    Creditor, CreditorInvoice, CreditorPayment, CreditorJournal,
    CreditorOpenItem, OpenItemAllocation, RFC, RFCLineItem,
    OpenItemAudit, GRNLineItem
)
from apps.settings.models import TaxCode


# ============================================================================
# CREDITOR SIGNALS
# ============================================================================

@receiver(pre_save, sender=Creditor)
def validate_creditor(sender, instance, **kwargs):
    """Validate creditor data before saving"""
    # Validate balance brought forward is not negative without reason
    if instance.balance_brought_forward and instance.balance_brought_forward < 0:
        # Log warning but allow negative balances for legacy data
        pass


@receiver(post_save, sender=Creditor)
def creditor_post_save(sender, instance, created, **kwargs):
    """Handle creditor post-save logic"""
    if created:
        # Initialize aged balances if bringing forward balance
        if instance.balance_brought_forward and instance.balance_brought_forward > 0:
            instance.balance_current = instance.balance_brought_forward
            instance.save(update_fields=['balance_current'])


# ============================================================================
# GOODS RECEIVED NOTE SIGNALS
# ============================================================================

@receiver(post_save, sender=GRNLineItem)
def grn_lineitem_post_save(sender, instance, created, **kwargs):
    """Update GRN totals when line items are added/updated"""
    grn = instance.grn
    
    # Recalculate GRN totals
    from django.db.models import Sum, F
    from django.db.models.functions import Coalesce
    
    totals = GRNLineItem.objects.filter(grn=grn).aggregate(
        subtotal=Sum(F('quantity_received') * F('unit_cost'), output_field=DecimalField()),
        total_tax=Sum('tax_amount')
    )
    
    grn.subtotal = totals['subtotal'] or Decimal('0')
    grn.total_vat = totals['total_tax'] or Decimal('0')
    grn.total_amount = grn.subtotal + grn.total_vat
    grn.save(update_fields=['subtotal', 'total_vat', 'total_amount'])


# ============================================================================
# CREDITOR INVOICE SIGNALS
# ============================================================================

@receiver(pre_save, sender=CreditorInvoice)
def creditor_invoice_pre_save(sender, instance, **kwargs):
    """Validate and prepare creditor invoice before saving"""
    # Calculate due date based on credit terms
    if not instance.due_date and instance.creditor and instance.creditor.credit_terms:
        credit_days = instance.creditor.credit_terms.credit_days or 30
        instance.due_date = instance.transaction_date + timedelta(days=credit_days)
    
    # Validate due_date >= transaction_date
    if instance.due_date and instance.due_date < instance.transaction_date:
        instance.due_date = instance.transaction_date


@receiver(post_save, sender=CreditorInvoice)
def creditor_invoice_post_save(sender, instance, created, **kwargs):
    """Handle creditor invoice post-save logic"""
    if created:
        # Create open item for tracking
        creditor = instance.creditor
        
        CreditorOpenItem.objects.create(
            creditor=creditor,
            transaction_type='INVOICE',
            transaction_number=instance.transaction_number,
            transaction_date=instance.transaction_date,
            due_date=instance.due_date,
            original_amount=instance.total_amount,
            balance_due=instance.total_amount
        )


# ============================================================================
# CREDITOR PAYMENT SIGNALS
# ============================================================================

@receiver(post_save, sender=CreditorPayment)
def creditor_payment_post_save(sender, instance, created, **kwargs):
    """Handle creditor payment post-save logic"""
    if created:
        creditor = instance.creditor
        
        # Update last payment info
        creditor.last_paid_amount = instance.amount_paid
        creditor.last_paid_date = instance.transaction_date
        
        # Update purchases tracking if needed
        if instance.transaction_date.month == datetime.now().month:
            # Update MTD
            if not hasattr(creditor, 'purchases_mtd'):
                creditor.purchases_mtd = Decimal('0')
        
        creditor.save(update_fields=['last_paid_amount', 'last_paid_date'])
        
        # Create open item payment record
        CreditorOpenItem.objects.create(
            creditor=creditor,
            transaction_type='PAYMENT',
            transaction_number=instance.transaction_number,
            transaction_date=instance.transaction_date,
            original_amount=instance.amount_paid * Decimal('-1'),
            balance_due=instance.amount_paid * Decimal('-1'),
            is_fully_allocated=False
        )


# ============================================================================
# OPEN ITEM ALLOCATION SIGNALS
# ============================================================================

@receiver(post_save, sender=OpenItemAllocation)
def open_item_allocation_post_save(sender, instance, created, **kwargs):
    """Handle open item allocation post-save logic"""
    if not created:
        return
    
    open_item = instance.open_item
    
    # Update balance due
    open_item.balance_due -= instance.amount_paid
    
    # Mark as fully allocated if balance reaches zero
    if open_item.balance_due <= Decimal('0'):
        open_item.is_fully_allocated = True
        open_item.balance_due = Decimal('0')
    
    open_item.save(update_fields=['balance_due', 'is_fully_allocated'])
    
    # Create audit record
    OpenItemAudit.objects.create(
        creditor=open_item.creditor,
        transaction_type=open_item.transaction_type,
        transaction_number=open_item.transaction_number,
        transaction_date=open_item.transaction_date,
        original_amount=open_item.original_amount,
        balance_due=open_item.balance_due,
        this_transaction_type='ALLOCATION',
        amount_this_transaction=instance.amount_paid,
        action='Payment allocation',
        audit_timestamp=datetime.now()
    )
    
    # Recalculate aged balances for creditor
    instance.payment.creditor.recalculate_aged_balances()


# ============================================================================
# CREDITOR JOURNAL SIGNALS
# ============================================================================

@receiver(post_save, sender=CreditorJournal)
def creditor_journal_post_save(sender, instance, created, **kwargs):
    """Handle creditor journal post-save logic"""
    if not created:
        return
    
    creditor = instance.creditor
    
    # Create open item for journal
    is_debit = instance.journal_type == 'DEBIT'
    
    CreditorOpenItem.objects.create(
        creditor=creditor,
        transaction_type='JOURNAL',
        transaction_number=instance.transaction_number,
        transaction_date=instance.transaction_date,
        original_amount=instance.journal_amount,
        balance_due=instance.journal_amount if is_debit else instance.journal_amount * Decimal('-1')
    )


# ============================================================================
# RFC SIGNALS
# ============================================================================

@receiver(post_save, sender=RFCLineItem)
def rfc_lineitem_post_save(sender, instance, created, **kwargs):
    """Update RFC totals when line items change"""
    rfc = instance.rfc
    
    # Recalculate RFC totals
    from django.db.models import Sum, F, DecimalField
    
    totals = RFCLineItem.objects.filter(rfc=rfc).aggregate(
        subtotal=Sum(
            F('quantity_returned') * F('unit_cost'),
            output_field=DecimalField()
        ),
        total_tax=Sum('tax_amount')
    )
    
    rfc.total_value_exclusive = totals['subtotal'] or Decimal('0')
    rfc.total_vat = totals['total_tax'] or Decimal('0')
    rfc.total_value_inclusive = rfc.total_value_exclusive + rfc.total_vat
    rfc.save(update_fields=['total_value_exclusive', 'total_vat', 'total_value_inclusive'])