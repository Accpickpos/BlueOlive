#!/usr/bin/env python
"""
Check what tables exist in tenant_tnt public schema.
This will be our reference for what all new tenants should have.
"""
import os
import sys
import django
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/c/Users/accpi/OneDrive/Documents/GitHub/BlueOlive/backend/core')
django.setup()

from django.conf import settings

# Get DB credentials from settings
DB_USER = settings.DATABASES['default']['USER']
DB_PASSWORD = settings.DATABASES['default']['PASSWORD']
DB_HOST = settings.DATABASES['default']['HOST']
DB_PORT = settings.DATABASES['default']['PORT']

print("="*80)
print("CHECKING TENANT_TNT PUBLIC SCHEMA TABLES")
print("="*80)

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database='tenant_tnt'
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n1. TABLES IN PUBLIC SCHEMA:")
    print("-" * 80)
    
    # Get all tables in public schema
    cur.execute("""
        SELECT t.table_name, 
               array_agg(c.column_name ORDER BY c.ordinal_position) as columns
        FROM information_schema.tables t
        LEFT JOIN information_schema.columns c 
            ON t.table_schema = c.table_schema 
            AND t.table_name = c.table_name
        WHERE t.table_schema = 'public'
        GROUP BY t.table_name
        ORDER BY t.table_name
    """)
    
    tables = cur.fetchall()
    
    print(f"\nTotal tables: {len(tables)}\n")
    
    for i, row in enumerate(tables, 1):
        table_name = row['table_name']
        columns = row['columns'] if row['columns'] else []
        print(f"{i:2}. {table_name:45} ({len(columns)} columns)")
    
    print("\n" + "="*80)
    print("2. DETAILED TABLE INFORMATION:")
    print("="*80)
    
    for row in tables:
        table_name = row['table_name']
        print(f"\nTable: {table_name}")
        
        # Get column details
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cur.fetchall()
        print(f"  Columns ({len(columns)}):")
        for col in columns:
            nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
            default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
            print(f"    - {col['column_name']:35} {col['data_type']:20} {nullable}{default}")
        
        # Get primary key
        cur.execute("""
            SELECT constraint_name, column_name
            FROM information_schema.constraint_column_usage
            WHERE table_schema = 'public' AND table_name = %s
            AND constraint_name IN (
                SELECT constraint_name FROM information_schema.table_constraints
                WHERE table_schema = 'public' AND table_name = %s
                AND constraint_type = 'PRIMARY KEY'
            )
            ORDER BY ordinal_position
        """, (table_name, table_name))
        
        pk = cur.fetchall()
        if pk:
            print(f"  Primary Key: {', '.join([col['column_name'] for col in pk])}")
        
        # Get foreign keys
        cur.execute("""
            SELECT constraint_name, column_name, referenced_table_name, referenced_column_name
            FROM (
                SELECT 
                    kcu.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS referenced_table_name,
                    ccu.column_name AS referenced_column_name
                FROM information_schema.key_column_usage AS kcu
                JOIN information_schema.referential_constraints AS rc
                    ON kcu.constraint_name = rc.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON rc.unique_constraint_name = ccu.constraint_name
                WHERE kcu.table_schema = 'public' AND kcu.table_name = %s
            ) fks
            ORDER BY constraint_name, column_name
        """, (table_name,))
        
        fks = cur.fetchall()
        if fks:
            print(f"  Foreign Keys:")
            for fk in fks:
                print(f"    - {fk['column_name']} -> {fk['referenced_table_name']}.{fk['referenced_column_name']}")
        
        # Get indexes
        cur.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = %s
            AND indexname NOT LIKE 'pg_%'
        """, (table_name,))
        
        indexes = cur.fetchall()
        if indexes:
            print(f"  Indexes ({len(indexes)}):")
            for idx in indexes:
                print(f"    - {idx['indexname']}")
    
    print("\n" + "="*80)
    print("3. TABLE CREATION SUMMARY:")
    print("="*80)
    
    print(f"""
This is what every new tenant should have:
  Total Tables: {len(tables)}
  
Tables to Create:
""")
    
    for i, row in enumerate(tables, 1):
        print(f"  {i:2}. {row['table_name']}")
    
    cur.close()
    conn.close()
    
    print("\n" + "="*80)
    print("4. RECOMMENDED APPROACH:")
    print("="*80)
    print("""
Update create_missing_tables_manually() in tenancy/shop_manager.py to include ALL these tables.

Current approach only creates:
  - django_session
  - shop_users_shopuser
  - django_admin_log
  - token_blacklist_outstandingtoken
  - token_blacklist_blacklistedtoken

Should create all of them above.
""")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
