#!/usr/bin/env python
"""
Script to migrate a specific tenant database.
Usage: python migrate_tenant.py [tenant_id]
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command
from tenancy.models import Tenant
from tenancy.utils import register_tenant_connection

def migrate_tenant(tenant_id=None):
    """Register tenant database and run migrations."""
    # Get tenant
    if tenant_id:
        tenant = Tenant.objects.get(id=tenant_id)
    else:
        # Get first active tenant
        tenant = Tenant.objects.filter(is_active=True).first()
    
    if not tenant:
        print("❌ No active tenant found")
        return False
    
    print(f"✓ Found tenant: {tenant.name}")
    print(f"  DB: {tenant.db_name}")
    print(f"  Host: {tenant.db_host}:{tenant.db_port}")
    
    # Register the tenant connection
    try:
        register_tenant_connection(tenant)
        print(f"✓ Registered connection {tenant.db_alias}")
    except Exception as e:
        print(f"❌ Failed to register connection: {e}")
        return False
    
    # Run migrations for this database
    print(f"\n📦 Running migrations for {tenant.db_alias}...")
    try:
        # Set environment variable for db_router to allow migrations
        os.environ['TENANT_DB_ALIAS'] = tenant.db_alias
        call_command('migrate', database=tenant.db_alias, verbosity=2)
        print(f"✓ Migrations completed successfully")
        return True
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    tenant_id = sys.argv[1] if len(sys.argv) > 1 else None
    success = migrate_tenant(tenant_id)
    sys.exit(0 if success else 1)
