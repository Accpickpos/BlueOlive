"""Import cashbook transactions (cbtran.dbf) and unpresented cheques (cbcheq.dbf)."""

import calendar
from datetime import date

from apps.cash_book.models import CashBookTransaction, UnpresentedCheque
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    open_dbf,
    to_decimal,
    to_int,
    to_str,
    translate_code,
)

TYPE_MAP = {
    "I": "RECEIPT",
    "R": "RECEIPT",
    "P": "PAYMENT",
    "D": "DEPOSIT",
    "W": "WITHDRAWAL",
    "T": "TRANSFER",
    "B": "BANK_CHARGE",
}
TAG_MAP = {"R": "R", "P": "P", "D": "D", "U": "U"}


class Command(TenantAwareLegacyImportCommand):
    help = "Import cashbook transactions from cbtran.dbf and unpresented cheques from cbcheq.dbf"

    def run(self, **options):
        self._import_transactions()
        self._import_cheques()

    def _import_transactions(self):
        path = self.pdf_dir / "cbtran.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        for record in open_dbf(path):
            transaction_number = to_str(record.get("CBTRANO"), 20)
            transaction_date = record.get("DATE") or None
            if not transaction_number or not transaction_date:
                self.skipped += 1
                continue

            transaction_type = translate_code(
                self,
                record.get("TYPE"),
                TYPE_MAP,
                "RECEIPT",
                context=f"cbtran.dbf TYPE (txn {transaction_number})",
            )
            value = to_decimal(record.get("VALUE"))
            tax = to_decimal(record.get("TAX"))
            total = to_decimal(record.get("TOTAL")) or (value + tax)
            reference = to_str(record.get("CBREF"), 20)

            try:
                _, created = CashBookTransaction.objects.using(
                    self.db_alias
                ).update_or_create(
                    transaction_number=transaction_number,
                    defaults={
                        "transaction_type": transaction_type,
                        "transaction_date": transaction_date,
                        "amount": abs(total) or (abs(value) + abs(tax)),
                        "category_id": to_int(record.get("CATNO"), default=None),
                        "audit_type": to_int(record.get("CBAUDIT")) or 2,
                        "bank_recon_tag": translate_code(
                            self,
                            record.get("CBTAG"),
                            TAG_MAP,
                            "U",
                            context=f"cbtran.dbf CBTAG (txn {transaction_number})",
                        ),
                        "reference": reference,
                        "description": reference
                        or f"{transaction_type} {transaction_number}",
                        "value_excl_vat": value,
                        "tax_amount": tax,
                        "total_incl_vat": total,
                    },
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ CB txn {transaction_number}: {e}")
                )
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS("  ✓ Cashbook transactions imported from cbtran.dbf")
        )

    def _import_cheques(self):
        path = self.pdf_dir / "cbcheq.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        for record in open_dbf(path):
            cheque_number = to_str(record.get("CBTRANO"), 6)
            cheque_date = record.get("DATE") or None
            if not cheque_number or not cheque_date:
                self.skipped += 1
                continue

            value = to_decimal(record.get("VALUE"))
            total = to_decimal(record.get("TOTAL")) or value
            if total < value:
                total = value
            last_day = calendar.monthrange(cheque_date.year, cheque_date.month)[1]
            month_end_date = date(cheque_date.year, cheque_date.month, last_day)

            try:
                _, created = UnpresentedCheque.objects.using(
                    self.db_alias
                ).update_or_create(
                    cheque_number=cheque_number,
                    defaults={
                        "cheque_date": cheque_date,
                        "reference": to_str(record.get("CBREF"), 20),
                        "value": value,
                        "total": total,
                        "tag": translate_code(
                            self,
                            record.get("CBTAG"),
                            TAG_MAP,
                            "U",
                            context=f"cbcheq.dbf CBTAG (cheque {cheque_number})",
                        ),
                        "month_end_date": month_end_date,
                    },
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ Cheque {cheque_number}: {e}")
                )
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS("  ✓ Unpresented cheques imported from cbcheq.dbf")
        )
