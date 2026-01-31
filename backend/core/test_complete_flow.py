#!/usr/bin/env python
"""
Complete test: Create tenant and login
"""
import os, django, json, urllib.request, urllib.error, uuid, time
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Generate unique tenant
unique_id = str(uuid.uuid4())[:8]
tenant_name = f'Login Test {unique_id}'
tenant_email = f'admin@logintest{unique_id}.local'
tenant_password = 'LoginTest123!'

print(f'='*60)
print(f'STEP 1: CREATE TENANT')
print(f'='*60)
print(f'Name: {tenant_name}')
print(f'Email: {tenant_email}')
print(f'Password: {tenant_password}')
print()

try:
    # Create tenant
    tenant_data = {
        'name': tenant_name,
        'phone': '555-0001',
        'email': tenant_email,
        'password': tenant_password
    }
    
    data = json.dumps(tenant_data).encode('utf-8')
    req = urllib.request.Request('http://localhost:8000/api/tenants/', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req, timeout=90) as response:
        response_data = json.loads(response.read().decode('utf-8'))
        tenant_slug = response_data.get('slug')
        print(f'✓ Tenant created!')
        print(f'  Slug: {tenant_slug}')
        print(f'  DB: {response_data.get("db_name")}')
        print()
        
except urllib.error.HTTPError as e:
    print(f'✗ HTTP Error {e.code}:')
    print(json.dumps(json.loads(e.read().decode()), indent=2))
    exit(1)
except Exception as e:
    print(f'✗ Error: {e}')
    exit(1)

# Wait for tenant to be fully set up
time.sleep(2)

print(f'='*60)
print(f'STEP 2: LOGIN TO TENANT')
print(f'='*60)
print(f'Tenant Slug: {tenant_slug}')
print(f'Email: {tenant_email}')
print()

try:
    # Login
    login_data = {
        'tenant_slug': tenant_slug,
        'username': tenant_email,
        'password': tenant_password
    }
    
    data = json.dumps(login_data).encode('utf-8')
    req = urllib.request.Request('http://localhost:8000/api/auth/login/', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-CSRFToken', 'test')  # Simple CSRF bypass for testing
    
    print('Sending login request...')
    with urllib.request.urlopen(req, timeout=90) as response:
        response_data = json.loads(response.read().decode('utf-8'))
        
        print(f'✓ Login successful!')
        print(f'  Access Token: {response_data.get("access")[:20]}...')
        print(f'  Refresh Token: {response_data.get("refresh")[:20]}...')
        print()
        print(f'✓✓✓ COMPLETE FLOW WORKING! ✓✓✓')
        
except urllib.error.HTTPError as e:
    error_msg = e.read().decode()
    print(f'✗ HTTP Error {e.code}:')
    try:
        print(json.dumps(json.loads(error_msg), indent=2))
    except:
        print(error_msg)
    exit(1)
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
