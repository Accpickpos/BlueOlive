import os, django
os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.db import connections
conn = connections['tenant_1']
with conn.cursor() as cur:
    cur.execute('SHOW search_path')
    print('Search path:', cur.fetchone()[0])
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename LIMIT 30")
    print('\nTables in public schema:')
    for row in cur.fetchall():
        print(f'  - {row[0]}')
