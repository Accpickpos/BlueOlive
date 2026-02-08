import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from tenancy.utils import create_tenant_database_postgres, register_tenant_connection
from tenancy.shop_manager import migrate_tenant_database
from django.conf import settings

# Create test tenant
print("Creating tenant...")
tenant = Tenant.objects.create(
    name='TestMigFix',
    slug='testmigfix',
    subdomain='testmigfix',
    db_name='test_mig_fix',
    db_user=settings.DATABASES['default']['USER'],
    db_password=settings.DATABASES['default']['PASSWORD'],
    db_host='localhost',
    db_port=5432,
)

# Create database
print("Creating database...")
superuser_conn_info = {
    'host': 'localhost',
    'port': 5432,
    'user': settings.DATABASES['default']['USER'],
    'password': settings.DATABASES['default']['PASSWORD'],
    'dbname': 'postgres'
}
create_tenant_database_postgres(tenant, superuser_conn_info)

# Register connection
print("Registering connection...")
register_tenant_connection(tenant)

# Run migrations
print("Running migrations...")
try:
    migrate_tenant_database(tenant)
    print('[SUCCESS] Migrations completed')
except Exception as e:
    print(f'[ERROR] Migrations failed: {e}')
    import traceback
    traceback.print_exc()

# Verify tables exist
print("\nVerifying tables...")
from django.db import connections
alias = tenant.db_alias
conn = connections[alias]
with conn.cursor() as cur:
    cur.execute('SET search_path TO public')
    cur.execute("""
        SELECT tablename FROM pg_tables 
        WHERE schemaname = 'public' 
        ORDER BY tablename
    """)
    tables = cur.fetchall()
    for (table,) in tables:
        print(f"  - {table}")

print(f"\nTotal tables: {len(tables)}")
