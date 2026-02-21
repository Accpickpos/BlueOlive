# tenancy/management/commands/migrate_all_tenants.py
from django.core.management.base import BaseCommand
from tenancy.models import Tenant
from tenancy.shop_manager import migrate_tenant_database


class Command(BaseCommand):
    help = 'Migrate all tenant databases'

    def handle(self, *args, **options):
        tenants = Tenant.objects.all()
        
        self.stdout.write(f"Found {tenants.count()} tenants to migrate")
        
        for tenant in tenants:
            self.stdout.write(f"\nMigrating: {tenant.name} ({tenant.db_alias})")
            try:
                migrate_tenant_database(tenant)
                self.stdout.write(self.style.SUCCESS(f"✓ {tenant.slug} migrated"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ {tenant.slug} failed: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS("\n✓ All tenants processed"))