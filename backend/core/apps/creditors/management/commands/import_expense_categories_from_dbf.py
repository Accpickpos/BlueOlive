"""
Import creditor-side expense category monthly balances from supexp.dbf.
supexp.dbf has one row per category (no year column) — the year being
imported must be supplied via --year.
"""

from apps.creditors.models import ExpenseCategoryMonthlyBalance
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_int, to_str
from apps.settings.models import ExpenseCategory


class Command(TenantAwareLegacyImportCommand):
    help = "Import creditor-side expense category monthly balances from supexp.dbf"

    def add_legacy_arguments(self, parser):
        parser.add_argument(
            "--year",
            type=int,
            required=True,
            help="Financial year these balances belong to (supexp.dbf has no year column)",
        )

    def run(self, **options):
        path = self.pdf_dir / "supexp.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        categories = {
            c.number: c for c in ExpenseCategory.objects.using(self.db_alias).all()
        }
        year = options["year"]

        for record in open_dbf(path):
            category = categories.get(to_int(record.get("EXPCAT")))
            if category is None:
                self.skipped += 1
                continue

            defaults = {
                "expense_category_name": to_str(record.get("EXPCATNAME"), 20),
                "expense_mtd": to_decimal(record.get("EXPMTD")),
                "input_vat_mtd": to_decimal(record.get("EXPINVAT")),
            }
            for i in range(1, 13):
                defaults[f"exp_month_{i}"] = to_decimal(record.get(f"EXP{i}"))

            try:
                _, created = ExpenseCategoryMonthlyBalance.objects.using(
                    self.db_alias
                ).update_or_create(
                    expense_category=category, year=year, defaults=defaults
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ category {category.number}: {e}")
                )
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Expense category balances imported from {path.name}"
            )
        )
