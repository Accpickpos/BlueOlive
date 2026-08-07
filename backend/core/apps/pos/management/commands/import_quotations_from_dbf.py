"""
Import quotations from qmast.dbf (master) + qtran.dbf (lines).
QuotationLine.description is required with no direct DBF source in
qtran.dbf (only CODE) — looked up from the matching StockItem, falling back
to the stock code itself if not found.
"""
from apps.debtors.models import Debtor
from apps.pos.models import Quotation, QuotationLine
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_int, to_str, translate_code
from apps.stock_control.models import StockItem

STATUS_MAP = {'A': 'ACTIVE', 'I': 'INVOICED', 'X': 'CANCELLED', 'E': 'EXPIRED', 'J': 'JOB'}


class Command(TenantAwareLegacyImportCommand):
    help = 'Import quotations from qmast.dbf + qtran.dbf'

    def run(self, **options):
        self._import_master()
        self._import_lines()

    def _import_master(self):
        path = self.pdf_dir / 'qmast.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        debtors = {d.dno: d for d in Debtor.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            quotation_number = to_str(record.get('QUOTENO'), 20)
            quotation_date = record.get('DATE') or None
            expiry_date = record.get('EXPDATE') or None
            if not quotation_number or not quotation_date or not expiry_date:
                self.skipped += 1
                continue

            status = translate_code(
                self, record.get('STATUS'), STATUS_MAP, 'ACTIVE', context=f'qmast.dbf STATUS (quote {quotation_number})'
            )

            try:
                _, created = Quotation.objects.using(self.db_alias).update_or_create(
                    quotation_number=quotation_number,
                    defaults={
                        'quotation_date': quotation_date,
                        'expiry_date': expiry_date,
                        'customer_name': to_str(record.get('NAME'), 200) or 'Unknown',
                        'address_line1': to_str(record.get('ADD1'), 25),
                        'address_line2': to_str(record.get('ADD2'), 25),
                        'address_line3': to_str(record.get('ADD3'), 25),
                        'telephone': to_str(record.get('TEL'), 15),
                        'debtor_account': debtors.get(to_int(record.get('DNO'), default=None)),
                        'station_number': to_int(record.get('STANUM')) or 1,
                        'comment1': to_str(record.get('COMMENT1'), 30),
                        'comment2': to_str(record.get('COMMENT2'), 30),
                        'total_amount': to_decimal(record.get('TOTAL')),
                        'status': status,
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Quote {quotation_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS('  ✓ Quotation master imported from qmast.dbf'))

    def _import_lines(self):
        path = self.pdf_dir / 'qtran.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        quotations = {q.quotation_number: q for q in Quotation.objects.using(self.db_alias).all()}
        stock_items = {s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()}
        line_counters = {}

        for record in open_dbf(path):
            quotation_number = to_str(record.get('QUOTENO'), 20)
            quotation = quotations.get(quotation_number)
            if quotation is None:
                self.skipped += 1
                continue

            stock_code = to_str(record.get('CODE'), 13)
            stock_item = stock_items.get(stock_code)
            description = stock_item.description if stock_item else (stock_code or 'Unknown item')

            line_counters[quotation_number] = line_counters.get(quotation_number, 0) + 1

            try:
                _, created = QuotationLine.objects.using(self.db_alias).update_or_create(
                    quotation=quotation, line_number=line_counters[quotation_number],
                    defaults={
                        'stock_code': stock_code,
                        'description': description,
                        'quantity': to_decimal(record.get('QTY')) or 1,
                        'unit_price': to_decimal(record.get('SPRICE')),
                        'discount_percentage': min(to_decimal(record.get('DISC')), 100),
                        'cost_price': to_decimal(record.get('COST')),
                        'department': to_str(record.get('DEPT'), 3),
                        'tax_code': to_int(record.get('TAXIND')) or 1,
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Quote {quotation_number} line: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS('  ✓ Quotation lines imported from qtran.dbf'))
