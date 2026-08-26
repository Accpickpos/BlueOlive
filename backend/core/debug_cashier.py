#!/usr/bin/env python
"""
Debug: Check cashier user details
"""

import os

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django  # noqa: E402

django.setup()

from django.db import connections  # noqa: E402
from tenancy.models import Shop, Tenant  # noqa: E402

# Get Acme tenant
tenant = Tenant.objects.get(slug="acme")
print(f"Tenant: {tenant.name}")

# Register tenant connection
from tenancy.utils import register_tenant_connection  # noqa: E402

register_tenant_connection(tenant)

db_alias = tenant.db_alias
print(f"Database: {db_alias}")

# Get shop-specific alias based on first shop
shop = tenant.shops.first()
if shop:
    shop_alias = f"{db_alias}_{shop.name.lower().replace(' ', '_')}"
else:
    shop_alias = db_alias

print(f"Shop: {shop.name if shop else 'None'}, Alias: {shop_alias}")

# Check tables in shop schema
print("\n=== Tables in first shop schema ===")
cursor = connections[shop_alias].cursor()
cursor.execute(
    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'acme_main' ORDER BY table_name"
)
tables = cursor.fetchall()
for t in tables[:15]:
    print(f"  {t[0]}")

# Check users
print("\n=== Users in tenant database ===")
cursor.execute(
    "SELECT id, username, role, shop_ids FROM shop_users_shopuser ORDER BY id"
)
users = cursor.fetchall()
for u in users:
    print(f"  ID:{u[0]} User:{u[1]} Role:{u[2]} Shops:{u[3]}")

# Get shops from default db
print("\n=== Shops for Acme ===")
shops = Shop.objects.filter(tenant=tenant, is_active=True)
for s in shops:
    print(f"  ID:{s.id} Name:{s.name} Schema:{s.schema_name}")

print("\nDone!")
