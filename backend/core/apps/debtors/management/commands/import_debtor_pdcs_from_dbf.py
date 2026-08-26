"""Import post-dated cheques from dpdc.dbf."""

from apps.debtors.models import Debtor, Dpdc
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_int, to_str

STATUS_MAP = {"O": "OUTSTANDING", "R": "RECEIVED", "C": "CLEARED", "D": "DISHONOURED"}


class Command(TenantAwareLegacyImportCommand):
    help = "Import post-dated cheques from dpdc.dbf"

    def run(self, **options):
        path = self.pdf_dir / "dpdc.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        debtors = {d.dno: d for d in Debtor.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            dno = to_int(record.get("DNO"), default=None)
            debtor = debtors.get(dno)
            date = record.get("DATE") or None
            amount = to_decimal(record.get("AMOUNT"))
            if debtor is None or not date or amount <= 0:
                self.skipped += 1
                continue

            status_raw = to_str(record.get("STATUS"))
            status = STATUS_MAP.get(status_raw, "OUTSTANDING")

            try:
                Dpdc.objects.using(self.db_alias).create(
                    dno=debtor,
                    date=date,
                    amount=amount,
                    status=status,
                )
                self.created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Debtor {dno} PDC: {e}"))
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Post-dated cheques imported from {path.name}")
        )
