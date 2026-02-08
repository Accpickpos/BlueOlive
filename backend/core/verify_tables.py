import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.db import connections
from tenancy.models import Tenant

tenant = Tenant.objects.get(slug='volt')
alias = tenant.db_alias
print(f'Checking tables in {alias}...')

try:
    conn = connections[alias]
    with conn.cursor() as cursor:
        # Check for sales_departments
        cursor.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'sales_departments')")
        exists = cursor.fetchone()[0]
        print(f'sales_departments exists: {exists}')
        
        # List all tables with 'department' in name
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE '%department%'")
        public_tables = cursor.fetchall()
        print(f'Tables containing "department" in public schema: {public_tables}')
        
        # Check all tables in database
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")
        all_tables = cursor.fetchall()
        print(f'\nAll tables in {alias}:')
        for table in all_tables:
            print(f'  - {table[0]}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
