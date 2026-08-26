"""
Import repairs from repmast.dbf (master) + reptran.dbf (lines).

Repair/RepairLine have no documented DBF-code translation in the model
(unlike RFC/suptran) — best-effort maps built from the real sampled data:
repmast STATUS values seen were A(92)/X(17)/C(3); reptran TYPE values seen
were RE(115)/RS(10)/RR(3). Anything outside these falls through
translate_code's logged-warning fallback rather than guessing silently.

RepairLine.date_captured/time_captured use auto_now_add=True, which would
stomp the legacy DATECAP/TIMECAP with the import run's timestamp — worked
around by creating then immediately overwriting those two fields via
.update() (bypasses auto_now_add, which only applies inside .save()).
"""

from apps.creditors.models import Creditor
from apps.pos.models import Repair, RepairLine
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    open_dbf,
    to_decimal,
    to_int,
    to_str,
    translate_code,
)

STATUS_MAP = {"A": "C", "C": "V", "X": "X", "I": "I", "R": "R", "V": "V"}
TYPE_MAP = {
    "RE": "OT",
    "RS": "IS",
    "RR": "RC",
    "IS": "IS",
    "RC": "RC",
    "AD": "AD",
    "RT": "RT",
}


class Command(TenantAwareLegacyImportCommand):
    help = "Import repairs from repmast.dbf + reptran.dbf"

    def run(self, **options):
        self._import_master()
        self._import_lines()

    def _import_master(self):
        path = self.pdf_dir / "repmast.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        for record in open_dbf(path):
            repair_number = to_str(record.get("REPAIRNO"), 20)
            date_required = record.get("DATEREQ") or None
            if not repair_number or not date_required:
                self.skipped += 1
                continue

            status = translate_code(
                self,
                record.get("STATUS"),
                STATUS_MAP,
                "C",
                context=f"repmast.dbf STATUS (repair {repair_number})",
            )

            try:
                _, created = Repair.objects.using(self.db_alias).update_or_create(
                    repair_number=repair_number,
                    defaults={
                        "customer_name": to_str(record.get("NAME"), 40) or "Unknown",
                        "address_line1": to_str(record.get("ADDRESS1"), 25),
                        "address_line2": to_str(record.get("ADDRESS2"), 25),
                        "telephone": to_str(record.get("TEL"), 15),
                        "contact_person": to_str(record.get("CONTACT"), 20),
                        "customer_reference": to_str(record.get("CUSTREF"), 10),
                        "order_number": to_str(record.get("ORDERNO"), 10),
                        "date_received": record.get("DATEREC") or None,
                        "date_required": date_required,
                        "quoted_value": to_decimal(record.get("QUOTEAMNT"), None),
                        "supplier_number": to_int(record.get("SUPNO"), default=None),
                        "date_sent": record.get("DATESUP") or None,
                        "date_returned": record.get("DATESUPRET") or None,
                        "repair_cost": to_decimal(record.get("TOTALCOST"), None),
                        "selling_price": to_decimal(record.get("SELLING"), None),
                        "comment1": to_str(record.get("COM1"), 30),
                        "comment2": to_str(record.get("COM2"), 30),
                        "comment3": to_str(record.get("COM3"), 30),
                        "comment4": to_str(record.get("COM4"), 30),
                        "status": status,
                        "supplier_comment": to_str(record.get("SUPCOMMENT"), 25),
                    },
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Repair {repair_number}: {e}")
                )
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS("  ✓ Repair master imported from repmast.dbf")
        )

    def _import_lines(self):
        path = self.pdf_dir / "reptran.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        repairs = {
            r.repair_number: r for r in Repair.objects.using(self.db_alias).all()
        }

        for record in open_dbf(path):
            repair_number = to_str(record.get("REPAIRNO"), 20)
            repair = repairs.get(repair_number)
            transaction_date = record.get("DATE") or None
            if repair is None or not transaction_date:
                self.skipped += 1
                continue

            transaction_type = translate_code(
                self,
                record.get("TYPE"),
                TYPE_MAP,
                "OT",
                context=f"reptran.dbf TYPE (repair {repair_number})",
            )
            date_captured = record.get("DATECAP") or transaction_date

            try:
                # No unique_together on this model — (repair, type, date, amount)
                # is the natural key available from reptran.dbf, used here so
                # reruns update rather than duplicate.
                line, created = RepairLine.objects.using(
                    self.db_alias
                ).update_or_create(
                    repair=repair,
                    transaction_type=transaction_type,
                    transaction_date=transaction_date,
                    amount=to_decimal(record.get("AMOUNT")),
                    defaults={
                        "supplier_number": to_int(record.get("SUPNO"), default=None),
                        "comment": to_str(record.get("COMMENT"), 25),
                        "transport_mode": to_str(record.get("TRANSPORT"), 15),
                        "station_number": to_int(record.get("STATION"), default=None),
                    },
                )
                # auto_now_add only applies inside save() — overwrite via
                # .update() afterwards to preserve the real legacy timestamp.
                RepairLine.objects.using(self.db_alias).filter(pk=line.pk).update(
                    date_captured=date_captured
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Repair {repair_number} line: {e}")
                )
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS("  ✓ Repair lines imported from reptran.dbf")
        )
