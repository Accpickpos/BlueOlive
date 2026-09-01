"""
Management command wrapper for the Data Integrity Report (manual §8.8).
Shares the same service functions as the
system-config/data_integrity_report/ REST endpoint — read-only detection,
no auto-fix.
"""

from apps.settings.data_integrity_services import (
    check_creditor_balances,
    check_debtor_balances,
    check_stock_quantities,
)
from django.core.management.base import BaseCommand

CHECKS = {
    "debtors": ("Debtor balances", check_debtor_balances),
    "creditors": ("Creditor balances", check_creditor_balances),
    "stock": ("Stock quantities", check_stock_quantities),
}


class Command(BaseCommand):
    help = "Run the Data Integrity Report: Debtor/Creditor balance and Stock quantity reconciliation (read-only)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--checks",
            default="debtors,creditors,stock",
            help="Comma-separated subset of checks to run (default: all)",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="List every discrepancy found"
        )

    def handle(self, *args, **options):
        requested = {c.strip() for c in options["checks"].split(",") if c.strip()}

        for key, (label, check_fn) in CHECKS.items():
            if key not in requested:
                continue

            self.stdout.write(f"Checking {label}...")
            result = check_fn()

            if result["discrepancy_count"] == 0:
                self.stdout.write(
                    self.style.SUCCESS(f"  {label}: {result['checked']} checked, no discrepancies")
                )
                continue

            self.stdout.write(
                self.style.ERROR(
                    f"  {label}: {result['discrepancy_count']} discrepancies out of {result['checked']} checked"
                )
            )
            shown = result["discrepancies"] if options["verbose"] else result["discrepancies"][:10]
            for d in shown:
                self.stdout.write(f"    {d}")
            if not options["verbose"] and len(result["discrepancies"]) > 10:
                self.stdout.write(f"    ... and {len(result['discrepancies']) - 10} more (use --verbose)")
