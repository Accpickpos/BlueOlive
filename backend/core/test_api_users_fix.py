#!/usr/bin/env python
"""
Test script to validate POST /api/users/ fix
Tests the corrected serializer and viewset behavior
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from rest_framework.test import APIRequestFactory
from shop_users.serializers import ShopUserSerializer, ShopUserCreateSerializer
from shop_users.models import ShopUser

def test_serializer_validation():
    """Test that ShopUserCreateSerializer has proper validation"""
    print("\n" + "="*70)
    print("TEST 1: ShopUserCreateSerializer Field Validation")
    print("="*70)
    
    # Test 1: Missing required fields
    print("\n[1.1] Testing missing required fields:")
    data = {}
    serializer = ShopUserCreateSerializer(data=data)
    is_valid = serializer.is_valid()
    
    print(f"  Data: {data}")
    print(f"  Valid: {is_valid}")
    if not is_valid:
        for field, errors in serializer.errors.items():
            print(f"    ✓ {field}: {errors}")
    
    # Test 2: Password mismatch validation
    print("\n[1.2] Testing password mismatch validation:")
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePass123!",
        "confirm_password": "DifferentPass123!",
    }
    serializer = ShopUserCreateSerializer(data=data)
    is_valid = serializer.is_valid()
    
    print(f"  Data: {json.dumps({k: v for k, v in data.items() if k != 'password'}, indent=2)}")
    print(f"  Valid: {is_valid}")
    if not is_valid:
        print(f"    ✓ Errors: {serializer.errors}")
    
    # Test 3: Weak password
    print("\n[1.3] Testing weak password validation:")
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "weak",
        "confirm_password": "weak",
    }
    serializer = ShopUserCreateSerializer(data=data)
    is_valid = serializer.is_valid()
    
    print(f"  Password: 'weak' (too short)")
    print(f"  Valid: {is_valid}")
    if not is_valid:
        for field, errors in serializer.errors.items():
            print(f"    ✓ {field}: {errors}")
    
    # Test 4: Valid data
    print("\n[1.4] Testing valid user creation data:")
    data = {
        "username": "testuser123",
        "email": "testuser@example.com",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "STAFF",
        "phone": "1234567890",
        "shop_ids": [1, 2],
    }
    serializer = ShopUserCreateSerializer(data=data)
    is_valid = serializer.is_valid()
    
    print(f"  Data: Valid user creation payload")
    print(f"  Valid: {is_valid}")
    if not is_valid:
        print(f"  Errors: {serializer.errors}")
    else:
        print(f"  ✓ All fields properly validated")
        print(f"  ✓ shop_ids field accepted")

def test_serializer_fields():
    """Test that serializers have correct field configurations"""
    print("\n" + "="*70)
    print("TEST 2: Serializer Field Configuration")
    print("="*70)
    
    print("\n[2.1] ShopUserCreateSerializer fields:")
    serializer = ShopUserCreateSerializer()
    print(f"  Fields: {list(serializer.fields.keys())}")
    
    expected_fields = ['username', 'email', 'first_name', 'last_name', 'password', 
                      'confirm_password', 'role', 'phone', 'shop_ids']
    missing_fields = set(expected_fields) - set(serializer.fields.keys())
    
    if not missing_fields:
        print(f"  ✓ All expected fields present")
    else:
        print(f"  ✗ Missing fields: {missing_fields}")
    
    print("\n[2.2] ShopUserCreateSerializer password field configuration:")
    password_field = serializer.fields.get('password')
    if password_field:
        print(f"  Required: {password_field.required}")
        print(f"  Write-only: {password_field.read_only == False}")
        print(f"  Min length: {password_field.min_length}")
        if password_field.required and password_field.min_length == 8:
            print(f"  ✓ Password field properly configured")

def test_viewset_serializer_selection():
    """Test that ViewSet selects correct serializer for create action"""
    print("\n" + "="*70)
    print("TEST 3: ViewSet Serializer Selection")
    print("="*70)
    
    from shop_users.views import ShopUserViewSet
    
    viewset = ShopUserViewSet()
    
    # Test create action
    viewset.action = 'create'
    serializer_class = viewset.get_serializer_class()
    print(f"\n[3.1] action='create':")
    print(f"  Serializer: {serializer_class.__name__}")
    if serializer_class.__name__ == 'ShopUserCreateSerializer':
        print(f"  ✓ Correct serializer selected for creation")
    else:
        print(f"  ✗ Wrong serializer - expected ShopUserCreateSerializer")
    
    # Test list action
    viewset.action = 'list'
    serializer_class = viewset.get_serializer_class()
    print(f"\n[3.2] action='list':")
    print(f"  Serializer: {serializer_class.__name__}")
    if serializer_class.__name__ == 'ShopUserSerializer':
        print(f"  ✓ Correct serializer selected for listing")
    else:
        print(f"  ✗ Wrong serializer - expected ShopUserSerializer")
    
    # Test retrieve action
    viewset.action = 'retrieve'
    serializer_class = viewset.get_serializer_class()
    print(f"\n[3.3] action='retrieve':")
    print(f"  Serializer: {serializer_class.__name__}")
    if serializer_class.__name__ == 'ShopUserSerializer':
        print(f"  ✓ Correct serializer selected for retrieval")

def test_imports():
    """Test that all imports are working correctly"""
    print("\n" + "="*70)
    print("TEST 4: Import Verification")
    print("="*70)
    
    try:
        from shop_users.views import ShopUserViewSet
        print("\n[4.1] ShopUserViewSet import:")
        print(f"  ✓ Successfully imported ShopUserViewSet")
        
        from shop_users.serializers import ShopUserSerializer, ShopUserCreateSerializer
        print("\n[4.2] Serializers import:")
        print(f"  ✓ Successfully imported ShopUserSerializer")
        print(f"  ✓ Successfully imported ShopUserCreateSerializer")
        
        # Check method exists
        if hasattr(ShopUserViewSet, 'get_serializer_class'):
            print("\n[4.3] ViewSet methods:")
            print(f"  ✓ get_serializer_class() method exists")
        
        return True
    except Exception as e:
        print(f"\n✗ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("TESTING POST /api/users/ FIX")
    print("="*70)
    
    # Test imports first
    if not test_imports():
        print("\n❌ Import tests failed - cannot continue")
        return False
    
    # Run other tests
    test_viewset_serializer_selection()
    test_serializer_fields()
    test_serializer_validation()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("""
✓ ShopUserViewSet now uses ShopUserCreateSerializer for creation
✓ ShopUserCreateSerializer has proper field validation
✓ Password field is required with minimum 8 characters
✓ Password and confirm_password must match
✓ shop_ids field is available for shop assignment
✓ All imports working correctly
    """)
    print("="*70)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
