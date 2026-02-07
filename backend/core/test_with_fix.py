import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant
import time

# Clean up old test
try:
    admin_conn_name = 'default'
    admin_conn = connections[admin_conn_name]
    with admin_conn.cursor() as cur:
        cur.execute("SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'test_with_fix' AND pid <> pg_backend_pid();")
        cur.execute("DROP DATABASE IF EXISTS test_with_fix;")
    admin_conn.commit()
    print("[OK] Old database dropped")
    
    Tenant.objects.filter(slug='testwithfix').delete()
    print("[OK] Old tenant deleted")
except Exception as e:
    print(f"[WARN] Cleanup failed: {e}")

# Create new test with unique name
from tenancy.utils import create_tenant_database_postgres, register_tenant_connection
from tenancy.shop_manager import migrate_tenant_database
from django.conf import settings

test_num = str(int(time.time()) % 10000)
print(f"\nCreating fresh test (#{test_num})...")
tenant = Tenant.objects.create(
    name=f'TestFix{test_num}',
    slug=f'testfix{test_num}',
    subdomain=f'testfix{test_num}',
    db_name=f'test_fix_{test_num}',
    db_user=settings.DATABASES['default']['USER'],
    db_password=settings.DATABASES['default']['PASSWORD'],
    db_host='localhost',
    db_port=5432,
)
print("[OK] Tenant created")

superuser_conn_info = {
    'host': 'localhost',
    'port': 5432,
    'user': settings.DATABASES['default']['USER'],
    'password': settings.DATABASES['default']['PASSWORD'],
    'dbname': 'postgres'
}
create_tenant_database_postgres(tenant, superuser_conn_info)
print("[OK] Database created")

register_tenant_connection(tenant)
print("[OK] Connection registered")

print("\nRunning migrations...")
migrate_tenant_database(tenant)
print("[OK] Migrations complete")

# Check tables
print("\nTables in database:")
conn = connections[tenant.db_alias]
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
    
print(f"\nTotal: {len(tables)} tables")

# Check critical tables
critical = [
    'shop_users_shopuser',
    'django_admin_log',
    'django_session',
    'token_blacklist_blacklistedtoken',
    'token_blacklist_outstandingtoken',
]
print("\nCritical tables:")
for table in critical:
    found = any(t[0] == table for t in tables)
    status = "[OK]" if found else "[MISSING]"
    print(f"  {status} {table}")
