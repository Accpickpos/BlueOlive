import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from tenancy.utils import create_tenant_database_postgres, register_tenant_connection
from django.conf import settings
from django.db import connections
from django.core.management import call_command

# Create test tenant
tenant = Tenant.objects.create(
    name='TestFinal',
    slug='testfinal',
    subdomain='testfinal',
    db_name='test_final',
    db_user=settings.DATABASES['default']['USER'],
    db_password=settings.DATABASES['default']['PASSWORD'],
    db_host='localhost',
    db_port=5432,
)

# Create database
superuser_conn_info = {
    'host': 'localhost',
    'port': 5432,
    'user': settings.DATABASES['default']['USER'],
    'password': settings.DATABASES['default']['PASSWORD'],
    'dbname': 'postgres'
}
create_tenant_database_postgres(tenant, superuser_conn_info)

# Register connection
register_tenant_connection(tenant)

alias = tenant.db_alias
os.environ['TENANT_DB_ALIAS'] = alias

try:
    # Set search path
    conn = connections[alias]
    with conn.cursor() as cur:
        cur.execute('SET search_path TO public')
    conn.commit()
    
    # Test each migration individually
    for app in ['contenttypes', 'auth', 'admin', 'sessions', 'token_blacklist', 'shop_users']:
        print(f"\n--- Migrating {app} ---")
        try:
            call_command('migrate', app, database=alias, verbosity=1, interactive=False)
            print(f"✓ {app} migrated")
        except Exception as e:
            print(f"✗ {app} error: {e}")
            import traceback
            print(traceback.format_exc())

finally:
    if 'TENANT_DB_ALIAS' in os.environ:
        del os.environ['TENANT_DB_ALIAS']
