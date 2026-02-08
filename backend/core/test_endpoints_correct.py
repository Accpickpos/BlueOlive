#!/usr/bin/env python
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client

# Make requests with proper HOST header for localhost
client = Client(enforce_csrf_checks=False, SERVER_NAME='localhost', SERVER_PORT='8000')

print("=" * 60)
print("Testing /api/users/auth/csrf/")
print("=" * 60)
try:
    response = client.get('/api/users/auth/csrf/', HTTP_HOST='localhost:8000')
    print(f"Status Code: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"Response: {response.content.decode()}")
    else:
        print(f"Error Response: {response.content.decode()[:500]}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 60)
print("Testing /api/users/auth/profile/ (unauthenticated)")
print("=" * 60)
try:
    response = client.get('/api/users/auth/profile/', HTTP_HOST='localhost:8000')
    print(f"Status Code: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"Response: {response.content.decode()}")
    else:
        print(f"Error Response: {response.content.decode()[:500]} (Expected 401 Unauthorized)")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {str(e)}")

print("\n" + "=" * 60)
print("Testing /api/users/auth/login/ (POST)")
print("=" * 60)
try:
    response = client.post(
        '/api/users/auth/login/',
        data=json.dumps({'username': 'admin', 'password': 'admin', 'tenant_slug': 'dev'}),
        content_type='application/json',
        HTTP_HOST='localhost:8000'
    )
    print(f"Status Code: {response.status_code}")
    if response.status_code in [200, 201]:
        print(f"Response: {response.content.decode()}")
    else:
        print(f"Error Response: {response.content.decode()[:500]}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {str(e)}")
