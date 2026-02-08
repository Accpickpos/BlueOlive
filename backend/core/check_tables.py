import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.db import connections
from tenancy.models import Tenant

tenant = Tenant.objects.get(slug='testmigfix')
conn = connections[tenant.db_alias]

with conn.cursor() as cur:
    cur.execute('SET search_path TO public')
    cur.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename
    """)
    tables = cur.fetchall()
    print(f'Tables in test_mig_fix ({len(tables)} total):')
    for (table,) in tables:
        print(f'  - {table}')
