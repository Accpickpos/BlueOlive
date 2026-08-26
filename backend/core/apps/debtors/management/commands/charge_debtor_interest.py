"""
Month-end interest charging batch routine (manual §2.2 [223.htm]).

Manual: "This should only be done at month end after a backup." — a
deliberate, operator-triggered administrative action, not an automatic
scheduled job, matching a management command rather than a Celery task.

DebtorService.charge_interest_batch() already existed but had no caller
anywhere in the codebase (confirmed via repo-wide grep during the Debtors
module audit) — this command is that missing caller.
"""

from apps.debtors.services import DebtorService
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand

# Manual: "Start Charging at" period selection — 2=30 days, 3=60, ... 7=180.
START_PERIOD_CHOICES = {
    2: "30 days",
    3: "60 days",
    4: "90 days",
    5: "120 days",
    6: "150 days",
    7: "180 days",
}


class Command(TenantAwareLegacyImportCommand):
    help = "Charge monthly interest on overdue debtor balances (dintflag=Y accounts)"

    def add_legacy_arguments(self, parser):
        parser.add_argument(
            "--rate",
            type=float,
            required=True,
            help="Monthly interest rate as a decimal fraction, e.g. 0.01 for 1%%",
        )
        parser.add_argument(
            "--start-period",
            type=int,
            default=2,
            choices=sorted(START_PERIOD_CHOICES),
            help="Charge interest on balances at or beyond this age: "
            + ", ".join(f"{k}={v}" for k, v in START_PERIOD_CHOICES.items())
            + " (default: 2 = 30 days)",
        )
        parser.add_argument(
            "--charge-credit-balances",
            action="store_true",
            help='Also apply the rate to accounts in credit (manual: "Pay Interest on Credit Balances"). Default: no.',
        )

    def run(self, **options):
        result = DebtorService.charge_interest_batch(
            rate=options["rate"],
            start_period=options["start_period"],
            charge_credit_balances=options["charge_credit_balances"],
        )
        self.created = result["debtors_charged"]  # reuse base class's summary line
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Charged interest to {result['debtors_charged']} debtor(s), "
                f"total R{result['total_interest']}"
            )
        )
