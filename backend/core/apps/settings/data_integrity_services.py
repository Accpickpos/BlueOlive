"""
═══════════════════════════════════════════════════════════════════════════
SETTINGS APP - Data Integrity Report (manual §8.8)
Read-only reconciliation checks: Debtor/Creditor stored balances vs.
transaction history, and Stock quantity_on_hand vs. summed StockTransaction
movements. Detection only — no auto-fix (this is a report in the spec, not
a repair tool).

Duplicate Stock Codes and Markup auto-adjust (the other two legacy checks)
are already structurally covered elsewhere and are not repeated here:
- StockItem.stock_code is unique=True, primary_key=True (DB-enforced).
- apps.stock_control.signals.calculate_stock_item_markups (pre_save)
  already recalculates markup from cost/selling price on every save.
═══════════════════════════════════════════════════════════════════════════
"""

from decimal import Decimal

from apps.creditors.models import Creditor
from apps.debtors.models import Debtor
from apps.stock_control.models import StockItem, StockTransaction
from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

TOLERANCE = Decimal("0.01")


def check_debtor_balances() -> dict:
    """
    Diff each Debtor's stored total_balance (sum of aging-bucket fields)
    against an independent sum of DebtorTransaction.signed_amount.
    """
    discrepancies = []
    checked = 0

    for debtor in Debtor.objects.all().iterator():
        checked += 1
        stored_balance = debtor.total_balance
        computed_balance = sum(
            (t.signed_amount for t in debtor.transactions.only("total_amount", "transaction_type")),
            Decimal("0"),
        )
        diff = stored_balance - computed_balance
        if abs(diff) > TOLERANCE:
            discrepancies.append(
                {
                    "dno": debtor.dno,
                    "name": debtor.dname,
                    "stored_balance": stored_balance,
                    "computed_balance": computed_balance,
                    "difference": diff,
                }
            )

    return {
        "checked": checked,
        "discrepancy_count": len(discrepancies),
        "discrepancies": discrepancies,
    }


def check_creditor_balances() -> dict:
    """
    Diff each Creditor's stored total_outstanding_balance against a
    recalculation from open items (reuses Creditor.recalculate_aged_balances
    in dry-run mode, persist=False, so nothing is written to the DB).
    """
    discrepancies = []
    checked = 0

    for creditor in Creditor.objects.all().iterator():
        checked += 1
        stored_balance = creditor.total_outstanding_balance
        creditor.recalculate_aged_balances(persist=False)
        recomputed_balance = (
            creditor.balance_current
            + creditor.balance_30_days
            + creditor.balance_60_days
            + creditor.balance_90_days
            + creditor.balance_120_days
            + creditor.balance_150_days
            + creditor.balance_180_days
        )
        diff = stored_balance - recomputed_balance
        if abs(diff) > TOLERANCE:
            discrepancies.append(
                {
                    "supplier_number": creditor.supplier_number,
                    "name": creditor.name,
                    "stored_balance": stored_balance,
                    "computed_balance": recomputed_balance,
                    "difference": diff,
                }
            )

    return {
        "checked": checked,
        "discrepancy_count": len(discrepancies),
        "discrepancies": discrepancies,
    }


def check_stock_quantities() -> dict:
    """
    Diff each StockItem.quantity_on_hand against net(quantity_in - quantity_out)
    summed from its StockTransaction history.
    """
    movement_totals = StockTransaction.objects.values("stock_item_id").annotate(
        net_movement=Coalesce(Sum("quantity_in"), Value(0), output_field=DecimalField())
        - Coalesce(Sum("quantity_out"), Value(0), output_field=DecimalField())
    )
    movement_by_item = {row["stock_item_id"]: row["net_movement"] for row in movement_totals}

    discrepancies = []
    checked = 0
    for item in StockItem.objects.all().iterator():
        checked += 1
        computed_qoh = movement_by_item.get(item.stock_code, Decimal("0"))
        diff = item.quantity_on_hand - computed_qoh
        if abs(diff) > TOLERANCE:
            discrepancies.append(
                {
                    "stock_code": item.stock_code,
                    "description": getattr(item, "description", ""),
                    "stored_quantity_on_hand": item.quantity_on_hand,
                    "computed_from_transactions": computed_qoh,
                    "difference": diff,
                }
            )

    return {
        "checked": checked,
        "discrepancy_count": len(discrepancies),
        "discrepancies": discrepancies,
    }
