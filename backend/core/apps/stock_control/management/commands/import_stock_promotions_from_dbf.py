"""Import promotional pricing/messaging from stock_promo.dbf."""
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_date, to_decimal, to_int, to_str
from apps.settings.models import SalesDepartment
from apps.stock_control.models import StockItem, StockPromotion


class Command(TenantAwareLegacyImportCommand):
    help = 'Import promotional pricing/messaging from stock_promo.dbf'

    def run(self, **options):
        path = self.pdf_dir / 'stock_promo.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        stock_items = {s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()}
        departments = {d.number: d for d in SalesDepartment.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            stock_code = to_str(record.get('CODE'), 13)
            start_date = to_date(record.get('STARTDATE'))
            end_date = to_date(record.get('ENDDATE'))
            stock_item = stock_items.get(stock_code)
            if not stock_item or not start_date or not end_date:
                self.skipped += 1
                continue

            try:
                _, created = StockPromotion.objects.using(self.db_alias).update_or_create(
                    stock_item=stock_item, start_date=start_date, end_date=end_date,
                    defaults={
                        'department': departments.get(to_int(record.get('DEPT'), default=None)),
                        'basis': to_str(record.get('BASIS'), 1),
                        'amount': to_decimal(record.get('AMOUNT')),
                        'message_line1': to_str(record.get('MESSAGE1'), 40),
                        'message_line2': to_str(record.get('MESSAGE2'), 40),
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ {stock_code}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Stock promotions imported from {path.name}'))
