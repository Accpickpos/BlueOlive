"""
Import the debtor (customer) master from the legacy dmast.dbf.

Debtor.save() calls full_clean(), which enforces a few business rules the
raw legacy data doesn't always satisfy — sanitized here rather than left to
crash the whole record:
  - vatref must be blank or exactly 10 digits (South African format)
  - price must be 1-3 (clamped, default 1)
  - acctype == 'C' (cash customer) must have dclimit == 0
"""

import re

from apps.debtors.models import Debtor
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    clean_email,
    open_dbf,
    to_decimal,
    to_int,
    to_str,
    translate_code,
)

_DIGITS_RE = re.compile(r"\D")

# Legacy BLOCKFLAG carries extra numeric codes (4/5/6) beyond the model's
# choices ('0'-'3', 'Y', 'N') — map unknown codes to '1' (Credit Hold), the
# conservative choice, rather than crash or silently leave the account active.
BLOCKFLAG_MAP = {str(i): str(i) for i in range(4)}
BLOCKFLAG_MAP.update({"Y": "Y", "N": "N"})


def clean_vatref(value):
    digits = _DIGITS_RE.sub("", to_str(value))
    return digits if len(digits) == 10 else ""


class Command(TenantAwareLegacyImportCommand):
    help = "Import the debtor (customer) master from dmast.dbf"

    def run(self, **options):
        path = self.pdf_dir / "dmast.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        for record in open_dbf(path):
            dno = to_int(record.get("DNO"), default=None)
            dname = to_str(record.get("DNAME"), 100)
            if dno is None or not dname:
                self.skipped += 1
                continue

            price = to_int(record.get("PRICE"), 1)
            if price not in (1, 2, 3):
                price = 1

            acctype = to_str(record.get("ACCTYPE"), 1)
            dclimit = to_decimal(record.get("DCLIMIT"))
            if acctype == "C":
                dclimit = 0

            defaults = {
                "dname": dname,
                "dsname": to_str(record.get("DSNAME"), 20),
                "dcontact": to_str(record.get("DCONTACT"), 50),
                "dtel": to_str(record.get("DTEL"), 20),
                "dtel2": to_str(record.get("TEL2"), 20),
                "dfax": to_str(record.get("DFAX"), 20),
                "email": clean_email(record.get("EMAIL")),
                "address_line1": to_str(record.get("DADD1"), 100),
                "address_line2": to_str(record.get("DADD2"), 100),
                "address_line3": to_str(record.get("DADD3"), 100),
                "postal_code": to_str(record.get("DPCODE"), 10),
                "delivery_address1": to_str(record.get("DELAD1"), 100),
                "delivery_address2": to_str(record.get("DELAD2"), 100),
                "delivery_address3": to_str(record.get("DELAD3"), 100),
                "delivery_address4": to_str(record.get("DELAD4"), 100),
                "dtaxno": to_str(record.get("DTAXNO"), 30),
                "vatref": clean_vatref(record.get("VATREF")),
                "darea": to_int(record.get("DAREA"), default=None),
                "acctype": acctype,
                "price": price,
                "terms": to_int(record.get("TERMS"), 30),
                "ddiscper": to_decimal(record.get("DDISCPER")),
                "pdisc": to_decimal(record.get("PDISC")),
                "discount_printable": (
                    "Y" if to_str(record.get("DISCPRN")).upper() == "Y" else "N"
                ),
                "dclimit": dclimit,
                "blockflag": (
                    translate_code(
                        self,
                        record.get("BLOCKFLAG"),
                        BLOCKFLAG_MAP,
                        "1",
                        context=f"dmast.dbf BLOCKFLAG (debtor {dno})",
                    )
                    if to_str(record.get("BLOCKFLAG"))
                    else "0"
                ),
                "dintflag": (
                    "Y" if to_str(record.get("DINTFLAG")).upper() == "Y" else "N"
                ),
                "dposbal": "N" if to_str(record.get("DPOSBAL")).upper() == "N" else "Y",
                "dbalbfwd": to_decimal(record.get("DBALBFWD")),
                "dcrnt": to_decimal(record.get("DCRNT")),
                "d30": to_decimal(record.get("D30")),
                "d60": to_decimal(record.get("D60")),
                "d90": to_decimal(record.get("D90")),
                "d120": to_decimal(record.get("D120")),
                "d150": to_decimal(record.get("D150")),
                "d180": to_decimal(record.get("D180")),
                "dsalesm": to_decimal(record.get("DSALESM")),
                "dsalesy": to_decimal(record.get("DSALESY")),
                "dprofitm": to_decimal(record.get("DPROFITM")),
                "dprofity": to_decimal(record.get("DPROFITY")),
                "damtlpd": to_decimal(record.get("DAMTLPD")),
                "ddatlpd": record.get("DDATLPD") or None,
                "dateopened": record.get("DATEOPENED") or None,
                "notes": to_str(record.get("NOTES")),
            }

            try:
                _, created = Debtor.objects.using(self.db_alias).update_or_create(
                    dno=dno, defaults=defaults
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Debtor {dno}: {e}"))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f"  ✓ Debtors imported from {path.name}"))
