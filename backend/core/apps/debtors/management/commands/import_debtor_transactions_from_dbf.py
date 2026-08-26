"""
Import debtor transaction headers from dtran.dbf/dtran3.dbf.

DebtorTransaction.save() calls full_clean(), enforcing: subtotal+vat ≈
total (within 0.01), and credit-type transactions (CN/CR/RF) must have a
negative total. Legacy DTYPE is a shorter/different code set than the
model's 2-3 char TRANSACTION_TYPE_CHOICES — translated via DTYPE_MAP, with
sign correction applied afterwards for credit types.
"""

from apps.debtors.models import Debtor, DebtorTransaction
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    open_dbf,
    parse_hhmm,
    to_decimal,
    to_int,
    to_str,
    translate_code,
)

DTYPE_MAP = {
    "I": "IN",
    "IN": "IN",
    "CN": "CN",
    "C": "CN",
    "CS": "CS",
    "CR": "CR",
    "P": "PM",
    "PM": "PM",
    "RCP": "RCP",
    "R": "RCP",
    "INT": "INT",
    "JD": "JD",
    "JC": "JC",
    "RF": "RF",
}
CREDIT_TYPES = {"CN", "CR", "RF"}
VAT_STATUS_MAP = {"S": "S", "E": "E", "Z": "Z", "1": "S", "0": "Z"}


class Command(TenantAwareLegacyImportCommand):
    help = "Import debtor transaction headers from dtran.dbf/dtran3.dbf"

    def run(self, **options):
        debtors = {d.dno: d for d in Debtor.objects.using(self.db_alias).all()}

        for filename in ("dtran.dbf", "dtran3.dbf"):
            path = self.pdf_dir / filename
            if not path.exists():
                self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
                continue

            for record in open_dbf(path):
                dno = to_int(record.get("DNO"), default=None)
                debtor = debtors.get(dno)
                transaction_number = to_str(record.get("DTRANO"), 6)
                transaction_date = record.get("DTDATE") or None
                if debtor is None or not transaction_number or not transaction_date:
                    self.skipped += 1
                    continue

                transaction_type = translate_code(
                    self,
                    record.get("DTYPE"),
                    DTYPE_MAP,
                    "IN",
                    context=f"{filename} DTYPE (debtor {dno})",
                )
                subtotal = to_decimal(record.get("DTSUB"))
                vat_amount = to_decimal(record.get("DTGST"))
                total_amount = to_decimal(record.get("DTTOT")) or (
                    subtotal + vat_amount
                )

                if transaction_type in CREDIT_TYPES:
                    subtotal, vat_amount, total_amount = (
                        -abs(subtotal),
                        -abs(vat_amount),
                        -abs(total_amount),
                    )
                else:
                    subtotal, vat_amount, total_amount = (
                        abs(subtotal),
                        abs(vat_amount),
                        abs(total_amount),
                    )

                vat_status = VAT_STATUS_MAP.get(to_str(record.get("DTAXSTAT")), "S")

                try:
                    _, created = DebtorTransaction.objects.using(
                        self.db_alias
                    ).update_or_create(
                        debtor=debtor,
                        transaction_number=transaction_number,
                        transaction_date=transaction_date,
                        defaults={
                            "transaction_type": transaction_type,
                            "transaction_time": parse_hhmm(record.get("TIME")),
                            "subtotal": subtotal,
                            "vat_amount": vat_amount,
                            "total_amount": total_amount,
                            "vat_status": vat_status,
                            "source_station": to_int(record.get("SOURCE")) or 0,
                            "order_number": to_str(record.get("ORDNO"), 10),
                            "customer_reference": to_str(record.get("CUSTREF"), 10),
                            "description_line1": to_str(record.get("DEL1"), 100),
                            "description_line2": to_str(record.get("DEL2"), 100),
                            "description_line3": to_str(record.get("DEL3"), 100),
                            "description_line4": to_str(record.get("DEL4"), 100),
                            "station": to_str(record.get("STATION"), 5),
                            "vat_reference": to_str(record.get("VATREF"), 10),
                            "source_type": "IMPORT",
                        },
                    )
                    self.created += created
                    self.updated += not created
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ Debtor {dno}/{transaction_number}: {e}"
                        )
                    )
                    self.errors += 1

            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Debtor transactions imported from {filename}")
            )
