#!/usr/bin/env python
"""Check all schemas for pos_jobcard table"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import connection  # noqa: E402

cursor = connection.cursor()

# List all schemas
cursor.execute(
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'public')"
)
schemas = cursor.fetchall()

print("Schemas found:")
for s in schemas:
    schema = s[0]
    print(f"  - {schema}")

    # Check for pos_jobcard in each schema
    # `schema` is read from information_schema.schemata above, not external input.
    query = f"""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = '{schema}' AND table_name = 'pos_jobcard'
    """
    cursor.execute(query)  # nosec B608
    tables = cursor.fetchall()
    if tables:
        print("    pos_jobcard EXISTS")

        # Check columns
        query = f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = 'pos_jobcard'
        """
        cursor.execute(query)  # nosec B608
        cols = cursor.fetchall()
        print(f"    Columns ({len(cols)}):")
        for c in cols:
            print(f"      - {c[0]}")

        # Check for debtor_account_number
        query = f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = 'pos_jobcard'
            AND column_name = 'debtor_account_number'
        """
        cursor.execute(query)  # nosec B608
        result = cursor.fetchall()
        print(f"    debtor_account_number exists: {len(result) > 0}")
    else:
        print("    pos_jobcard NOT FOUND")
