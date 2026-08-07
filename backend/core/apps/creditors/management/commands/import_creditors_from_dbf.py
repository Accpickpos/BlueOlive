"""
Import the supplier (creditor) master from the legacy supmast.dbf.
Must run before stock import (StockItem.supplier FKs into Creditor).
"""
from apps.creditors.models import Creditor
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import clean_email, open_dbf, to_decimal, to_int, to_str

ACCTYPE_MAP = {'B': 'BBF', 'O': 'OI', '': ''}


class Command(TenantAwareLegacyImportCommand):
    help = 'Import the supplier (creditor) master from supmast.dbf'

    def run(self, **options):
        path = self.pdf_dir / 'supmast.dbf'
        if not path.exists():
            self.stdout.write(self.style.WARNING(f'  ⚠ {path} not found'))
            return

        for record in open_dbf(path):
            supplier_number = to_str(record.get('SUPNO'))
            name = to_str(record.get('SUPNAME'), 30)
            if not supplier_number or not name:
                self.skipped += 1
                continue

            defaults = {
                'name': name,
                'contact_person': to_str(record.get('SUPCONT'), 20),
                'telephone': to_str(record.get('SUPTEL'), 15),
                'fax': to_str(record.get('SUPFAX'), 15),
                'email': clean_email(record.get('EMAIL'), 60),
                'physical_address_line1': to_str(record.get('SUPADD1'), 25),
                'physical_address_line2': to_str(record.get('SUPADD2'), 25),
                'physical_address_line3': to_str(record.get('SUPADD3'), 25),
                'postal_address_line1': to_str(record.get('SUPPADD1'), 20),
                'postal_address_line2': to_str(record.get('SUPPADD2'), 20),
                'postal_address_line3': to_str(record.get('SUPPADD3'), 20),
                'our_account_number': to_str(record.get('SUPOURACC'), 15),
                'payment_terms_days': to_int(record.get('SUPTERMS'), 30),
                'account_category': ACCTYPE_MAP.get(to_str(record.get('ACCTYPE')), 'BBF'),
                'update_selling_price_on_receipt': to_str(record.get('UPDSTKSP')).upper() in ('Y', 'YES', 'T', 'TRUE', '1'),
                'prompt_payment_discount_percent': to_decimal(record.get('SUPDISC')),
                'bank_name': to_str(record.get('BANK'), 10),
                'branch_code': to_str(record.get('BANKCODE'), 10),
                'account_number': to_str(record.get('BANKACC'), 15),
                'balance_brought_forward': to_decimal(record.get('SUPBALBFWD')),
                'balance_current': to_decimal(record.get('SUPCRNT')),
                'balance_30_days': to_decimal(record.get('SUP30')),
                'balance_60_days': to_decimal(record.get('SUP60')),
                'balance_90_days': to_decimal(record.get('SUP90')),
                'balance_120_days': to_decimal(record.get('SUP120')),
                'balance_150_days': to_decimal(record.get('SUP150')),
                'last_paid_amount': to_decimal(record.get('SUPPMT')),
                'last_paid_date': record.get('SUPPMTDATE') or None,
                'purchases_mtd': to_decimal(record.get('SUPURCHMTD')),
                'purchases_ytd': to_decimal(record.get('SUPURCHYTD')),
            }

            try:
                _, created = Creditor.objects.using(self.db_alias).update_or_create(
                    supplier_number=supplier_number, defaults=defaults
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Supplier {supplier_number}: {e}'))
                self.errors += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Creditors imported from {path.name}'))
