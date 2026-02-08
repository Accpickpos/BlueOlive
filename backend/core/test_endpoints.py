#!/usr/bin/env python
import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.test import Client
from django.http import HttpResponse

# Make requests with proper HOST header for localhost
client = Client(enforce_csrf_checks=False, SERVER_NAME='localhost', SERVER_PORT='8000')

print("=" * 60)
print("Testing /api/auth/csrf/")
print("=" * 60)
try:
    response = client.get('/api/auth/csrf/', HTTP_HOST='localhost:8000')
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.items())}")
    if response.status_code in [200, 201]:
        print(f"Response: {response.content.decode()}")
    else:
        print(f"Error Response: {response.content.decode()[:500]}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing /api/auth/profile/")
print("=" * 60)
try:
    response = client.get('/api/auth/profile/', HTTP_HOST='localhost:8000')
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.items())}")
    if response.status_code in [200, 201]:
        print(f"Response: {response.content.decode()}")
    else:
        print(f"Error Response (first 500 chars): {response.content.decode()[:500]}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Testing /api/auth/login/ (POST)")
print("=" * 60)
try:
    response = client.post(
        '/api/auth/login/',
        data=json.dumps({'username': 'admin', 'password': 'admin', 'tenant_slug': 'dev'}),
        content_type='application/json',
        HTTP_HOST='localhost:8000'
    )
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.items())}")
    if response.status_code in [200, 201]:
        print(f"Response: {response.content.decode()}")
    else:
        print(f"Error Response (first 500 chars): {response.content.decode()[:500]}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
