"""
Management command to validate and recalculate cash book balances
"""

from decimal import Decimal

from apps.cash_book.models import CashBookTransaction
from apps.cash_book.services import BalanceCalculationService
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction


class Command(BaseCommand):
    help = "Validate and recalculate all cash book balances"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix",
            action="store_true",
            help="Recalculate balances if discrepancies found",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed output"
        )

    def handle(self, *args, **options):
        self.stdout.write("Validating cash book balances...")

        transactions = CashBookTransaction.objects.all().order_by(
            "transaction_date", "transaction_number"
        )

        if transactions.count() == 0:
            self.stdout.write(self.style.WARNING("No transactions found"))
            return

        # Recalculate balances
        cash_balance = Decimal("0")
        bank_balance = Decimal("0")
        errors = []

        for txn in transactions:
            # Calculate expected balance
            if txn.is_debit:
                if txn.account_type == "CASH":
                    cash_balance += txn.amount
                else:
                    bank_balance += txn.amount
            elif txn.is_credit:
                if txn.account_type == "CASH":
                    cash_balance -= txn.amount
                else:
                    bank_balance -= txn.amount

            # Check for discrepancies
            if txn.running_balance_cash != cash_balance:
                errors.append(
                    {
                        "txn": txn.transaction_number,
                        "field": "running_balance_cash",
                        "expected": cash_balance,
                        "actual": txn.running_balance_cash,
                    }
                )

            if txn.running_balance_bank != bank_balance:
                errors.append(
                    {
                        "txn": txn.transaction_number,
                        "field": "running_balance_bank",
                        "expected": bank_balance,
                        "actual": txn.running_balance_bank,
                    }
                )

            if options["verbose"]:
                self.stdout.write(
                    f"{txn.transaction_number}: Cash={cash_balance}, Bank={bank_balance}"
                )

        if errors:
            self.stdout.write(
                self.style.ERROR(f"Found {len(errors)} balance discrepancies")
            )

            for error in errors[:10]:  # Show first 10
                self.stdout.write(
                    f"  {error['txn']}: {error['field']} "
                    f"(expected={error['expected']}, actual={error['actual']})"
                )

            if len(errors) > 10:
                self.stdout.write(f"  ... and {len(errors) - 10} more")

            if options["fix"]:
                self.stdout.write("Recalculating all balances...")
                with db_transaction.atomic():
                    BalanceCalculationService.update_running_balances()
                self.stdout.write(self.style.SUCCESS("Balances recalculated"))
            else:
                self.stdout.write(
                    self.style.WARNING("Use --fix to recalculate balances")
                )
        else:
            self.stdout.write(self.style.SUCCESS("All balances are correct"))

        # Final summary
        final_txn = transactions.last()
        if final_txn:
            self.stdout.write(
                f"\nFinal balances:"
                f"\n  Cash: {final_txn.running_balance_cash}"
                f"\n  Bank: {final_txn.running_balance_bank}"
                f"\n  Total: {final_txn.running_balance_cash + final_txn.running_balance_bank}"
            )
