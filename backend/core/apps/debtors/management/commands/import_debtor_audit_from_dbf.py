"""Import the debtor audit trail from debtoaud.dbf."""
from apps.debtors.models import Debtor, DebtorAudit
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_int, to_str, translate_code

TYPE_MAP = {t: t for t in ('IN', 'CR', 'PA', 'AD', 'DM', 'CM', 'AL')}


class Command(TenantAwareLegacyImportCommand):
    help = 'Import the debtor audit trail from debtoaud.dbf'

    def run(self, **options):
        path = self.pdf_dir / 'debtoaud.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        debtors = {d.dno: d for d in Debtor.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            dno = to_int(record.get('DNO'), default=None)
            debtor = debtors.get(dno)
            transaction_date = record.get('DATE') or None
            if debtor is None or not transaction_date:
                self.skipped += 1
                continue

            type_code = translate_code(self, record.get('TYPE'), TYPE_MAP, 'AD', context=f'debtoaud.dbf TYPE (debtor {dno})')
            this_type = translate_code(self, record.get('THISTYPE'), TYPE_MAP, type_code, context=f'debtoaud.dbf THISTYPE (debtor {dno})')

            try:
                _, created = DebtorAudit.objects.using(self.db_alias).update_or_create(
                    dno=debtor, dtrano=to_str(record.get('DTRANO'), 6), date=transaction_date,
                    defaults={
                        'type': type_code,
                        'thistype': this_type,
                        'thistran': to_str(record.get('THISTRAN'), 6),
                        'amount': abs(to_decimal(record.get('AMOUNT'))),
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Debtor {dno} audit: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Debtor audit imported from {path.name}'))
