"""Import creditor open-item audit trail from supoaud.dbf."""
from apps.creditors.models import Creditor, OpenItemAudit
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_date, to_decimal, to_int, to_str


class Command(TenantAwareLegacyImportCommand):
    help = 'Import creditor open-item audit trail from supoaud.dbf'

    def run(self, **options):
        path = self.pdf_dir / 'supoaud.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        creditors = {c.supplier_number: c for c in Creditor.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            creditor = creditors.get(to_str(record.get('SUPNO')))
            if creditor is None:
                self.skipped += 1
                continue

            try:
                OpenItemAudit.objects.using(self.db_alias).create(
                    creditor=creditor,
                    transaction_number=to_str(record.get('TRANO'), 10),
                    transaction_type=to_str(record.get('TYPE'), 2),
                    this_transaction_type=to_str(record.get('THISTYPE'), 2),
                    this_transaction_number=to_int(record.get('THISTRAN')),
                    transaction_date=to_date(record.get('DATE')),
                    amount=to_decimal(record.get('AMOUNT')),
                )
                self.created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ {creditor.supplier_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Creditor audit imported from {path.name}'))
