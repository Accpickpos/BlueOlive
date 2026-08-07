"""
Create the "Deposits Held" GL account (and optionally wire up the other
rental GL accounts) for the current tenant schema.

Usage:
    python manage.py setup_rental_gl_accounts --deposits-held-accno 21500000 \\
        --cash-accno 10000000 --sales-revenue-accno 40000000 \\
        --vat-output-accno 22000000 --writeoff-income-accno 41000000

Run once per tenant during onboarding, against the tenant's real chart of
accounts (accno values are tenant-specific — there is no safe default to
hardcode). Confirms the account appears correctly on Balance Sheet reports
before any live rental transaction is accepted (see /plan-eng-review
Cross-model tension 2 and /plan-ceo-review Section 9 cutover smoke test).
"""
from django.core.management.base import BaseCommand, CommandError

from apps.general_ledger.models import GLMast
from apps.rentals.models import RentalSettings


class Command(BaseCommand):
    help = 'Create/wire the GL accounts the rentals app posts to'

    def add_arguments(self, parser):
        parser.add_argument('--deposits-held-accno', type=int, required=True,
                             help='Balance Sheet liability account number for deposits held')
        parser.add_argument('--deposits-held-name', type=str, default='Deposits Held',
                             help='Account name if the account needs to be created')
        parser.add_argument('--deposits-held-repline', type=int, default=0,
                             help='Balance sheet report line number for the new account')
        parser.add_argument('--cash-accno', type=int, required=False)
        parser.add_argument('--sales-revenue-accno', type=int, required=False)
        parser.add_argument('--vat-output-accno', type=int, required=False)
        parser.add_argument('--writeoff-income-accno', type=int, required=False)

    def handle(self, *args, **options):
        accno = options['deposits_held_accno']
        account, created = GLMast.objects.get_or_create(
            accno=accno,
            defaults=dict(
                name=options['deposits_held_name'],
                type=GLMast.ACCOUNT_TYPE_CHOICES[1][0],  # 'B' - Balance Sheet
                drorcr=GLMast.DEBIT_CREDIT_CHOICES[1][0],  # 'C' - normal credit balance (liability)
                repline=options['deposits_held_repline'],
            ),
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                f"Created GLMast account {accno} ({account.name}) — "
                f"verify it appears correctly on your Balance Sheet report before go-live."
            ))
        else:
            if account.type != 'B':
                raise CommandError(
                    f"GLMast account {accno} exists but is type={account.type!r}, "
                    f"expected 'B' (Balance Sheet). Refusing to reuse — pick a different accno."
                )
            self.stdout.write(self.style.WARNING(
                f"GLMast account {accno} already exists ({account.name}) — reusing it."
            ))

        settings_row = RentalSettings.get_solo()
        settings_row.deposits_held_accno = accno
        for opt_key, field in [
            ('cash_accno', 'cash_accno'),
            ('sales_revenue_accno', 'sales_revenue_accno'),
            ('vat_output_accno', 'vat_output_accno'),
            ('writeoff_income_accno', 'writeoff_income_accno'),
        ]:
            if options.get(opt_key) is not None:
                setattr(settings_row, field, options[opt_key])
        settings_row.save()

        self.stdout.write(self.style.SUCCESS('RentalSettings GL account mapping updated.'))
