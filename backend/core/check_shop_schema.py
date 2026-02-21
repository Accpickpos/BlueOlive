#!/usr/bin/env python
"""Check where debtors tables are located."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection

tenant = Tenant.objects.filter(is_active=True).first()
shop = tenant.shops.first()
print(f'Tenant: {tenant.name}')
print(f'Shop: {shop.name if shop else "None"}')
if shop:
    print(f'Schema: {shop.schema_name}')

register_tenant_connection(tenant)

# Check all schemas
with connections[tenant.db_alias].cursor() as cursor:
    cursor.execute('SELECT schema_name FROM information_schema.schemata')
    schemas = [row[0] for row in cursor.fetchall()]
    print(f'\nSchemas in {tenant.db_alias}:')
    for schema in sorted(schemas):
        if not schema.startswith('pg_') and schema != 'information_schema':
            print(f'  - {schema}')
    
    # Check tables in shop schema
    if shop:
        cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname=%s AND tablename LIKE %s", 
                       [shop.schema_name, '%debtor%'])
        tables = [row[0] for row in cursor.fetchall()]
        if tables:
            print(f'\n✓ Debtors tables in {shop.schema_name} schema: {tables}')
        else:
            cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname=%s LIMIT 20", 
                          [shop.schema_name])
            all_tables = [row[0] for row in cursor.fetchall()]
            print(f'\nTables in {shop.schema_name}: {all_tables}')
