#!/usr/bin/env python
"""Check if debtors tables exist in tenant database."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant
from tenancy.utils import register_tenant_connection

# Get tenant and register connection
tenant = Tenant.objects.filter(is_active=True).first()
if not tenant:
    print("❌ No active tenant found")
    exit(1)

register_tenant_connection(tenant)
print(f"✓ Registered tenant: {tenant.name} ({tenant.db_alias})")

# Query using the tenant alias
with connections[tenant.db_alias].cursor() as cursor:
    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"\nTables in {tenant.db_alias} public schema:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    # Check for debtors tables
    debtor_tables = [t for t in tables if 'debtor' in t]
    if debtor_tables:
        print(f"\n✓ Debtors tables found: {', '.join(debtor_tables)}")
    else:
        print(f"\n❌ Debtors tables NOT found")
        print("\nAll tables:", ', '.join(sorted(tables)[:20]))
