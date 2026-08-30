"""
Enterprise-grade signals for Creditors module
Handles balance updates, validations, audit trails, and business logic
"""

from datetime import datetime, timedelta
from decimal import Decimal

from apps.settings.models import TaxCode
from django.db import transaction as db_transaction
from django.db.models import DecimalField, F, Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

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
    ExpenseCategoryMonthlyBalance,
    ExpenseCategoryTransaction,
    GoodsReceivedNote,
    GRNLineItem,
    OpenItemAllocation,
    OpenItemAudit,
    RFCLineItem,
)

TWO_PLACES = Decimal("0.01")


def _q2(value):
    """
    Quantize to 2 decimal places. Postgres NUMERIC multiplication (used by
    the F(a)*F(b) aggregates below) returns a result scaled to the sum of
    its operands' scales — two NUMERIC(15,2) columns multiplied yield 4
    decimal places, not 2 — so an unquantized aggregate silently carries
    extra precision in Python even though the DB column it eventually gets
    saved into is 2dp. That excess precision then fails
    Creditor.full_clean()'s decimal_places=2 validator the moment it flows
    into purchases_mtd/ytd.
    """
    return (value or Decimal("0")).quantize(TWO_PLACES)


# ============================================================================
# HELPERS — stock movement / expense accumulation / purchases tracking
# ============================================================================


def _move_stock_incoming(stock_item, quantity, unit_cost, supplier, comments, txn_date):
    """Receive stock (GRN). Local import: avoids a hard import-order
    dependency between the creditors and stock_control apps at Django
    app-loading time."""
    from apps.stock_control.services import StockTransactionService

    StockTransactionService.create_incoming_transaction(
        stock_item,
        quantity,
        unit_cost=unit_cost,
        supplier=supplier,
        comments=comments[:30],
        transaction_date=txn_date,
    )


def _move_stock_return(stock_item, quantity, unit_cost, supplier, comments, txn_date):
    """Return stock to supplier (Credit Note)."""
    from apps.stock_control.services import StockTransactionService

    StockTransactionService.create_return_transaction(
        stock_item,
        quantity,
        unit_cost=unit_cost,
        supplier=supplier,
        comments=comments[:30],
        transaction_date=txn_date,
    )


def _apply_new_cost(stock_item, unit_cost, creditor):
    """
    Manual: a GRN's new cost price must flow through to the stock item, and
    — when the supplier is flagged UPDSTKSP (update_selling_price_on_receipt)
    — selling prices must be recomputed from the stored markup percentages.
    Previously the GRN never touched StockItem.cost_price at all.
    """
    if not unit_cost:
        return
    stock_item.refresh_from_db(fields=["cost_price"])
    if unit_cost != stock_item.cost_price:
        stock_item.cost_price = unit_cost
        stock_item.save(update_fields=["cost_price"])
        if creditor.update_selling_price_on_receipt:
            stock_item.apply_markups()


def _accumulate_purchases(creditor, transaction_date, amount_delta):
    """
    Manual: Creditor.purchases_mtd/ytd must reflect real GRN/Invoice
    posting, not just the legacy DBF import. `amount_delta` is the
    incremental change in the transaction's VAT-inclusive total since the
    last time this handler ran for it (may fire more than once per
    transaction as line items are added — see grn_post_save) so summing the
    deltas across every fire converges to the correct final total exactly
    once, with no double counting.
    """
    if not amount_delta:
        return
    today = timezone.now().date()
    if transaction_date.year == today.year:
        creditor.purchases_ytd = creditor.purchases_ytd + amount_delta
        if transaction_date.month == today.month:
            creditor.purchases_mtd = creditor.purchases_mtd + amount_delta


def _accumulate_expense(line, invoice):
    """
    Manual: expense postings must feed ExpenseCategoryTransaction (the live
    ledger) and ExpenseCategoryMonthlyBalance (the per-category/year rollup
    read by the Monthly Expense Details / Expense & Tax enquiries) at
    posting time — previously only the legacy DBF importer ever wrote
    either of these.
    """
    ExpenseCategoryTransaction.objects.create(
        expense_category=line.expense_category,
        creditor=invoice.creditor,
        transaction_date=invoice.transaction_date,
        transaction_number=invoice.transaction_number,
        amount_exclusive=line.amount,
        tax_indicator=invoice.tax_indicator,
        source_type=invoice.transaction_type,
        grn_number=invoice.related_grn.grn_number if invoice.related_grn_id else None,
    )

    year = invoice.transaction_date.year
    month = invoice.transaction_date.month
    balance, _ = ExpenseCategoryMonthlyBalance.objects.get_or_create(
        expense_category=line.expense_category,
        year=year,
        defaults={"expense_category_name": line.expense_category.name[:20]},
    )
    balance.set_month(month, balance.get_month(month) + line.amount)
    balance.expense_mtd = balance.expense_mtd + line.amount
    balance.input_vat_mtd = balance.input_vat_mtd + line.tax_amount
    balance.save()


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
    """
    Update GRN totals when line items are added/updated, and — on first
    creation of the line only — move stock and refresh cost price. Manual
    §Transactions "GRN": "updates Stock Quantity, Cost & Supplier Balance
    simultaneously." `created` gates the stock movement to fire exactly
    once per line, independent of how many times the header below
    re-aggregates (once per line added to the same GRN).
    """
    grn = instance.grn

    from django.db.models import Sum
    from django.db.models.functions import Coalesce

    totals = GRNLineItem.objects.filter(grn=grn).aggregate(
        subtotal=Sum(
            F("quantity_received") * F("unit_cost"), output_field=DecimalField()
        ),
        total_tax=Sum("tax_amount"),
    )

    grn.subtotal = _q2(totals["subtotal"])
    grn.total_vat = _q2(totals["total_tax"])
    grn.total_amount = grn.subtotal + grn.total_vat
    grn.save(update_fields=["subtotal", "total_vat", "total_amount"])

    if created:
        _move_stock_incoming(
            instance.stock_item,
            instance.quantity_received,
            instance.unit_cost,
            grn.creditor,
            f"GRN {grn.transaction_number}",
            grn.transaction_date,
        )
        _apply_new_cost(instance.stock_item, instance.unit_cost, grn.creditor)


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
    if was_created:
        delta = instance.total_amount
    elif open_item.balance_due == open_item.original_amount:
        # Nothing has been allocated against it yet — safe to refresh as lines change.
        delta = instance.total_amount - open_item.original_amount
        open_item.original_amount = instance.total_amount
        open_item.balance_due = instance.total_amount
        open_item.save(update_fields=["original_amount", "balance_due"])
    else:
        delta = Decimal("0")

    _accumulate_purchases(instance.creditor, instance.transaction_date, delta)
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
    """Update invoice totals when line items are added/updated (mirrors GRN),
    and — on first creation of the line only — feed the live expense
    accumulation (ExpenseCategoryTransaction + ExpenseCategoryMonthlyBalance)."""
    invoice = instance.invoice

    totals = CreditorInvoiceLineItem.objects.filter(invoice=invoice).aggregate(
        subtotal=Sum("amount"),
        total_tax=Sum("tax_amount"),
    )

    invoice.subtotal = totals["subtotal"] or Decimal("0")
    invoice.total_vat = totals["total_tax"] or Decimal("0")
    invoice.total_amount = invoice.subtotal + invoice.total_vat
    invoice.save(update_fields=["subtotal", "total_vat", "total_amount"])

    if created:
        _accumulate_expense(instance, invoice)


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
    if was_created:
        delta = instance.total_amount
    elif open_item.balance_due == open_item.original_amount:
        delta = instance.total_amount - open_item.original_amount
        open_item.original_amount = instance.total_amount
        open_item.balance_due = instance.total_amount
        open_item.save(update_fields=["original_amount", "balance_due"])
    else:
        delta = Decimal("0")

    _accumulate_purchases(instance.creditor, instance.transaction_date, delta)
    instance.creditor.recalculate_aged_balances()


# ============================================================================
# CREDITOR CREDIT NOTE SIGNALS
# ============================================================================


@receiver(post_save, sender=CreditorCreditNoteLineItem)
def creditor_creditnote_lineitem_post_save(sender, instance, created, **kwargs):
    """Update credit note totals when line items are added/updated (mirrors
    GRN), and — on first creation of the line only — return stock to the
    supplier. Manual §Transactions "Returns (Credit Note)": same
    stock-movement promise as GRN, in reverse."""
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

    if created:
        _move_stock_return(
            instance.stock_item,
            instance.quantity_returned,
            instance.unit_cost,
            credit_note.creditor,
            f"CN {credit_note.transaction_number}",
            credit_note.transaction_date,
        )


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
    # transaction_number (e.g. "PAY-000004"), same convention the models use
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

    # Manual: "the full value of the journal may only be allocated to ONE
    # ageing period" — no due_date (nothing to naturally age it forward
    # from), instead the item is pinned to instance.age_period via
    # ageing_flag. See Creditor.recalculate_aged_balances /
    # CreditorOpenItem.get_age_bucket, which both check ageing_flag first.
    CreditorOpenItem.objects.create(
        creditor=creditor,
        journal=instance,
        transaction_type=instance.journal_type,
        transaction_number=instance.transaction_number,
        transaction_date=instance.transaction_date,
        due_date=None,
        ageing_flag=instance.age_period,
        original_amount=signed_amount,
        balance_due=signed_amount,
    )

    creditor.recalculate_aged_balances()


# ============================================================================
# RFC SIGNALS
# ============================================================================


@receiver(post_save, sender=RFCLineItem)
def rfc_lineitem_post_save(sender, instance, created, **kwargs):
    """Update RFC totals when line items change, and — on first creation of
    the line while the RFC is still pending — move stock out to the RFC
    bucket. Manual: "Stock movement between normal stock and the RFC
    bucket." Resolution-side movement (replaced/cancelled) is handled in
    RFCViewSet.update_status, since it depends on the status the user picks."""
    rfc = instance.rfc

    totals = RFCLineItem.objects.filter(rfc=rfc).aggregate(
        subtotal=Sum(
            F("quantity_returned") * F("unit_cost"), output_field=DecimalField()
        ),
        total_tax=Sum("tax_amount"),
    )

    rfc.total_value_exclusive = _q2(totals["subtotal"])
    total_vat = _q2(totals["total_tax"])
    rfc.total_value_inclusive = rfc.total_value_exclusive + total_vat
    rfc.save(update_fields=["total_value_exclusive", "total_value_inclusive"])

    if created and rfc.status == "PE":
        from apps.stock_control.models import StockTransaction
        from apps.stock_control.services import StockTransactionService

        stock_item = instance.stock_item
        alias = stock_item._state.db or "default"
        with db_transaction.atomic(using=alias):
            StockTransaction.objects.create(
                transaction_type="RFC_IN",
                stock_item=stock_item,
                quantity_out=instance.quantity_returned,
                unit_cost=instance.unit_cost,
                supplier=rfc.creditor,
                transaction_date=rfc.date_sent or timezone.now().date(),
                comments=f"RFC {rfc.rfc_number}"[:30],
            )
            StockTransactionService.adjust_quantity_on_hand(
                stock_item, -instance.quantity_returned
            )
