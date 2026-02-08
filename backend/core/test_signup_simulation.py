#!/usr/bin/env python
"""
Simulate the signup flow to identify where token_blacklist table creation is failing.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tenancy.models import Tenant
from tenancy.utils import create_tenant_database_postgres
from tenancy.shop_manager import migrate_tenant_database, verify_and_create_missing_tables
from tenancy.tenant_context import set_current_tenant
from shop_users.models import ShopUser
from django.db import connections
from django.conf import settings
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

print("\n" + "="*80)
print("SIMULATING SIGNUP FLOW TO DEBUG TOKEN TABLE CREATION")
print("="*80)

try:
    # 1. Create tenant
    print("\n[STEP 1] Creating tenant...")
    db_settings = settings.DATABASES.get('default', {})
    tenant_slug = f'testsignup{os.urandom(4).hex()}'
    tenant = Tenant.objects.create(
        name=f'TestSignup',
        slug=tenant_slug,
        subdomain=tenant_slug,
        db_name=f'tenant_{tenant_slug}',
        db_user=db_settings.get('USER', 'postgres'),
        db_password=db_settings.get('PASSWORD', ''),
        db_host=db_settings.get('HOST', 'localhost'),
        db_port=db_settings.get('PORT', 5432),
    )
    print(f"✓ Tenant created: {tenant.name} (ID: {tenant.id})")
    
    # 2. Create database
    print(f"\n[STEP 2] Creating database {tenant.db_name}...")
    superuser_conn_info = {
        'host': tenant.db_host,
        'port': tenant.db_port,
        'user': tenant.db_user,
        'password': tenant.db_password,
        'dbname': 'postgres'
    }
    create_tenant_database_postgres(tenant, superuser_conn_info)
    print(f"✓ Database created")
    
    # 3. Register connection
    print(f"\n[STEP 3] Registering database connection...")
    from tenancy.utils import register_tenant_connection
    register_tenant_connection(tenant)
    print(f"✓ Connection registered")
    
    # 4. Set current tenant
    print(f"\n[STEP 4] Setting current tenant...")
    set_current_tenant(tenant)
    print(f"✓ Current tenant set")
    
    # 5. Run migrations
    print(f"\n[STEP 5] Running migrations...")
    migrate_tenant_database(tenant)
    print(f"✓ Migrations completed")
    
    # 6. Verify tables exist
    print(f"\n[STEP 6] Verifying token_blacklist tables...")
    conn = connections[tenant.db_alias]
    with conn.cursor() as cur:
        cur.execute('SET search_path TO public')
        
        for table in ['token_blacklist_outstandingtoken', 'token_blacklist_blacklistedtoken']:
            cur.execute(f"""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table,))
            exists = cur.fetchone()[0]
            status = "✓ EXISTS" if exists else "✗ MISSING"
            print(f"  {table}: {status}")
    
    # 7. Create user
    print(f"\n[STEP 7] Creating user...")
    user = ShopUser.objects.create_user(
        username='testsignup',
        email='testsignup@example.com',
        password='TestPassword123!',
        tenant_id=tenant.id,
        using=tenant.db_alias
    )
    print(f"✓ User created: {user.username}")
    
    # 8. Create token
    print(f"\n[STEP 8] Creating refresh token...")
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    print(f"✓ Token created successfully!")
    
    print("\n" + "="*80)
    print("✓ SIGNUP SIMULATION SUCCESSFUL")
    print("="*80)
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)
finally:
    from tenancy.tenant_context import clear_current_tenant
    clear_current_tenant()
