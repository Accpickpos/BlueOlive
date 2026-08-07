"""
Import Returns-For-Credit from supcrmas.dbf (master) + supcrtrn.dbf (lines).
Uses RFC.STATUS_CHOICES' own documented DBF mapping (A->PE, C->CR, R->RE, X->CA).
supcrtrn.dbf has no tax field, so RFCLineItem.tax_code defaults to the
lowest-numbered active TaxCode (matching the existing stock importer's
tax-fallback convention).
"""
from apps.creditors.models import RFC, Creditor, RFCLineItem
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, parse_hhmm, to_date, to_decimal, to_str, translate_code
from apps.settings.models import TaxCode
from apps.stock_control.models import StockItem

STATUS_MAP = {'A': 'PE', 'C': 'CR', 'R': 'RE', 'X': 'CA'}


class Command(TenantAwareLegacyImportCommand):
    help = 'Import Returns-For-Credit from supcrmas.dbf + supcrtrn.dbf'

    def run(self, **options):
        default_tax_code = TaxCode.objects.using(self.db_alias).order_by('code').first()
        if default_tax_code is None:
            self.stdout.write(self.style.ERROR('  ✗ No TaxCode exists — seed tax codes before importing RFCs'))
            return

        self._import_master()
        self._import_lines(default_tax_code)

    def _import_master(self):
        path = self.pdf_dir / 'supcrmas.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        creditors = {c.supplier_number: c for c in Creditor.objects.using(self.db_alias).all()}

        for record in open_dbf(path):
            rfc_number = to_str(record.get('RFCNO'), 6)
            if not rfc_number:
                self.skipped += 1
                continue

            creditor = creditors.get(to_str(record.get('SUPNO')))
            if creditor is None:
                self.stdout.write(self.style.WARNING(f'  ⚠ RFC {rfc_number}: unknown supplier, skipping'))
                self.skipped += 1
                continue

            date_sent = to_date(record.get('DATESENT'))
            status = translate_code(self, record.get('STATUS'), STATUS_MAP, 'PE', context='supcrmas.dbf STATUS')

            try:
                _, created = RFC.objects.using(self.db_alias).update_or_create(
                    rfc_number=rfc_number,
                    defaults={
                        'creditor': creditor,
                        'date_sent': date_sent,
                        'date_returned': to_date(record.get('DATERETN')),
                        'return_date': date_sent,
                        'status': status,
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ RFC {rfc_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ RFC master imported from {path.name}'))

    def _import_lines(self, default_tax_code):
        path = self.pdf_dir / 'supcrtrn.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        rfcs = {r.rfc_number: r for r in RFC.objects.using(self.db_alias).all()}
        stock_items = {s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()}
        line_counters = {}

        for record in open_dbf(path):
            rfc_number = to_str(record.get('RFCNO'), 6)
            rfc = rfcs.get(rfc_number)
            stock_item = stock_items.get(to_str(record.get('CODE'), 13))
            if rfc is None or stock_item is None:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠ supcrtrn.dbf: RFC {rfc_number!r}/stock {record.get("CODE")!r} not found, skipping'
                ))
                self.skipped += 1
                continue

            line_counters[rfc_number] = line_counters.get(rfc_number, 0) + 1
            line_number = line_counters[rfc_number]

            try:
                _, created = RFCLineItem.objects.using(self.db_alias).update_or_create(
                    rfc=rfc, line_number=line_number,
                    defaults={
                        'stock_item': stock_item,
                        'quantity_returned': to_decimal(record.get('QTYRFC')),
                        'quantity_credited': to_decimal(record.get('QTYCRED'), None),
                        'quantity_stock': to_decimal(record.get('QTY')),
                        'line_value': to_decimal(record.get('VAL')),
                        'tax_code': default_tax_code,
                        'rfc_line_date': to_date(record.get('DATE')),
                        'rfc_line_time': to_str(record.get('TIME'), 5),
                        'original_transaction_type': to_str(record.get('TYPE'), 2),
                        'original_transaction_date': to_date(record.get('PURCHDATE')),
                        'supplier_reference_number': to_str(record.get('SUPREFNO'), 10),
                        'reason': to_str(record.get('COMMENT')),
                    }
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ RFC {rfc_number} line {line_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ RFC lines imported from {path.name}'))
