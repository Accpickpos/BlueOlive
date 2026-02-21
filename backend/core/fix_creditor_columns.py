"""
Quick script to add missing creditor columns to existing shops.
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection

def fix_creditor_columns():
    tenants = Tenant.objects.filter(is_active=True)
    print(f'Found {tenants.count()} active tenants')
    
    for tenant in tenants:
        print(f'\nProcessing tenant: {tenant.name} ({tenant.db_alias})')
        register_tenant_connection(tenant)
        
        shops = Shop.objects.using('default').filter(tenant=tenant, is_active=True)
        for shop in shops:
            schema = shop.schema_name
            print(f'  Shop: {schema}')
            conn = connections[tenant.db_alias]
            
            with conn.cursor() as cur:
                # Check current
                cur.execute(f'SET search_path TO "{schema}"')
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'creditors' 
                    AND column_name LIKE '%address%'
                """)
                cols = [r[0] for r in cur.fetchall()]
                print(f'    Address columns: {cols}')
                
                # Add missing columns
                for col, typ, default in [
                    ('physical_address_line3', 'varchar(100)', "''"),
                    ('postal_address_line3', 'varchar(100)', "''"),
                    ('total_outstanding_balance', 'decimal(15,2)', '0'),
                    ('payment_terms_days', 'smallint', '30'),
                ]:
                    if col not in cols:
                        print(f'    Adding {col}...')
                        try:
                            cur.execute(f'ALTER TABLE creditors ADD COLUMN {col} {typ} DEFAULT {default}')
                            conn.commit()
                            print(f'      Added {col}')
                        except Exception as e:
                            print(f'      Error: {e}')
                
                # Verify
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'creditors' 
                    AND column_name IN ('physical_address_line3', 'postal_address_line3', 'total_outstanding_balance', 'payment_terms_days')
                """)
                new_cols = [r[0] for r in cur.fetchall()]
                print(f'    New columns now: {new_cols}')

if __name__ == '__main__':
    fix_creditor_columns()
    print('\nDone!')
