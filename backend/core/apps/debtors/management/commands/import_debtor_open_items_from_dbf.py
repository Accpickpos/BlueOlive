"""
Import debtor open items from debtopen.dbf into debtors.Debtopen.

CORRECTED during the Debtors module behavior audit (2026): this previously
targeted debtors.DebtorOpenItem, chosen at the time because it shares the
'debtopen' table and adds due_date/fully_paid conveniences. Auditing the
live app's actual open-item code (DebtorService.post_debtran,
DebtopenViewSet, DebtopenSerializer) showed it exclusively reads/writes
Debtopen — DebtorOpenItem is never referenced anywhere in views.py,
services.py, or serializers.py. Data imported into DebtorOpenItem would be
invisible to every enquiry/allocation/aging screen in the app. No real data
was lost by the original choice (debtopen.dbf has 0 live records in the
current pdf/ export), but the importer itself needed correcting before a
fuller export is ever run against it.
"""

from apps.debtors.models import Debtopen, Debtor
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_int, to_str

TYPE_MAP = {t: t for t in ("IN", "CN", "PY", "JD", "JC", "DM", "CM")}


class Command(TenantAwareLegacyImportCommand):
    help = "Import debtor open items from debtopen.dbf into Debtopen"

    def run(self, **options):
        path = self.pdf_dir / "debtopen.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        debtors = {d.dno: d for d in Debtor.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            dno = to_int(record.get("DNO"), default=None)
            debtor = debtors.get(dno)
            dtrano = to_str(record.get("DTRANO"), 6)
            transaction_date = record.get("DATE") or None
            if debtor is None or not dtrano or not transaction_date:
                self.skipped += 1
                continue

            transaction_type = TYPE_MAP.get(to_str(record.get("TYPE"), 2), "IN")
            total = to_decimal(record.get("TOTAL"))
            balancedue = min(to_decimal(record.get("BALANCEDUE")), total)

            try:
                _, created = Debtopen.objects.using(self.db_alias).update_or_create(
                    dno=debtor,
                    dtrano=dtrano,
                    defaults={
                        "type": transaction_type,
                        "date": transaction_date,
                        "total": total,
                        "balancedue": balancedue,
                        "ageflag": to_str(record.get("AGEFLAG"), 1) or "0",
                        "posted": to_str(record.get("POSTED"), 10) or "Y",
                    },
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Debtor {dno}/{dtrano}: {e}"))
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Debtor open items imported from {path.name}")
        )
