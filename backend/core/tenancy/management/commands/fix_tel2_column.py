"""
Management command to fix tel2 column NOT NULL issue in tenant databases.
"""
from django.core.management.base import BaseCommand
from django.db import connections
from tenancy.models import Tenant, Shop


def fix_tel2_column_for_shop(tenant, schema_name):
    """
    Fix the tel2 column in a shop schema.
    This is a standalone function that can be called programmatically.
    
    Args:
        tenant: The Tenant object
        schema_name: The shop schema name (e.g., 'acme_main')
    """
    from tenancy.utils import register_tenant_connection
    from django.conf import settings
    
    # Register the tenant connection
    register_tenant_connection(tenant)
    
    # Get the database alias for this tenant
    alias = f'tenant_{tenant.id}'
    
    # Get the connection
    if alias not in connections:
        # Try alternative aliases
        for shop in tenant.shops.all():
            alt_alias = f'tenant_{tenant.id}_{shop.code}'
            if alt_alias in connections:
                alias = alt_alias
                break
    
    conn = connections[alias]
    
    with conn.cursor() as cursor:
        # Check current state
        cursor.execute("""
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'dmast' 
            AND column_name = 'tel2'
            AND table_schema = %s
        """, [schema_name])
        
        result = cursor.fetchone()
        
        if not result:
            return False
        
        column_name, is_nullable, column_default = result
        
        # The issue is NOT NULL without DEFAULT - need to add default
        # First drop NOT NULL, then set DEFAULT, then add NOT NULL back
        if is_nullable == 'NO' and column_default is None:
            # Step 1: Drop NOT NULL constraint
            cursor.execute("ALTER TABLE dmast ALTER COLUMN tel2 DROP NOT NULL")
            # Step 2: Set DEFAULT
            cursor.execute("ALTER TABLE dmast ALTER COLUMN tel2 SET DEFAULT ''")
            # Step 3: Re-add NOT NULL constraint
            cursor.execute("ALTER TABLE dmast ALTER COLUMN tel2 SET NOT NULL")
            conn.commit()
            return True
        
        return False


class Command(BaseCommand):
    help = 'Fix tel2 column NOT NULL constraint in tenant shop schemas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-slug',
            type=str,
            help='Specific tenant slug to fix (default: all tenants)',
        )
        parser.add_argument(
            '--shop-code',
            type=str,
            help='Specific shop code to fix (default: all shops)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )

    def handle(self, *args, **options):
        tenant_slug = options.get('tenant_slug')
        shop_code = options.get('shop_code')
        dry_run = options.get('dry_run', False)

        # Get tenants to process
        if tenant_slug:
            tenants = Tenant.objects.filter(slug=tenant_slug)
        else:
            tenants = Tenant.objects.all()

        total_fixed = 0

        for tenant in tenants:
            self.stdout.write(f'\nProcessing tenant: {tenant.name} ({tenant.slug})')

            # Get shops to process
            if shop_code:
                shops = tenant.shops.filter(code=shop_code)
            else:
                shops = tenant.shops.all()

            for shop in shops:
                self.stdout.write(f'  Shop: {shop.name} (schema: {shop.schema_name})')

                try:
                    fixed = self.fix_tel2_column(tenant, shop, dry_run)
                    if fixed:
                        total_fixed += 1
                        self.stdout.write(self.style.SUCCESS(f'    Fixed tel2 column in {shop.schema_name}'))
                    else:
                        self.stdout.write(f'    tel2 already correct in {shop.schema_name}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'    Error: {str(e)}'))

        self.stdout.write(f'\n{"Would fix" if dry_run else "Fixed"} {total_fixed} schemas')

    def fix_tel2_column(self, tenant, shop, dry_run=False):
        """
        Fix the tel2 column in the shop schema.
        Returns True if changes were made, False if already correct.
        """
        from tenancy.utils import register_tenant_connection
        from django.conf import settings

        # Register the tenant connection
        register_tenant_connection(tenant)

        # Get the database alias for this tenant
        alias = f'tenant_{tenant.id}'

        # Get all connections for this tenant's shops
        connections_list = [
            f'tenant_{tenant.id}_main',
            f'tenant_{tenant.id}_{shop.code}'
        ]
        
        # Try to find the right connection
        conn = None
        for conn_alias in connections_list:
            if conn_alias in connections:
                conn = connections[conn_alias]
                break
        
        if not conn:
            # Try the generic tenant alias
            alias = f'tenant_{tenant.id}'
            if alias in connections:
                conn = connections[alias]

        if not conn:
            self.stdout.write(f'    Could not find connection for shop {shop.schema_name}')
            return False

        with conn.cursor() as cursor:
            # First check if column exists and its current state
            cursor.execute("""
                SELECT column_name, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'dmast' 
                AND column_name = 'tel2'
                AND table_schema = %s
            """, [shop.schema_name])
            
            result = cursor.fetchone()
            
            if not result:
                self.stdout.write(f'    WARNING: tel2 column not found in {shop.schema_name}')
                return False
            
            column_name, is_nullable, column_default = result
            self.stdout.write(f'    Current state: nullable={is_nullable}, default={column_default}')
            
            # The issue is NOT NULL without DEFAULT - need to add default
            # First drop NOT NULL, then set DEFAULT, then add NOT NULL back
            if is_nullable == 'NO' and column_default is None:
                self.stdout.write(f'    Column is NOT NULL but has no DEFAULT - this causes empty string to become NULL')
                if not dry_run:
                    # Step 1: Drop NOT NULL constraint
                    cursor.execute("ALTER TABLE dmast ALTER COLUMN tel2 DROP NOT NULL")
                    self.stdout.write(f'    Dropped NOT NULL constraint')
                    # Step 2: Set DEFAULT
                    cursor.execute("ALTER TABLE dmast ALTER COLUMN tel2 SET DEFAULT ''")
                    self.stdout.write(f'    Set DEFAULT empty string')
                    # Step 3: Re-add NOT NULL constraint
                    cursor.execute("ALTER TABLE dmast ALTER COLUMN tel2 SET NOT NULL")
                    self.stdout.write(f'    Re-added NOT NULL constraint')
                return True
            
            # Check if there are NULL values
            cursor.execute(f'SET search_path TO "{shop.schema_name}"')
            cursor.execute("SELECT COUNT(*) FROM dmast WHERE tel2 IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                self.stdout.write(f'    Found {null_count} rows with NULL tel2')
                if not dry_run:
                    cursor.execute('UPDATE dmast SET tel2 = empty_string() WHERE tel2 IS NULL')
                    # Use empty string literal
                    cursor.execute("UPDATE dmast SET tel2 = '' WHERE tel2 IS NULL")
                    self.stdout.write(f'    Updated {null_count} NULL values to empty string')
            
            # Check if we need to add NOT NULL constraint
            if is_nullable == 'YES':
                if not dry_run:
                    cursor.execute("ALTER TABLE dmast ALTER COLUMN tel2 SET NOT NULL")
                self.stdout.write(f'    Would add NOT NULL constraint')
                return True
            
            return False