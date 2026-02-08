#!/usr/bin/env python
"""
Fix: Remove shop tables from public schema in tenant databases.
These tables should only exist in their respective shop schemas.
"""
import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from django.conf import settings
from tenancy.models import Tenant, Shop

# Get shop app labels that should NEVER be in public schema
SHOP_APP_LABELS = getattr(settings, 'SHOP_APP_LABELS', [])

# Map app labels to their table prefixes (roughly)
APP_TABLE_PREFIXES = {
    'cash_book': ['bank_', 'cash_', 'cashbook_', 'expense_', 'income_', 'interest_', 'other_'],
    'creditors': ['creditor_', 'contract_', 'credit_terms'],
    'debtors': ['debtors_'],
    'stock_control': ['stock_', 'bundle_', 'shrink_wrap', 'special_deal', 'future_price', 'goods_received_', 'grn_', 'tax_codes', 'costing_'],
    'purchase_orders': ['purchase_order', 'rfc'],
    'settings': ['sales_', 'sales_department', 'department_monthly_', 'sales_area_monthly_', 'system_configuration', 'payment_method'],
    'pos': ['pos_', 'pack_bundle', 'back_order', 'one_touch_'],
}

print("=" * 70)
print("CLEANUP: Removing shop tables from public schema")
print("=" * 70)

for tenant in Tenant.objects.all():
    print(f"\nProcessing Tenant: {tenant.name}")
    print("-" * 70)
    
    alias = tenant.db_alias
    conn = connections[alias]
    
    # Get all shops for this tenant
    shops = tenant.shops.all()
    print(f"  Shops: {', '.join(s.name for s in shops)}")
    
    # Get tables in public schema
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        public_tables = [row[0] for row in cur.fetchall()]
    
    print(f"  Tables in public schema: {len(public_tables)}")
    
    # Find tables that should be removed (they're shop app tables)
    tables_to_drop = []
    for table_name in public_tables:
        for app_label, prefixes in APP_TABLE_PREFIXES.items():
            if any(table_name.startswith(prefix) for prefix in prefixes):
                tables_to_drop.append(table_name)
                break
    
    if tables_to_drop:
        print(f"  Tables to DROP from public: {len(tables_to_drop)}")
        for table in sorted(tables_to_drop):
            print(f"    - {table}")
        
        # Ask for confirmation
        confirm = input(f"\n  ⚠️  Drop {len(tables_to_drop)} tables from {tenant.name}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            with conn.cursor() as cur:
                # Drop tables one by one, handling dependencies
                for table in sorted(tables_to_drop, reverse=True):
                    try:
                        # DROP with CASCADE to handle foreign keys
                        cur.execute(f'DROP TABLE IF EXISTS public."{table}" CASCADE')
                        print(f"    ✓ Dropped: {table}")
                    except Exception as e:
                        print(f"    ✗ Error dropping {table}: {e}")
                
                conn.commit()
                print(f"\n  ✓ Cleanup complete for {tenant.name}")
        else:
            print("  Skipped")
    else:
        print(f"  ✓ No shop tables found in public schema")

print("\n" + "=" * 70)
print("Cleanup complete!")
print("=" * 70)
