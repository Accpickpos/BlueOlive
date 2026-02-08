#!/usr/bin/env python
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections

conn = connections['tenant_2']
with conn.cursor() as cur:
    cur.execute("""
        SELECT a.data_type
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.columns a
          ON a.column_name = kcu.column_name
        WHERE tc.table_schema = 'public'
          AND tc.table_name = 'django_admin_log'
          AND tc.constraint_type = 'PRIMARY KEY'
        LIMIT 1
    """)
    result = cur.fetchone()
    print(f"PK Type Query Result: {result}")
    print(f"Data Type: {result[0]}")
