#!/usr/bin/env python
"""
Check stock items in tenant database.
Run from backend/core directory: python check_stock.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant, Shop

print("=" * 60)
print("CHECKING STOCK ITEMS IN TENANT DATABASE")
print("=" * 60)

# Get all tenants
tenants = Tenant.objects.all()
print(f"\nFound {tenants.count()} tenant(s):")

for tenant in tenants:
    print(f"\n--- Tenant: {tenant.name} (slug: {tenant.slug}) ---")
    
    # Register connection
    from tenancy.utils import register_tenant_connection
    register_tenant_connection(tenant)
    
    db_alias = tenant.db_alias
    print(f"Database alias: {db_alias}")
    
    # Check shops
    shops = Shop.objects.filter(tenant=tenant, is_active=True)
    print(f"Shops: {shops.count()}")
    for shop in shops:
        print(f"  - {shop.name} (schema: {shop.schema_name})")
    
    # Check stock items
    try:
        from apps.stock_control.models import StockItem
        count = StockItem.objects.using(db_alias).count()
        print(f"Stock items in {db_alias}: {count}")
        
        if count > 0:
            # Show first few items
            items = StockItem.objects.using(db_alias).all()[:5]
            print("Sample items:")
            for item in items:
                print(f"  - {item.stock_code}: {item.description}")
        else:
            print("⚠️  No stock items found! You need to import stock data.")
    except Exception as e:
        print(f"Error checking stock: {e}")

print("\n" + "=" * 60)
print("DONE")
print("=" * 60)
