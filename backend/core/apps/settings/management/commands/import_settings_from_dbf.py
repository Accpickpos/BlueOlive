"""
Import legacy reference data from the pdf/ DBF export: sales departments
(deptfile.dbf), sales areas (darea.dbf), and expense/income categories
(cbexp.dbf, cbinc.dbf, supexp.dbf). Must run before any other legacy
importer, since StockItem/Creditor/etc. all FK into these.
"""
from apps.debtors.models import Darea
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import dedupe_name, open_dbf, to_decimal, to_int, to_str
from apps.settings.models import ExpenseCategory, IncomeCategory, SalesArea, SalesDepartment


class Command(TenantAwareLegacyImportCommand):
    help = 'Import sales departments, sales areas, and expense/income categories from legacy DBF files'

    def run(self, **options):
        self._import_departments()
        self._import_sales_areas()
        self._import_expense_categories()
        self._import_income_categories()

    def _import_departments(self):
        path = self.pdf_dir / 'deptfile.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found, skipping departments'))
            return
        for record in open_dbf(path):
            number = to_int(record.get('DEPT'))
            name = to_str(record.get('DEPTNAME'), 100)
            if not number or not name:
                self.skipped += 1
                continue
            name = dedupe_name(SalesDepartment.objects.using(self.db_alias), name, 'number', number, 100)
            defaults = {
                'name': name,
                'sales_mtd': to_decimal(record.get('SLSMTD')),
            }
            for i in range(1, 13):
                defaults[f'sales_p{i}'] = to_decimal(record.get(f'SLS{i}'))
            _, created = SalesDepartment.objects.using(self.db_alias).update_or_create(
                number=number, defaults=defaults
            )
            self.created += created
            self.updated += not created
        self.stdout.write(self.style.SUCCESS(f'  ✓ Departments imported from {path.name}'))

    def _import_sales_areas(self):
        path = self.pdf_dir / 'darea.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found, skipping sales areas'))
            return
        for record in open_dbf(path):
            code = to_str(record.get('DAREA'))
            name = to_str(record.get('DAREANAME'), 100)
            if not code or not name:
                self.skipped += 1
                continue
            monthly = {f'arsls{i}': to_decimal(record.get(f'ARSLS{i}')) for i in range(1, 13)}

            # settings.SalesArea — the real FK target used across the app
            number = to_int(code)
            if number:
                sa_defaults = {'name': name, 'sales_mtd': sum(monthly.values())}
                _, created = SalesArea.objects.using(self.db_alias).update_or_create(
                    number=number, defaults=sa_defaults
                )
                self.created += created
                self.updated += not created

            # debtors.Darea — raw DBF mirror (Debtor.darea is a bare int, not FK'd to either)
            darea_defaults = {'dareaname': name[:20], **{k: v for k, v in monthly.items()}}
            Darea.objects.using(self.db_alias).update_or_create(
                darea=code[:2], defaults=darea_defaults
            )
        self.stdout.write(self.style.SUCCESS(f'  ✓ Sales areas imported from {path.name}'))

    def _import_expense_categories(self):
        for filename in ('cbexp.dbf', 'supexp.dbf'):
            path = self.pdf_dir / filename
            if not path.exists():
                self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found, skipping'))
                continue
            for record in open_dbf(path):
                number = to_int(record.get('EXPCAT'))
                name = to_str(record.get('EXPCATNAME'), 100)
                if not number or not name:
                    self.skipped += 1
                    continue
                name = dedupe_name(ExpenseCategory.objects.using(self.db_alias), name, 'number', number, 100)
                _, created = ExpenseCategory.objects.using(self.db_alias).update_or_create(
                    number=number, defaults={'name': name}
                )
                self.created += created
                self.updated += not created
            self.stdout.write(self.style.SUCCESS(f'  ✓ Expense categories imported from {filename}'))

    def _import_income_categories(self):
        path = self.pdf_dir / 'cbinc.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found, skipping income categories'))
            return
        for record in open_dbf(path):
            number = to_int(record.get('INCCAT'))
            name = to_str(record.get('INCCATNAME'), 100)
            if not number or not name:
                self.skipped += 1
                continue
            name = dedupe_name(IncomeCategory.objects.using(self.db_alias), name, 'number', number, 100)
            _, created = IncomeCategory.objects.using(self.db_alias).update_or_create(
                number=number, defaults={'name': name}
            )
            self.created += created
            self.updated += not created
        self.stdout.write(self.style.SUCCESS(f'  ✓ Income categories imported from {path.name}'))
