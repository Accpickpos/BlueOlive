import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from django.core.management import call_command
from apps.debtors.models import Debtor
from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection
from decimal import Decimal
from datetime import datetime


class Command(BaseCommand):
    help = 'Import debtors/customers from CSV file (supports comma and semicolon delimiters)'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str)
        parser.add_argument('--delimiter', type=str, default=',', help='CSV delimiter (default: comma)')
        parser.add_argument('--tenant', type=str, help='Tenant name or ID to import into')
        parser.add_argument('--shop', type=str, help='Shop name or code to import into')
        parser.add_argument('--migrate', action='store_true', help='Run migrations before importing')

    def handle(self, *args, **options):
        try:
            # Get tenant if specified
            tenant = None
            db_alias = DEFAULT_DB_ALIAS
            schema_name = None
            
            if options.get('tenant'):
                tenant = self._get_tenant(options['tenant'])
                if not tenant:
                    raise CommandError(f"Tenant '{options['tenant']}' not found")
                register_tenant_connection(tenant)
                db_alias = tenant.db_alias
                self.stdout.write(f'Using tenant: {tenant.name}')
            
            # Get shop if specified
            if options.get('shop'):
                if not tenant:
                    raise CommandError('--shop requires --tenant to be specified')
                shop = self._get_shop(tenant, options['shop'])
                if not shop:
                    raise CommandError(f"Shop '{options['shop']}' not found in tenant '{tenant.name}'")
                schema_name = shop.schema_name
                self.stdout.write(f'Using shop: {shop.name} (schema: {schema_name})')
            elif tenant:
                # Use first shop if tenant is specified but shop is not
                shop = tenant.shops.first()
                if shop:
                    schema_name = shop.schema_name
                    self.stdout.write(f'Using default shop: {shop.name} (schema: {schema_name})')
            
            # Check if migrations have been run
            if db_alias != DEFAULT_DB_ALIAS:
                if not self._check_table_exists(db_alias, 'debtors_debtor'):
                    if options.get('migrate'):
                        self.stdout.write(self.style.WARNING('Running migrations...'))
                        try:
                            call_command('migrate', database=db_alias, verbosity=1)
                            self.stdout.write(self.style.SUCCESS('Migrations completed'))
                        except Exception as e:
                            raise CommandError(f'Migration failed: {str(e)}')
                    else:
                        raise CommandError(
                            f'Debtors table does not exist in schema "{schema_name}". '
                            f'Run migrations first:\n'
                            f'  python manage.py migrate --database={db_alias}\n'
                            f'Or use --migrate flag to run automatically:\n'
                            f'  python manage.py import_debtors_csv dmast.csv --migrate --tenant "McM" --shop "Grayling"'
                        )
            
            with open(options['file_path'], 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile, delimiter=options['delimiter'])
                
                if not reader.fieldnames:
                    raise CommandError('CSV file is empty')
                
                created = 0
                updated = 0
                errors = 0
                
                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Normalize column names to lowercase
                        row_normalized = {k.lower(): v for k, v in row.items()}
                        
                        # Required field
                        dno = row_normalized.get('dno', '').strip()
                        if not dno:
                            self.stdout.write(f'Row {row_num}: Missing DNO, skipping')
                            errors += 1
                            continue
                        
                        try:
                            dno = int(dno)
                        except ValueError:
                            self.stdout.write(f'Row {row_num}: DNO must be numeric, skipping')
                            errors += 1
                            continue
                        
                        # Helper function to safely get and convert values
                        def get_string(key, maxlen=None):
                            val = row_normalized.get(key, '').strip()
                            return val[:maxlen] if maxlen else val
                        
                        def get_decimal(key):
                            try:
                                val = row_normalized.get(key, '0').strip()
                                return Decimal(val) if val else Decimal(0)
                            except:
                                return Decimal(0)
                        
                        def get_int(key, default=0):
                            try:
                                val = row_normalized.get(key, str(default)).strip()
                                return int(float(val)) if val else default
                            except:
                                return default
                        
                        # Perform update_or_create
                        debtor, created_flag = Debtor.objects.using(db_alias).update_or_create(
                            dno=dno,
                            defaults={
                                'dname': get_string('dname', 40),
                                'dsname': get_string('dsname', 5),
                                'dcontact': get_string('dcontact', 20),
                                'dtel': get_string('dtel', 15),
                                'dfax': get_string('dfax', 15),
                                'dadd1': get_string('dadd1', 25),
                                'dadd2': get_string('dadd2', 25),
                                'dadd3': get_string('dadd3', 25),
                                'dpcode': get_string('dpcode', 4),
                                'delad1': get_string('delad1', 25),
                                'delad2': get_string('delad2', 25),
                                'delad3': get_string('delad3', 25),
                                'delad4': get_string('delad4', 25),
                                'dtaxno': get_string('dtaxno', 20),
                                'darea': get_int('darea', 0),
                                'acctype': get_string('acctype', 1),
                                'price': get_int('price', 1),
                                'terms': get_int('terms', 30),
                                'ddiscper': get_decimal('ddiscper'),
                                'pdisc': get_decimal('pdisc'),
                                'discprn': get_string('discprn', 1),
                                'dclimit': get_decimal('dclimit'),
                                'dintflag': get_string('dintflag', 1),
                                'blockflag': get_string('blockflag', 1),
                                'dposbal': get_string('dposbal', 1),
                                'dbalbfwd': get_decimal('dbalbfwd'),
                            }
                        )
                        
                        if created_flag:
                            created += 1
                        else:
                            updated += 1
                            
                    except Exception as e:
                        self.stdout.write(f'Row {row_num}: Error - {str(e)}')
                        errors += 1
                
                # Summary output
                self.stdout.write(self.style.SUCCESS(f'\n✓ Import completed:'))
                self.stdout.write(f'  Created: {created}')
                self.stdout.write(f'  Updated: {updated}')
                if errors:
                    self.stdout.write(self.style.WARNING(f'  Errors: {errors}'))
                    
        except FileNotFoundError:
            raise CommandError(f'File not found: {options["file_path"]}')
        except Exception as e:
            raise CommandError(f'Import failed: {str(e)}')

    def _get_tenant(self, identifier):
        """Get tenant by ID or name"""
        try:
            # Try by ID first
            return Tenant.objects.get(id=int(identifier))
        except (ValueError, Tenant.DoesNotExist):
            # Try by name
            return Tenant.objects.filter(name=identifier).first()

    def _get_shop(self, tenant, identifier):
        """Get shop from tenant by code or name"""
        return (
            tenant.shops.filter(code=identifier).first() or
            tenant.shops.filter(name=identifier).first()
        )

    def _check_table_exists(self, db_alias, table_name):
        """Check if a table exists in the database"""
        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
            return True
        except Exception:
            return False
