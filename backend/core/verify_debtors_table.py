import os
import django

os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections

alias = 'tenant_1'
conn = connections[alias]

with conn.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM debtors_debtor")
    count = cur.fetchone()[0]
    print(f"✓ SUCCESS! Debtors table exists with {count} records")
