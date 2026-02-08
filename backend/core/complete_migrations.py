#!/usr/bin/env python
"""
Complete the remaining migrations one by one with better error handling.
"""

import os
import sys
import django

# Setup Django
os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from django.core.management import call_command

alias = 'tenant_1'
conn = connections[alias]

# Check which apps have already been migrated
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT DISTINCT app FROM django_migrations
    """)
    migrated_apps = set(row[0] for row in cursor.fetchall())
    print("Already migrated apps:")
    for app in sorted(migrated_apps):
        print(f"  - {app}")

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

pending_apps = [app for app in apps_to_migrate if app not in migrated_apps]

if not pending_apps:
    print("\n✓ All apps already migrated!")
else:
    print(f"\nApps needing migration ({len(pending_apps)}):")
    for app in pending_apps:
        print(f"  - {app}")
        
    print("\nRunning remaining migrations...\n")
    
    for app in pending_apps:
        try:
            print(f"  Migrating {app}...", end=" ", flush=True)
            call_command('migrate', app, database=alias, verbosity=0)
            print("✓ OK")
        except Exception as e:
            print(f"✗ ERROR: {type(e).__name__}: {str(e)[:100]}")

# Final table count
print("\n" + "="*80)
print("FINAL VERIFICATION")
print("="*80)

with conn.cursor() as cursor:
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'volt_gray' AND table_type = 'BASE TABLE'
    """)
    count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'volt_gray' AND table_name = 'debtors_debtor'
        )
    """)
    has_debtors = cursor.fetchone()[0]
    
    print(f"\n📊 Tables in volt_gray schema: {count}")
    
    if has_debtors:
        print(f"✅ debtors_debtor table: EXISTS")
    else:
        print(f"❌ debtors_debtor table: MISSING")
    
    if count > 10 and has_debtors:
        print("\n✅ SUCCESS! Schema migration complete!")
    else:
        print(f"\n⚠ WARNING: Expected more tables. Have {count}, debtors_table={has_debtors}")
