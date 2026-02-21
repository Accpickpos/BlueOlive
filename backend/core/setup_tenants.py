#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from tenancy.utils import register_tenant_connection
from django.core.management import call_command
from django.db import connection

# First, check if tenant table exists
print("Checking if Tenant table exists...")
try:
    Tenant.objects.all().count()
    print("✓ Tenant table exists")
except Exception as e:
    print(f"⚠ Tenant table error: {e}")
    print("Creating Tenant table...")
    call_command('migrate', database='default')
    print("✓ Tenant table created")

# Get all tenants
tenants = Tenant.objects.all()
print(f"\nFound {tenants.count()} tenants:")
for tenant in tenants:
    db_alias = tenant.db_alias if hasattr(tenant, 'db_alias') else f'tenant_{tenant.id}'
    print(f"  - {tenant.slug} (id={tenant.id}, db_alias={db_alias})")

# Migrate each tenant
print("\nMigrating tenant databases...")
for tenant in tenants:
    db_alias = tenant.db_alias if hasattr(tenant, 'db_alias') else f'tenant_{tenant.id}'
    print(f"\n  Migrating {tenant.slug} (db_alias={db_alias})...")
    try:
        # Register the connection for this tenant
        register_tenant_connection(tenant)
        # Run migrations for tenant apps
        call_command('migrate', database=db_alias)
        print(f"    ✓ {tenant.slug} migrated successfully")
    except Exception as e:
        print(f"    ✗ Error migrating {tenant.slug}: {e}")

print("\n✓ Migration complete")
