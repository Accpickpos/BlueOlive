#!/usr/bin/env python
"""Check database config and tables."""

import os
import sys

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import django  # noqa: E402

django.setup()

# Print settings
from django.conf import settings  # noqa: E402

print("=== Database Configuration ===")
for name, config in settings.DATABASES.items():
    print(f"\nDatabase: {name}")
    print(f"  ENGINE: {config['ENGINE']}")
    print(f"  NAME: {config.get('NAME', 'Not set')}")
    print(f"  HOST: {config.get('HOST', 'Not set')}")
    print(f"  PORT: {config.get('PORT', 'Not set')}")
    print(f"  USER: {config.get('USER', 'Not set')}")

# Test connections
print("\n=== Testing Connections ===")
from django.db import connections  # noqa: E402

for alias in connections.databases:
    print(f"\nAlias: {alias}")
    try:
        conn = connections[alias]
        cursor = conn.cursor()
        cursor.execute("SELECT current_database()")
        db_name = cursor.fetchone()
        print(f"  Connected to: {db_name[0]}")

        # List tables in public schema
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'pos_%'
        """)
        tables = cursor.fetchall()
        if tables:
            print(f"  pos_* tables: {[t[0] for t in tables]}")
        else:
            print("  No pos_* tables in public schema")
    except Exception as e:
        print(f"  Error: {e}")

print("\n=== Done ===")
