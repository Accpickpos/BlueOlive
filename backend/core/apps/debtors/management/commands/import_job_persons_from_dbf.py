"""Import job operators from jperson.dbf."""
from apps.debtors.models import JobPerson
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_str


class Command(TenantAwareLegacyImportCommand):
    help = 'Import job operators from jperson.dbf'

    def run(self, **options):
        path = self.pdf_dir / 'jperson.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        for record in open_dbf(path):
            operator_number = to_str(record.get('NUMBER'), 10)
            name = to_str(record.get('NAME'), 20)
            if not operator_number or not name:
                self.skipped += 1
                continue

            try:
                _, created = JobPerson.objects.using(self.db_alias).update_or_create(
                    operator_number=operator_number, defaults={'operator_name': name}
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Operator {operator_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Job operators imported from {path.name}'))
