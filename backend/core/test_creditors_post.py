#!/usr/bin/env python
"""Test POST to creditors/suppliers endpoint"""
import os
import django
import json
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.settings.models import CreditTerms

User = get_user_model()

# Create a test client
client = Client()

# Get or create a test user
try:
    user = User.objects.get(username='testuser')
except User.DoesNotExist:
    user = User.objects.create_user(username='testuser', password='testpass')

# Login
client.login(username='testuser', password='testpass')

# Get or create default credit terms
credit_terms, _ = CreditTerms.objects.get_or_create(
    name='Net 30',
    defaults={'days': 30}
)

# Test data for creating a supplier
test_data = {
    'supplier_number': 'SUP001',
    'account_number': 'ACC001',
    'name': 'Test Supplier',
    'short_name': 'TS',
    'telephone1': '555-1234',
    'email': 'test@example.com',
    'credit_terms': credit_terms.id,
}

# Make POST request
response = client.post(
    '/api/creditors/suppliers/',
    data=json.dumps(test_data),
    content_type='application/json'
)

print(f"Status Code: {response.status_code}")
print(f"Response Content: {response.content.decode()}")
