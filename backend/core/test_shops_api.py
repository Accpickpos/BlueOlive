import os
import django
from django.test import RequestFactory

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.middleware import TenantMiddleware
from tenancy.tenant_context import get_current_tenant
from tenancy.views import ShopViewSet
from shop_users.models import ShopUser
from rest_framework.test import force_authenticate
from tenancy.models import Tenant

# Get a test user
tenant = Tenant.objects.filter(slug='mcmillan-gatsi').first()
user = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id, role='ADMIN').first()

print(f"User: {user.username}")
print(f"Tenant: {tenant.name}")

# Create a mock request
factory = RequestFactory()
request = factory.get('/api/shops/', HTTP_HOST='mcmillan-gatsi.localhost:3000')

# Apply middleware
middleware = TenantMiddleware(lambda r: None)

# Force authenticate
force_authenticate(request, user=user)

print(f"\nRequest tenant context: {get_current_tenant()}")

# Test the viewset
viewset = ShopViewSet()
viewset.request = request
viewset.action = 'list'

try:
    queryset = viewset.get_queryset()
    print(f"ShopViewSet queryset count: {queryset.count()}")
    for shop in queryset:
        print(f"  - {shop.name}")
except Exception as e:
    print(f"Error: {e}")
