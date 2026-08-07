"""
Import laybyes from lbmast.dbf (master) + lbtran.dbf (lines).
deposit_amount/balance_due have no direct DBF field: balance_due is computed
as TOTALDUE - PDTODATE; deposit_amount from the first 'SP' (sale/deposit)
line in lbtran.dbf for that laybye, or 0 if there are no lines yet.
"""
from apps.pos.models import Laybye, LaybyeLine
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, parse_hhmm, to_decimal, to_int, to_str, translate_code

STATUS_MAP = {'A': 'ACTIVE', 'C': 'COMPLETED', 'X': 'CANCELLED', 'E': 'EXPIRED'}
TYPE_MAP = {'SP': 'SP', 'PM': 'PM', 'AD': 'AD', 'RT': 'RT'}


class Command(TenantAwareLegacyImportCommand):
    help = 'Import laybyes from lbmast.dbf + lbtran.dbf'

    def run(self, **options):
        deposits = self._first_sale_amounts()
        self._import_master(deposits)
        self._import_lines()

    def _first_sale_amounts(self):
        """Pre-scan lbtran.dbf for each laybye's first SP-type line amount, to use as deposit_amount."""
        path = self.pdf_dir / 'lbtran.dbf'
        deposits = {}
        if not path.exists():
            return deposits
        for record in open_dbf(path):
            lbno = to_str(record.get('LBNO'), 20)
            if to_str(record.get('TYPE'), 2) == 'SP' and lbno not in deposits:
                deposits[lbno] = to_decimal(record.get('QTY')) * to_decimal(record.get('SPRICE'))
        return deposits

    def _import_master(self, deposits):
        path = self.pdf_dir / 'lbmast.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        for record in open_dbf(path):
            laybye_number = to_str(record.get('LBNO'), 20)
            laybye_date = record.get('DATE') or None
            expiry_date = record.get('EXPDATE') or None
            if not laybye_number or not laybye_date or not expiry_date:
                self.skipped += 1
                continue

            total_amount = to_decimal(record.get('TOTALDUE'))
            paid_to_date = to_decimal(record.get('PDTODATE'))
            balance_due = max(total_amount - paid_to_date, 0)
            status = translate_code(self, record.get('STATUS'), STATUS_MAP, 'ACTIVE', context=f'lbmast.dbf STATUS (laybye {laybye_number})')

            try:
                _, created = Laybye.objects.using(self.db_alias).update_or_create(
                    laybye_number=laybye_number,
                    defaults={
                        'customer_name': to_str(record.get('NAME'), 40) or 'Unknown',
                        'address_line1': to_str(record.get('ADD1'), 25),
                        'address_line2': to_str(record.get('ADD2'), 25),
                        'address_line3': to_str(record.get('ADD3'), 25),
                        'telephone': to_str(record.get('TEL'), 15),
                        'laybye_date': laybye_date,
                        'expiry_date': expiry_date,
                        'date_last_paid': record.get('DATELPD') or None,
                        'total_amount': total_amount,
                        'deposit_amount': deposits.get(laybye_number, 0),
                        'amount_paid': paid_to_date,
                        'balance_due': balance_due,
                        'comment1': to_str(record.get('COMMENT1'), 30),
                        'comment2': to_str(record.get('COMMENT2'), 30),
                        'status': status,
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Laybye {laybye_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS('  ✓ Laybye master imported from lbmast.dbf'))

    def _import_lines(self):
        path = self.pdf_dir / 'lbtran.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        laybyes = {l.laybye_number: l for l in Laybye.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            laybye_number = to_str(record.get('LBNO'), 20)
            laybye = laybyes.get(laybye_number)
            transaction_date = record.get('DATE') or None
            transaction_time = parse_hhmm(record.get('TIME'))
            if laybye is None or not transaction_date or not transaction_time:
                self.skipped += 1
                continue

            transaction_type = translate_code(
                self, record.get('TYPE'), TYPE_MAP, 'OT', context=f'lbtran.dbf TYPE (laybye {laybye_number})'
            )
            quantity = to_decimal(record.get('QTY')) or 1
            unit_price = to_decimal(record.get('SPRICE'))

            try:
                _, created = LaybyeLine.objects.using(self.db_alias).update_or_create(
                    laybye=laybye, stock_code=to_str(record.get('CODE'), 13),
                    transaction_date=transaction_date, transaction_time=transaction_time,
                    defaults={
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'cost_price': to_decimal(record.get('COST')),
                        'transaction_type': transaction_type,
                        'station_number': to_int(record.get('STANUM'), default=None),
                        'salesman_number': to_int(record.get('SALESMAN'), default=None),
                        'line_total': quantity * unit_price,
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Laybye {laybye_number} line: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS('  ✓ Laybye lines imported from lbtran.dbf'))
