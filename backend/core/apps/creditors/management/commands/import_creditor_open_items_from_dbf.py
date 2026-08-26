"""
Import creditor open items from supopen.dbf. Set is_legacy=True so
CreditorOpenItem.clean() doesn't require a typed GRN/Invoice/CreditNote/
Journal link (legacy rows only ever have a transaction_number/type, not one
of the app's own typed transaction objects).
"""

from apps.creditors.models import Creditor, CreditorOpenItem, SupplierLedgerEntry
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_date, to_decimal, to_str


class Command(TenantAwareLegacyImportCommand):
    help = "Import creditor open items from supopen.dbf"

    def run(self, **options):
        path = self.pdf_dir / "supopen.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        creditors = {
            c.supplier_number: c for c in Creditor.objects.using(self.db_alias).all()
        }

        for record in open_dbf(path):
            creditor = creditors.get(to_str(record.get("SUPNO")))
            transaction_number = to_str(record.get("TRANO"), 10)
            transaction_type = to_str(record.get("TYPE"), 2)
            if creditor is None or not transaction_number:
                self.skipped += 1
                continue

            ledger_entry = (
                SupplierLedgerEntry.objects.using(self.db_alias)
                .filter(creditor=creditor, transaction_number=transaction_number)
                .first()
            )

            try:
                _, created = CreditorOpenItem.objects.using(
                    self.db_alias
                ).update_or_create(
                    creditor=creditor,
                    transaction_number=transaction_number,
                    transaction_type=transaction_type,
                    defaults={
                        "transaction_date": to_date(record.get("DATE")),
                        "original_amount": to_decimal(record.get("TOTAL")),
                        "balance_due": to_decimal(record.get("BALANCEDUE")),
                        "ageing_flag": to_str(record.get("AGEFLAG"), 1),
                        "is_fully_allocated": to_decimal(record.get("BALANCEDUE")) <= 0,
                        "is_legacy": True,
                        "ledger_entry": ledger_entry,
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
            self.style.SUCCESS(f"  ✓ Creditor open items imported from {path.name}")
        )
