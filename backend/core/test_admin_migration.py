import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
os.environ['TENANT_DB_ALIAS'] = 'test'

import django
django.setup()

from django.db import connections
from django.core.management import call_command
from tenancy.models import Tenant

tenant = Tenant.objects.get(slug='testmigfix')
alias = tenant.db_alias

# Set TENANT_DB_ALIAS for the router
os.environ['TENANT_DB_ALIAS'] = alias

try:
    # First, clear django_migrations except auth and contenttypes
    conn = connections[alias]
    with conn.cursor() as cur:
        cur.execute('SET search_path TO public')
        cur.execute("DELETE FROM django_migrations WHERE app NOT IN ('auth', 'contenttypes')")
    conn.commit()
    print("[OK] Cleared non-auth migrations")
    
    # Now try to migrate admin
    print("\nAttempting to migrate admin...")
    call_command('migrate', 'admin', database=alias, verbosity=2, interactive=False)
    print("[OK] Admin migrated")
    
    # Check what tables exist now
    with conn.cursor() as cur:
        cur.execute('SET search_path TO public')
        cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
        for (table,) in cur.fetchall():
            print(f"  - {table}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    print(traceback.format_exc())

finally:
    if 'TENANT_DB_ALIAS' in os.environ:
        del os.environ['TENANT_DB_ALIAS']
