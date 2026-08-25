"""Import serial-number tracked items from serial_number.dbf."""
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_date, to_decimal, to_int, to_str
from apps.stock_control.models import SerializedStockItem, StockItem


class Command(TenantAwareLegacyImportCommand):
    help = 'Import serial-number tracked items from serial_number.dbf'

    def run(self, **options):
        path = self.pdf_dir / 'serial_number.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        stock_items = {s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            serial_number = to_str(record.get('SERIALNO'), 20)
            if not serial_number:
                self.skipped += 1
                continue

            defaults = {
                'stock_item': stock_items.get(to_str(record.get('CODE'), 13)),
                'item_detail': to_str(record.get('ITEMDETAIL'), 30),
                'transaction_date': to_date(record.get('DATE')),
                'transaction_type': to_str(record.get('TRANSTYPE'), 2),
                'transaction_number': to_int(record.get('TRANSNO'), default=None),
                'value': to_decimal(record.get('VALUE')),
                'warranty_period_months': to_int(record.get('WARRANTPER'), default=None),
                'comment1': to_str(record.get('COMMENT1'), 30),
                'comment2': to_str(record.get('COMMENT2'), 30),
                'comment3': to_str(record.get('COMMENT3'), 30),
                'comment4': to_str(record.get('COMMENT4'), 30),
                'customer_name': to_str(record.get('NAME'), 40),
                'address_line1': to_str(record.get('ADD1'), 25),
                'address_line2': to_str(record.get('ADD2'), 25),
                'address_line3': to_str(record.get('ADD3'), 25),
                'telephone': to_str(record.get('TEL'), 15),
                'email': to_str(record.get('EMAIL'), 50),
                'is_stolen': to_str(record.get('STOLEN')).upper() in ('Y', 'T', 'TRUE', '1'),
            }

            try:
                _, created = SerializedStockItem.objects.using(self.db_alias).update_or_create(
                    serial_number=serial_number, defaults=defaults
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Serial {serial_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Serial numbers imported from {path.name}'))
