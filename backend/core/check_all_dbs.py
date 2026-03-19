#!/usr/bin/env python
"""Check all databases for pos_jobcard table"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections

# Check each database
for db_alias in ['default', 'tenant_dev', 'tenant_acme']:
    try:
        conn = connections[db_alias]
        cursor = conn.cursor()
        
        # Check for tables
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'pos_jobcard'")
        tables = cursor.fetchall()
        
        print(f"\n=== Database: {db_alias} ===")
        print(f"Settings: host={conn.settings_dict['HOST']}, db={conn.settings_dict['NAME']}")
        
        if tables:
            print(f"  pos_jobcard EXISTS")
            
            # Check columns
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'pos_jobcard'")
            cols = cursor.fetchall()
            print(f"  Columns ({len(cols)}):")
            for c in cols:
                print(f"    - {c[0]}")
                
            # Check for debtor_account_number
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'pos_jobcard' AND column_name = 'debtor_account_number'")
            result = cursor.fetchall()
            print(f"  debtor_account_number exists: {len(result) > 0}")
        else:
            print(f"  pos_jobcard NOT FOUND")
            
    except Exception as e:
        print(f"\n=== Database: {db_alias} ===")
        print(f"  ERROR: {e}")
