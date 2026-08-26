"""
Outstanding Deposits report (T8) — total liability exposure + overdue rentals.

On-demand, run manually by shop staff — matches import_from_dbf.py's existing
CLI-command convention rather than a scheduled job or new admin UI page.

Sourced only from NEW GL postings this milestone creates going forward — NOT
from historical COBOL data (general_ledger/cash_book history is not imported,
see the /office-hours design doc's Open Questions). Cutover assumption: the
pilot customer's opening balance is seeded via
`seed_opening_rental_balance` (manual physical count) before this report is
first trusted — see /plan-ceo-review's cutover-mechanism decision.

Usage:
    python manage.py report_outstanding_deposits
"""

from apps.gas.models import RentalTransaction
from django.core.management.base import BaseCommand
from django.db.models import Sum


class Command(BaseCommand):
    help = "Report total outstanding cylinder deposit liability and overdue rentals"

    def handle(self, *args, **options):
        open_rentals = RentalTransaction.objects.filter(
            status=RentalTransaction.STATUS_OPEN
        )

        if not open_rentals.exists():
            self.stdout.write("No outstanding deposits.")
            return

        total_liability = open_rentals.aggregate(total=Sum("deposit_amount"))["total"]
        self.stdout.write(f"Total deposit liability outstanding: {total_liability}")
        self.stdout.write(f"Open rentals: {open_rentals.count()}")
        self.stdout.write("")

        overdue = [r for r in open_rentals if r.is_overdue]
        if overdue:
            self.stdout.write(self.style.WARNING(f"Overdue rentals ({len(overdue)}):"))
            for r in overdue:
                self.stdout.write(
                    f"  #{r.pk} {r.debtor.dname} — {r.stock_item.description} x{r.quantity} "
                    f"— deposit {r.deposit_amount} — due {r.due_date}"
                )
        else:
            self.stdout.write("No overdue rentals.")
