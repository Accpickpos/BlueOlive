"""
Import per-item stock movement history from the legacy stmove<code>.dbf
files (one file per stock item, filename encodes the stock code).
"""

from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    code_from_filename,
    open_dbf,
    parse_hhmm,
    parse_yyyymmdd,
    to_decimal,
    to_int,
    to_str,
)
from apps.stock_control.models import StockItem, StockMovementLedger


class Command(TenantAwareLegacyImportCommand):
    help = "Import per-item stock movement ledgers from stmove<code>.dbf files"

    def run(self, **options):
        paths = sorted(self.pdf_dir.glob("stmove*.dbf"))
        if not paths:
            self.stdout.write(self.style.WARNING("  ⚠ No stmove*.dbf files found"))
            return

        stock_items = {
            s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()
        }

        for path in paths:
            code = code_from_filename(path)
            stock_item = stock_items.get(code)
            if stock_item is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ {path.name}: no stock item for code {code!r}, skipping file"
                    )
                )
                self.skipped += 1
                continue

            for record in open_dbf(path):
                movement_date = parse_yyyymmdd(record.get("DATE"))
                if not movement_date:
                    self.skipped += 1
                    continue
                record_reference = to_str(record.get("RECORD"), 15) or None
                defaults = dict(
                    movement_time=parse_hhmm(record.get("TIME")),
                    movement_type=to_str(record.get("TYPE"), 2),
                    transaction_number=to_int(record.get("TRANO"), default=None),
                    details=to_str(record.get("DETAILS"), 30) or None,
                    quantity_in=to_decimal(record.get("QTYIN")),
                    quantity_out=to_decimal(record.get("QTYOUT")),
                    balance=to_decimal(record.get("BALANCE")),
                    brought_forward=to_decimal(record.get("BFWD")),
                    per_unit_cost=to_decimal(record.get("PERUNIT")),
                    supplier_details=to_str(record.get("SUPDETAILS"), 25) or None,
                )
                try:
                    if record_reference:
                        # RECORD is a natural dedup key when present — makes reruns idempotent.
                        _, created = StockMovementLedger.objects.using(
                            self.db_alias
                        ).update_or_create(
                            stock_item=stock_item,
                            record_reference=record_reference,
                            movement_date=movement_date,
                            defaults=defaults,
                        )
                        self.created += created
                        self.updated += not created
                    else:
                        StockMovementLedger.objects.using(self.db_alias).create(
                            stock_item=stock_item,
                            movement_date=movement_date,
                            record_reference=None,
                            **defaults,
                        )
                        self.created += 1
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠ {path.name}: {e}"))
                    self.errors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Stock movements imported from {len(paths)} stmove*.dbf files"
            )
        )
