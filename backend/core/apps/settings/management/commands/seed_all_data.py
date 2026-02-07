"""
Master seed script - Seeds all test data in the correct order
Usage: 
    python manage.py seed_all_data                    # Seeds first tenant
    python manage.py seed_all_data --tenant-id 1      # Seeds specific tenant
    python manage.py seed_all_data --tenant-slug mycompany
    python manage.py seed_all_data --list             # List available tenants
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from tenancy.models import Tenant, Shop
from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current


class Command(BaseCommand):
    help = 'Seed all test data in the correct order for a specific tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Tenant ID to seed data for'
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            help='Tenant slug to seed data for'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available tenants'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('═' * 70))
        self.stdout.write(self.style.SUCCESS('STARTING COMPREHENSIVE DATA SEEDING'))
        self.stdout.write(self.style.SUCCESS('═' * 70))
        
        # Handle list option
        if options.get('list'):
            self._list_tenants()
            return
        
        # Get the tenant to seed
        tenant = self._get_tenant(options)
        if not tenant:
            return
        
        # Get the shop for this tenant
        shop = self._get_shop(tenant)
        if not shop:
            return
        
        # Set tenant context
        set_current_tenant(tenant)
        set_current_shop(shop.schema_name)
        
        self.stdout.write(self.style.SUCCESS(f'\n📍 Seeding for Tenant: {tenant.name}'))
        self.stdout.write(self.style.SUCCESS(f'   Database: {tenant.db_name}'))
        self.stdout.write(self.style.SUCCESS(f'   Shop: {shop.name} (schema: {shop.schema_name})'))
        
        try:
            # Step 1: Seed settings (dependencies for all other apps)
            self.stdout.write(self.style.WARNING('\n[1/4] Seeding Settings Data...'))
            call_command('seed_settings')
            
            # Step 2: Seed debtors
            self.stdout.write(self.style.WARNING('\n[2/4] Seeding Debtors Data...'))
            call_command('seed_debtors')
            
            # Step 3: Seed creditors
            self.stdout.write(self.style.WARNING('\n[3/4] Seeding Creditors Data...'))
            call_command('seed_creditors')
            
            # Step 4: Seed stock items
            self.stdout.write(self.style.WARNING('\n[4/4] Seeding Stock Items Data...'))
            call_command('seed_stock_items')
            
            self.stdout.write(self.style.SUCCESS('\n' + '═' * 70))
            self.stdout.write(self.style.SUCCESS('✓ ALL DATA SEEDED SUCCESSFULLY!'))
            self.stdout.write(self.style.SUCCESS('═' * 70))
            self.stdout.write('\nYou can now test your frontend with the following sample data:')
            self.stdout.write('  • 5 Debtors (Customers)')
            self.stdout.write('  • 5 Creditors (Suppliers)')
            self.stdout.write('  • 10 Stock Items (Electronics, Furniture, Clothing, Books, Hardware)')
            self.stdout.write('  • Reference data (Departments, Sales Areas, Tax Codes, etc.)')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Error during seeding: {str(e)}'))
            self.stdout.write(self.style.ERROR('\nMake sure you have:'))
            self.stdout.write(self.style.ERROR('  1. Run migrations: python manage.py migrate'))
            self.stdout.write(self.style.ERROR('  2. Created a superuser/staff user'))
        finally:
            clear_current()
    
    def _list_tenants(self):
        """List all available tenants."""
        tenants = Tenant.objects.all()
        
        if not tenants.exists():
            self.stdout.write(self.style.WARNING('No tenants found!'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n📋 Available Tenants:'))
        self.stdout.write('─' * 70)
        
        for tenant in tenants:
            self.stdout.write(f'\n  ID: {tenant.id}')
            self.stdout.write(f'  Name: {tenant.name}')
            self.stdout.write(f'  Slug: {tenant.slug}')
            self.stdout.write(f'  Database: {tenant.db_name}')
            
            shops = tenant.shops.all()
            if shops.exists():
                self.stdout.write(f'  Shops:')
                for shop in shops:
                    self.stdout.write(f'    - {shop.name} (schema: {shop.schema_name})')
            else:
                self.stdout.write(f'  Shops: None')
        
        self.stdout.write('\n' + '─' * 70)
        self.stdout.write('\n💡 Usage:')
        self.stdout.write('  python manage.py seed_all_data --tenant-id 1')
        self.stdout.write('  python manage.py seed_all_data --tenant-slug mycompany')
        self.stdout.write('  python manage.py seed_all_data  (uses first tenant)')
    
    def _get_tenant(self, options):
        """Get the tenant to seed based on options."""
        tenant_id = options.get('tenant_id')
        tenant_slug = options.get('tenant_slug')
        
        try:
            if tenant_id:
                tenant = Tenant.objects.get(id=tenant_id)
                self.stdout.write(self.style.SUCCESS(f'✓ Found tenant by ID: {tenant.name}'))
                return tenant
            elif tenant_slug:
                tenant = Tenant.objects.get(slug=tenant_slug)
                self.stdout.write(self.style.SUCCESS(f'✓ Found tenant by slug: {tenant.name}'))
                return tenant
            else:
                # Use first tenant
                tenant = Tenant.objects.first()
                if not tenant:
                    self.stdout.write(self.style.ERROR('✗ No tenants found!'))
                    self.stdout.write('  Run: python manage.py seed_all_data --list')
                    self.stdout.write('  or create a tenant first')
                    return None
                self.stdout.write(self.style.SUCCESS(f'✓ Using first tenant: {tenant.name}'))
                return tenant
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'✗ Tenant not found!'))
            self.stdout.write('  Run: python manage.py seed_all_data --list')
            return None
    
    def _get_shop(self, tenant):
        """Get the head office shop for the tenant."""
        # Try to get head office first
        shop = tenant.shops.filter(is_head_office=True).first()
        
        if shop:
            self.stdout.write(self.style.SUCCESS(f'✓ Using head office: {shop.name}'))
            return shop
        
        # Fall back to any shop
        shop = tenant.shops.first()
        if shop:
            self.stdout.write(self.style.WARNING(f'⚠️  No head office found, using: {shop.name}'))
            return shop
        
        self.stdout.write(self.style.ERROR(f'✗ No shops found for tenant {tenant.name}!'))
        self.stdout.write(f'  Create a shop first.')
        return None
