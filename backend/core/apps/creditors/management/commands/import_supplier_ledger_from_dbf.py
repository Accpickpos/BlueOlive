"""Import supplier ledger entries from suptran.dbf (raw creditor ledger mirror)."""

from apps.creditors.models import Creditor, SupplierLedgerEntry
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    open_dbf,
    to_date,
    to_decimal,
    to_int,
    to_str,
)


class Command(TenantAwareLegacyImportCommand):
    help = "Import supplier ledger entries from suptran.dbf"

    def run(self, **options):
        path = self.pdf_dir / "suptran.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        creditors = {
            c.supplier_number: c for c in Creditor.objects.using(self.db_alias).all()
        }

        for record in open_dbf(path):
            creditor = creditors.get(to_str(record.get("SUPNO")))
            transaction_number = to_str(record.get("STRANO"), 10)
            if creditor is None or not transaction_number:
                self.skipped += 1
                continue

            try:
                _, created = SupplierLedgerEntry.objects.using(
                    self.db_alias
                ).update_or_create(
                    creditor=creditor,
                    transaction_number=transaction_number,
                    defaults={
                        "transaction_date": to_date(record.get("STDATE")),
                        "due_date": to_date(record.get("SDUEDATE")),
                        "transaction_type": to_str(record.get("STYPE"), 2),
                        "subtotal": to_decimal(record.get("STSUB")),
                        "vat_amount": to_decimal(record.get("STGST")),
                        "total_amount": to_decimal(record.get("STTOT")),
                        "reference": to_str(record.get("STREF"), 20),
                        "grn_number": to_int(record.get("GRNNO"), default=None),
                        "station": to_str(record.get("STATION"), 2),
                        "created_by_user": to_str(record.get("USER"), 20),
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
            self.style.SUCCESS(f"  ✓ Supplier ledger imported from {path.name}")
        )
