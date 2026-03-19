#!/usr/bin/env python
"""Check all schemas for pos_jobcard table"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()

# List all schemas
cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'public')")
schemas = cursor.fetchall()

print("Schemas found:")
for s in schemas:
    schema = s[0]
    print(f"  - {schema}")
    
    # Check for pos_jobcard in each schema
    cursor.execute(f"""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = '{schema}' AND table_name = 'pos_jobcard'
    """)
    tables = cursor.fetchall()
    if tables:
        print(f"    pos_jobcard EXISTS")
        
        # Check columns
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = '{schema}' AND table_name = 'pos_jobcard'
        """)
        cols = cursor.fetchall()
        print(f"    Columns ({len(cols)}):")
        for c in cols:
            print(f"      - {c[0]}")
            
        # Check for debtor_account_number
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = '{schema}' AND table_name = 'pos_jobcard' 
            AND column_name = 'debtor_account_number'
        """)
        result = cursor.fetchall()
        print(f"    debtor_account_number exists: {len(result) > 0}")
    else:
        print(f"    pos_jobcard NOT FOUND")
