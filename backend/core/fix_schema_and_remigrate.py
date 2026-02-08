#!/usr/bin/env python
"""
Fix schema targeting for migrations by:
1. Cleaning all tables from both public and volt_gray schemas
2. Re-running migrations with the updated register_tenant_connection() that uses shop schema
3. Verifying tables are created in volt_gray schema
"""

import os
import sys
import django

# Setup Django
os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.db import connections
from django.core.management import call_command
from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection

# Get tenant
tenant = Tenant.objects.get(id=1)
shop = tenant.shops.first()

if not shop:
    print("❌ ERROR: No shop found for tenant_1")
    sys.exit(1)

schema_name = shop.schema_name
print(f"✓ Found tenant: {tenant.name}")
print(f"✓ Found shop: {shop.name}")
print(f"✓ Shop schema: {schema_name}")

alias = 'tenant_1'

print("\n" + "="*80)
print("PHASE 1: DROPPING ALL TABLES FROM BOTH SCHEMAS")
print("="*80)

conn = connections[alias]
with conn.cursor() as cursor:
    for target_schema in [schema_name, 'public']:
        print(f"\n🔍 Getting all tables in schema '{target_schema}'...")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
        """, [target_schema])
        
        tables = [row[0] for row in cursor.fetchall()]
        if not tables:
            print(f"   (no tables found)")
            continue
            
        print(f"   Found {len(tables)} tables")
        
        # Drop tables
        for table in tables:
            try:
                if target_schema == 'public':
                    # For public schema, only drop Django system tables
                    if table.startswith(('auth_', 'django_', 'token_', 'shop_users_')):
                        cursor.execute(f'DROP TABLE IF EXISTS "{target_schema}"."{table}" CASCADE')
                        print(f"   ✓ Dropped {target_schema}.{table}")
                else:
                    # For shop schema, drop everything
                    cursor.execute(f'DROP TABLE IF EXISTS "{target_schema}"."{table}" CASCADE')
                    print(f"   ✓ Dropped {target_schema}.{table}")
            except Exception as e:
                print(f"   ⚠ Error dropping {target_schema}.{table}: {e}")

# Clear django_migrations table to force re-migration (if it exists)
print(f"\n🔄 Clearing django_migrations table...")
with conn.cursor() as cursor:
    # Check if table exists first
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'django_migrations'
        )
    """)
    if cursor.fetchone()[0]:
        cursor.execute('DELETE FROM public."django_migrations"')
        print(f"   ✓ django_migrations cleared")
    else:
        print(f"   (table doesn't exist, will be recreated)")

print("\n" + "="*80)
print("PHASE 2: RE-REGISTERING TENANT CONNECTION WITH SHOP SCHEMA")
print("="*80)

print(f"\n🔄 Re-registering tenant connection with search_path='{schema_name},public'...")
register_tenant_connection(tenant)

# Verify the connection config
db_config = settings.DATABASES[alias]
print(f"\nDatabase config for '{alias}':")
print(f"  - NAME: {db_config['NAME']}")
print(f"  - OPTIONS: {db_config.get('OPTIONS', {})}")

print("\n" + "="*80)
print("PHASE 3: RUNNING MIGRATIONS")
print("="*80)

apps_to_migrate = [
    'auth',
    'contenttypes',
    'admin',
    'token_blacklist',
    'shop_users',
    'cash_book',
    'debtors',
    'creditors',
    'stock_control',
    'purchase_orders',
    'pos',
    'settings'
]

print(f"\n🔄 Running migrations for {len(apps_to_migrate)} apps...\n")

for app in apps_to_migrate:
    try:
        print(f"  Migrating {app}...", end=" ", flush=True)
        call_command('migrate', app, database=alias, verbosity=0)
        print("✓ OK")
    except Exception as e:
        print(f"✗ ERROR: {e}")

print("\n" + "="*80)
print("PHASE 4: VERIFYING TABLE CREATION")
print("="*80)

with conn.cursor() as cursor:
    for target_schema in [schema_name, 'public']:
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
        """, [target_schema])
        count = cursor.fetchone()[0]
        print(f"\n📊 Tables in '{target_schema}' schema: {count}")
        
        if count > 0:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, [target_schema])
            for table in cursor.fetchall():
                print(f"   - {table[0]}")

# Final verification
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = %s AND table_type = 'BASE TABLE'
    """, [schema_name])
    debtors_table_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'debtors_debtor'
        )
    """, [schema_name])
    has_debtors_table = cursor.fetchone()[0]

print("\n" + "="*80)
print("FINAL RESULT")
print("="*80)

if debtors_table_count > 0 and has_debtors_table:
    print(f"\n✅ SUCCESS!")
    print(f"   Tables created in correct schema: {schema_name}")
    print(f"   Total tables: {debtors_table_count}")
    print(f"   debtors_debtor table: EXISTS ✓")
else:
    print(f"\n❌ FAILED!")
    print(f"   Tables in {schema_name}: {debtors_table_count}")
    if not has_debtors_table:
        print(f"   debtors_debtor table: MISSING ✗")
