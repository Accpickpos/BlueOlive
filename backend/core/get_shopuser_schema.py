#!/usr/bin/env python
"""
Get exact schema for shop_users_shopuser from tenant_tnt
"""
import os
import sys
import django
import psycopg2

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/c/Users/accpi/OneDrive/Documents/GitHub/BlueOlive/backend/core')
django.setup()

from django.conf import settings

DB_USER = settings.DATABASES['default']['USER']
DB_PASSWORD = settings.DATABASES['default']['PASSWORD']
DB_HOST = settings.DATABASES['default']['HOST']
DB_PORT = settings.DATABASES['default']['PORT']

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database='tenant_tnt'
    )
    cur = conn.cursor()
    
    print("="*80)
    print("EXACT SCHEMA: shop_users_shopuser")
    print("="*80)
    
    # Get the actual table definition
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'shop_users_shopuser'
        ORDER BY ordinal_position
    """)
    
    print("\nColumns:")
    for row in cur.fetchall():
        col_name, data_type, nullable, default = row
        nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
        default_str = f" DEFAULT {default}" if default else ""
        print(f"  {col_name:35} {data_type:25} {nullable_str}{default_str}")
    
    print("\n" + "="*80)
    print("PostgreSQL CREATE TABLE (for reference):")
    print("="*80 + "\n")
    
    # Get actual CREATE TABLE statement
    cur.execute("""
        SELECT pg_get_createtablestmt('shop_users_shopuser'::regclass)
    """)
    
    try:
        result = cur.fetchone()
        if result:
            print(result[0])
        else:
            print("Could not get CREATE TABLE statement")
    except:
        print("(Could not retrieve CREATE TABLE statement)")
    
    conn.close()

except Exception as e:
    print(f"ERROR: {e}")
