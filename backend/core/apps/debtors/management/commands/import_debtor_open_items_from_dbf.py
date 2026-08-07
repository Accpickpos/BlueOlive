"""
Import debtor open items from debtopen.dbf into debtors.DebtorOpenItem
(chosen over the raw-mirror debtors.Debtopen per user decision — shares the
same underlying 'debtopen' table and adds due_date/fully_paid conveniences).
"""
from apps.debtors.models import Debtor, DebtorOpenItem
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_int, to_str

AGE_FLAG_MAP = {'0': '0', '1': '1', '2': '2', '3': '3', '4': '4'}
TYPE_MAP = {t: t for t in ('IN', 'CN', 'PY', 'JD', 'JC', 'DM', 'CM')}


class Command(TenantAwareLegacyImportCommand):
    help = 'Import debtor open items from debtopen.dbf into DebtorOpenItem'

    def run(self, **options):
        path = self.pdf_dir / 'debtopen.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        debtors = {d.dno: d for d in Debtor.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            dno = to_int(record.get('DNO'), default=None)
            debtor = debtors.get(dno)
            transaction_number = to_str(record.get('DTRANO'), 6)
            transaction_date = record.get('DATE') or None
            if debtor is None or not transaction_number or not transaction_date:
                self.skipped += 1
                continue

            transaction_type = TYPE_MAP.get(to_str(record.get('TYPE'), 2), 'IN')
            original_amount = to_decimal(record.get('TOTAL'))
            balance_due = min(to_decimal(record.get('BALANCEDUE')), original_amount)

            try:
                _, created = DebtorOpenItem.objects.using(self.db_alias).update_or_create(
                    debtor=debtor, transaction_number=transaction_number,
                    defaults={
                        'transaction_type': transaction_type,
                        'transaction_date': transaction_date,
                        'original_amount': original_amount,
                        'balance_due': balance_due,
                        'age_flag': AGE_FLAG_MAP.get(to_str(record.get('AGEFLAG')), '0'),
                        'posted': to_str(record.get('POSTED'), 10) or 'Y',
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Debtor {dno}/{transaction_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Debtor open items imported from {path.name}'))
