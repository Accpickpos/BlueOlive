#!/usr/bin/env python
"""Clear debtors and dependent migrations, then reapply in order."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ['TENANT_DB_ALIAS'] = 'tenant_1'

django.setup()

from django.db import connections
from django.core.management import call_command

alias = 'tenant_1'
conn = connections[alias]

print("=" * 60)
print(f"Fixing debtors migrations for {alias} database...")
print("=" * 60)

# All tenant apps - clear and reapply
# Also clearing admin and token_blacklist because they depend on shop_users
apps_to_fix = ['debtors', 'creditors', 'stock_control', 'cash_book', 'purchase_orders', 'pos', 'shop_users', 'settings', 'admin', 'token_blacklist']

print(f"\nClearing migration records for: {', '.join(apps_to_fix)}")
with conn.cursor() as cursor:
    for app in apps_to_fix:
        cursor.execute("DELETE FROM django_migrations WHERE app = %s", [app])
    conn.commit()
    print("✓ Cleared migration records")

# Reapply migrations in the correct order
print(f"\nReapplying migrations in order...")
for app in apps_to_fix:
    print(f"\n  Applying {app}...")
    try:
        call_command('migrate', app, database=alias, verbosity=1)
        print(f"  ✓ {app} migrated")
    except Exception as e:
        print(f"  ✗ {app} error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Verify the table exists
print("\nVerifying debtors_debtor table...")
try:
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'debtors_debtor'
            );
        """)
        table_exists = cursor.fetchone()[0]
    
    if table_exists:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM debtors_debtor")
            count = cursor.fetchone()[0]
        print(f"✓ debtors_debtor table exists! Records: {count}")
    else:
        print("✗ debtors_debtor table still does not exist")
        sys.exit(1)
        
except Exception as e:
    print(f"✗ Error verifying table: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ SUCCESS! Debtors migrations applied to tenant_1")
print("=" * 60)
