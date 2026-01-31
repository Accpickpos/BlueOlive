import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from shop_users.models import ShopUser

# Get all tenants
tenants = Tenant.objects.all()
print(f"Total tenants: {tenants.count()}")

for tenant in tenants:
    print(f"\nTenant: {tenant.name} (db_alias: {tenant.db_alias})")
    # Query users from tenant database
    users = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id)
    print(f"  Users count: {users.count()}")
    for user in users:
        is_admin = user.is_superuser or user.role == 'ADMIN'
        print(f"    - {user.username} ({user.email}) - admin: {is_admin}")
