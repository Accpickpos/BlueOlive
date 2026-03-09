import os
import sys

# Add the core directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'core'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

import psycopg2
from django.conf import settings

# Get database config
db = settings.DATABASES['default']
conn = psycopg2.connect(
    host=db.get('HOST', 'localhost'),
    port=db.get('PORT', 5432),
    dbname=db.get('NAME'),
    user=db.get('USER'),
    password=db.get('PASSWORD')
)
cursor = conn.cursor()

# List all schemas
cursor.execute("""
    SELECT schema_name 
    FROM information_schema.schemata 
    WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'public')
    ORDER BY schema_name
""")
schemas = cursor.fetchall()

print('=== Schemas in database ===')
if schemas:
    for s in schemas:
        print(f'  {s[0]}')
else:
    print('  (none - only public and system schemas exist)')

print()

# List tables in each schema
for s in schemas:
    schema = s[0]
    cursor.execute(f"""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = '{schema}'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    print(f'=== Tables in schema "{schema}" ===')
    for t in tables:
        print(f'  {t[0]}')
    print()

# Also check tables in public schema that are shop-related
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    AND table_name LIKE 'dmast%' OR table_name LIKE 'pos_%' OR table_name LIKE 'creditors_%'
    ORDER BY table_name
""")
public_tables = cursor.fetchall()

print('=== Shop-related tables in public schema ===')
if public_tables:
    for t in public_tables:
        print(f'  public.{t[0]}')
else:
    print('  (none)')

cursor.close()
conn.close()
