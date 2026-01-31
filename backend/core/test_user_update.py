import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.tenant_context import set_current_tenant
from tenancy.models import Tenant
from shop_users.models import ShopUser
from shop_users.serializers import ShopUserSerializer

# Get tenant
tenant = Tenant.objects.filter(slug='mcmillan-gatsi').first()
set_current_tenant(tenant)

# Get a user to update
user = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id, role='ADMIN').first()

print(f"User: {user.username}")
print(f"Current role: {user.role}")
print(f"Current shop_ids: {user.shop_ids}")

# Try updating with serializer
update_data = {
    'role': 'MANAGER',
    'is_active': True,
    'shop_ids': [1, 10]  # Some shop IDs
}

serializer = ShopUserSerializer(user, data=update_data, partial=True)

if serializer.is_valid():
    print(f"\nSerialization valid!")
    print(f"Validated data: {serializer.validated_data}")
    serializer.save(using=tenant.db_alias)
    print(f"Updated successfully!")
else:
    print(f"\nSerialization errors:")
    print(serializer.errors)
