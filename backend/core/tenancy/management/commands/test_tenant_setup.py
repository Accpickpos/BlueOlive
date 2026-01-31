# tenancy/management/commands/test_tenant_setup.py
"""
Management command to test the complete tenant and shop setup flow.

Usage:
    python manage.py test_tenant_setup --tenant-name "Test Corp"
    python manage.py test_tenant_setup --cleanup  # Remove test data
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction, connections
from tenancy.models import Tenant, Shop
from tenancy.shop_manager import get_schema_info, delete_shop_schema
import time


class Command(BaseCommand):
    help = 'Test tenant and shop setup (creates and verifies test tenant)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-name',
            type=str,
            default='Test Tenant',
            help='Name for the test tenant'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Remove test tenant and data'
        )
        parser.add_argument(
            '--db-name',
            type=str,
            default='test_tenant_db',
            help='Database name for test tenant'
        )

    def handle(self, *args, **options):
        if options['cleanup']:
            self.cleanup_test_data()
            return
        
        tenant_name = options['tenant_name']
        db_name = options['db_name']
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("TENANT & SHOP SETUP TEST")
        self.stdout.write("="*80 + "\n")
        
        try:
            # Phase 1: Create Tenant
            self.stdout.write(self.style.HTTP_INFO("Phase 1: Creating Tenant..."))
            tenant = self.create_test_tenant(tenant_name, db_name)
            
            # Wait for signals to complete
            self.stdout.write("Waiting for tenant setup to complete...")
            time.sleep(2)
            
            # Verify tenant database
            self.verify_tenant_database(tenant)
            
            # Phase 2: Create Shops
            self.stdout.write(self.style.HTTP_INFO("\nPhase 2: Creating Shops..."))
            shops = self.create_test_shops(tenant)
            
            # Wait for signals to complete
            self.stdout.write("Waiting for shop schemas to be created...")
            time.sleep(2)
            
            # Phase 3: Verify Shops
            self.stdout.write(self.style.HTTP_INFO("\nPhase 3: Verifying Shop Schemas..."))
            for shop in shops:
                self.verify_shop_schema(shop)
            
            # Summary
            self.print_summary(tenant, shops)
            
            self.stdout.write(self.style.SUCCESS("\n✅ All tests passed!"))
            self.stdout.write(f"\nTo clean up, run: python manage.py test_tenant_setup --cleanup")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Test failed: {str(e)}"))
            raise

    def create_test_tenant(self, name, db_name):
        """Create a test tenant."""
        self.stdout.write(f"  Creating tenant: {name}")
        
        tenant = Tenant.objects.create(
            name=name,
            slug="test-tenant",
            db_name=db_name,
            db_host="localhost",
            db_port=5432,
            db_user="postgres",
            db_password="postgres",  # Change this!
            is_active=True
        )
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Tenant created (ID: {tenant.id})"))
        self.stdout.write(f"    Database: {tenant.db_name}")
        self.stdout.write(f"    Alias: {tenant.db_alias}")
        
        return tenant

    def verify_tenant_database(self, tenant):
        """Verify that tenant database was created and migrated."""
        self.stdout.write(f"\n  Verifying tenant database: {tenant.db_name}")
        
        try:
            conn = connections[tenant.db_alias]
            
            # Check if we can connect
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                self.stdout.write(f"  ✓ Connected to PostgreSQL")
                
                # Check for expected tables in public schema
                cur.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename IN ('auth_user', 'shop_users_shopuser', 
                                     'admin_logentry', 'token_blacklist_outstandingtoken')
                    ORDER BY tablename
                """)
                tables = [row[0] for row in cur.fetchall()]
                
                self.stdout.write(f"  ✓ Found {len(tables)} expected tables in public schema:")
                for table in tables:
                    self.stdout.write(f"    - {table}")
                
                # Check migrations
                cur.execute("""
                    SELECT COUNT(DISTINCT app)
                    FROM django_migrations
                """)
                app_count = cur.fetchone()[0]
                self.stdout.write(f"  ✓ Migrations applied for {app_count} apps")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ✗ Database verification failed: {str(e)}"))
            raise

    def create_test_shops(self, tenant):
        """Create test shops."""
        shop_configs = [
            {"name": "Test Shop Alpha", "slug": "alpha", "schema": "shop_alpha"},
            {"name": "Test Shop Beta", "slug": "beta", "schema": "shop_beta"},
        ]
        
        shops = []
        for config in shop_configs:
            self.stdout.write(f"  Creating shop: {config['name']}")
            
            shop = Shop.objects.create(
                tenant=tenant,
                name=config['name'],
                slug=config['slug'],
                schema_name=config['schema'],
                is_active=True
            )
            
            shops.append(shop)
            self.stdout.write(self.style.SUCCESS(f"  ✓ Shop created (ID: {shop.id})"))
            self.stdout.write(f"    Schema: {shop.schema_name}")
        
        return shops

    def verify_shop_schema(self, shop):
        """Verify that shop schema was created correctly."""
        self.stdout.write(f"\n  Verifying shop: {shop.name} (schema: {shop.schema_name})")
        
        tenant = shop.tenant
        info = get_schema_info(tenant, shop.schema_name)
        
        if not info['exists']:
            raise CommandError(f"Schema '{shop.schema_name}' does not exist!")
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Schema exists"))
        self.stdout.write(f"  ✓ Tables: {info['table_count']}")
        
        # Check for expected tables
        expected_prefixes = ['cash_book', 'creditors', 'stock_control', 'purchase_orders']
        found_prefixes = set()
        
        for table in info['tables']:
            for prefix in expected_prefixes:
                if table.startswith(prefix):
                    found_prefixes.add(prefix)
        
        if found_prefixes:
            self.stdout.write(f"  ✓ Found tables for apps: {', '.join(found_prefixes)}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠ No business app tables found"))
        
        # Check migrations
        migration_apps = set(m['app'] for m in info['migrations'])
        self.stdout.write(f"  ✓ Migrations for: {', '.join(migration_apps)}")

    def print_summary(self, tenant, shops):
        """Print a summary of what was created."""
        self.stdout.write("\n" + "="*80)
        self.stdout.write("SUMMARY")
        self.stdout.write("="*80)
        
        self.stdout.write(f"\nTenant: {tenant.name}")
        self.stdout.write(f"  ID: {tenant.id}")
        self.stdout.write(f"  Database: {tenant.db_name}")
        self.stdout.write(f"  Alias: {tenant.db_alias}")
        
        self.stdout.write(f"\nShops: {len(shops)}")
        for shop in shops:
            self.stdout.write(f"  - {shop.name}")
            self.stdout.write(f"    ID: {shop.id}")
            self.stdout.write(f"    Schema: {shop.schema_name}")
        
        # Database structure
        self.stdout.write("\nDatabase Structure:")
        self.stdout.write(f"  {tenant.db_name}/")
        self.stdout.write(f"    public/")
        self.stdout.write(f"      - auth, contenttypes")
        self.stdout.write(f"      - admin, token_blacklist")
        self.stdout.write(f"      - shop_users")
        
        for shop in shops:
            self.stdout.write(f"    {shop.schema_name}/")
            self.stdout.write(f"      - cash_book")
            self.stdout.write(f"      - creditors")
            self.stdout.write(f"      - stock_control")
            self.stdout.write(f"      - purchase_orders")

    def cleanup_test_data(self):
        """Remove test tenant and associated data."""
        self.stdout.write(self.style.WARNING("\n⚠️  CLEANING UP TEST DATA"))
        
        # Find test tenants
        test_tenants = Tenant.objects.filter(slug__startswith='test-')
        
        if not test_tenants.exists():
            self.stdout.write("No test tenants found.")
            return
        
        for tenant in test_tenants:
            self.stdout.write(f"\nRemoving tenant: {tenant.name}")
            
            # Get shops
            shops = Shop.objects.filter(tenant=tenant)
            
            # Delete shop schemas
            for shop in shops:
                self.stdout.write(f"  Deleting schema: {shop.schema_name}")
                try:
                    delete_shop_schema(tenant, shop.schema_name, cascade=True)
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Schema deleted"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠ Failed: {str(e)}"))
            
            # Delete shop records
            shop_count = shops.count()
            shops.delete()
            self.stdout.write(f"  ✓ Deleted {shop_count} shop record(s)")
            
            # Drop database (manual - can't do this through Django)
            self.stdout.write(self.style.WARNING(
                f"  ⚠ Please manually drop database: DROP DATABASE {tenant.db_name};"
            ))
            
            # Delete tenant record
            tenant.delete()
            self.stdout.write(self.style.SUCCESS(f"  ✓ Tenant record deleted"))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Cleanup complete"))