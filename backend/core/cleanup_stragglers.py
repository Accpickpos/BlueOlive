#!/usr/bin/env python
"""Remove remaining shop tables from public schema."""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant

# Additional tables that snuck through
TABLES_TO_DROP = ['bundles', 'creditors']

print("=" * 70)
print("ADDITIONAL CLEANUP: Removing stragglers from public schema")
print("=" * 70)

for tenant in Tenant.objects.all():
    print(f"\nTenant: {tenant.name}")
    
    alias = tenant.db_alias
    conn = connections[alias]
    
    with conn.cursor() as cur:
        # Check which tables exist
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = ANY(%s)
        """, [TABLES_TO_DROP])
        tables_to_drop = [row[0] for row in cur.fetchall()]
        
        if tables_to_drop:
            print(f"  Found tables to drop: {tables_to_drop}")
            for table in tables_to_drop:
                try:
                    cur.execute(f'DROP TABLE IF EXISTS public."{table}" CASCADE')
                    print(f"    ✓ Dropped: {table}")
                except Exception as e:
                    print(f"    ✗ Error: {e}")
            conn.commit()
            print(f"  ✓ Done")
        else:
            print(f"  No straggler tables found")

print("\nDone!")
