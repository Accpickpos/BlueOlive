#!/usr/bin/env python
"""Apply debtors migrations directly to tenant_1 database."""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ['TENANT_DB_ALIAS'] = 'tenant_1'

django.setup()

from django.db import connections, connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.loader import MigrationLoader

# Get the tenant database
alias = 'tenant_1'
conn = connections[alias]

# Load migrations for debtors app
loader = MigrationLoader(None)
executor = MigrationExecutor(conn)

# Get all pending migrations for debtors
plan = executor.migration_plan(loader.graph.leaf_nodes())
pending_debtors = [migration for migration in plan if migration[0].app_label == 'debtors']

print(f"Found {len(pending_debtors)} pending migrations for debtors app")

# Apply all pending migrations  
if pending_debtors:
    for migration, backwards in pending_debtors:
        print(f"  Applying: {migration.name}")
        executor.apply_migration(None, migration)
    print(f"\n✓ Successfully applied {len(pending_debtors)} migrations!")
else:
    print("All migrations are already applied!")

# Verify the table exists
try:
    from apps.debtors.models import Debtor
    # Use the tenant_1 database explicitly
    count = Debtor.objects.using(alias).count()
    print(f"✓ Debtors table exists! Current record count: {count}")
except Exception as e:
    print(f"✗ Error checking debtors table: {e}")
    sys.exit(1)
