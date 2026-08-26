"""
Import the daily till/POS reconciliation history from the legacy
cf<DDMMYY>.dbf files (one per trading day, e.g. cf010224.dbf = 2024-02-01)
into the new DailyTillTransaction model. cfile.dbf/5cfile.dbf share the same
structure (current-period working files) and are imported the same way,
keyed off their own last-modified date since their filenames don't encode one.
"""

import re
from datetime import datetime

from apps.cash_book.models import DailyTillTransaction
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_int, to_str

_FILENAME_RE = re.compile(r"^cf(\d{2})(\d{2})(\d{2})$", re.IGNORECASE)


def trading_date_from_filename(path):
    match = _FILENAME_RE.match(path.stem)
    if not match:
        return None
    dd, mm, yy = match.groups()
    year = 2000 + int(yy)
    try:
        return datetime(year, int(mm), int(dd)).date()
    except ValueError:
        return None


class Command(TenantAwareLegacyImportCommand):
    help = "Import daily till history from cf<DDMMYY>.dbf (+ cfile.dbf/5cfile.dbf) into DailyTillTransaction"

    def run(self, **options):
        paths = sorted(self.pdf_dir.glob("cf??????.dbf"))
        extra_paths = [
            p
            for p in (self.pdf_dir / "cfile.dbf", self.pdf_dir / "5cfile.dbf")
            if p.exists()
        ]

        for path in paths:
            trading_date = trading_date_from_filename(path)
            if trading_date is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ {path.name}: unrecognised filename pattern, skipping"
                    )
                )
                self.skipped += 1
                continue
            self._import_file(path, trading_date)

        for path in extra_paths:
            with open(path, "rb") as f:
                header = f.read(3)
            # dBase header stores last-update date as YY MM DD (bytes 1-3)
            yy, mm, dd = header[0], header[1], header[2]
            try:
                trading_date = datetime(2000 + yy, mm, dd).date()
            except ValueError:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ {path.name}: could not derive trading date, skipping"
                    )
                )
                self.skipped += 1
                continue
            self._import_file(path, trading_date)

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Daily till history imported from {len(paths) + len(extra_paths)} file(s)"
            )
        )

    def _import_file(self, path, trading_date):
        for record in open_dbf(path):
            source = to_str(record.get("SOURCE"), 2)
            transaction_number = to_int(record.get("TRANO")) or 0

            try:
                _, created = DailyTillTransaction.objects.using(
                    self.db_alias
                ).update_or_create(
                    trading_date=trading_date,
                    transaction_number=transaction_number,
                    source=source,
                    defaults={
                        "cash_total": to_decimal(record.get("CASHDAY")),
                        "cheque_total": to_decimal(record.get("CHEQDAY")),
                        "card_total": to_decimal(record.get("CARDDAY")),
                        "invoice_total": to_decimal(record.get("INVTOT")),
                        "credit_note_total": to_decimal(record.get("CNOTETOT")),
                        "reconciliation_account_total": to_decimal(
                            record.get("RECONACC")
                        ),
                        "output_vat": to_decimal(record.get("OUTVAT")),
                        "input_vat": to_decimal(record.get("INVAT")),
                        "transaction_time": to_str(record.get("TIME"), 5),
                        "transaction_type": to_str(record.get("TYPE"), 2),
                        "change_given": to_decimal(record.get("CHANGE")),
                        "laybye_amount": to_decimal(record.get("LAYBYE")),
                        "comments": to_str(record.get("COMMENTS"), 75),
                        "speedpoint_total": to_decimal(record.get("SPEEDPOINT")),
                        "adjustment": to_decimal(record.get("ADJUST")),
                        "captured_by_user": to_str(record.get("USER"), 25),
                    },
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠ {path.name} ({trading_date}): {e}")
                )
                self.errors += 1
