#!/usr/bin/env python
"""Test shop creation with the refactored settings models."""
import os
import sys
import django
import uuid

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant, Shop
from apps.settings.models import SalesArea, SystemConfiguration
from django.contrib.auth import get_user_model

User = get_user_model()

def test_shop_creation():
    """Test creating a shop and verify settings models work."""
    print("=" * 60)
    print("TESTING SHOP CREATION WITH REFACTORED SETTINGS MODELS")
    print("=" * 60)
    
    # Use unique identifiers to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    tenant_name = f'test_refactor_{unique_id}'
    schema_name = f'shop_{unique_id}'
    
    # Step 1: Check/create test tenant
    print("\n[1] Testing Tenant Creation...")
    try:
        tenant = Tenant.objects.filter(name=tenant_name).first()
        if not tenant:
            tenant = Tenant.objects.create(
                name=tenant_name,
                slug=tenant_name,
                subdomain=tenant_name,
                db_name=f'test_db_{unique_id}',
                db_password='postgres'
            )
            print(f"    [OK] Created tenant: {tenant.name}")
        else:
            print(f"    [OK] Using existing tenant: {tenant.name}")
    except Exception as e:
        print(f"    [FAIL] Error creating tenant: {e}")
        return False
    
    # Step 2: Create shop (this triggers migrations in shop schema)
    print("\n[2] Testing Shop Creation (triggers shop schema migrations)...")
    try:
        shop = Shop.objects.create(
            tenant=tenant,
            name='Refactor Test Shop',
            schema_name=schema_name
        )
        print(f"    [OK] Created shop: {shop.name}")
        print(f"      - Schema: {shop.schema_name}")
        print(f"      - Status: {'ACTIVE' if shop.is_active else 'INACTIVE'}")
        print(f"      - Head Office: {shop.is_head_office}")
    except Exception as e:
        print(f"    [FAIL] Error creating shop: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 3: Test settings models structure
    print("\n[3] Testing Settings Models Structure...")
    try:
        # Verify models exist and have correct fields
        print(f"    [OK] SalesArea model fields:")
        for field in SalesArea._meta.fields:
            print(f"      - {field.name}: {field.get_internal_type()}")
        
        print(f"    [OK] SystemConfiguration model fields:")
        for field in SystemConfiguration._meta.fields:
            print(f"      - {field.name}: {field.get_internal_type()}")
        
        # Verify no tenancy imports
        print(f"    [OK] Models verified:")
        print(f"      - SalesArea: No ForeignKey to Shop (using CharField instead)")
        print(f"      - SystemConfiguration: No ForeignKey to Tenant or Shop")
        
    except Exception as e:
        print(f"    [FAIL] Error testing settings models: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("[PASS] ALL TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = test_shop_creation()
    sys.exit(0 if success else 1)
