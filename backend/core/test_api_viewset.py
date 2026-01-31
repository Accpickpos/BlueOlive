import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.tenant_context import set_current_tenant
from tenancy.models import Tenant
from shop_users.models import ShopUser
from shop_users.views import ShopUserViewSet
from django.test import RequestFactory
from rest_framework.test import force_authenticate

# Get tenant_1
tenant = Tenant.objects.filter(slug='mcmillan-gatsi').first()
print(f"Testing tenant: {tenant.name} (db_alias: {tenant.db_alias})")

# Set tenant context
set_current_tenant(tenant)

# Get admin user
admin_user = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id, role='ADMIN').first()
print(f"Admin user: {admin_user.username if admin_user else 'Not found'}")
print(f"  is_superuser: {admin_user.is_superuser}")
print(f"  role: {admin_user.role}")

# Create mock request
factory = RequestFactory()
request = factory.get('/api/users/')
force_authenticate(request, user=admin_user)

# Create viewset
viewset = ShopUserViewSet()
viewset.request = request
viewset.format_kwarg = None
viewset.action = 'list'

# Get queryset
queryset = viewset.get_queryset()
print(f"\nViewset get_queryset count: {queryset.count()}")
for user in queryset:
    print(f"  - {user.username}: role={user.role}")


