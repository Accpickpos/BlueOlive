#!/usr/bin/env python
"""Drop and recreate debtors_debtor table."""
import os
import django

os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from django.core.management import call_command

alias = 'tenant_1'
conn = connections[alias]

print("Cleaning up debtors schema...")
cursor = conn.cursor()

# Drop the table
cursor.execute('DROP TABLE IF EXISTS debtors_debtor CASCADE')
print("✓ Dropped debtors_debtor table")

# Delete migration records for debtors and dependent apps
for app in ['debtors', 'creditors', 'stock_control', 'purchase_orders', 'pos', 'cash_book']:
    cursor.execute('DELETE FROM django_migrations WHERE app = %s', [app])
    print(f"✓ Cleared {app} migration records")

conn.commit()

# Now reapply migrations
print("\nReapplying migrations in correct order...")
apps_in_order = ['debtors', 'creditors', 'stock_control', 'purchase_orders', 'cash_book']

for app in apps_in_order:
    print(f"\n  Applying {app}...")
    try:
        os.environ['TENANT_DB_ALIAS'] = alias
        call_command('migrate', app, database=alias, verbosity=1)
        print(f"  ✓ {app} migrated successfully")
    except Exception as e:
        print(f"  ✗ {app} error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("Verifying debtors_debtor table...")
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'debtors_debtor'
    );
""")
table_exists = cursor.fetchone()[0]

if table_exists:
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'debtors_debtor' 
        ORDER BY ordinal_position 
        LIMIT 10
    """)
    print("✓ debtors_debtor table exists with columns:")
    for (col,) in cursor.fetchall():
        print(f"  - {col}")
else:
    print("✗ debtors_debtor table still does not exist!")
