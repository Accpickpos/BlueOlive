import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from django.db import connections
from tenancy.models import Tenant

tenant = Tenant.objects.get(slug='volt')
alias = tenant.db_alias
print(f'Checking schemas in {alias}...')

try:
    conn = connections[alias]
    with conn.cursor() as cursor:
        # List all schemas
        cursor.execute("SELECT schema_name FROM information_schema.schemata ORDER BY schema_name")
        schemas = cursor.fetchall()
        print(f'Schemas in {alias}:')
        for schema in schemas:
            print(f'  - {schema[0]}')
        
        # Check each schema for sales_departments
        print(f'\nSearching for sales_departments in all schemas:')
        for schema in schemas:
            schema_name = schema[0]
            cursor.execute(
                f"SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = 'sales_departments')",
                [schema_name]
            )
            exists = cursor.fetchone()[0]
            if exists:
                print(f'  ✓ Found in schema: {schema_name}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
