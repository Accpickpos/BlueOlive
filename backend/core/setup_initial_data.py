# setup_initial_data.py
"""
Quick setup script to create initial tenant and admin user.
Run this after migrations: python setup_initial_data.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from django.db import transaction
from tenancy.models import Tenant, Shop
from shop_users.models import ShopUser
from tenancy.utils import create_tenant_database_postgres, register_tenant_connection


def setup():
    print("=" * 60)
    print("INITIAL SETUP - Create Tenant and Admin User")
    print("=" * 60)
    
    # Check if tenant exists
    if Tenant.objects.exists():
        print("\n⚠️  Tenants already exist:")
        for tenant in Tenant.objects.all():
            print(f"   - {tenant.name} ({tenant.slug})")
        print("\nSkipping tenant creation...")
        return
    
    # Create tenant
    print("\n--- Create Tenant ---")
    tenant_name = os.environ.get('TENANT_NAME', 'Test Company')
    print(f"Tenant name: {tenant_name}")

    from django.utils.text import slugify
    slug = slugify(tenant_name)
    subdomain = slug
    db_name = f"{slug}_db"

    db_password = os.environ.get('DB_PASSWORD', 'postgres')
    print(f"DB password: {db_password}")
    
    print(f"\nCreating tenant: {tenant_name}")
    print(f"  Slug: {slug}")
    print(f"  Database: {db_name}")
    
    try:
        tenant = Tenant.objects.create(
            name=tenant_name,
            slug=slug,
            subdomain=subdomain,
            db_name=db_name,
            db_user='postgres',
            db_password=db_password,
            db_host='localhost',
            db_port=5432,
        )
        print(f"Tenant created: {tenant.name}")

    except Exception as e:
        print(f"Error creating tenant: {str(e)}")
        return
    
    # Wait for signals to complete
    import time
    print("\nWaiting for database setup...")
    time.sleep(2)
    
    # Register connection
    try:
        register_tenant_connection(tenant)
        print(f"✓ Database connection registered")
    except Exception as e:
        print(f"⚠️  Connection registration issue: {str(e)}")
    
    # Check if shop was created by signal
    shops = Shop.objects.filter(tenant=tenant)
    if not shops.exists():
        print("\n⚠️  No shop was created by signal, creating manually...")
        try:
            shop = Shop.objects.create(
                tenant=tenant,
                name='Main Office',
                schema_name=f'{slug}_main',
                subdomain='main',
                is_head_office=True,
            )
            print(f"✓ Shop created: {shop.name}")
            time.sleep(2)  # Wait for shop signals
        except Exception as e:
            print(f"✗ Error creating shop: {str(e)}")
            return
    else:
        shop = shops.first()
        print(f"✓ Shop already exists: {shop.name}")
    
    # Create admin user
    print("\n--- Create Admin User ---")
    username = os.environ.get('ADMIN_USERNAME', 'admin')
    email = os.environ.get('ADMIN_EMAIL', 'admin@test.com')
    password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    print(f"Username: {username}")
    print(f"Email: {email}")
    print(f"Password: {password}")
    
    try:
        # Create superuser in default DB (superusers are tenant-independent)
        user = ShopUser.objects.using('default').create(
            username=username,
            email=email,
            password=make_password(password),
            tenant_id=tenant.id,  # Still associate with tenant
            role='ADMIN',
            is_staff=True,
            is_superuser=True,
            is_active=True,
        )
        
        print(f"Admin user created successfully!")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        print(f"  Password: {password}")
        print(f"  Tenant: {tenant.name}")

        print("\n" + "=" * 60)
        print("SETUP COMPLETE!")
        print("=" * 60)
        print("\nYou can now:")
        print(f"1. Start the server: python manage.py runserver")
        print(f"2. Login at: http://{subdomain}.localhost:8000/api/auth/login/")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"\n3. Or use the admin panel: http://localhost:8000/admin/")

    except Exception as e:
        print(f"Error creating user: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    setup()