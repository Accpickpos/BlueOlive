"""Import cash-book-side expense/income category monthly balances from cbexp.dbf/cbinc.dbf."""
from apps.cash_book.models import ExpenseCategoryBalance, IncomeCategoryBalance
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_int
from apps.settings.models import ExpenseCategory, IncomeCategory


class Command(TenantAwareLegacyImportCommand):
    help = 'Import cash-book-side expense/income category monthly balances from cbexp.dbf/cbinc.dbf'

    def run(self, **options):
        self._import_expense()
        self._import_income()

    def _import_expense(self):
        path = self.pdf_dir / 'cbexp.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        categories = {c.number: c for c in ExpenseCategory.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            category = categories.get(to_int(record.get('EXPCAT')))
            if category is None:
                self.skipped += 1
                continue

            defaults = {
                'balance_month_to_date': to_decimal(record.get('EXPMTD')),
                'input_vat_month_to_date': to_decimal(record.get('EXPINVAT')),
            }
            for i in range(1, 13):
                defaults[f'balance_month_{i:02d}'] = to_decimal(record.get(f'EXP{i}'))

            try:
                _, created = ExpenseCategoryBalance.objects.using(self.db_alias).update_or_create(
                    expense_category=category, defaults=defaults
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ expense category {category.number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS('  ✓ Expense category balances imported from cbexp.dbf'))

    def _import_income(self):
        path = self.pdf_dir / 'cbinc.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        categories = {c.number: c for c in IncomeCategory.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            category = categories.get(to_int(record.get('INCCAT')))
            if category is None:
                self.skipped += 1
                continue

            defaults = {
                'balance_month_to_date': to_decimal(record.get('INCMTD')),
                'output_vat_month_to_date': to_decimal(record.get('INCINVAT')),
            }
            for i in range(1, 13):
                defaults[f'balance_month_{i:02d}'] = to_decimal(record.get(f'INC{i}'))

            try:
                _, created = IncomeCategoryBalance.objects.using(self.db_alias).update_or_create(
                    income_category=category, defaults=defaults
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ income category {category.number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS('  ✓ Income category balances imported from cbinc.dbf'))
