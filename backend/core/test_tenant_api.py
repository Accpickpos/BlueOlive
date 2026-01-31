#!/usr/bin/env python
"""
Test tenant creation and login flow
"""
import os
import django
import json
import urllib.request
import urllib.error

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings

# Verify credentials are loaded
print(f"✓ Django settings loaded")
print(f"  DB User: {settings.DATABASES['default']['USER']}")
print(f"  DB Password: {settings.DATABASES['default']['PASSWORD']}")
print(f"  DB Host: {settings.DATABASES['default']['HOST']}")
print()

# Test data
tenant_data = {
    "name": "API Test Tenant",
    "phone": "555-0001",
    "email": "admin@apitesttenant.local",
    "password": "ApiTestPass123!"
}

print(f"Creating tenant with data:")
print(json.dumps(tenant_data, indent=2))
print()

try:
    # Create tenant
    url = 'http://localhost:8000/api/tenants/'
    data = json.dumps(tenant_data).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req, timeout=30) as response:
        status_code = response.status
        response_data = json.loads(response.read().decode('utf-8'))
        
        print(f"Status Code: {status_code}")
        print(f"Response:")
        print(json.dumps(response_data, indent=2))
        
        if status_code in [200, 201]:
            print(f"\n✓ Tenant created successfully!")
            print(f"  Slug: {response_data.get('slug')}")
            print(f"  DB Name: {response_data.get('db_name')}")
            print(f"  DB User: {response_data.get('db_user')}")
            print(f"  DB Password: {response_data.get('db_password')}")
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}:")
    try:
        response_data = json.loads(e.read().decode('utf-8'))
        print(json.dumps(response_data, indent=2))
    except:
        print(e.read().decode('utf-8'))
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
