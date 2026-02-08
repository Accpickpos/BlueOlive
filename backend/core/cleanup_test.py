import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant

# Drop test_final database
admin_conn_name = 'default'
admin_conn = connections[admin_conn_name]

with admin_conn.cursor() as cur:
    # Terminate all connections to test_final
    cur.execute("SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE datname = 'test_final' AND pid <> pg_backend_pid();")
    # Drop the database
    cur.execute("DROP DATABASE IF EXISTS test_final;")

admin_conn.commit()
print("[OK] test_final dropped")

# Delete the tenant record
Tenant.objects.filter(slug='testfinal').delete()
print("[OK] TestFinal tenant deleted from database")
