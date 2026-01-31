import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from shop_users.models import ShopUser
from tenancy.tenant_context import set_current_tenant
from shop_users.serializers import ShopUserSerializer

# Get tenant_1 (McMillan Gatsi)
tenant = Tenant.objects.filter(slug='mcmillan-gatsi').first()
print(f"Current tenant: {tenant.name} (db_alias: {tenant.db_alias})")

# Set tenant context
set_current_tenant(tenant)

# Get users like the API does
users = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id)
print(f"\nTotal users in tenant: {users.count()}")

# Serialize them
serializer = ShopUserSerializer(users, many=True)
print(f"\nSerialized data:")
print(json.dumps(serializer.data, indent=2))
