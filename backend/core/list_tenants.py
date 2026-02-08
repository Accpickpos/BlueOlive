#!/usr/bin/env python
"""
Check available tenants in the system.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant

# List all tenants
tenants = Tenant.objects.all()
print(f"Total tenants: {tenants.count()}")
for tenant in tenants:
    print(f"  - {tenant.name} (ID: {tenant.id}, DB: {tenant.db_name})")

# Check if any has 'tenant_' database pattern
tenants_with_db = Tenant.objects.exclude(db_name__isnull=True)
print(f"\nTenants with databases: {tenants_with_db.count()}")
for tenant in tenants_with_db:
    print(f"  - {tenant.name} (ID: {tenant.id}, DB: {tenant.db_name})")
