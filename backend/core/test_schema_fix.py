#!/usr/bin/env python
"""
Test script to verify the SchemaMiddleware fix for departments.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant, Shop
from apps.settings.models import SalesDepartment
from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current

def test_department_query():
    """Test that SalesDepartment can be queried with proper schema context."""
    try:
        # Get the Volt tenant
        tenant = Tenant.objects.get(slug='volt')
        print(f"✓ Found tenant: {tenant.name}")
        
        # Get a shop
        shop = Shop.objects.filter(tenant=tenant, is_active=True).first()
        if not shop:
            print("✗ No shop found for tenant")
            return False
        print(f"✓ Found shop: {shop.name} (schema: {shop.schema_name})")
        
        # Set context as middleware would
        set_current_tenant(tenant)
        set_current_shop(shop.schema_name)
        print(f"✓ Set context: tenant={tenant.slug}, shop_schema={shop.schema_name}")
        
        # Simulate setting search_path as SchemaMiddleware does
        db_alias = tenant.db_alias
        conn = connections[db_alias]
        with conn.cursor() as cursor:
            cursor.execute(f"SET search_path TO {shop.schema_name}, public")
            print(f"✓ Set search_path to: {shop.schema_name}, public")
        
        # Try to query SalesDepartment
        count = SalesDepartment.objects.using(db_alias).count()
        print(f"✓ SalesDepartment query successful: {count} records found")
        
        # Get all departments
        departments = SalesDepartment.objects.using(db_alias).all()[:5]
        for dept in departments:
            print(f"  - {dept.name} (ID: {dept.id})")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        clear_current()

if __name__ == '__main__':
    print("Testing department query with schema context...\n")
    success = test_department_query()
    print(f"\n{'SUCCESS' if success else 'FAILED'}")
    exit(0 if success else 1)
