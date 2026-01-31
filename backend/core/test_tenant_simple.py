#!/usr/bin/env python
"""
Simple test tenant creation
"""
import os
import django
import json
import urllib.request
import urllib.error

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

print("Testing tenant creation...")

# Test data
tenant_data = {
    "name": "Test Tenant",
    "phone": "555-0001",
    "email": "admin@testtenant.local",
    "password": "TestPass123!"
}

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
        print("Response:")
        print(json.dumps(response_data, indent=2))

        if status_code in [200, 201]:
            print("SUCCESS: Tenant created successfully!")
        else:
            print("ERROR: Tenant creation failed")

except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}:")
    try:
        response_data = json.loads(e.read().decode('utf-8'))
        print(json.dumps(response_data, indent=2))
    except:
        print(e.read().decode('utf-8'))

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()