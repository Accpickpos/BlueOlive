#!/usr/bin/env python
"""Check columns in debtors_debtor table."""
import os
import django

os.environ['TENANT_DB_ALIAS'] = 'tenant_1'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from apps.debtors.models import Debtor

alias = 'tenant_1'
conn = connections[alias]

print("Current columns in debtors_debtor table:")
print("=" * 70)
cursor = conn.cursor()
cursor.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name='debtors_debtor' 
    ORDER BY ordinal_position
""")

actual_cols = {}
for row in cursor.fetchall():
    col_name, data_type, nullable, default = row
    actual_cols[col_name] = (data_type, nullable, default)
    nullable_str = "NULL" if nullable == 'YES' else "NOT NULL"
    print(f"  {col_name:40} {data_type:20} {nullable_str}")

print("\n\nExpected columns from Debtor model:")
print("=" * 70)
model_fields = {f.name: f for f in Debtor._meta.get_fields()}
for field_name, field in sorted(model_fields.items()):
    if not field.many_to_one and not field.one_to_many and not field.many_to_many:
        print(f"  {field_name:40} {str(field.get_internal_type()):20}")

print("\n\nComparison:")
print("=" * 70)

# Find missing columns
missing = set(model_fields.keys()) - set(actual_cols.keys())
if missing:
    print(f"\nMISSING columns in database: {missing}")
    for col in missing:
        field = model_fields[col]
        print(f"  - {col} ({field.get_internal_type()})")
else:
    print("\n✓ All model fields have database columns")

# Find extra columns
extra = set(actual_cols.keys()) - set(model_fields.keys())
if extra:
    print(f"\nEXTRA columns in database: {extra}")
    for col in extra:
        data_type, nullable, default = actual_cols[col]
        print(f"  - {col} ({data_type})")
else:
    print("✓ No extra columns in database")
