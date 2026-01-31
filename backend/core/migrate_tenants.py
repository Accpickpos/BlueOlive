import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from tenancy.models import Tenant

# Get all tenants
tenants = Tenant.objects.all()

for tenant in tenants:
    print(f"\n{'='*50}")
    print(f"Migrating tenant: {tenant.name} (db: {tenant.db_alias})")
    print('='*50)
    
    # Run migration for this tenant database
    call_command('migrate', 'shop_users', database=tenant.db_alias)

print("\n" + "="*50)
print("All tenant databases migrated successfully!")
print("="*50)
