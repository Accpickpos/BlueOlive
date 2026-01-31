import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant, Shop

# Get all tenants and their shops
tenants = Tenant.objects.all()
for tenant in tenants:
    shops = Shop.objects.filter(tenant=tenant)
    print(f"\nTenant: {tenant.name}")
    print(f"  Shops count: {shops.count()}")
    for shop in shops:
        print(f"    - {shop.id}: {shop.name}")
