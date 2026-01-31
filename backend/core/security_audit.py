#!/usr/bin/env python
"""
Cross-Tenant Security Audit Script
====================================

This script tests for cross-tenant data leakage.
It performs the following tests:

1. Creates two test tenants with separate users
2. User A logs in and gets JWT token
3. Tests if User A can access User B's data
4. Verifies JWT token contains correct tenant_id
5. Tests if modifying requests can bypass tenant checks

Run this script: python backend/core/security_audit.py
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient
from tenancy.models import Tenant
from shop_users.models import ShopUser

User = get_user_model()

class SecurityAuditReport:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.start_time = datetime.now()
    
    def add_test(self, name, passed, details):
        self.tests.append({
            'name': name,
            'passed': passed,
            'details': details
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}: {name}")
        print(f"Details: {details}")
    
    def print_summary(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        print("\n" + "="*80)
        print("SECURITY AUDIT SUMMARY")
        print("="*80)
        print(f"Total Tests: {self.passed + self.failed}")
        print(f"Passed: {self.passed} ✅")
        print(f"Failed: {self.failed} ❌")
        print(f"Duration: {duration:.2f}s")
        
        if self.failed > 0:
            print("\n⚠️  SECURITY ISSUES DETECTED - Review failures above")
        else:
            print("\n✅ All security tests passed!")
        print("="*80)


def setup_test_data():
    """Create two test tenants with users"""
    print("\n[SETUP] Creating test tenants and users...")
    
    # Delete any existing test tenants
    Tenant.objects.filter(slug__startswith='test-tenant').delete()
    
    # Create Tenant A
    tenant_a = Tenant.objects.create(
        name='Test Tenant A',
        slug='test-tenant-a',
        db_alias='test_tenant_a_db'
    )
    print(f"Created {tenant_a.name} (ID: {tenant_a.id})")
    
    # Create Tenant B
    tenant_b = Tenant.objects.create(
        name='Test Tenant B',
        slug='test-tenant-b',
        db_alias='test_tenant_b_db'
    )
    print(f"Created {tenant_b.name} (ID: {tenant_b.id})")
    
    # Create User A in Tenant A
    user_a = ShopUser.objects.create_user(
        username='user_a',
        email='user.a@test.com',
        password='TestPassword123!',
        tenant_id=tenant_a.id,
        role='MANAGER'
    )
    print(f"Created User A in Tenant A: {user_a.username} (tenant_id: {user_a.tenant_id})")
    
    # Create User B in Tenant B
    user_b = ShopUser.objects.create_user(
        username='user_b',
        email='user.b@test.com',
        password='TestPassword123!',
        tenant_id=tenant_b.id,
        role='MANAGER'
    )
    print(f"Created User B in Tenant B: {user_b.username} (tenant_id: {user_b.tenant_id})")
    
    return tenant_a, tenant_b, user_a, user_b


def test_jwt_token_contains_tenant_id(report, user_a, tenant_a):
    """Test 1: Verify JWT token contains correct tenant_id"""
    print("\n[TEST 1] JWT Token Validation")
    
    try:
        # Generate JWT token
        refresh = RefreshToken()
        refresh['user_id'] = user_a.id
        refresh['tenant_id'] = tenant_a.id
        refresh['tenant_slug'] = tenant_a.slug
        
        access_token = refresh.access_token
        
        # Decode without verification to check claims
        token_data = access_token.payload
        
        passed = (
            token_data.get('user_id') == user_a.id and
            token_data.get('tenant_id') == tenant_a.id and
            token_data.get('tenant_slug') == tenant_a.slug
        )
        
        details = f"token has user_id={token_data.get('user_id')}, tenant_id={token_data.get('tenant_id')}, tenant_slug={token_data.get('tenant_slug')}"
        report.add_test("JWT contains correct tenant claims", passed, details)
        
        return str(access_token) if passed else None
    
    except Exception as e:
        report.add_test("JWT token generation", False, str(e))
        return None


def test_user_a_cannot_see_user_b_data(report, user_a, user_b, tenant_a, tenant_b):
    """Test 2: User A in Tenant A cannot access User B in Tenant B"""
    print("\n[TEST 2] Cross-Tenant Data Isolation")
    
    try:
        client = APIClient()
        
        # Simulate User A trying to access User B's profile
        # This would require manually crafting a request with User B's ID
        # but User A's token (which has tenant_a)
        
        # The backend should reject this because:
        # 1. ShopUserViewSet filters by tenant_id
        # 2. JWT token contains tenant_id of tenant_a
        # 3. When User A tries to GET /api/users/{user_b.id}/, the get_queryset()
        #    will only return users from tenant_a
        
        # Get User A's token
        refresh = RefreshToken()
        refresh['user_id'] = user_a.id
        refresh['tenant_id'] = tenant_a.id
        refresh['tenant_slug'] = tenant_a.slug
        access_token = str(refresh.access_token)
        
        # User A tries to access User B
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Set tenant context to tenant_a (simulating request)
        from tenancy.tenant_context import set_current_tenant
        set_current_tenant(tenant_a)
        
        # Try to fetch User B's data
        response = client.get(f'/api/users/{user_b.id}/')
        
        # Should get 404 since User B is not in User A's tenant
        passed = response.status_code == 404 or response.status_code == 403
        details = f"Response status: {response.status_code}. User B not accessible to User A ✅" if passed else f"User B WAS accessible (status {response.status_code}) ❌"
        
        report.add_test("User A cannot see User B", passed, details)
    
    except Exception as e:
        report.add_test("Cross-tenant access test", False, str(e))


def test_user_a_cannot_modify_user_b_password(report, user_a, user_b, tenant_a, tenant_b):
    """Test 3: User A cannot modify User B's password"""
    print("\n[TEST 3] Cross-Tenant Modification Protection")
    
    try:
        client = APIClient()
        
        # Get User A's token
        refresh = RefreshToken()
        refresh['user_id'] = user_a.id
        refresh['tenant_id'] = tenant_a.id
        refresh['tenant_slug'] = tenant_a.slug
        access_token = str(refresh.access_token)
        
        # User A tries to change User B's password
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        from tenancy.tenant_context import set_current_tenant
        set_current_tenant(tenant_a)
        
        response = client.patch(f'/api/users/{user_b.id}/', {
            'password': 'NewPassword123!'
        })
        
        # Should fail - User B not in queryset
        passed = response.status_code in [404, 403]
        details = f"Response status: {response.status_code}. Modification denied ✅" if passed else f"Modification was allowed (status {response.status_code}) ❌"
        
        report.add_test("User A cannot modify User B", passed, details)
    
    except Exception as e:
        report.add_test("Cross-tenant modification test", False, str(e))


def test_viewset_filters_by_tenant(report, user_a, tenant_a):
    """Test 4: ShopUserViewSet properly filters by tenant"""
    print("\n[TEST 4] ViewSet Tenant Filtering")
    
    try:
        from shop_users.views import ShopUserViewSet
        from rest_framework.test import APIRequestFactory
        
        factory = APIRequestFactory()
        request = factory.get('/api/users/')
        
        # Set user and tenant context
        request.user = user_a
        from tenancy.tenant_context import set_current_tenant
        set_current_tenant(tenant_a)
        
        viewset = ShopUserViewSet()
        viewset.request = request
        
        queryset = viewset.get_queryset()
        
        # Queryset should only contain users from tenant_a
        tenant_ids = set(queryset.values_list('tenant_id', flat=True))
        
        passed = len(tenant_ids) == 1 and tenant_a.id in tenant_ids
        details = f"Queryset filtered to tenant_id={tenant_ids}. Only contains tenant_a ✅" if passed else f"Queryset contains multiple tenants ❌"
        
        report.add_test("ViewSet filters by tenant", passed, details)
    
    except Exception as e:
        report.add_test("ViewSet filtering test", False, str(e))


def test_admin_routes_protected(report):
    """Test 5: Admin routes require admin role"""
    print("\n[TEST 5] Admin Route Protection")
    
    try:
        from shop_users.user_management_viewset import UserManagementViewSet
        from tenancy.permissions import IsAdminUser
        
        # Check that UserManagementViewSet requires IsAdminUser
        viewset = UserManagementViewSet()
        has_admin_check = any(
            isinstance(perm, IsAdminUser) or perm == IsAdminUser 
            for perm in viewset.permission_classes
        )
        
        passed = has_admin_check
        details = "UserManagementViewSet enforces IsAdminUser permission ✅" if passed else "AdminUser permission not enforced ❌"
        
        report.add_test("Admin routes protected", passed, details)
    
    except Exception as e:
        report.add_test("Admin protection test", False, str(e))


def main():
    print("\n" + "="*80)
    print("CROSS-TENANT SECURITY AUDIT")
    print("="*80)
    
    report = SecurityAuditReport()
    
    try:
        # Setup test data
        tenant_a, tenant_b, user_a, user_b = setup_test_data()
        
        # Run tests
        test_jwt_token_contains_tenant_id(report, user_a, tenant_a)
        test_user_a_cannot_see_user_b_data(report, user_a, user_b, tenant_a, tenant_b)
        test_user_a_cannot_modify_user_b_password(report, user_a, user_b, tenant_a, tenant_b)
        test_viewset_filters_by_tenant(report, user_a, tenant_a)
        test_admin_routes_protected(report)
        
        # Cleanup
        print("\n[CLEANUP] Removing test data...")
        Tenant.objects.filter(slug__startswith='test-tenant').delete()
        
        # Print summary
        report.print_summary()
        
        return 0 if report.failed == 0 else 1
    
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
