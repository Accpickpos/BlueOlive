#!/usr/bin/env python
"""
Export the exact schema from tenant_tnt for all 12 tables.
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections

def get_columns(alias, table_name):
    """Get column definitions for a table."""
    conn = connections[alias]
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                column_name,
                data_type,
                is_nullable,
                column_default,
                ordinal_position
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        return cur.fetchall()

def get_constraints(alias, table_name):
    """Get primary keys and unique constraints."""
    conn = connections[alias]
    with conn.cursor() as cur:
        # Get primary key
        cur.execute("""
            SELECT column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            WHERE tc.table_schema = 'public'
              AND tc.table_name = %s
              AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """, (table_name,))
        pk = cur.fetchall()
        
        return pk

def main():
    """Export schema from tenant_tnt."""
    tables = [
        'django_content_type',
        'django_migrations',
        'auth_permission',
        'auth_group',
        'auth_group_permissions',
        'django_session',
        'shop_users_shopuser',
        'shop_users_shopuser_groups',
        'shop_users_shopuser_user_permissions',
        'django_admin_log',
        'token_blacklist_outstandingtoken',
        'token_blacklist_blacklistedtoken',
    ]
    
    alias = 'tenant_2'  # TnT is ID 2
    
    for table in tables:
        print(f"\n{'='*80}")
        print(f"TABLE: {table}")
        print(f"{'='*80}")
        
        try:
            cols = get_columns(alias, table)
            if not cols:
                print(f"  ✗ Table does not exist!")
                continue
            
            print(f"  Columns: {len(cols)}")
            for col in cols:
                name, dtype, is_null, default, pos = col
                null_str = "NULL" if is_null == "YES" else "NOT NULL"
                default_str = f" DEFAULT {default}" if default else ""
                print(f"    {pos}. {name}: {dtype} {null_str}{default_str}")
            
            pk = get_constraints(alias, table)
            if pk:
                print(f"  Primary Key: {', '.join([col[0] for col in pk])}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    main()
