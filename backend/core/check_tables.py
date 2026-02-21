import os
import sys
import django

# Setup Django before importing models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant
from tenancy.utils import register_tenant_connection

tenant = Tenant.objects.first()
print(f'Tenant: {tenant.name}')
register_tenant_connection(tenant)
conn = connections[tenant.db_alias]

with conn.cursor() as cur:
    cur.execute('SET search_path TO "tech_tech"')
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'tech_tech' AND table_name LIKE '%creditor%'")
    print('Creditor tables:', [r[0] for r in cur.fetchall()])
    
    # Also check all tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'tech_tech'")
    print('All tables:', [r[0] for r in cur.fetchall()])
