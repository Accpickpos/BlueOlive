#!/usr/bin/env python
"""
Test complete signup flow with fresh tenant creation.
This tests that the original signup error is resolved.
"""
import os
import sys
import django
import json
import requests
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/c/Users/accpi/OneDrive/Documents/GitHub/BlueOlive/backend/core')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from tenancy.models import Tenant
from rest_framework.test import APIClient

# Test data
timestamp = int(datetime.now().timestamp() * 1000) % 1000000
SHOP_NAME = f"TestShop{timestamp}"
SHOP_SLUG = f"test-shop-{timestamp}"
TEST_EMAIL = f"user{timestamp}@testshop.local"
TEST_PASSWORD = "TestPass123!@#"
TENANT_DB_NAME = f"test_tenant_{timestamp}"

print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                         TESTING SIGNUP FLOW                                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Test Configuration:
  Shop Name: {SHOP_NAME}
  Shop Slug: {SHOP_SLUG}
  Email: {TEST_EMAIL}
  Database: {TENANT_DB_NAME}
""")

def check_tenant_tables(db_name):
    """Verify all required tables exist in the tenant database."""
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='postgres',
        database=db_name
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get list of tables
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cur.fetchall()]
        
        critical_tables = [
            'shop_users_shopuser',
            'django_admin_log',
            'django_session',
            'token_blacklist_blacklistedtoken',
            'token_blacklist_outstandingtoken'
        ]
        
        print(f"\n✓ Tenant database tables ({len(tables)} total):")
        for table in sorted(tables):
            status = "✓" if table in critical_tables else " "
            print(f"  [{status}] {table}")
        
        missing = [t for t in critical_tables if t not in tables]
        if missing:
            print(f"\n✗ MISSING CRITICAL TABLES: {missing}")
            return False
        
        print(f"\n✓ All critical tables present!")
        return True
        
    finally:
        cur.close()
        conn.close()

def test_signup_api():
    """Test signup through API."""
    print("\n" + "="*80)
    print("PHASE 1: Testing Signup API")
    print("="*80)
    
    client = APIClient()
    
    signup_data = {
        'email': TEST_EMAIL,
        'password': TEST_PASSWORD,
        'password2': TEST_PASSWORD,
        'shop_name': SHOP_NAME,
        'shop_slug': SHOP_SLUG,
    }
    
    print(f"\nPOST /api/auth/signup/ with:")
    print(f"  Email: {TEST_EMAIL}")
    print(f"  Shop: {SHOP_NAME} ({SHOP_SLUG})")
    
    try:
        response = client.post('/api/auth/signup/', signup_data, format='json')
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"\n✓ SIGNUP SUCCESSFUL!")
            print(f"  User: {data.get('user', {}).get('email')}")
            print(f"  Tenant: {data.get('tenant', {}).get('slug')}")
            print(f"  Tokens: {'access' in data and 'refresh' in data}")
            return True, data
        else:
            print(f"\n✗ SIGNUP FAILED!")
            print(f"  Response: {response.json()}")
            return False, response.json()
            
    except Exception as e:
        print(f"\n✗ SIGNUP ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, str(e)

def verify_user_in_database(tenant_slug, email):
    """Verify user was created in tenant database."""
    print("\n" + "="*80)
    print("PHASE 2: Verifying User in Tenant Database")
    print("="*80)
    
    try:
        tenant = Tenant.objects.get(slug=tenant_slug)
        print(f"\n✓ Found tenant: {tenant.name} ({tenant.slug})")
        print(f"  Database: {tenant.db_name}")
        
        # Check tables in tenant database
        if not check_tenant_tables(tenant.db_name):
            print("\n✗ CRITICAL: Missing tables in tenant database!")
            return False
        
        # Check if user exists using tenant connection
        from django.db import connections
        from tenancy.utils import register_tenant_connection
        
        alias = tenant.get_database_alias()
        if alias not in connections:
            register_tenant_connection(tenant)
        
        # Query user in tenant database
        with connections[alias].cursor() as cursor:
            cursor.execute(
                "SELECT id, email, tenant_id FROM shop_users_shopuser WHERE email = %s",
                [email]
            )
            user = cursor.fetchone()
        
        if user:
            print(f"\n✓ User found in tenant database!")
            print(f"  ID: {user[0]}")
            print(f"  Email: {user[1]}")
            print(f"  Tenant ID: {user[2]}")
            return True
        else:
            print(f"\n✗ User not found in tenant database!")
            return False
            
    except Tenant.DoesNotExist:
        print(f"\n✗ Tenant not found: {tenant_slug}")
        return False
    except Exception as e:
        print(f"\n✗ Database verification error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run tests
try:
    success, response_data = test_signup_api()
    
    if success:
        tenant_slug = response_data.get('tenant', {}).get('slug')
        user_email = response_data.get('user', {}).get('email')
        
        if tenant_slug and user_email:
            verify_success = verify_user_in_database(tenant_slug, user_email)
            
            print("\n" + "="*80)
            print("FINAL RESULT")
            print("="*80)
            if verify_success:
                print("""
✓ ✓ ✓ SIGNUP FLOW COMPLETE SUCCESS ✓ ✓ ✓

  1. Tenant created successfully
  2. Database created and migrations executed
  3. All required tables created
  4. User created in tenant database
  5. No 'relation does not exist' errors
                
The original signup error has been RESOLVED!
                """)
            else:
                print("""
✗ Signup API succeeded but database verification failed.
  Check tenant database for issues.
                """)
    else:
        print("\n" + "="*80)
        print("FINAL RESULT")
        print("="*80)
        print("""
✗ Signup API request failed.
  Check error details above.
        """)

except Exception as e:
    print(f"\n✗ Test execution error: {e}")
    import traceback
    traceback.print_exc()
