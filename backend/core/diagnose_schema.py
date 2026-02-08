#!/usr/bin/env python
"""Diagnose schema issues in tenant databases."""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant

# Get a tenant database
tenant = Tenant.objects.first()
if tenant:
    print(f"\nTenant: {tenant.name} (DB: {tenant.db_name}, Alias: {tenant.db_alias})")
    print("=" * 60)
    
    # Connect to tenant database
    alias = tenant.db_alias
    conn = connections[alias]
    
    # Get all schemas
    with conn.cursor() as cur:
        cur.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1')
            ORDER BY schema_name
        """)
        schemas = cur.fetchall()
        print("\nSchemas in tenant database:")
        for schema in schemas:
            print(f"  - {schema[0]}")
        
        # Get all tables in each schema
        print("\n" + "=" * 60)
        print("Tables by Schema:")
        print("=" * 60)
        for schema in schemas:
            schema_name = schema[0]
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                ORDER BY table_name
            """, [schema_name])
            tables = cur.fetchall()
            if tables:
                print(f"\n{schema_name}:")
                for table in tables:
                    print(f"  - {table[0]}")
else:
    print("No tenants found")
