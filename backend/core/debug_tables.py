#!/usr/bin/env python
"""
Debug signup issue - check table creation status.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from django.db import connections
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get the last created tenant
tenants = Tenant.objects.all().order_by('-id')
if not tenants:
    print("No tenants found")
    sys.exit(1)

latest_tenant = tenants[0]
print(f"\nChecking tenant: {latest_tenant.name} (ID: {latest_tenant.id})")
print(f"Database: {latest_tenant.db_name}")

alias = f'tenant_{latest_tenant.id}'
print(f"Alias: {alias}")

try:
    conn = connections[alias]
    
    # Check if token_blacklist tables exist
    with conn.cursor() as cur:
        cur.execute('SET search_path TO public')
        
        tables_to_check = [
            'token_blacklist_outstandingtoken',
            'token_blacklist_blacklistedtoken',
            'shop_users_shopuser',
            'django_migrations'
        ]
        
        print(f"\nChecking tables in {latest_tenant.db_name}:")
        for table_name in tables_to_check:
            cur.execute(f"""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table_name,))
            exists = cur.fetchone()[0]
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"  {table_name}: {status}")
        
        # Check what's in django_migrations
        print(f"\nMigrations applied in {latest_tenant.db_name}:")
        cur.execute("""
            SELECT app, COUNT(*) as count
            FROM django_migrations
            GROUP BY app
            ORDER BY app
        """)
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} migrations")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
