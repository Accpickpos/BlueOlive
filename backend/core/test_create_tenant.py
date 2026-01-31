import os, django, json, urllib.request, urllib.error, uuid
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

unique_id = str(uuid.uuid4())[:8]
tenant_data = {
    'name': f'Test Tenant {unique_id}',
    'phone': '555-0002',
    'email': f'admin@test{unique_id}.local',
    'password': 'TestPass123!'
}
print(f'Creating tenant: {tenant_data["name"]}')
print('Sending request...')

try:
    data = json.dumps(tenant_data).encode('utf-8')
    req = urllib.request.Request('http://localhost:8000/api/tenants/', data=data, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    with urllib.request.urlopen(req, timeout=90) as response:
        status_code = response.status
        response_data = json.loads(response.read().decode('utf-8'))
        print(f'✓ Status: {status_code}')
        print(f'✓ Slug: {response_data.get("slug")}')
        print(f'✓ DB User: {response_data.get("db_user")}')
        print(f'✓ DB Password set: {response_data.get("db_password") is not None}')
        
except urllib.error.HTTPError as e:
    print(f'HTTP Error {e.code}:')
    try:
        resp = json.loads(e.read().decode())
        print(json.dumps(resp, indent=2))
    except:
        print(e.read().decode())
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
