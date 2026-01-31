# fix_tenant_complete.py
"""
Complete fix for broken tenant databases.
Resets migration state and re-runs everything properly.
Usage: python fix_tenant_complete.py <tenant_slug>
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management import call_command
from django.db import connections
from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection
from tenancy.tenant_context import set_current_tenant, clear_current_tenant


def fix_tenant(tenant_slug):
    """Complete fix for a broken tenant database"""
    
    print(f"\n{'='*70}")
    print(f"COMPLETE FIX FOR TENANT: {tenant_slug}")
    print(f"{'='*70}\n")
    
    try:
        tenant = Tenant.objects.get(slug=tenant_slug)
    except Tenant.DoesNotExist:
        print(f"❌ Tenant '{tenant_slug}' not found")
        return False
    
    print(f"Tenant: {tenant.name}")
    print(f"Database: {tenant.db_name}")
    print(f"Alias: {tenant.db_alias}\n")
    
    # Register connection
    register_tenant_connection(tenant)
    alias = tenant.db_alias
    set_current_tenant(tenant)
    
    try:
        conn = connections[alias]
        conn.close()
        conn.connect()
        conn.set_autocommit(True)
        
        with conn.cursor() as cur:
            cur.execute('SET search_path TO public')
        
        print("="*70)
        print("STEP 1: Checking current state...")
        print("="*70)
        
        # Check what tables exist
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                AND tablename NOT LIKE 'django_%'
                ORDER BY tablename
            """)
            existing_tables = [row[0] for row in cur.fetchall()]
            
            print(f"\nExisting tables: {len(existing_tables)}")
            for table in existing_tables:
                print(f"  - {table}")
        
        # Check django_migrations
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    SELECT app, name 
                    FROM django_migrations 
                    ORDER BY app, id
                """)
                migrations = cur.fetchall()
                print(f"\nRecorded migrations: {len(migrations)}")
                for app, name in migrations:
                    print(f"  - {app}.{name}")
            except:
                print("\n⚠️  django_migrations table doesn't exist yet")
        
        print(f"\n{'='*70}")
        print("STEP 2: Resetting migration state...")
        print("="*70)
        
        # Clear migration records that failed
        with conn.cursor() as cur:
            try:
                # Delete failed migration records
                cur.execute("""
                    DELETE FROM django_migrations 
                    WHERE app IN ('shop_users', 'admin')
                """)
                deleted = cur.rowcount
                print(f"✓ Cleared {deleted} problematic migration records")
            except Exception as e:
                print(f"⚠️  Could not clear migrations: {str(e)}")
        
        print(f"\n{'='*70}")
        print("STEP 3: Phase 1 - Migrate Django core apps...")
        print("="*70)
        
        # Migrate Django core first
        core_apps = ['contenttypes', 'auth', 'sessions']
        
        for app in core_apps:
            print(f"\nMigrating {app}...")
            try:
                call_command(
                    'migrate',
                    app,
                    database=alias,
                    verbosity=1,
                    interactive=False,
                )
                print(f"✓ {app} migrated successfully")
            except Exception as e:
                print(f"❌ {app} failed: {str(e)}")
                return False
        
        print(f"\n{'='*70}")
        print("STEP 4: Phase 2 - Migrate tenant apps...")
        print("="*70)
        
        # Now migrate shop_users
        print(f"\nMigrating shop_users...")
        try:
            call_command(
                'migrate',
                'shop_users',
                database=alias,
                verbosity=1,
                interactive=False,
            )
            print(f"✓ shop_users migrated successfully")
        except Exception as e:
            print(f"❌ shop_users failed: {str(e)}")
            return False
        
        # Migrate admin
        print(f"\nMigrating admin...")
        try:
            call_command(
                'migrate',
                'admin',
                database=alias,
                verbosity=1,
                interactive=False,
            )
            print(f"✓ admin migrated successfully")
        except Exception as e:
            print(f"⚠️  admin: {str(e)} (non-critical)")
        
        # Migrate token_blacklist
        print(f"\nMigrating token_blacklist...")
        try:
            call_command(
                'migrate',
                'token_blacklist',
                database=alias,
                verbosity=1,
                interactive=False,
            )
            print(f"✓ token_blacklist migrated successfully")
        except Exception as e:
            print(f"⚠️  token_blacklist: {str(e)} (non-critical)")
        
        print(f"\n{'='*70}")
        print("STEP 5: Verifying tables...")
        print("="*70)
        
        # Verify tables were created
        with conn.cursor() as cur:
            cur.execute("""
                SELECT tablename 
                FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """)
            tables = cur.fetchall()
            
            print(f"\n✓ Total tables in public schema: {len(tables)}")
            
            # Check for critical tables
            table_names = [t[0] for t in tables]
            critical_tables = [
                'auth_user',
                'auth_group',
                'auth_permission',
                'shop_users_shopuser',
            ]
            
            print("\nCritical tables:")
            for table in critical_tables:
                if table in table_names:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ❌ {table} MISSING!")
                    return False
        
        print(f"\n{'='*70}")
        print("STEP 6: Setting up shops...")
        print("="*70)
        
        # Get or create shops
        shops = Shop.objects.filter(tenant=tenant)
        
        if not shops.exists():
            print("\n⚠️  No shops found. Creating default shop...")
            from django.utils.text import slugify
            shop = Shop.objects.create(
                tenant=tenant,
                name='Main Office',
                schema_name=f'{tenant.slug}_main',
                subdomain='main',
                is_head_office=True,
            )
            shops = [shop]
        
        # Migrate shop schemas
        from django.conf import settings
        shop_apps = getattr(settings, 'SHOP_APP_LABELS', [])
        
        for shop in shops:
            print(f"\nShop: {shop.name} (schema: {shop.schema_name})")
            
            # Create schema
            with conn.cursor() as cur:
                cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{shop.schema_name}"')
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')
            
            print(f"✓ Schema ready")
            
            # Migrate shop apps
            if shop_apps:
                for app in shop_apps:
                    print(f"  Migrating {app}...")
                    try:
                        call_command(
                            'migrate',
                            app,
                            database=alias,
                            verbosity=0,
                            interactive=False,
                        )
                        print(f"  ✓ {app}")
                    except Exception as e:
                        print(f"  ⚠️  {app}: {str(e)}")
        
        print(f"\n{'='*70}")
        print("✅ TENANT DATABASE FIXED SUCCESSFULLY!")
        print(f"{'='*70}\n")
        
        print("Next steps:")
        print("1. Create admin user (see below)")
        print("2. Test login via API")
        print("\nCreate admin user:")
        print("-" * 70)
        print(f"python manage.py shell\n")
        print(f"from tenancy.models import Tenant")
        print(f"from shop_users.models import ShopUser")
        print(f"from django.contrib.auth.hashers import make_password")
        print(f"from tenancy.utils import register_tenant_connection")
        print(f"")
        print(f"tenant = Tenant.objects.get(slug='{tenant.slug}')")
        print(f"register_tenant_connection(tenant)")
        print(f"")
        print(f"user = ShopUser.objects.using(tenant.db_alias).create(")
        print(f"    username='admin',")
        print(f"    email='admin@{tenant.slug}.com',")
        print(f"    password=make_password('admin123'),")
        print(f"    tenant_id=tenant.id,")
        print(f"    role='ADMIN',")
        print(f"    is_staff=True,")
        print(f"    is_superuser=True,")
        print(f"    is_active=True,")
        print(f")")
        print(f"")
        print(f"print(f'✓ User created: {{user.username}}')")
        print("-" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        clear_current_tenant()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python fix_tenant_complete.py <tenant_slug>")
        print("\nAvailable tenants:")
        from tenancy.models import Tenant
        for t in Tenant.objects.all():
            print(f"  - {t.slug} ({t.name})")
        sys.exit(1)
    
    tenant_slug = sys.argv[1]
    success = fix_tenant(tenant_slug)
    sys.exit(0 if success else 1)