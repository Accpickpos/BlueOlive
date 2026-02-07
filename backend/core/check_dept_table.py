#!/usr/bin/env python
"""
Check if SalesDepartment table has data.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.db import connections
from tenancy.models import Tenant, Shop

tenant = Tenant.objects.get(slug='volt')
shop = Shop.objects.filter(tenant=tenant, is_active=True).first()

print(f"Checking table in {shop.schema_name}...")

conn = connections[tenant.db_alias]
with conn.cursor() as cursor:
    # Set search path
    cursor.execute(f"SET search_path TO {shop.schema_name}, public")
    
    # Check table structure
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = %s AND table_name = 'sales_departments'
        ORDER BY ordinal_position
    """, [shop.schema_name])
    
    columns = cursor.fetchall()
    print(f"\nTable structure:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]}")
    
    # Check row count
    cursor.execute("SELECT COUNT(*) FROM sales_departments")
    count = cursor.fetchone()[0]
    print(f"\nRows in sales_departments: {count}")
    
    # If there are rows, show them
    if count > 0:
        cursor.execute("SELECT id, name FROM sales_departments LIMIT 5")
        rows = cursor.fetchall()
        print("\nSample data:")
        for row in rows:
            print(f"  - ID {row[0]}: {row[1]}")
