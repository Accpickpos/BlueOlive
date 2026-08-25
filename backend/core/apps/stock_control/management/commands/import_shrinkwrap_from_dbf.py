"""Import bulk/shrink pack relationships from shrink.dbf/shrin5.dbf."""
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_str
from apps.stock_control.models import ShrinkWrap, StockItem


class Command(TenantAwareLegacyImportCommand):
    help = 'Import bulk/shrink pack relationships from shrink.dbf/shrin5.dbf'

    def run(self, **options):
        stock_items = {s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()}

        for filename in ('shrink.dbf', 'shrin5.dbf'):
            path = self.pdf_dir / filename
            if not path.exists():
                self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
                continue

            for record in open_dbf(path):
                scode = to_str(record.get('SCODE'), 13)
                bcode = to_str(record.get('BCODE'), 13)
                if not scode or not bcode:
                    self.skipped += 1
                    continue

                shrink_item = stock_items.get(scode)
                bulk_item = stock_items.get(bcode)
                if shrink_item is None or bulk_item is None:
                    self.stdout.write(self.style.WARNING(
                        f'  ⚠ {filename}: no StockItem for {scode!r}/{bcode!r}, skipping'
                    ))
                    self.skipped += 1
                    continue

                try:
                    _, created = ShrinkWrap.objects.using(self.db_alias).update_or_create(
                        shrink_pack_code=shrink_item, bulk_pack_code=bulk_item,
                        defaults={'invoice_bulk_value': to_decimal(record.get('SINBULK')) or 1}
                    )
                    self.created += created
                    self.updated += not created
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ⚠ {scode}/{bcode}: {e}'))
                    self.errors += 1

            self.stdout.write(self.style.SUCCESS(f'  ✓ Shrink wraps imported from {filename}'))
