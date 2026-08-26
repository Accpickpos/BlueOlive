"""
Import workshop job costing cards from jmast.dbf/jtran.dbf into
debtors.JobCosting/JobCostingTransaction (per user decision — not
pos.JobCard, which is a separate forward-going concept). The quote-tracking
sub-fields on jmast.dbf (QUOTE_REQ/QUOTE_DATE/QUOTENO/QUOTE_VAL/etc.) have
no corresponding field on JobCosting and are dropped.
"""

from decimal import Decimal

from apps.debtors.models import Debtor, JobCosting, JobCostingTransaction
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    open_dbf,
    to_decimal,
    to_int,
    to_str,
    translate_code,
)

STATUS_MAP = {"A": "A", "C": "C", "D": "D"}


class Command(TenantAwareLegacyImportCommand):
    help = "Import workshop job costing cards from jmast.dbf/jtran.dbf"

    def run(self, **options):
        self._import_master()
        self._import_lines()

    def _import_master(self):
        path = self.pdf_dir / "jmast.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        debtors = {d.dno: d for d in Debtor.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            job_number = to_str(record.get("JOBNO"), 6)
            job_date = record.get("DATE") or None
            if not job_number or not job_date:
                self.skipped += 1
                continue

            status = translate_code(
                self,
                record.get("STATUS"),
                STATUS_MAP,
                "A",
                context=f"jmast.dbf STATUS (job {job_number})",
            )
            completion_date = record.get("COMPLDATE") or None
            if status == "D" and not completion_date:
                completion_date = job_date

            defaults = {
                "time_start": to_str(record.get("TIMESTART"), 5),
                "customer_name": to_str(record.get("NAME"), 40) or "Unknown",
                "address_line1": to_str(record.get("ADD1"), 25),
                "address_line2": to_str(record.get("ADD2"), 25),
                "address_line3": to_str(record.get("ADD3"), 25),
                "order_number": to_str(record.get("ORDERNO"), 10),
                "vehicle_registration": to_str(record.get("REGNO"), 10),
                "vehicle_make_model": to_str(record.get("MAKEMODEL"), 15),
                "odometer_reading": to_int(record.get("KMS"), default=None),
                "telephone": to_str(record.get("TEL"), 25),
                "contact_person": to_str(record.get("CONTACT"), 20),
                "status": status,
                "total_value": to_decimal(record.get("TOTAL")),
                "salesman_number": to_int(record.get("SALESMAN"), default=None),
                "station_number": to_int(record.get("STANUM"), default=None),
                "debtor": debtors.get(to_int(record.get("DNO"), default=None)),
                "completion_date": completion_date,
                "time_completed": to_str(record.get("TIMECOMPL"), 5),
                "amount_charged": min(
                    to_decimal(record.get("CHARGEAMNT")),
                    to_decimal(record.get("TOTAL")) or Decimal("999999999"),
                ),
                "transaction_number": to_int(record.get("TRANO"), default=None),
                "transaction_type": to_str(record.get("TRANTYPE"), 1),
                "station_completion": to_str(record.get("STANUMCOMP"), 2),
                "operator_number": to_str(record.get("OPERATOR"), 10),
                "comment_line1": to_str(record.get("COMMENT1"), 30),
                "comment_line2": to_str(record.get("COMMENT2"), 30),
                "comment_line3": to_str(record.get("COMMENT3"), 30),
                "comment_line4": to_str(record.get("COMMENT4"), 30),
            }

            try:
                _, created = JobCosting.objects.using(self.db_alias).update_or_create(
                    job_number=job_number, defaults={**defaults, "job_date": job_date}
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Job {job_number}: {e}"))
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS("  ✓ Job costing master imported from jmast.dbf")
        )

    def _import_lines(self):
        path = self.pdf_dir / "jtran.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        job_costings = {
            j.job_number: j for j in JobCosting.objects.using(self.db_alias).all()
        }

        for record in open_dbf(path):
            job_number = to_str(record.get("JOBNO"), 6)
            job_costing = job_costings.get(job_number)
            transaction_date = record.get("DATE") or None
            if job_costing is None or not transaction_date:
                self.skipped += 1
                continue

            try:
                JobCostingTransaction.objects.using(self.db_alias).create(
                    job_costing=job_costing,
                    code=to_str(record.get("CODE"), 13),
                    quantity=to_decimal(record.get("QTY")) or 1,
                    selling_price=to_decimal(record.get("SPRICE")),
                    discount=min(to_decimal(record.get("DISC")), 100),
                    cost_price=to_decimal(record.get("COST")),
                    department=to_str(record.get("DEPT"), 3),
                    tax_code=to_str(record.get("TAXIND"), 1),
                    comments=to_str(record.get("COMMENTS"), 30),
                    transaction_date=transaction_date,
                )
                self.created += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Job {job_number} line: {e}"))
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS("  ✓ Job costing lines imported from jtran.dbf")
        )
