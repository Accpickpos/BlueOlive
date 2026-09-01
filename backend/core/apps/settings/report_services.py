"""
═══════════════════════════════════════════════════════════════════════════
SETTINGS APP - Cross-module Utilities reports
Consolidated Expenditure (manual §8.5) and Tax Control / VAT-201 (manual §8.2)
═══════════════════════════════════════════════════════════════════════════
"""

from calendar import monthrange
from datetime import date
from decimal import Decimal

from apps.cash_book.models import CashBookTransaction
from apps.creditors.models import (
    CreditorCreditNote,
    CreditorInvoice,
    ExpenseCategoryTransaction,
)
from apps.debtors.models import DebtorTransaction
from apps.pos.models import CashSale
from apps.settings.models import ExpenseCategory
from django.db.models import Q, Sum


def _period_bounds(period: str, ytd: bool) -> tuple[date, date]:
    """period is 'YYYY-MM'. Returns (start, end) inclusive."""
    year, month = (int(p) for p in period.split("-"))
    start = date(year, 1, 1) if ytd else date(year, month, 1)
    end = date(year, month, monthrange(year, month)[1])
    return start, end


def get_consolidated_expenditure(period: str, ytd: bool = False) -> dict:
    """
    Manual §8.5: Creditors Expense + Cash Book Expense transactions,
    combined by ExpenseCategory, for a month or Year-to-Date.
    """
    start, end = _period_bounds(period, ytd)

    creditor_totals = {
        row["expense_category"]: row["total"]
        for row in ExpenseCategoryTransaction.objects.filter(
            transaction_date__gte=start, transaction_date__lte=end
        )
        .values("expense_category")
        .annotate(total=Sum("amount_inclusive"))
    }

    cash_book_totals = {
        row["other_expense__expense_category"]: row["total"]
        for row in CashBookTransaction.objects.filter(
            audit_type=4,
            transaction_date__gte=start,
            transaction_date__lte=end,
            other_expense__isnull=False,
        )
        .values("other_expense__expense_category")
        .annotate(total=Sum("total_incl_vat"))
    }

    category_ids = set(creditor_totals) | set(cash_book_totals)
    categories = {c.id: c.name for c in ExpenseCategory.objects.filter(id__in=category_ids)}

    rows = []
    grand_total = Decimal("0")
    for cat_id in category_ids:
        creditor_amount = creditor_totals.get(cat_id) or Decimal("0")
        cash_book_amount = cash_book_totals.get(cat_id) or Decimal("0")
        total = creditor_amount + cash_book_amount
        grand_total += total
        rows.append(
            {
                "category_id": cat_id,
                "category_name": categories.get(cat_id, f"Category {cat_id}"),
                "creditor_amount": creditor_amount,
                "cash_book_amount": cash_book_amount,
                "total": total,
            }
        )
    rows.sort(key=lambda r: r["category_name"])

    return {
        "period": period,
        "ytd": ytd,
        "start_date": str(start),
        "end_date": str(end),
        "rows": rows,
        "grand_total": grand_total,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Tax Control / VAT-201 (manual §8.2)
# ═══════════════════════════════════════════════════════════════════════════

# Debtors: which transaction types are VAT-bearing sales/credits, and which
# side of the VAT201 return they fall on (per DebtorTransaction.models.py:577-588).
_DEBTOR_VAT_TYPES = {
    "IN": ("output", "Debtors — Invoices"),
    "CS": ("output", "Debtors — Cash Sales"),
    "CN": ("output", "Debtors — Credit Notes (reduces output)"),
    "RF": ("output", "Debtors — Refunds (reduces output)"),
}


def get_tax_control_report(start_date: str, end_date: str) -> dict:
    """
    Manual §8.2: VAT reconciled across Debtors (Invoices/Cash Sales/Laybye/
    Other Income), Creditors (Credit Notes/Settlement Discounts/Invoices/
    Other Expenses), and Cash Book, grouped into category buckets, alongside
    each source module's own total for cross-reconciliation.

    NOTE: the manual names SARS VAT201 "categories A-F" without giving their
    literal definitions here — the buckets below are a reasonable grouping,
    not a confirmed SARS line-item mapping. Treat the category labels as
    provisional.
    """
    categories: dict[str, Decimal] = {}

    def add(label: str, amount: Decimal | None):
        if not amount:
            return
        categories[label] = categories.get(label, Decimal("0")) + amount

    # --- Debtors: output VAT from Invoices/Cash Sales, netted by Credit Notes/Refunds ---
    debtor_totals = {
        row["transaction_type"]: row["total"]
        for row in DebtorTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
            transaction_type__in=_DEBTOR_VAT_TYPES.keys(),
        )
        .values("transaction_type")
        .annotate(total=Sum("vat_amount"))
    }
    debtors_output_vat = Decimal("0")
    for ttype, (_, label) in _DEBTOR_VAT_TYPES.items():
        amount = debtor_totals.get(ttype) or Decimal("0")
        debtors_output_vat += amount
        add(label, amount)

    # --- POS cash sales not yet converted to a Debtor invoice (avoid double-count) ---
    # CashSale.convert_cash_sale_to_invoice() reuses is_cancelled=True to mark
    # a converted sale (see pos/services.py) — no distinct "converted" flag
    # exists, so is_posted=True, is_cancelled=False identifies real,
    # not-yet-converted cash sales.
    unconverted_cash_sales = CashSale.objects.filter(
        sale_date__gte=start_date,
        sale_date__lte=end_date,
        is_posted=True,
        is_cancelled=False,
    ).aggregate(total=Sum("vat_amount"))["total"] or Decimal("0")
    add("POS — Cash Sales (not converted to invoice)", unconverted_cash_sales)
    debtors_output_vat += unconverted_cash_sales

    # --- Creditors: input VAT from Invoices, netted by Credit Notes; Other Expenses separately ---
    creditor_invoice_vat = CreditorInvoice.objects.filter(
        transaction_date__gte=start_date, transaction_date__lte=end_date
    ).aggregate(total=Sum("total_vat"))["total"] or Decimal("0")
    add("Creditors — Invoices (input VAT)", creditor_invoice_vat)

    creditor_credit_note_vat = CreditorCreditNote.objects.filter(
        transaction_date__gte=start_date, transaction_date__lte=end_date
    ).aggregate(total=Sum("total_vat"))["total"] or Decimal("0")
    add("Creditors — Credit Notes (reduces input VAT)", creditor_credit_note_vat)

    creditor_expense_vat = ExpenseCategoryTransaction.objects.filter(
        transaction_date__gte=start_date, transaction_date__lte=end_date
    ).aggregate(total=Sum("input_vat_amount"))["total"] or Decimal("0")
    add("Creditors — Other Expenses (input VAT)", creditor_expense_vat)

    creditors_input_vat = creditor_invoice_vat - creditor_credit_note_vat + creditor_expense_vat

    # --- Cash Book: reuse the audit_type categorization (includes the audit_type=4 fix) ---
    cash_book_vat = CashBookTransaction.objects.filter(
        transaction_date__gte=start_date, transaction_date__lte=end_date
    ).aggregate(
        input_vat=Sum("tax_amount", filter=Q(audit_type__in=[3, 4])),
        output_vat=Sum("tax_amount", filter=Q(audit_type__in=[1, 2])),
    )
    cash_book_input_vat = cash_book_vat["input_vat"] or Decimal("0")
    cash_book_output_vat = cash_book_vat["output_vat"] or Decimal("0")
    add("Cash Book — Input VAT (Payments/Expenses)", cash_book_input_vat)
    add("Cash Book — Output VAT (Receipts/Sundry Income)", cash_book_output_vat)

    total_output_vat = debtors_output_vat + cash_book_output_vat
    total_input_vat = creditors_input_vat + cash_book_input_vat

    return {
        "start_date": start_date,
        "end_date": end_date,
        "categories": [{"label": label, "amount": amount} for label, amount in categories.items()],
        "totals": {
            "output_vat": total_output_vat,
            "input_vat": total_input_vat,
            "net_vat_payable": total_output_vat - total_input_vat,
        },
        "reconciliation": {
            "debtors_module_output_vat": debtors_output_vat,
            "creditors_module_input_vat": creditors_input_vat,
            "cash_book_module_input_vat": cash_book_input_vat,
            "cash_book_module_output_vat": cash_book_output_vat,
        },
        "assumptions": (
            "SARS VAT201 category letters (A-F) are not literally reproduced here — "
            "the manual references them without definitions. Categories below group "
            "by source module/transaction type; reconcile against each module's own "
            "Transaction Report before submission."
        ),
    }
