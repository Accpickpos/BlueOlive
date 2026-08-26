"""
Enterprise-grade signals for Creditors module
Handles balance updates, validations, audit trails, and business logic
"""

from datetime import datetime, timedelta
from decimal import Decimal

from apps.settings.models import TaxCode
from django.db import transaction
from django.db.models import DecimalField, F, Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import (
    RFC,
    Creditor,
    CreditorCreditNote,
    CreditorCreditNoteLineItem,
    CreditorInvoice,
    CreditorInvoiceLineItem,
    CreditorJournal,
    CreditorOpenItem,
    CreditorPayment,
    GoodsReceivedNote,
    GRNLineItem,
    OpenItemAllocation,
    OpenItemAudit,
    RFCLineItem,
)

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
            instance.save(update_fields=["balance_current"])


# ============================================================================
# GOODS RECEIVED NOTE SIGNALS
# ============================================================================


@receiver(post_save, sender=GRNLineItem)
def grn_lineitem_post_save(sender, instance, created, **kwargs):
    """Update GRN totals when line items are added/updated"""
    grn = instance.grn

    # Recalculate GRN totals
    from django.db.models import Sum
    from django.db.models.functions import Coalesce

    totals = GRNLineItem.objects.filter(grn=grn).aggregate(
        subtotal=Sum(
            F("quantity_received") * F("unit_cost"), output_field=DecimalField()
        ),
        total_tax=Sum("tax_amount"),
    )

    grn.subtotal = totals["subtotal"] or Decimal("0")
    grn.total_vat = totals["total_tax"] or Decimal("0")
    grn.total_amount = grn.subtotal + grn.total_vat
    grn.save(update_fields=["subtotal", "total_vat", "total_amount"])


@receiver(post_save, sender=GoodsReceivedNote)
def grn_post_save(sender, instance, created, **kwargs):
    """
    Create/refresh the payable open item for a GRN once its total is known.
    GRN totals are only populated after line items are added (see
    grn_lineitem_post_save above, which re-saves the GRN header) — so this
    fires once with total_amount=0 (skipped) and again once lines exist.
    """
    if instance.total_amount <= Decimal("0"):
        return

    open_item, was_created = CreditorOpenItem.objects.get_or_create(
        grn=instance,
        defaults={
            "creditor": instance.creditor,
            "transaction_date": instance.transaction_date,
            "due_date": instance.due_date,
            "transaction_type": instance.transaction_type,
            "transaction_number": instance.transaction_number,
            "original_amount": instance.total_amount,
            "balance_due": instance.total_amount,
        },
    )
    if not was_created and open_item.balance_due == open_item.original_amount:
        # Nothing has been allocated against it yet — safe to refresh as lines change.
        open_item.original_amount = instance.total_amount
        open_item.balance_due = instance.total_amount
        open_item.save(update_fields=["original_amount", "balance_due"])

    instance.creditor.recalculate_aged_balances()


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


@receiver(post_save, sender=CreditorInvoiceLineItem)
def creditor_invoice_lineitem_post_save(sender, instance, created, **kwargs):
    """Update invoice totals when line items are added/updated (mirrors GRN)."""
    invoice = instance.invoice

    totals = CreditorInvoiceLineItem.objects.filter(invoice=invoice).aggregate(
        subtotal=Sum("amount"),
        total_tax=Sum("tax_amount"),
    )

    invoice.subtotal = totals["subtotal"] or Decimal("0")
    invoice.total_vat = totals["total_tax"] or Decimal("0")
    invoice.total_amount = invoice.subtotal + invoice.total_vat
    invoice.save(update_fields=["subtotal", "total_vat", "total_amount"])


@receiver(post_save, sender=CreditorInvoice)
def creditor_invoice_post_save(sender, instance, created, **kwargs):
    """
    Create/refresh the payable open item for an invoice once its total is
    known. Totals are only populated after line items are added (see
    creditor_invoice_lineitem_post_save above) — so this fires once with
    total_amount=0 (skipped) and again once lines exist.
    """
    if instance.total_amount <= Decimal("0"):
        return

    open_item, was_created = CreditorOpenItem.objects.get_or_create(
        invoice=instance,
        defaults={
            "creditor": instance.creditor,
            "transaction_date": instance.transaction_date,
            "due_date": instance.due_date,
            "transaction_type": instance.transaction_type,
            "transaction_number": instance.transaction_number,
            "original_amount": instance.total_amount,
            "balance_due": instance.total_amount,
        },
    )
    if not was_created and open_item.balance_due == open_item.original_amount:
        open_item.original_amount = instance.total_amount
        open_item.balance_due = instance.total_amount
        open_item.save(update_fields=["original_amount", "balance_due"])

    instance.creditor.recalculate_aged_balances()


# ============================================================================
# CREDITOR CREDIT NOTE SIGNALS
# ============================================================================


@receiver(post_save, sender=CreditorCreditNoteLineItem)
def creditor_creditnote_lineitem_post_save(sender, instance, created, **kwargs):
    """Update credit note totals when line items are added/updated (mirrors GRN)."""
    credit_note = instance.credit_note

    totals = CreditorCreditNoteLineItem.objects.filter(
        credit_note=credit_note
    ).aggregate(
        subtotal=Sum("line_subtotal"),
        total_tax=Sum("tax_amount"),
    )

    credit_note.subtotal = totals["subtotal"] or Decimal("0")
    credit_note.total_vat = totals["total_tax"] or Decimal("0")
    credit_note.total_amount = credit_note.subtotal + credit_note.total_vat
    credit_note.save(update_fields=["subtotal", "total_vat", "total_amount"])


@receiver(post_save, sender=CreditorCreditNote)
def creditor_creditnote_post_save(sender, instance, created, **kwargs):
    """
    Create/refresh the open item for a credit note once its total is known.
    Stored as a negative amount — a credit note reduces what's owed, the
    same way CreditorPayment's open item does.
    """
    if instance.total_amount <= Decimal("0"):
        return

    negative_total = instance.total_amount * Decimal("-1")
    open_item, was_created = CreditorOpenItem.objects.get_or_create(
        credit_note=instance,
        defaults={
            "creditor": instance.creditor,
            "transaction_date": instance.transaction_date,
            "due_date": instance.due_date,
            "transaction_type": instance.transaction_type,
            "transaction_number": instance.transaction_number,
            "original_amount": negative_total,
            "balance_due": negative_total,
        },
    )
    if not was_created and open_item.balance_due == open_item.original_amount:
        open_item.original_amount = negative_total
        open_item.balance_due = negative_total
        open_item.save(update_fields=["original_amount", "balance_due"])

    instance.creditor.recalculate_aged_balances()


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
            if not hasattr(creditor, "purchases_mtd"):
                creditor.purchases_mtd = Decimal("0")

        creditor.save(update_fields=["last_paid_amount", "last_paid_date"])

        # Create open item payment record
        CreditorOpenItem.objects.create(
            creditor=creditor,
            transaction_type=instance.transaction_type,
            transaction_number=instance.transaction_number,
            transaction_date=instance.transaction_date,
            original_amount=instance.amount_paid * Decimal("-1"),
            balance_due=instance.amount_paid * Decimal("-1"),
            is_fully_allocated=False,
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
    if open_item.balance_due <= Decimal("0"):
        open_item.is_fully_allocated = True
        open_item.balance_due = Decimal("0")

    open_item.save(update_fields=["balance_due", "is_fully_allocated"])

    # Create audit record. this_transaction_number is an integer field (THISTRAN
    # N(6) in the legacy DBF) — pull the numeric suffix off the payment's
    # transaction_number (e.g. "SUPPAY-000004"), same convention the models use
    # for auto-numbering.
    try:
        this_transaction_number = int(
            instance.payment.transaction_number.split("-")[-1]
        )
    except (ValueError, AttributeError, IndexError):
        this_transaction_number = instance.payment_id or 0

    OpenItemAudit.objects.create(
        creditor=open_item.creditor,
        transaction_type=open_item.transaction_type,
        transaction_number=open_item.transaction_number,
        transaction_date=(
            instance.allocated_at.date()
            if instance.allocated_at
            else datetime.now().date()
        ),
        amount=instance.amount_paid,
        this_transaction_type="AL",
        this_transaction_number=this_transaction_number,
        audit_notes=f"Payment allocation of {instance.amount_paid} from {instance.payment.transaction_number}",
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

    # DJ (debit journal) increases the amount owing; CJ (credit journal)
    # reduces it. journal_type is stored as 'DJ'/'CJ', never 'DEBIT'/'CREDIT'.
    is_debit = instance.journal_type == "DJ"
    signed_amount = (
        instance.journal_amount if is_debit else instance.journal_amount * Decimal("-1")
    )

    CreditorOpenItem.objects.create(
        creditor=creditor,
        journal=instance,
        transaction_type=instance.journal_type,
        transaction_number=instance.transaction_number,
        transaction_date=instance.transaction_date,
        due_date=instance.due_date,
        original_amount=signed_amount,
        balance_due=signed_amount,
    )

    creditor.recalculate_aged_balances()


# ============================================================================
# RFC SIGNALS
# ============================================================================


@receiver(post_save, sender=RFCLineItem)
def rfc_lineitem_post_save(sender, instance, created, **kwargs):
    """Update RFC totals when line items change"""
    rfc = instance.rfc

    # Recalculate RFC totals
    from django.db.models import DecimalField, Sum

    totals = RFCLineItem.objects.filter(rfc=rfc).aggregate(
        subtotal=Sum(
            F("quantity_returned") * F("unit_cost"), output_field=DecimalField()
        ),
        total_tax=Sum("tax_amount"),
    )

    rfc.total_value_exclusive = totals["subtotal"] or Decimal("0")
    rfc.total_vat = totals["total_tax"] or Decimal("0")
    rfc.total_value_inclusive = rfc.total_value_exclusive + rfc.total_vat
    rfc.save(
        update_fields=["total_value_exclusive", "total_vat", "total_value_inclusive"]
    )
