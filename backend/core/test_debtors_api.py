#!/usr/bin/env python
"""
Test script to identify the debtors API error
"""
import os
import sys
import django
from django.test import Client

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from tenancy.models import Tenant
from shop_users.models import ShopUser

User = get_user_model()

# Get or create test tenant
tenant, _ = Tenant.objects.get_or_create(
    slug='test',
    defaults={
        'name': 'Test Tenant',
        'subdomain': 'test'
    }
)

# Get or create test user
try:
    user = ShopUser.objects.get(username='testuser')
except ShopUser.DoesNotExist:
    user = ShopUser.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        tenant_id=tenant.id
    )

# Create client and login
client = Client(enforce_csrf_checks=False)
if client.login(username='testuser', password='testpass123'):
    print("Successfully logged in as testuser")
else:
    print("Failed to login - trying with admin user")
    # Try to create superuser instead
    try:
        User.objects.get(username='admin')
    except User.DoesNotExist:
        User.objects.create_superuser('admin', 'admin@test.com', 'admin123')
    client.login(username='admin', password='admin123')

# Test debtors endpoint
print("Testing /api/debtors/debtors/ endpoint...")
try:
    response = client.get('/api/debtors/debtors/', HTTP_HOST='localhost:8000')
    print(f"Status Code: {response.status_code}")
    response_text = response.content.decode()
    print(f"Response Length: {len(response_text)}")
    print(f"Response Preview: {response_text[:500]}")
    
    if response.status_code >= 400:
        # Print full response for debugging
        print(f"\nFull Response:\n{response_text}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

