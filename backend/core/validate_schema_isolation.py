#!/usr/bin/env python
"""
Utility to verify schema isolation is correct across all tenants.
Use this to validate that shop tables are properly isolated.
"""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from django.conf import settings
from tenancy.models import Tenant

SHOP_APP_LABELS = getattr(settings, 'SHOP_APP_LABELS', [])
TENANT_ONLY_TABLES = [
    'admin_*',
    'token_blacklist_*',
    'shop_users_*',
    'auth_*',
    'django_content_type',
    'django_migrations',
    'django_admin_log',
]

def validate_schema_isolation():
    """Validate that schemas are properly isolated."""
    print("=" * 80)
    print("SCHEMA ISOLATION VALIDATION")
    print("=" * 80)
    
    issues_found = False
    
    for tenant in Tenant.objects.all():
        print(f"\n✓ Validating {tenant.name} ({tenant.db_alias})...")
        
        alias = tenant.db_alias
        conn = connections[alias]
        
        # Get public schema tables
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            public_tables = set(row[0] for row in cur.fetchall())
            
            # Get shop schema tables
            cur.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema NOT IN ('public', 'pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1')
                AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name
            """)
            shop_tables = {}
            for schema, table in cur.fetchall():
                if schema not in shop_tables:
                    shop_tables[schema] = []
                shop_tables[schema].append(table)
        
        # Validate public schema
        print(f"  Public schema: {len(public_tables)} tables")
        
        # Check for tables that shouldn't be in public
        app_label_prefixes = {
            'cash_book': ['bank_', 'cash_', 'cashbook_', 'expense_', 'income_', 'interest_', 'other_'],
            'creditors': ['creditor_', 'contract_', 'credit_terms', 'creditors'],
            'debtors': ['debtors_'],
            'stock_control': ['stock_', 'bundle_', 'bundles', 'shrink_wrap', 'special_deal', 'future_', 'goods_received_', 'grn_', 'tax_code', 'costing_', 'contract_pricing'],
            'purchase_orders': ['purchase_order', 'rfc'],
            'settings': ['sales_', 'department_', 'system_configuration', 'payment_method'],
            'pos': ['pos_', 'pack_bundle', 'pack_', 'back_order', 'one_touch_'],
        }
        
        bad_tables = []
        for table in public_tables:
            for app_label, prefixes in app_label_prefixes.items():
                if any(table.startswith(prefix) for prefix in prefixes):
                    bad_tables.append((table, app_label))
                    break
        
        if bad_tables:
            issues_found = True
            print(f"    ⚠️  FOUND {len(bad_tables)} shop tables in public schema:")
            for table, app_label in bad_tables:
                print(f"      - {table} (belongs to {app_label})")
        else:
            print(f"    ✓ No shop tables in public schema")
        
        # Validate shop schemas
        print(f"  Shop schemas: {len(shop_tables)}")
        for schema_name in sorted(shop_tables.keys()):
            tables = shop_tables[schema_name]
            print(f"    - {schema_name}: {len(tables)} tables")
            
            # Verify tables in shop schema are actually shop tables
            non_shop_tables = []
            for table in tables:
                is_shop_table = False
                for app_label, prefixes in app_label_prefixes.items():
                    if any(table.startswith(prefix) for prefix in prefixes):
                        is_shop_table = True
                        break
                
                if not is_shop_table and table != 'django_migrations':
                    non_shop_tables.append(table)
            
            if non_shop_tables:
                issues_found = True
                print(f"      ⚠️  Found {len(non_shop_tables)} non-shop tables:")
                for table in non_shop_tables:
                    print(f"        - {table}")
    
    print("\n" + "=" * 80)
    if issues_found:
        print("⚠️  ISSUES FOUND - Schema isolation is compromised")
        print("   Run cleanup_public_schema.py to fix")
        return False
    else:
        print("✅ VALIDATION PASSED - All schemas are properly isolated")
        return True
    print("=" * 80)

if __name__ == '__main__':
    success = validate_schema_isolation()
    sys.exit(0 if success else 1)
