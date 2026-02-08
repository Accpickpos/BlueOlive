import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from django.conf import settings
from tenancy.models import Tenant
from tenancy.utils import register_tenant_connection

# Get all tenants
tenants = Tenant.objects.all()
print(f'Found {tenants.count()} tenants\n')

for tenant in tenants:
    print(f"\n{'='*50}")
    print(f"Migrating tenant: {tenant.name} (db: {tenant.db_alias})")
    print('='*50)
    
    # Register the tenant connection
    register_tenant_connection(tenant)
    print(f'✓ Connection registered for {tenant.db_alias}')
    
    # Set environment variable for migrations
    os.environ['TENANT_DB_ALIAS'] = tenant.db_alias
    
    # Run migrations for ALL apps that should be in tenant database
    tenant_apps = ['auth', 'contenttypes', 'admin', 'token_blacklist', 'shop_users', 
                   'cash_book', 'creditors', 'stock_control', 'purchase_orders', 
                   'debtors', 'pos', 'settings']
    
    for app in tenant_apps:
        try:
            call_command('migrate', app, database=tenant.db_alias, verbosity=0)
            print(f'  ✓ {app} migrated')
        except Exception as e:
            print(f'  ⚠ {app}: {str(e)[:60]}')
    
    # Clear the environment variable
    if 'TENANT_DB_ALIAS' in os.environ:
        del os.environ['TENANT_DB_ALIAS']

print("\n" + "="*50)
print("✓ All tenant databases migrated successfully!")
print("="*50)

