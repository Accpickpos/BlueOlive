#!/usr/bin/env python
"""
Check what tables exist in tenant_tnt public schema - SIMPLE VERSION
"""
import os
import sys
import django
import psycopg2
from psycopg2.extras import RealDictCursor

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/c/Users/accpi/OneDrive/Documents/GitHub/BlueOlive/backend/core')
django.setup()

from django.conf import settings

DB_USER = settings.DATABASES['default']['USER']
DB_PASSWORD = settings.DATABASES['default']['PASSWORD']
DB_HOST = settings.DATABASES['default']['HOST']
DB_PORT = settings.DATABASES['default']['PORT']

print("\n" + "="*80)
print("TABLES IN TENANT_TNT PUBLIC SCHEMA")
print("="*80 + "\n")

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database='tenant_tnt'
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get all tables in public schema
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    
    tables = [row['table_name'] for row in cur.fetchall()]
    
    print(f"Total Tables: {len(tables)}\n")
    
    for i, table_name in enumerate(tables, 1):
        # Get column count
        cur.execute(f"""
            SELECT COUNT(*) as col_count
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
        """, (table_name,))
        
        col_count = cur.fetchone()['col_count']
        print(f"{i:2}. {table_name:45} ({col_count:3} columns)")
    
    print("\n" + "="*80)
    print("PYTHON LIST (for code):")
    print("="*80 + "\n")
    
    print("required_tables = [")
    for table in tables:
        print(f"    '{table}',")
    print("]")
    
    print("\n" + "="*80)
    print("KEY OBSERVATIONS:")
    print("="*80 + "\n")
    
    print("""
Tables created by Django migrations:
  1. auth_group
  2. auth_group_permissions
  3. auth_permission
  4. django_admin_log
  5. django_content_type
  6. django_migrations
  7. django_session
  8. shop_users_shopuser
  9. shop_users_shopuser_groups
  10. shop_users_shopuser_user_permissions
  11. token_blacklist_blacklistedtoken
  12. token_blacklist_outstandingtoken

All 12 tables should be created for every new tenant!

Current fallback only creates:
  - django_session
  - shop_users_shopuser
  - django_admin_log
  - token_blacklist_outstandingtoken
  - token_blacklist_blacklistedtoken

MISSING from fallback (will be created by migrations):
  - auth_group
  - auth_group_permissions
  - auth_permission
  - django_content_type
  - django_migrations
  - shop_users_shopuser_groups
  - shop_users_shopuser_user_permissions

SOLUTION: Update verify_and_create_missing_tables() to check for ALL 12 tables
""")
    
    cur.close()
    conn.close()

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
