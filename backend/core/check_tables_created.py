#!/usr/bin/env python
"""Check which tables were created after migrations."""
import os
import django

os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant, Shop

tenant = Tenant.objects.get(id=1)
alias = tenant.db_alias
shop = tenant.shops.filter(is_active=True).first()
schema_name = shop.schema_name

conn = connections[alias]
cursor = conn.cursor()

# Check tables in the tenant schema
print(f"Tables in schema '{schema_name}':")
print("=" * 70)
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = %s 
    AND table_type = 'BASE TABLE'
    ORDER BY table_name
""", [schema_name])

tables = cursor.fetchall()
if tables:
    for (table,) in tables:
        print(f"  {table}")
    print(f"\nTotal: {len(tables)} tables")
    
    # Check if debtors_debtor exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = %s AND table_name = 'debtors_debtor'
        )
    """, [schema_name])
    
    if cursor.fetchone()[0]:
        print("\nSUCCESS: debtors_debtor table exists!")
    else:
        print("\nWARNING: debtors_debtor table NOT FOUND")
        
        # Check if it's in public schema
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'debtors_debtor'
        """)
        if cursor.fetchone():
            print("  (But it exists in public schema)")
else:
    print("  NO TABLES FOUND!")
    print(f"\nChecking public schema...")
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name LIMIT 20
    """)
    for (table,) in cursor.fetchall():
        print(f"  {table}")
