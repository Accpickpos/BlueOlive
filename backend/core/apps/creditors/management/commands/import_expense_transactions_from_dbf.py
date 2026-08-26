"""Import individual creditor expense postings from supexpt.dbf."""

from apps.creditors.models import Creditor, ExpenseCategoryTransaction
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    open_dbf,
    to_date,
    to_decimal,
    to_int,
    to_str,
)
from apps.settings.models import ExpenseCategory


class Command(TenantAwareLegacyImportCommand):
    help = "Import individual creditor expense postings from supexpt.dbf"

    def run(self, **options):
        path = self.pdf_dir / "supexpt.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        categories = {
            c.number: c for c in ExpenseCategory.objects.using(self.db_alias).all()
        }
        creditors = {
            c.supplier_number: c for c in Creditor.objects.using(self.db_alias).all()
        }

        for record in open_dbf(path):
            category = categories.get(to_int(record.get("EXPCAT")))
            creditor = creditors.get(to_str(record.get("SUPNO")))
            transaction_number = to_str(record.get("TRANO"), 10)
            if category is None or creditor is None:
                self.skipped += 1
                continue

            value = to_decimal(record.get("VALUE"))
            invat = to_decimal(record.get("INVAT"))
            total = to_decimal(record.get("TOTAL")) or (value + invat)

            try:
                _, created = ExpenseCategoryTransaction.objects.using(
                    self.db_alias
                ).update_or_create(
                    expense_category=category,
                    creditor=creditor,
                    transaction_number=transaction_number,
                    transaction_date=to_date(record.get("DATE")),
                    defaults={
                        "amount_exclusive": value,
                        "tax_indicator": to_int(record.get("TAXIND")),
                        "source_type": to_str(record.get("SOURCE"), 2),
                        "grn_number": to_int(record.get("GRNNO"), default=None),
                        "input_vat_amount": invat,
                        "amount_inclusive": total,
                    },
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ {creditor.supplier_number}/{transaction_number}: {e}"
                    )
                )
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Expense transactions imported from {path.name}")
        )
