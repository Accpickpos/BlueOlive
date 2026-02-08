"""
Base command class for all seeding operations.
Provides common functionality and error handling.
"""
from django.core.management.base import BaseCommand, CommandError
from apps.settings.seeding_utils import (
    get_tenant, get_shop, get_or_create_admin_user, set_seeding_context,
    clear_seeding_context, SeedingException
)


class BaseSeedCommand(BaseCommand):
    """
    Base class for all seeding commands.
    Provides common argument handling and error management.
    """
    
    # Subclasses should define these
    COMMAND_TITLE = "Seeding Data"
    COMMAND_DESCRIPTION = "Seed data for development/testing"
    STEP_NUMBER = None  # e.g., "1/4"
    
    def add_arguments(self, parser):
        """Add common arguments to all seeding commands."""
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Tenant ID to seed data for (defaults to first tenant)'
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            help='Tenant slug to seed data for'
        )
        parser.add_argument(
            '--shop-id',
            type=int,
            help='Shop ID to seed data for (defaults to first active shop)'
        )
        parser.add_argument(
            '--shop-slug',
            type=str,
            help='Shop slug to seed data for'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be seeded without creating data'
        )
    
    def handle(self, *args, **options):
        """
        Main entry point for seeding command.
        Handles setup and cleanup automatically.
        """
        try:
            # Print header
            step = f"[{self.STEP_NUMBER}] " if self.STEP_NUMBER else ""
            self.print_header(f"{step}{self.COMMAND_TITLE}")
            
            # Get tenant and shop
            tenant_id = options.get('tenant_id')
            tenant_slug = options.get('tenant_slug')
            tenant = get_tenant(tenant_id=tenant_id, tenant_slug=tenant_slug)
            
            shop_id = options.get('shop_id')
            shop_slug = options.get('shop_slug')
            shop = get_shop(tenant, shop_id=shop_id, shop_slug=shop_slug)
            
            # Get admin user
            user = get_or_create_admin_user()
            
            # Print context info
            self.stdout.write(self.style.SUCCESS(f'\n📍 Tenant: {tenant.name}'))
            self.stdout.write(self.style.SUCCESS(f'   Database: {tenant.db_name}'))
            self.stdout.write(self.style.SUCCESS(f'   Shop: {shop.name} (schema: {shop.schema_name})'))
            self.stdout.write(self.style.SUCCESS(f'   Admin: {user.username}\n'))
            
            # Set context
            set_seeding_context(tenant, shop)
            
            # Get options
            dry_run = options.get('dry_run', False)
            
            # Call subclass seed method
            self.seed(user=user, tenant=tenant, shop=shop, dry_run=dry_run, **options)
            
            # Success message
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ {self.COMMAND_DESCRIPTION} completed successfully!'
            ))
            
        except SeedingException as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Seeding Error: {str(e)}'))
            raise CommandError(str(e))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ Unexpected error: {str(e)}'))
            import traceback
            traceback.print_exc()
            raise CommandError(str(e))
        finally:
            clear_seeding_context()
    
    def seed(self, user, tenant, shop, dry_run=False, **options):
        """
        Subclasses should override this method to implement seeding logic.
        
        Args:
            user: Admin user for creation tracking
            tenant: Tenant being seeded
            shop: Shop being seeded
            dry_run: If True, show what would be done without creating data
            **options: Additional command options
        """
        raise NotImplementedError("Subclasses must implement the seed() method")
    
    def print_header(self, title):
        """Print a formatted header."""
        self.stdout.write(self.style.SUCCESS('═' * 70))
        self.stdout.write(self.style.SUCCESS(title))
        self.stdout.write(self.style.SUCCESS('═' * 70))
    
    def print_section(self, section_title):
        """Print a formatted section header."""
        self.stdout.write(self.style.WARNING(f'\n{section_title}'))
        self.stdout.write(self.style.WARNING('─' * 70))
    
    def success(self, message):
        """Print a success message."""
        self.stdout.write(f'  ✓ {message}')
    
    def skip(self, message):
        """Print a skip message."""
        self.stdout.write(f'  ⊘ {message}')
    
    def error(self, message):
        """Print an error message."""
        self.stdout.write(self.style.ERROR(f'  ✗ {message}'))
    
    def info(self, message):
        """Print an info message."""
        self.stdout.write(f'  → {message}')
