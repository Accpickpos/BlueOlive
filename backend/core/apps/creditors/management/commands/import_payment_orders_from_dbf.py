"""
Import scheduled supplier payment orders from suppo.dbf. This file has no
SUPNO field, so creditor stays null on every legacy row (matches the
model's own documented behaviour).
"""

from apps.creditors.models import SupplierPaymentOrder
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_date, to_decimal, to_str


class Command(TenantAwareLegacyImportCommand):
    help = "Import scheduled supplier payment orders from suppo.dbf"

    def run(self, **options):
        path = self.pdf_dir / "suppo.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        for record in open_dbf(path):
            payment_date = to_date(record.get("DATE"))
            amount = to_decimal(record.get("AMOUNT"))
            if not payment_date or amount <= 0:
                self.skipped += 1
                continue

            try:
                SupplierPaymentOrder.objects.using(self.db_alias).create(
                    payment_date=payment_date,
                    amount=amount,
                    detail_line1=to_str(record.get("DETAIL1"), 25),
                    detail_line2=to_str(record.get("DETAIL2"), 25),
                    detail_line3=to_str(record.get("DETAIL3"), 25),
                )
                self.created += 1
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ payment order {payment_date}: {e}")
                )
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Payment orders imported from {path.name}")
        )
