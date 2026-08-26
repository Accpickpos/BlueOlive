# tenancy/tests_jwt.py
"""
Test cases for JWT authentication in multi-tenant system
Run with: python manage.py test tenancy.tests_jwt
"""
from types import SimpleNamespace
from django.db import connections
from django.test import TestCase, Client, RequestFactory, SimpleTestCase
from django.contrib.auth.hashers import make_password
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from tenancy.middleware import TenantMiddleware
from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection
from shop_users.models import ShopUser
import json


class JWTAuthenticationTestCase(APITestCase):
    """Test JWT authentication endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create tenant
        self.tenant = Tenant.objects.create(
            name='Test Tenant',
            slug='test-tenant',
            subdomain='test-tenant',
            db_name='test_db',
            db_user='postgres',
            db_password='0660089932@G',
            db_host='localhost',
            db_port=5432
        )
        
        # Create shop
        self.shop = Shop.objects.create(
            tenant=self.tenant,
            name='Main Shop',
            schema_name='test_tenant_main',
            subdomain='main',
            is_head_office=True
        )
        
        # Create test user
        self.user = ShopUser.objects.create(
            username='testuser@example.com',
            email='testuser@example.com',
            first_name='Test',
            last_name='User',
            password=make_password('testpass123'),
            tenant_id=self.tenant.id,
            role='ADMIN',
            is_active=True
        )
        
        self.client = APIClient()
        self.login_url = '/api/auth/login/'
        self.refresh_url = '/api/auth/token/refresh/'
        self.logout_url = '/api/auth/logout/'
        self.profile_url = '/api/auth/profile/'
        self.verify_url = '/api/auth/verify/'
    
    def test_login_success(self):
        """Test successful login"""
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'testpass123',
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertIn('tenant', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')
        self.assertEqual(response.data['tenant']['slug'], 'test-tenant')
    
    def test_login_with_email(self):
        """Test login using email as username"""
        response = self.client.post(self.login_url, {
            'email': 'testuser@example.com',
            'password': 'testpass123',
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'wrongpassword',
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_invalid_tenant(self):
        """Test login with invalid tenant"""
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'testpass123',
            'tenant_slug': 'invalid-tenant'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials"""
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            # Missing password
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_inactive_user(self):
        """Test login with inactive user"""
        self.user.is_active = False
        self.user.save()
        
        response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'testpass123',
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_token_refresh(self):
        """Test token refresh"""
        # First login to get tokens
        login_response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'testpass123',
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        refresh_token = login_response.data['refresh']
        
        # Refresh the token
        response = self.client.post(self.refresh_url, {
            'refresh': refresh_token
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
    
    def test_token_verify(self):
        """Test token verification"""
        # Login to get token
        login_response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'testpass123',
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        access_token = login_response.data['access']
        
        # Verify token
        response = self.client.post(self.verify_url, {
            'token': access_token
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
    
    def test_token_verify_invalid(self):
        """Test verification of invalid token"""
        response = self.client.post(self.verify_url, {
            'token': 'invalid.token.here'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['valid'])
    
    def test_authenticated_request(self):
        """Test making authenticated request"""
        # Login to get token
        login_response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'testpass123',
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        access_token = login_response.data['access']
        
        # Make authenticated request
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')
    
    def test_unauthenticated_request(self):
        """Test making request without authentication"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout(self):
        """Test logout functionality"""
        # Login to get tokens
        login_response = self.client.post(self.login_url, {
            'username': 'testuser@example.com',
            'password': 'testpass123',
            'tenant_slug': 'test-tenant'
        }, format='json')
        
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.post(self.logout_url, {
            'refresh': refresh_token
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to use the refresh token again (should fail)
        refresh_response = self.client.post(self.refresh_url, {
            'refresh': refresh_token
        }, format='json')
        
        # Should fail because token is blacklisted
        self.assertNotEqual(refresh_response.status_code, status.HTTP_200_OK)


class TenantContextTestCase(APITestCase):
    """Test tenant context in JWT authentication"""
    
    def setUp(self):
        """Set up test data with multiple tenants"""
        # Create two tenants
        self.tenant1 = Tenant.objects.create(
            name='Tenant One',
            slug='tenant-one',
            subdomain='tenant1',
            db_name='tenant1_db',
            db_user='postgres',
            db_password='password',
        )
        
        self.tenant2 = Tenant.objects.create(
            name='Tenant Two',
            slug='tenant-two',
            subdomain='tenant2',
            db_name='tenant2_db',
            db_user='postgres',
            db_password='password',
        )
        
        # Create users for each tenant
        self.user1 = ShopUser.objects.create(
            username='user1@example.com',
            email='user1@example.com',
            password=make_password('pass123'),
            tenant_id=self.tenant1.id,
            role='ADMIN',
            is_active=True
        )
        
        self.user2 = ShopUser.objects.create(
            username='user2@example.com',
            email='user2@example.com',
            password=make_password('pass123'),
            tenant_id=self.tenant2.id,
            role='ADMIN',
            is_active=True
        )
        
        self.client = APIClient()
        self.login_url = '/api/auth/login/'
    
    def test_user_belongs_to_correct_tenant(self):
        """Test that user can only login to their own tenant"""
        # User1 should login successfully to tenant1
        response1 = self.client.post(self.login_url, {
            'username': 'user1@example.com',
            'password': 'pass123',
            'tenant_slug': 'tenant-one'
        }, format='json')
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data['tenant']['slug'], 'tenant-one')
        
        # User2 should login successfully to tenant2
        response2 = self.client.post(self.login_url, {
            'username': 'user2@example.com',
            'password': 'pass123',
            'tenant_slug': 'tenant-two'
        }, format='json')
        
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data['tenant']['slug'], 'tenant-two')
    
    def test_user_cannot_login_to_wrong_tenant(self):
        """Test that user cannot login to a different tenant"""
        # Try to login user1 to tenant2 (should fail)
        response = self.client.post(self.login_url, {
            'username': 'user1@example.com',
            'password': 'pass123',
            'tenant_slug': 'tenant-two'
        }, format='json')
        
        # Should fail - user1 doesn't exist in tenant2
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TenantMiddlewareNoShopConnectionTestCase(SimpleTestCase):
    """
    Regression test for: /token/refresh/ returning 500
    django.utils.connection.ConnectionDoesNotExist: The connection 'tenant_1' doesn't exist.

    TenantMiddleware calls set_current_tenant() unconditionally but used to
    skip register_tenant_connection() whenever no shop could be identified
    (e.g. /token/refresh/, which runs with authentication_classes=[] and is
    normally called with an *expired* access token, so shop lookup fails).
    TenantDatabaseRouter routes any TENANT_APP_LABELS model (e.g.
    token_blacklist, checked on every refresh) to tenant.db_alias based
    purely on get_current_tenant() - so leaving the alias unregistered
    raised ConnectionDoesNotExist on the first such query.
    """

    def setUp(self):
        self.tenant = SimpleNamespace(
            name="Regression Tenant",
            slug="regression-tenant",
            db_alias="tenant_regression_test",
            db_name="regression_test_db",
            db_host="localhost",
            db_port=5432,
            shops=SimpleNamespace(first=lambda: None),
        )
        self.addCleanup(connections.databases.pop, self.tenant.db_alias, None)

    def test_base_alias_registered_when_no_shop_identified(self):
        middleware = TenantMiddleware(get_response=lambda request: None)
        middleware._identify_tenant = lambda request: self.tenant
        middleware._identify_shop = lambda request, tenant: None

        request = RequestFactory().post('/api/v1/users/auth/token/refresh/')
        middleware(request)

        self.assertIn(
            self.tenant.db_alias,
            connections.databases,
            "tenant.db_alias must be registered even without an identified "
            "shop, or TENANT_APP_LABELS queries (e.g. token_blacklist during "
            "refresh) raise ConnectionDoesNotExist.",
        )


class RegisterTenantConnectionEvictsStaleBaseAliasTestCase(SimpleTestCase):
    """
    Regression test for a latent cross-shop data leak: register_tenant_connection()
    reassigns connections.databases[base_alias] to a new dict on every call, but
    Django's BaseDatabaseWrapper pins self.settings_dict to the exact dict object
    it was constructed with (django/db/backends/base/base.py) - a bare .close()
    reopens the socket using that SAME stale dict, it doesn't pick up the
    reassignment. base_alias (tenant.db_alias) is shared across every shop of a
    tenant and is what TenantDatabaseRouter falls back to for SHOP_APP_LABELS
    queries under a tenant context, so a worker thread that already opened a
    base_alias connection for one shop would keep silently querying through
    that shop's schema for every other shop routed there afterwards.
    """

    @staticmethod
    def _evict(alias):
        """hasattr/delattr, not `in connections._connections.__dict__` -
        see the CRITICAL #2 note in register_tenant_connection()."""
        if hasattr(connections._connections, alias):
            del connections[alias]

    def setUp(self):
        self.tenant = SimpleNamespace(
            name="Regression Tenant 2",
            slug="regression-tenant-2",
            db_alias="tenant_regression_test_2",
            db_name="regression_test_db_2",
            db_host="localhost",
            db_port=5432,
        )
        # register_tenant_connection() also creates a shop-specific alias
        # (base_alias + "_" + shop name) alongside the base one - clean up
        # all aliases this test registers, in both connections.databases
        # AND connections._connections, or Django's SimpleTestCase teardown
        # (_remove_databases_failures) trips over aliases that existed at
        # test end but weren't wrapped at setUpClass time.
        for alias in (
            self.tenant.db_alias,
            f"{self.tenant.db_alias}_shop_a",
            f"{self.tenant.db_alias}_shop_b",
        ):
            self.addCleanup(connections.databases.pop, alias, None)
            self.addCleanup(self._evict, alias)

    def test_base_alias_connection_evicted_on_shop_switch(self):
        shop_a = SimpleNamespace(name="Shop A", schema_name="shop_a")
        shop_b = SimpleNamespace(name="Shop B", schema_name="shop_b")

        register_tenant_connection(self.tenant, shop=shop_a)

        # Simulate a connection already opened for the base alias in this
        # thread (as a SHOP_APP_LABELS query routed via tenant.db_alias
        # would do), pinned to shop A's config.
        connections[self.tenant.db_alias] = SimpleNamespace(close=lambda: None)
        self.assertTrue(hasattr(connections._connections, self.tenant.db_alias))

        register_tenant_connection(self.tenant, shop=shop_b)

        self.assertFalse(
            hasattr(connections._connections, self.tenant.db_alias),
            "register_tenant_connection() must evict the cached connection "
            "for the shared base alias when the schema changes, otherwise "
            "the next query reuses a wrapper still pinned to the OLD shop's "
            "search_path.",
        )


if __name__ == '__main__':
    import sys
    from django.core.management import execute_from_command_line
    execute_from_command_line([sys.argv[0], 'test', 'tenancy.tests_jwt'])
