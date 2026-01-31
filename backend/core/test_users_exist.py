import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from shop_users.models import ShopUser

# Get tenant
tenant = Tenant.objects.filter(slug='mcmillan-gatsi').first()
print(f"Tenant: {tenant.name}")
print(f"DB alias: {tenant.db_alias}")

# Get all users
users = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id)
print(f"\nUsers count: {users.count()}")
for user in users:
    print(f"  - {user.username}: role={user.role}, is_superuser={user.is_superuser}")
