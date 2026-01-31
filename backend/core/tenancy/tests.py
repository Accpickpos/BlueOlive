# tenancy/tests_jwt.py
"""
Test cases for JWT authentication in multi-tenant system
Run with: python manage.py test tenancy.tests_jwt
"""
from django.test import TestCase, Client
from django.contrib.auth.hashers import make_password
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from tenancy.models import Tenant, Shop
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


if __name__ == '__main__':
    import sys
    from django.core.management import execute_from_command_line
    execute_from_command_line([sys.argv[0], 'test', 'tenancy.tests_jwt'])