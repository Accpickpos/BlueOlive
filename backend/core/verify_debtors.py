#!/usr/bin/env python
"""Verify debtors table was created successfully."""
import os
import django

os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from apps.debtors.models import Debtor

alias = 'tenant_1'
conn = connections[alias]
cursor = conn.cursor()

# Check if debtors_debtor table exists and has columns
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name='debtors_debtor' 
    ORDER BY ordinal_position 
    LIMIT 15
""")

print("=" * 70)
print("Debtors_debtor table columns (first 15):")
print("=" * 70)
columns = cursor.fetchall()
if columns:
    for col_name, data_type in columns:
        print(f"  {col_name:40} {data_type}")
    
    cursor.execute("SELECT COUNT(*) FROM debtors_debtor")
    count = cursor.fetchone()[0]
    print(f"\nTotal records: {count}")
    print("\nSUCCESS: debtors_debtor table is ready!")
else:
    print("ERROR: debtors_debtor table not found!")
    exit(1)
