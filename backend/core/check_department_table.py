#!/usr/bin/env python
"""Check acme_admin schema for sales_departments table"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import connection  # noqa: E402

cursor = connection.cursor()

# Check what's in the acme_admin schema
schema = "acme_admin"

print(f"Checking schema: {schema}")
print("=" * 50)

# Check for tables
query = f"""
    SELECT table_name, table_type
    FROM information_schema.tables
    WHERE table_schema = '{schema}'
    ORDER BY table_name
"""
cursor.execute(query)  # nosec B608 - `schema` is the hardcoded literal above
tables = cursor.fetchall()
print(f"\nTables in {schema}:")
for t in tables:
    print(f"  - {t[0]} ({t[1]})")

# Check specifically for sales_departments
query = f"""
    SELECT table_name, table_type
    FROM information_schema.tables
    WHERE table_schema = '{schema}' AND table_name = 'sales_departments'
"""
cursor.execute(query)  # nosec B608 - `schema` is the hardcoded literal above
result = cursor.fetchall()
print(f"\n sales_departments: {result}")

# Check for views
query = f"""
    SELECT table_name, view_definition
    FROM information_schema.views
    WHERE table_schema = '{schema}' AND table_name = 'sales_departments'
"""
cursor.execute(query)  # nosec B608 - `schema` is the hardcoded literal above
views = cursor.fetchall()
print("\n Views named sales_departments:")
for v in views:
    print(f"  - {v[0]}")
    if v[1]:
        print(f"    Definition: {v[1][:200]}...")

# Check for materialized views
query = f"""
    SELECT matviewname, definition
    FROM pg_matviews
    WHERE schemaname = '{schema}' AND matviewname = 'sales_departments'
"""
cursor.execute(query)  # nosec B608 - `schema` is the hardcoded literal above
matviews = cursor.fetchall()
print("\n Materialized views named sales_departments:")
for m in matviews:
    print(f"  - {m[0]}")
    if m[1]:
        print(f"    Definition: {m[1][:200]}...")

# Check columns
query = f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = '{schema}' AND table_name = 'sales_departments'
    ORDER BY ordinal_position
"""
cursor.execute(query)  # nosec B608 - `schema` is the hardcoded literal above
cols = cursor.fetchall()
print("\n Columns in sales_departments:")
for c in cols:
    print(f"  - {c[0]}: {c[1]}")

# Check what else is in public schema with similar name
cursor.execute("""
    SELECT table_schema, table_name, table_type
    FROM information_schema.tables
    WHERE table_name LIKE '%sales%dept%' OR table_name LIKE '%department%'
    ORDER BY table_schema, table_name
""")
dept_tables = cursor.fetchall()
print("\n All tables with 'department' in name:")
for t in dept_tables:
    print(f"  - {t[0]}.{t[1]} ({t[2]})")
