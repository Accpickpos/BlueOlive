"""
Seed opening rental balances from a manual physical count at cutover.

A live LPG shop always has some cylinders out with customers — there is no
COBOL rental data to migrate (rentals is a new BlueOlive concept), so the
only way to make the "Outstanding Deposits" report (T8) accurate from day one
is a physical count: staff count cylinders currently out and their deposit
amounts, then this command seeds that as opening state.

Creates RentalTransaction rows with status=OPEN and no gl_batchno_checkout
(these did not go through the normal checkout flow) and sets GLMast.balbfwd
on the Deposits Held account to the total — GLMast's own field for exactly
this "balance brought forward" purpose, not a fabricated offsetting GL entry.

Usage:
    python manage.py seed_opening_rental_balances --csv opening_rentals.csv

CSV columns (header row required): debtor_dno,stock_item_code,quantity,deposit_amount
"""
import csv
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.debtors.models import Debtor
from apps.general_ledger.models import GLMast
from apps.rentals.models import RentalSettings, RentalTransaction
from apps.stock_control.models import StockItem


class Command(BaseCommand):
    help = 'Seed opening rental balances from a manual physical count (cutover)'

    def add_arguments(self, parser):
        parser.add_argument('--csv', type=str, required=True,
                             help='Path to CSV: debtor_dno,stock_item_code,quantity,deposit_amount')
        parser.add_argument('--dry-run', action='store_true',
                             help='Validate and print totals without writing anything')

    def handle(self, *args, **options):
        settings_row = RentalSettings.get_solo()
        if settings_row.deposits_held_accno is None:
            raise CommandError(
                'RentalSettings.deposits_held_accno is not set — run '
                'setup_rental_gl_accounts first.'
            )

        rows = []
        with open(options['csv'], newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for lineno, row in enumerate(reader, start=2):
                try:
                    debtor = Debtor.objects.get(dno=row['debtor_dno'])
                    stock_item = StockItem.objects.get(stock_code=row['stock_item_code'])
                    quantity = Decimal(row['quantity'])
                    deposit_amount = Decimal(row['deposit_amount'])
                except Debtor.DoesNotExist:
                    raise CommandError(f"Line {lineno}: no debtor with dno={row['debtor_dno']}")
                except StockItem.DoesNotExist:
                    raise CommandError(f"Line {lineno}: no stock item with code={row['stock_item_code']}")
                except (InvalidOperation, KeyError) as exc:
                    raise CommandError(f"Line {lineno}: invalid row — {exc}")
                rows.append((debtor, stock_item, quantity, deposit_amount))

        total = sum(deposit_amount for _, _, _, deposit_amount in rows)
        self.stdout.write(f"Parsed {len(rows)} opening rentals, total deposit liability: {total}")

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('Dry run — nothing written.'))
            return

        with transaction.atomic():
            today = timezone.now().date()
            for debtor, stock_item, quantity, deposit_amount in rows:
                RentalTransaction.objects.create(
                    debtor=debtor, stock_item=stock_item, quantity=quantity,
                    deposit_amount=deposit_amount, checkout_date=today,
                    due_date=today + timezone.timedelta(days=settings_row.overdue_threshold_days),
                    notes='Opening balance — seeded from cutover physical count, not a new checkout.',
                )

            account = GLMast.objects.select_for_update().get(accno=settings_row.deposits_held_accno)
            account.balbfwd += total
            account.save(update_fields=['balbfwd', 'updated_at'])

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(rows)} opening rentals. GLMast {settings_row.deposits_held_accno} "
            f"balbfwd increased by {total}."
        ))
