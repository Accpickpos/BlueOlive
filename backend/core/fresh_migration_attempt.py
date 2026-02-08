#!/usr/bin/env python
"""
Fresh migration attempt with detailed logging.
Clear migration history and start completely fresh.
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

print("="*70)
print("FRESH MIGRATION ATTEMPT")
print("="*70)

# Step 0: Drop all existing tables in volt_gray
print("\n[0] Dropping all existing tables...")
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'volt_gray' AND table_type = 'BASE TABLE'
    """)
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        try:
            cursor.execute(f'DROP TABLE IF EXISTS volt_gray."{table}" CASCADE')
            print(f"    [OK] Dropped {table}")
        except Exception as e:
            print(f"    [ERROR] Could not drop {table}: {e}")

# Step 1: Clear all migration history (if table still exists)
print("\n[1] Clearing migration history...")
with conn.cursor() as cursor:
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'volt_gray' AND table_name = 'django_migrations'
        )
    """)
    if cursor.fetchone()[0]:
        cursor.execute("DELETE FROM django_migrations")
        print("    [OK] Cleared existing migration history")
    else:
        print("    [OK] django_migrations doesn't exist (will be created)")

# Step 2:  Run auth and contenttypes first (system migrations)
print("\n[2] Running system migrations (auth, contenttypes)...")
for app in ['auth', 'contenttypes']:
    try:
        print(f"    {app}...", end=" ", flush=True)
        call_command('migrate', app, database=alias, verbosity=0)
        print("OK")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

# Step 3: Run admin
print("\n[3] Running admin migration...")
try:
    call_command('migrate', 'admin', database=alias, verbosity=0)
    print("    [OK] admin")
except Exception as e:
    print(f"    [ERROR] admin: {e}")

# Step 4: Run token_blacklist
print("\n[4] Running token_blacklist migration...")
try:
    call_command('migrate', 'token_blacklist', database=alias, verbosity=0)
    print("    [OK] token_blacklist")
except Exception as e:
    print(f"    [ERROR] token_blacklist: {e}")

# Step 5: Run shop_users
print("\n[5] Running shop_users migration...")
try:
    call_command('migrate', 'shop_users', database=alias, verbosity=0)
    print("    [OK] shop_users")
except Exception as e:
    print(f"    [ERROR] shop_users: {e}")

# Step 6: RUN DEBTORS (the critical one)
print("\n[6] Running DEBTORS migration (CRITICAL)...")
try:
    call_command('migrate', 'debtors', database=alias, verbosity=0)
    print("    [OK] debtors")
except Exception as e:
    print(f"    [ERROR] debtors: {e}")
    import traceback
    traceback.print_exc()

# Final check
print("\n" + "="*70)
print("FINAL VERIFICATION")
print("="*70)

with conn.cursor() as cursor:
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'volt_gray' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nTables in volt_gray: {len(tables)}")
    for t in tables:
        print(f"   - {t}")
    
    if 'debtors_debtor' in tables:
        print("\n[SUCCESS] debtors_debtor found!")
    else:
        print("\n[FAILURE] debtors_debtor NOT found")
