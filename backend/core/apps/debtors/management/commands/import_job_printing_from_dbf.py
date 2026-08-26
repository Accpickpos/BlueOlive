"""Import job printing station config from jprint.dbf (DEFAULT field has no model equivalent, dropped)."""

from apps.debtors.models import JobPrinting
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_str


class Command(TenantAwareLegacyImportCommand):
    help = "Import job printing station config from jprint.dbf"

    def run(self, **options):
        path = self.pdf_dir / "jprint.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        for record in open_dbf(path):
            station = to_str(record.get("STANUM"), 2)
            if not station:
                self.skipped += 1
                continue

            try:
                _, created = JobPrinting.objects.using(self.db_alias).update_or_create(
                    station=station,
                    defaults={
                        "job_cards_station": to_str(record.get("JOBCARD"), 1),
                        "job_invoices_station": to_str(record.get("JOBINV"), 1),
                        "job_reports_station": to_str(record.get("JOBREPS"), 1),
                    },
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Station {station}: {e}"))
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Job printing config imported from {path.name}")
        )
