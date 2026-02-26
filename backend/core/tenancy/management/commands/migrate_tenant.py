# tenancy/management/commands/migrate_tenant.py
from django.core.management.base import BaseCommand
from tenancy.models import Tenant
from tenancy.shop_manager import migrate_tenant_database


class Command(BaseCommand):
    help = 'Migrate a specific tenant database by slug'

    def add_arguments(self, parser):
        parser.add_argument(
            '--slug',
            type=str,
            required=True,
            help='Tenant slug to migrate',
        )

    def handle(self, *args, **options):
        slug = options['slug']
        
        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Tenant not found: {slug}"))
            return

        self.stdout.write(f"Migrating tenant: {tenant.name} ({tenant.slug})")
        
        try:
            migrate_tenant_database(tenant)
            self.stdout.write(self.style.SUCCESS(f"✓ {tenant.slug} migrated successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ {tenant.slug} failed: {str(e)}"))
