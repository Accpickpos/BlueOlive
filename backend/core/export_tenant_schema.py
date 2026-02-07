#!/usr/bin/env python
"""
Export exact CREATE TABLE statements from tenant_tnt for all tables
This ensures fallback creation matches real schema
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

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database='tenant_tnt'
    )
    cur = conn.cursor()
    
    print("""
# Exact table definitions from tenant_tnt
# Use these for fallback table creation

create_sql = {
""")
    
    for table_name in tables:
        print(f"\n    '{table_name}': \"\"\"")
        
        # Get column definitions
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cur.fetchall()
        
        # Build CREATE TABLE
        col_defs = []
        for col_name, data_type, nullable, default, pos in columns:
            col_def = f"                {col_name} {data_type}"
            
            if nullable == 'NO':
                col_def += " NOT NULL"
            
            if default:
                col_def += f" DEFAULT {default}"
            
            col_defs.append(col_def)
        
        print(f"        CREATE TABLE IF NOT EXISTS {table_name} (")
        print(",\n".join(col_defs))
        print("            )")
        print("    \"\"\",")
    
    print("}")
    
    conn.close()

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
