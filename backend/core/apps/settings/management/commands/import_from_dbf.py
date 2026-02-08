"""
Import data from DBF files into Django models.
Supports Debtors, Creditors, and Stock Items.

Usage:
    python manage.py import_from_dbf --debtors /path/to/debtors.dbf
    python manage.py import_from_dbf --creditors /path/to/creditors.dbf
    python manage.py import_from_dbf --stock /path/to/stock.dbf
    python manage.py import_from_dbf --all /path/to/folder
"""

import os
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from dbfread import DBF
from apps.debtors.models import Debtor
from apps.creditors.models import Creditor
from apps.stock_control.models import StockItem
from apps.settings.models import SalesArea, SalesDepartment, TaxCode, CreditTerms, PaymentMethod


class Command(BaseCommand):
    help = 'Import data from DBF files (debtors, creditors, stock items)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--debtors',
            type=str,
            help='Path to debtors DBF file',
        )
        parser.add_argument(
            '--creditors',
            type=str,
            help='Path to creditors DBF file',
        )
        parser.add_argument(
            '--stock',
            type=str,
            help='Path to stock items DBF file',
        )
        parser.add_argument(
            '--all',
            type=str,
            help='Folder path containing debtors.dbf, creditors.dbf, and stock.dbf',
        )
        parser.add_argument(
            '--skip-validation',
            action='store_true',
            help='Skip validation of required foreign keys',
        )

    def handle(self, *args, **options):
        skip_validation = options['skip_validation']
        
        # Validate prerequisites unless skipping
        if not skip_validation:
            self._validate_prerequisites()

        if options['all']:
            folder = options['all']
            if not os.path.isdir(folder):
                raise CommandError(f'Folder does not exist: {folder}')
            
            debtors_file = os.path.join(folder, 'debtors.dbf')
            creditors_file = os.path.join(folder, 'creditors.dbf')
            stock_file = os.path.join(folder, 'stock.dbf')

            if os.path.exists(debtors_file):
                self._import_debtors(debtors_file)
            if os.path.exists(creditors_file):
                self._import_creditors(creditors_file)
            if os.path.exists(stock_file):
                self._import_stock(stock_file)
        else:
            if options['debtors']:
                self._import_debtors(options['debtors'])
            if options['creditors']:
                self._import_creditors(options['creditors'])
            if options['stock']:
                self._import_stock(options['stock'])

        if not any([options['all'], options['debtors'], options['creditors'], options['stock']]):
            raise CommandError('Please specify --debtors, --creditors, --stock, or --all')

    def _validate_prerequisites(self):
        """Check that required reference data exists."""
        departments = SalesDepartment.objects.exists()
        areas = SalesArea.objects.exists()
        tax_codes = TaxCode.objects.exists()
        
        if not departments:
            raise CommandError('No Sales Departments found. Run "python manage.py seed_settings" first.')
        if not areas:
            raise CommandError('No Sales Areas found. Run "python manage.py seed_settings" first.')
        if not tax_codes:
            raise CommandError('No Tax Codes found. Run "python manage.py seed_settings" first.')

    def _import_debtors(self, file_path):
        """Import debtors from DBF file."""
        if not os.path.exists(file_path):
            raise CommandError(f'File does not exist: {file_path}')

        self.stdout.write(f'\n✓ Importing Debtors from {file_path}...')
        
        try:
            dbf_table = DBF(file_path)
        except Exception as e:
            raise CommandError(f'Error reading DBF file: {str(e)}')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Get default values
        default_area = SalesArea.objects.first()

        for record in dbf_table:
            try:
                # Account number (required)
                account_number = (record.get('DNO') or record.get('ACCTNO') or record.get('ACCOUNT') or '').strip()
                if not account_number:
                    self.stdout.write(self.style.WARNING('  ⚠ Skipped: No account number'))
                    skipped_count += 1
                    continue

                # Name (required)
                name = (record.get('DNAME') or record.get('NAME') or record.get('ACCTNAME') or '').strip()
                if not name:
                    name = account_number

                # Search name (short name)
                search_name = (record.get('DSNAME') or name).strip()[:50]

                # Convert Y/N flags to boolean
                def to_bool(value):
                    return str(value).upper() in ('Y', 'YES', 'TRUE', '1') if value else False

                # Get or create debtor with ALL available fields
                debtor, created = Debtor.objects.update_or_create(
                    account_number=account_number,
                    defaults={
                        # Basic Information
                        'name': name,
                        'search_name': search_name,
                        
                        # Contact Information
                        'contact_person': (record.get('DCONTACT') or record.get('CONTACT') or '').strip()[:100],
                        'telephone1': (record.get('DTEL') or record.get('PHONE') or record.get('TEL1') or '').strip()[:50],
                        'telephone2': (record.get('TEL2') or '').strip()[:50],
                        'fax': (record.get('DFAX') or record.get('FAX') or '').strip()[:50],
                        
                        # Postal Address
                        'postal_address_line1': (record.get('DADD1') or record.get('ADDR1') or '').strip()[:200],
                        'postal_address_line2': (record.get('DADD2') or record.get('ADDR2') or '').strip()[:200],
                        'postal_address_line3': (record.get('DADD3') or record.get('ADDR3') or '').strip()[:200],
                        'postal_code': (record.get('DPCODE') or record.get('ZIP') or record.get('POSTAL') or '').strip()[:20],
                        
                        # Delivery Address
                        'delivery_address_line1': (record.get('DELAD1') or record.get('DADDR1') or '').strip()[:200],
                        'delivery_address_line2': (record.get('DELAD2') or record.get('DADDR2') or '').strip()[:200],
                        'delivery_address_line3': (record.get('DELAD3') or record.get('DADDR3') or '').strip()[:200],
                        'delivery_code': (record.get('DELAD4') or record.get('DZIP') or '').strip()[:20],
                        
                        # Business Details
                        'vat_number': (record.get('DTAXNO') or record.get('VATNUMBER') or '').strip()[:50],
                        
                        # Sales Area (DAREA is salesman/user code - store separately if needed)
                        'sales_area': default_area,
                        # TODO: DAREA = {record.get('DAREA')} is salesman/user code - map to user after import if needed
                        
                        # Account Settings
                        'account_category': (record.get('ACCTYPE') or record.get('CATEGORY') or '').strip() or 'O',
                        'trade_discount': self._to_decimal(record.get('DDISCPER', 0)),
                        'credit_limit': self._to_decimal(record.get('DCLIMIT', 0)),
                        'price_level': int(record.get('PRICE', 1)) if record.get('PRICE') else 1,
                        'terms': int(record.get('TERMS', 30)) if record.get('TERMS') else 30,
                        'prompt_discount_percentage': self._to_decimal(record.get('PDISC', 0)),
                        'print_discount_on_invoice': to_bool(record.get('DISCPRN')),
                        'charge_interest': to_bool(record.get('DINTFLAG')),
                        'print_balance_on_documents': to_bool(record.get('DPOSBAL')),
                        'is_blocked': to_bool(record.get('BLOCKFLAG')),
                        
                        # Balance Information (from legacy system)
                        'current_balance': self._to_decimal(record.get('DCRNT', 0)),
                        'balance_30_days': self._to_decimal(record.get('D30', 0)),
                        'balance_60_days': self._to_decimal(record.get('D60', 0)),
                        'balance_90_days': self._to_decimal(record.get('D90', 0)),
                        'balance_120_days': self._to_decimal(record.get('D120', 0)),
                        'balance_150_days': self._to_decimal(record.get('D150', 0)),
                        'balance_180_days': self._to_decimal(record.get('D180', 0)),
                        
                        # Statistics
                        'last_payment_amount': self._to_decimal(record.get('DAMTLPD', 0)),
                        'sales_mtd': self._to_decimal(record.get('DSALESM', 0)),
                        'sales_ytd': self._to_decimal(record.get('DSALESY', 0)),
                    }
                )

                # Handle date fields
                if record.get('DDATLPD'):
                    try:
                        debtor.last_payment_date = record.get('DDATLPD')
                        debtor.save(update_fields=['last_payment_date'])
                    except:
                        pass  # Skip invalid dates

                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created: {account_number} - {name}')
                else:
                    updated_count += 1
                    self.stdout.write(f'  ◈ Updated: {account_number}')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Error processing record: {str(e)}'))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Debtors import complete:\n'
            f'  Created: {created_count}\n'
            f'  Updated: {updated_count}\n'
            f'  Skipped: {skipped_count}'
        ))

    def _import_creditors(self, file_path):
        """Import creditors from DBF file."""
        if not os.path.exists(file_path):
            raise CommandError(f'File does not exist: {file_path}')

        self.stdout.write(f'\n✓ Importing Creditors from {file_path}...')
        
        try:
            dbf_table = DBF(file_path)
        except Exception as e:
            raise CommandError(f'Error reading DBF file: {str(e)}')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Get default values
        default_area = SalesArea.objects.first()
        default_terms = CreditTerms.objects.first()
        default_payment_method = PaymentMethod.objects.first()

        for record in dbf_table:
            try:
                account_number = (record.get('ACCTNO') or record.get('ACCOUNT') or '').strip()
                if not account_number:
                    self.stdout.write(self.style.WARNING('  ⚠ Skipped: No account number'))
                    skipped_count += 1
                    continue

                name = (record.get('NAME') or record.get('ACCTNAME') or '').strip()
                if not name:
                    name = account_number

                creditor, created = Creditor.objects.update_or_create(
                    account_number=account_number,
                    defaults={
                        'name': name,
                        'search_name': name[:50],
                        'contact_person': (record.get('CONTACT') or '').strip()[:100],
                        'telephone1': (record.get('PHONE') or record.get('TEL1') or '').strip()[:50],
                        'telephone2': (record.get('TEL2') or '').strip()[:50],
                        'fax': (record.get('FAX') or '').strip()[:50],
                        'email': (record.get('EMAIL') or '').strip()[:254],
                        'postal_address_line1': (record.get('ADDR1') or '').strip()[:200],
                        'postal_address_line2': (record.get('ADDR2') or '').strip()[:200],
                        'postal_address_line3': (record.get('ADDR3') or '').strip()[:200],
                        'postal_code': (record.get('ZIP') or record.get('POSTAL') or '').strip()[:20],
                        'delivery_address_line1': (record.get('DADDR1') or '').strip()[:200],
                        'delivery_address_line2': (record.get('DADDR2') or '').strip()[:200],
                        'delivery_address_line3': (record.get('DADDR3') or '').strip()[:200],
                        'delivery_code': (record.get('DZIP') or '').strip()[:20],
                        'sales_area': default_area,
                        'credit_limit': self._to_decimal(record.get('CREDLIMIT', 0)),
                        'credit_terms': default_terms,
                        'vat_number': (record.get('VATNUMBER') or '').strip()[:50],
                        'payment_method': default_payment_method,
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created: {account_number} - {name}')
                else:
                    updated_count += 1
                    self.stdout.write(f'  ◈ Updated: {account_number}')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Error processing record: {str(e)}'))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Creditors import complete:\n'
            f'  Created: {created_count}\n'
            f'  Updated: {updated_count}\n'
            f'  Skipped: {skipped_count}'
        ))

    def _import_stock(self, file_path):
        """Import stock items from DBF file."""
        if not os.path.exists(file_path):
            raise CommandError(f'File does not exist: {file_path}')

        self.stdout.write(f'\n✓ Importing Stock Items from {file_path}...')
        
        try:
            dbf_table = DBF(file_path)
        except Exception as e:
            raise CommandError(f'Error reading DBF file: {str(e)}')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        # Get default values
        default_department = SalesDepartment.objects.first()
        default_tax_code = TaxCode.objects.filter(code='V15').first() or TaxCode.objects.first()

        for record in dbf_table:
            try:
                stock_code = (record.get('CODE') or record.get('STOCKCODE') or record.get('ITEMCODE') or '').strip()
                if not stock_code:
                    self.stdout.write(self.style.WARNING('  ⚠ Skipped: No stock code'))
                    skipped_count += 1
                    continue

                description = (record.get('DESC') or record.get('DESCRIPTION') or '').strip()
                if not description:
                    description = stock_code

                # Get department from DBF or use default
                dept_name = (record.get('DEPARTMENT') or record.get('DEPT') or '').strip()
                department = default_department
                if dept_name:
                    department = SalesDepartment.objects.filter(
                        name__icontains=dept_name
                    ).first() or default_department

                stock_item, created = StockItem.objects.update_or_create(
                    stock_code=stock_code,
                    defaults={
                        'description': description,
                        'department': department,
                        'supplier_code': (record.get('SUPPLIERCODE') or record.get('SUPP_CODE') or '').strip()[:50],
                        'tax_code': default_tax_code,
                        'cost_price': self._to_decimal(record.get('COST', 0)),
                        'average_cost': self._to_decimal(record.get('AVGCOST', 0)),
                        'selling_price_1': self._to_decimal(record.get('PRICE1') or record.get('PRICE', 0)),
                        'selling_price_2': self._to_decimal(record.get('PRICE2', 0)),
                        'selling_price_3': self._to_decimal(record.get('PRICE3', 0)),
                        'quantity_on_hand': self._to_decimal(record.get('QOH') or record.get('QUANTITY', 0)),
                        'reorder_quantity': self._to_decimal(record.get('REORDER', 0)),
                        'quantity_on_order': self._to_decimal(record.get('QOO', 0)),
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f'  ✓ Created: {stock_code} - {description}')
                else:
                    updated_count += 1
                    self.stdout.write(f'  ◈ Updated: {stock_code}')

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  ⚠ Error processing record: {str(e)}'))
                skipped_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Stock items import complete:\n'
            f'  Created: {created_count}\n'
            f'  Updated: {updated_count}\n'
            f'  Skipped: {skipped_count}'
        ))

    @staticmethod
    def _to_decimal(value):
        """Convert value to Decimal, handling various formats."""
        if value is None or value == '':
            return Decimal('0')
        try:
            return Decimal(str(value))
        except:
            return Decimal('0')
    
    def _get_sales_area(self, area_code, default_area):
        """Get sales area by numeric code or return default."""
        if not area_code:
            return default_area
        
        try:
            area_num = int(area_code)
            # Try to find by ID first
            area = SalesArea.objects.filter(id=area_num).first()
            if area:
                return area
        except (ValueError, TypeError):
            pass
        
        return default_area
