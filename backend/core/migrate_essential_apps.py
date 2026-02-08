#!/usr/bin/env python
"""
Migrate only essential apps carefully, one by one with proper error handling.
Focus on getting debtors working.
"""

import os
import sys
import django

os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from django.core.management import call_command

alias = 'tenant_1'
conn = connections[alias]

# Check what's already migrated
with conn.cursor() as cursor:
    cursor.execute("SELECT DISTINCT app FROM django_migrations ORDER BY app")
    already_migrated = set(row[0] for row in cursor.fetchall())
    
print("Apps already migrated:")
for app in sorted(already_migrated):
    print(f"  ✓ {app}")

# Focus on these apps in order
essential_apps = [
    ('debtors', True),      # CRITICAL - this is what we need
    ('cash_book', False),   # needed for FK relationships
    ('creditors', False),
    ('stock_control', False),
    ('purchase_orders', False),
    ('settings', False),
    ('pos', False),
]

missing_apps = [app for app, critical in essential_apps if app not in already_migrated]

if not missing_apps:
    print("\n✓ All essential apps already migrated")
else:
    print(f"\nMissing apps ({len(missing_apps)}):")
    for app in missing_apps:
        print(f"  - {app}")
    
    print("\nMigrating apps one by one...\n")
    
    for app, critical in essential_apps:
        if app not in already_migrated:
            try:
                print(f"  [{app}] Running...", end=" ", flush=True)
                call_command('migrate', app, database=alias, verbosity=0, no_input=True)
                print("✓ OK")
            except KeyboardInterrupt:
                print("(interrupted)")
                break
            except Exception as e:
                errmsg = str(e)[:60]
                if critical:
                    print(f"✗ CRITICAL ERROR: {errmsg}")
                    print(f"\n    Full error: {e}")
                    sys.exit(1)
                else:
                    print(f"⚠ ERROR (skipped): {errmsg}")

# Verify debtors
print("\n" + "="*70)
print("VERIFICATION")
print("="*70)

with conn.cursor() as cursor:
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'volt_gray' AND table_name = 'debtors_debtor'
        )
    """)
    has_debtors = cursor.fetchone()[0]
    
    if has_debtors:
        cursor.execute("SELECT COUNT(*) FROM debtors_debtor")
        count = cursor.fetchone()[0]
        print(f"\n✅ SUCCESS!")
        print(f"   debtors_debtor table: EXISTS in volt_gray")
        print(f"   Records: {count}")
    else:
        # Check if it's in public
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'debtors_debtor'
            )
        """)
        if cursor.fetchone()[0]:
            print(f"\n⚠ debtors_debtor is in PUBLIC schema (should be in volt_gray)")
        else:
            print(f"\n✗ debtors_debtor table NOT FOUND in any schema")
    
    # Show all tables in volt_gray
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'volt_gray' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\nAll tables in volt_gray: {len(tables)}")
    for t in tables:
        print(f"   - {t}")
