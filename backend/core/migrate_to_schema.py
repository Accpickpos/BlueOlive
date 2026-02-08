#!/usr/bin/env python
"""Properly migrate all apps to the tenant schema."""
import os
import django

os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from django.core.management import call_command
from tenancy.models import Tenant, Shop

tenant = Tenant.objects.get(id=1)
alias = tenant.db_alias
shop = tenant.shops.filter(is_active=True).first()
schema_name = shop.schema_name

print("=" * 70)
print(f"Migrating apps to tenant schema: {schema_name}")
print(f"Database alias: {alias}")
print("=" * 70)

conn = connections[alias]
cursor = conn.cursor()

# First, create the schema if it doesn't exist
print(f"\nEnsuring schema '{schema_name}' exists...")
cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
conn.commit()
print(f"Schema ready")

# Set search path for this connection
print(f"\nSetting search_path to '{schema_name}'...")
cursor.execute(f'SET search_path TO "{schema_name}", public')
conn.commit()

# Now run migrations with search_path set
print(f"\n" + "=" * 70)
print("Running migrations...")
print("=" * 70)

os.environ['TENANT_DB_ALIAS'] = alias

apps_in_order = [
    'auth', 'contenttypes', 'admin', 'token_blacklist', 
    'shop_users', 'cash_book', 'debtors', 'creditors', 
    'stock_control', 'purchase_orders', 'pos', 'settings'
]

for app in apps_in_order:
    print(f"\n  Applying {app}...")
    try:
        call_command('migrate', app, database=alias, verbosity=0)
        print(f"  OK: {app} migrated")
    except Exception as e:
        error_msg = str(e).split('\n')[0][:70]
        print(f"  FAIL: {app} - {error_msg}")
        continue

print(f"\n" + "=" * 70)
print("Verifying tables in tenant schema...")
print("=" * 70)

# Set search path again and check tables
cursor.execute(f'SET search_path TO "{schema_name}", public')
cursor.execute("""
    SELECT COUNT(*) FROM information_schema.tables 
    WHERE table_schema = %s AND table_type = 'BASE TABLE'
""", [schema_name])

table_count = cursor.fetchone()[0]
print(f"\nFinal table count in schema '{schema_name}': {table_count}")

if table_count == 0:
    print("WARNING: No tables were created in the tenant schema!")
    print("\nTables in public schema:")
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name LIMIT 20
    """)
    for (table,) in cursor.fetchall():
        print(f"  - {table}")
else:
    print("SUCCESS: Tables created in tenant schema")
    
    # Show some example tables
    cursor.execute(f"""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
        ORDER BY table_name LIMIT 10
    """, [schema_name])
    print("\nExample tables:")
    for (table,) in cursor.fetchall():
        print(f"  - {table}")
