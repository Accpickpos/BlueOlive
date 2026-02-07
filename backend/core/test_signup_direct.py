#!/usr/bin/env python
"""
Direct test of signup flow by calling the function directly.
This tests that all tables are created and user creation works.
"""
import os
import sys
import django
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.insert(0, '/c/Users/accpi/OneDrive/Documents/GitHub/BlueOlive/backend/core')
django.setup()

from django.contrib.auth import get_user_model
from tenancy.models import Tenant
from tenancy.shop_manager import migrate_tenant_database
from django.db import connections

ShopUser = get_user_model()

# Test data
timestamp = int(datetime.now().timestamp() * 1000) % 1000000
SHOP_NAME = f"DirectTest{timestamp}"
SHOP_SLUG = f"direct-test-{timestamp}"
TEST_EMAIL = f"direct{timestamp}@test.local"
TEST_PASSWORD = "TestPass123!@#"

print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                 TESTING SIGNUP FLOW (Direct Function Call)                   ║
╚══════════════════════════════════════════════════════════════════════════════╝

Test Configuration:
  Shop Name: {SHOP_NAME}
  Shop Slug: {SHOP_SLUG}
  Email: {TEST_EMAIL}
""")

def check_tenant_tables(db_name):
    """Verify all required tables exist in the tenant database."""
    try:
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
            
            print(f"\n  Tenant database tables ({len(tables)} total):")
            for table in sorted(tables):
                status = "✓" if table in critical_tables else " "
                print(f"    [{status}] {table}")
            
            missing = [t for t in critical_tables if t not in tables]
            if missing:
                print(f"\n  ✗ MISSING CRITICAL TABLES: {missing}")
                return False
            
            print(f"\n  ✓ All critical tables present!")
            return True
            
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        print(f"\n  ✗ Database connection error: {e}")
        return False

print("\n" + "="*80)
print("PHASE 1: Creating Tenant and Running Migrations")
print("="*80)

try:
    # Create tenant in main database
    tenant = Tenant.objects.create(
        name=SHOP_NAME,
        slug=SHOP_SLUG
    )
    print(f"\n✓ Tenant created in main database")
    print(f"  ID: {tenant.id}")
    print(f"  Name: {tenant.name}")
    print(f"  Slug: {tenant.slug}")
    print(f"  Database: {tenant.db_name}")
    
except Exception as e:
    print(f"\n✗ Failed to create tenant: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("PHASE 2: Running Migrations on Tenant Database")
print("="*80)

try:
    alias = tenant.get_database_alias()
    print(f"\nRunning migrations on {alias}...")
    
    migrate_tenant_database(tenant)
    
    print(f"✓ Migrations completed!")
    
except Exception as e:
    print(f"✗ Migration failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("PHASE 3: Verifying Tables in Tenant Database")
print("="*80)

if not check_tenant_tables(tenant.db_name):
    print("\n✗ CRITICAL: Missing tables in tenant database!")
    sys.exit(1)

print("\n" + "="*80)
print("PHASE 4: Creating User in Tenant Database")
print("="*80)

try:
    alias = tenant.get_database_alias()
    
    print(f"\nCreating user in {alias}...")
    print(f"  Email: {TEST_EMAIL}")
    
    # Create user in tenant database using the tenant's alias
    user = ShopUser.objects.using(alias).create_user(
        email=TEST_EMAIL,
        password=TEST_PASSWORD,
        tenant_id=tenant.id,
        is_active=True
    )
    
    print(f"\n✓ User created successfully!")
    print(f"  ID: {user.id}")
    print(f"  Email: {user.email}")
    print(f"  Tenant ID: {user.tenant_id}")
    print(f"  Active: {user.is_active}")
    
    # Verify user can be retrieved
    retrieved_user = ShopUser.objects.using(alias).get(id=user.id)
    print(f"\n✓ User verified in database!")
    print(f"  Retrieved: {retrieved_user.email}")
    
except Exception as e:
    print(f"\n✗ User creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*80)
print("FINAL RESULT")
print("="*80)
print("""
✓ ✓ ✓ SIGNUP FLOW COMPLETE SUCCESS ✓ ✓ ✓

  1. ✓ Tenant created successfully
  2. ✓ Database created and migrations executed
  3. ✓ All required tables created (including shop_users_shopuser)
  4. ✓ User created in tenant database
  5. ✓ No 'relation does not exist' errors
  
The original signup error has been RESOLVED!

The fix is working correctly:
  - Migrations run on tenant databases before user creation
  - Tables created with proper dependency ordering
  - Users can be created without table not found errors
""")
