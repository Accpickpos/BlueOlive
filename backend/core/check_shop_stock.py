#!/usr/bin/env python
"""
Check stock items in specific shop schema.
Run from backend/core directory: python check_shop_stock.py
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import connections  # noqa: E402
from tenancy.models import Shop, Tenant  # noqa: E402
from tenancy.tenant_context import set_current_shop  # noqa: E402
from tenancy.utils import register_tenant_connection  # noqa: E402

print("=" * 60)
print("CHECKING STOCK ITEMS BY SHOP SCHEMA")
print("=" * 60)

# Get Acme tenant
tenant = Tenant.objects.get(slug="acme")
print(f"\nTenant: {tenant.name}")

# Register connection
register_tenant_connection(tenant)

# Get all shops for Acme
shops = Shop.objects.filter(tenant=tenant, is_active=True)
print(f"Found {shops.count()} shops:")

for shop in shops:
    print(f"\n--- Shop: {shop.name} (schema: {shop.schema_name}) ---")

    # Set the shop schema
    set_current_shop(shop.schema_name)

    # Re-register connection with specific shop
    register_tenant_connection(tenant, shop=shop)

    # Check stock items
    try:
        from apps.stock_control.models import StockItem

        db_alias = tenant.db_alias

        # Set search path for this connection
        with connections[db_alias].cursor() as cursor:
            cursor.execute(f'SET search_path TO "{shop.schema_name}", public')

        # Now query
        count = StockItem.objects.using(db_alias).count()
        print(f"Stock items: {count}")

        if count > 0:
            items = StockItem.objects.using(db_alias).all()[:5]
            print("Sample items:")
            for item in items:
                print(f"  - {item.stock_code}: {item.description}")
        else:
            print("⚠️  No stock items in this schema")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
