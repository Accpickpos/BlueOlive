"""Import staged/pending price updates from prupdate.dbf."""
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, parse_ddmmyy, to_decimal, to_str
from apps.stock_control.models import StagedPriceUpdate, StockItem


class Command(TenantAwareLegacyImportCommand):
    help = 'Import staged/pending price updates from prupdate.dbf'

    def run(self, **options):
        path = self.pdf_dir / 'prupdate.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        stock_items = {s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            stock_code = to_str(record.get('STOCKCODE'), 13)
            if not stock_code:
                self.skipped += 1
                continue

            effective_date = parse_ddmmyy(record.get('EFFECTDATE'))
            defaults = {
                'stock_item': stock_items.get(stock_code),
                'supplier_name': to_str(record.get('SUPNAME'), 30),
                'department_name': to_str(record.get('DEPARTMENT'), 20),
                'description': to_str(record.get('DESCRIP'), 30),
                'unit_of_measure': to_str(record.get('UNITOFMEAS'), 10),
                'cost_price': to_decimal(record.get('COST')),
                'sell_price_1': to_decimal(record.get('SELL1')),
                'sell_price_2': to_decimal(record.get('SELL2')),
                'sell_price_3': to_decimal(record.get('SELL3')),
            }

            try:
                # (stock_code, effective_date) is always available — unlike
                # stock_item, which is often None for discontinued codes —
                # so it's the key used here to make reruns idempotent.
                _, created = StagedPriceUpdate.objects.using(self.db_alias).update_or_create(
                    stock_code=stock_code, effective_date=effective_date, defaults=defaults
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ {stock_code}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Staged price updates imported from {path.name}'))
