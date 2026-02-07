#!/usr/bin/env python
"""
Test script to debug POST /api/users/ 400 error
"""
import os
import sys
import django
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from tenancy.models import Tenant

User = get_user_model()

def test_create_user():
    """Test creating a user via API"""
    client = APIClient()
    
    # First, get the admin user and tenant
    admin_user = User.objects.filter(is_superuser=True).first()
    tenant = Tenant.objects.first()
    
    if not admin_user:
        print("❌ No superuser found in database")
        return
    
    if not tenant:
        print("❌ No tenant found in database")
        return
    
    print(f"✓ Admin user: {admin_user.username}")
    print(f"✓ Tenant: {tenant.name} (slug={tenant.slug})")
    
    # Get the token for the admin user
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken()
    refresh['user_id'] = admin_user.id
    refresh['username'] = admin_user.username
    refresh['email'] = admin_user.email
    refresh['tenant_id'] = tenant.id
    refresh['tenant_slug'] = tenant.slug
    
    access_token = str(refresh.access_token)
    print(f"✓ Generated access token")
    
    # Test different POST payloads
    test_cases = [
        {
            "name": "Minimal required fields",
            "data": {
                "username": "testuser1",
                "email": "testuser1@example.com",
            }
        },
        {
            "name": "With password",
            "data": {
                "username": "testuser2",
                "email": "testuser2@example.com",
                "password": "TestPassword123!",
            }
        },
        {
            "name": "With all fields",
            "data": {
                "username": "testuser3",
                "email": "testuser3@example.com",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User",
                "role": "STAFF",
            }
        },
    ]
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test['name']}")
        print(f"Payload: {json.dumps(test['data'], indent=2)}")
        print(f"{'='*60}")
        
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = client.post(
            '/api/users/',
            data=test['data'],
            format='json'
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.data}")
        
        if response.status_code != 201:
            print(f"❌ Error: {response.status_code}")
        else:
            print(f"✓ Success: User created")

if __name__ == '__main__':
    print("Testing POST /api/users/ endpoint\n")
    test_create_user()
