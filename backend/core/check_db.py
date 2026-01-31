#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from tenancy.utils import register_tenant_connection
from django.db import connections

tenant = Tenant.objects.get(slug='test-tenant-2')
print(f"Tenant: {tenant.name}, DB: {tenant.db_name}, Alias: {tenant.db_alias}")

register_tenant_connection(tenant)
conn = connections[tenant.db_alias]
conn.close()
conn.connect()

with conn.cursor() as cur:
    cur.execute('SET search_path TO public')
    cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename LIKE '%shop%' ORDER BY tablename")
    tables = cur.fetchall()
    print('Shop tables:', tables)

    # Try to query the table
    try:
        cur.execute("SELECT id, username FROM shop_users_shopuser LIMIT 1")
        users = cur.fetchall()
        print('Users in table:', users)
    except Exception as e:
        print('Error querying table:', e)