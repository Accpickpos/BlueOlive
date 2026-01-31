import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.tenant_context import set_current_tenant
from tenancy.models import Tenant
from shop_users.models import ShopUser
from shop_users.views import ProfileView
from django.test import RequestFactory
from rest_framework.test import force_authenticate

# Get tenant
tenant = Tenant.objects.filter(slug='mcmillan-gatsi').first()
set_current_tenant(tenant)

# Get admin user
user = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id, role='ADMIN').first()

print(f"User: {user.username}")
print(f"Role: {user.role}")
print(f"is_superuser: {user.is_superuser}")

# Create mock request
factory = RequestFactory()
request = factory.get('/api/auth/profile/')

# Authenticate as this user
force_authenticate(request, user=user)

# Test ProfileView
view = ProfileView.as_view()
response = view(request)

print(f"\nProfileView response:")
print(f"Status code: {response.status_code}")
print(f"Data: {response.data}")
