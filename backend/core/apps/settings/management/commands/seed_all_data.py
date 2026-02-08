"""
Master seed script - Seeds all test data in the correct order
Orchestrates all seeding commands in the proper sequence.

Usage: 
    python manage.py seed_all_data                      # Seeds first tenant/shop
    python manage.py seed_all_data --tenant-id 1        # Seeds specific tenant
    python manage.py seed_all_data --tenant-slug mycompany
    python manage.py seed_all_data --shop-id 2           # Seeds specific shop
    python manage.py seed_all_data --dry-run             # Show what would be seeded
    python manage.py seed_all_data --list                # List available tenants
"""
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from apps.settings.seeding_utils import get_tenant, get_shop, SeedingException
from tenancy.models import Tenant


class Command(BaseCommand):
    help = 'Master seeding command - seeds all test data in the correct order'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Tenant ID to seed (defaults to first tenant)'
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            help='Tenant slug to seed'
        )
        parser.add_argument(
            '--shop-id',
            type=int,
            help='Shop ID to seed (defaults to first active shop)'
        )
        parser.add_argument(
            '--shop-slug',
            type=str,
            help='Shop slug to seed'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be seeded without creating data'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available tenants and shops'
        )

    def handle(self, *args, **options):
        self.print_header('STARTING COMPREHENSIVE DATA SEEDING')
        
        try:
            # Handle list option
            if options.get('list'):
                self._list_tenants()
                return
            
            # Get tenant and shop
            try:
                tenant = get_tenant(
                    tenant_id=options.get('tenant_id'),
                    tenant_slug=options.get('tenant_slug')
                )
            except SeedingException as e:
                self.stdout.write(self.style.ERROR(f'\n✗ {str(e)}'))
                return
            
            try:
                shop = get_shop(
                    tenant,
                    shop_id=options.get('shop_id'),
                    shop_slug=options.get('shop_slug')
                )
            except SeedingException as e:
                self.stdout.write(self.style.ERROR(f'\n✗ {str(e)}'))
                return
            
            # Display context
            dry_run = options.get('dry_run', False)
            self._print_context(tenant, shop, dry_run)
            
            # Build command arguments
            cmd_args = [
                f'--tenant-id={tenant.id}',
                f'--shop-id={shop.id}',
            ]
            if dry_run:
                cmd_args.append('--dry-run')
            
            # Execute seeding commands in order
            commands = [
                ('seed_settings', 'Settings/Reference Data'),
                ('seed_debtors', 'Debtors (Customers)'),
                ('seed_creditors', 'Creditors (Suppliers)'),
                ('seed_stock_items', 'Stock Items'),
            ]
            
            for i, (cmd_name, cmd_label) in enumerate(commands, 1):
                self.stdout.write(self.style.WARNING(f'\n[{i}/4] Seeding {cmd_label}...'))
                try:
                    call_command(cmd_name, *cmd_args)
                except CommandError as e:
                    self.stdout.write(self.style.ERROR(f'\n✗ Failed to seed {cmd_label}: {str(e)}'))
                    raise
            
            # Success summary
            self.print_header('✓ ALL DATA SEEDED SUCCESSFULLY!')
            self._print_summary()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Seeding failed: {str(e)}'))
            raise CommandError(str(e))
    
    def _print_context(self, tenant, shop, dry_run):
        """Print seeding context information."""
        self.stdout.write(self.style.SUCCESS(f'\n📍 Seeding Context:'))
        self.stdout.write(self.style.SUCCESS(f'   Tenant: {tenant.name} (ID: {tenant.id})'))
        self.stdout.write(self.style.SUCCESS(f'   Database: {tenant.db_name}'))
        self.stdout.write(self.style.SUCCESS(f'   Shop: {shop.name} (schema: {shop.schema_name})'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n   🔍 DRY RUN MODE - No data will be created'))
    
    def _print_summary(self):
        """Print a summary of what was seeded."""
        self.stdout.write('\n📊 Sample Data Created:')
        self.stdout.write('  ✓ 5 Sales Departments')
        self.stdout.write('  ✓ 3 Sales Areas')
        self.stdout.write('  ✓ 3 Tax Codes')
        self.stdout.write('  ✓ 5 Payment Methods')
        self.stdout.write('  ✓ 4 Credit Terms')
        self.stdout.write('  ✓ 4 Income Categories')
        self.stdout.write('  ✓ 6 Expense Categories')
        self.stdout.write('  ✓ 5 Debtors (Customers)')
        self.stdout.write('  ✓ 5 Creditors (Suppliers)')
        self.stdout.write('  ✓ 10 Stock Items')
        
        self.stdout.write('\n💡 Next Steps:')
        self.stdout.write('  1. Run the server: python manage.py runserver')
        self.stdout.write('  2. Test the API endpoints')
        self.stdout.write('  3. Check admin panel: http://localhost:8000/admin/')
    
    def _list_tenants(self):
        """List all available tenants and their shops."""
        tenants = Tenant.objects.all()
        
        if not tenants.exists():
            self.stdout.write(self.style.WARNING('\n⚠️  No tenants found in the system.'))
            self.stdout.write('Create a tenant first: python manage.py create_dev_tenant')
            return
        
        self.print_header('AVAILABLE TENANTS')
        
        for tenant in tenants:
            self.stdout.write(f'\n📦 {tenant.name}')
            self.stdout.write(f'   ID: {tenant.id}')
            self.stdout.write(f'   Slug: {tenant.slug}')
            self.stdout.write(f'   Database: {tenant.db_name}')
            
            shops = tenant.shops.all()
            if shops.exists():
                self.stdout.write(f'   Shops:')
                for shop in shops:
                    marker = '🏢' if shop.is_head_office else '  '
                    self.stdout.write(f'     {marker} {shop.name} (ID: {shop.id}, schema: {shop.schema_name})')
            else:
                self.stdout.write(f'   Shops: ⚠️  None found')
        
        self.stdout.write('\n' + '═' * 70)
        self.stdout.write('💡 Usage Examples:')
        self.stdout.write('  python manage.py seed_all_data --tenant-id 1')
        self.stdout.write('  python manage.py seed_all_data --tenant-slug mycompany')
        self.stdout.write('  python manage.py seed_all_data --shop-id 2')
        self.stdout.write('  python manage.py seed_all_data --dry-run')
    
    def print_header(self, title):
        """Print a formatted header."""
        self.stdout.write(self.style.SUCCESS('═' * 70))
        self.stdout.write(self.style.SUCCESS(title))
        self.stdout.write(self.style.SUCCESS('═' * 70))

