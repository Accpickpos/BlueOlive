# tenancy/management/commands/create_dev_tenant.py
"""
Create a development tenant for local testing.

Usage:
    python manage.py create_dev_tenant
    python manage.py create_dev_tenant --name "My Company" --slug mycompany
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from tenancy.models import Tenant, Shop
import sys


class Command(BaseCommand):
    help = 'Create a development tenant for localhost testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            type=str,
            default='Development Tenant',
            help='Tenant name'
        )
        parser.add_argument(
            '--slug',
            type=str,
            default='dev',
            help='Tenant slug (must match DEFAULT_TENANT_SLUG in settings)'
        )
        parser.add_argument(
            '--db-name',
            type=str,
            default='tenant_dev',
            help='Database name'
        )
        parser.add_argument(
            '--create-shop',
            action='store_true',
            help='Also create a default shop'
        )

    def handle(self, *args, **options):
        name = options['name']
        slug = options['slug']
        db_name = options['db_name']
        create_shop = options['create_shop']
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("CREATE DEVELOPMENT TENANT")
        self.stdout.write("="*80 + "\n")
        
        # Check if tenant already exists
        if Tenant.objects.filter(slug=slug).exists():
            self.stdout.write(self.style.WARNING(
                f"Tenant with slug '{slug}' already exists!"
            ))
            
            tenant = Tenant.objects.get(slug=slug)
            self.stdout.write(f"\nExisting tenant:")
            self.stdout.write(f"  Name: {tenant.name}")
            self.stdout.write(f"  Slug: {tenant.slug}")
            self.stdout.write(f"  Database: {tenant.db_name}")
            
            # Ask if they want to continue
            response = input("\nUse this existing tenant? [y/N]: ")
            if response.lower() != 'y':
                self.stdout.write(self.style.ERROR("Cancelled."))
                return
        else:
            # Create tenant
            self.stdout.write("Creating tenant...")
            
            try:
                from django.conf import settings
                db_password = getattr(settings, 'DATABASES', {}).get('default', {}).get('PASSWORD', 'postgres')

                tenant = Tenant.objects.create(
                    name=name,
                    slug=slug,
                    db_name=db_name,
                    db_host='localhost',
                    db_port=5432,
                    db_user='postgres',  # Change if needed
                    db_password=db_password,  # Use password from settings
                    # db_alias is auto-generated from slug as a property
                    is_active=True
                )
                
                self.stdout.write(self.style.SUCCESS(
                    f"✓ Tenant created: {tenant.name}"
                ))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Failed to create tenant: {str(e)}"
                ))
                return
        
        # Update settings check
        default_slug = getattr(settings, 'DEFAULT_TENANT_SLUG', None)
        
        if default_slug != slug:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  DEFAULT_TENANT_SLUG in settings is '{default_slug}'"
            ))
            self.stdout.write(self.style.WARNING(
                f"   Update settings.py to: DEFAULT_TENANT_SLUG = '{slug}'"
            ))
        
        # Create shop if requested
        if create_shop:
            self.stdout.write("\nCreating default shop...")
            
            shop_name = f"{name} - Main Shop"
            shop_slug = "main"
            schema_name = "shop_main"
            
            if Shop.objects.filter(tenant=tenant, slug=shop_slug).exists():
                self.stdout.write(self.style.WARNING(
                    f"Shop '{shop_slug}' already exists for this tenant"
                ))
            else:
                try:
                    shop = Shop.objects.create(
                        tenant=tenant,
                        name=shop_name,
                        slug=shop_slug,
                        schema_name=schema_name,
                        is_active=True
                    )
                    
                    self.stdout.write(self.style.SUCCESS(
                        f"✓ Shop created: {shop.name}"
                    ))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Failed to create shop: {str(e)}"
                    ))
        
        # Print access instructions
        self.stdout.write("\n" + "="*80)
        self.stdout.write("ACCESS INSTRUCTIONS")
        self.stdout.write("="*80 + "\n")
        
        self.stdout.write("You can now access your app at:")
        self.stdout.write(f"  • http://127.0.0.1:8000/")
        self.stdout.write(f"  • http://localhost:8000/")
        
        if create_shop:
            self.stdout.write(f"  • http://127.0.0.1:8000/?shop=main")
        
        self.stdout.write("\nOr with query parameters:")
        self.stdout.write(f"  • http://127.0.0.1:8000/?tenant={slug}")
        
        if create_shop:
            self.stdout.write(f"  • http://127.0.0.1:8000/?tenant={slug}&shop=main")
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("NEXT STEPS")
        self.stdout.write("="*80 + "\n")
        
        self.stdout.write("1. Ensure settings.py has:")
        self.stdout.write(f"   DEFAULT_TENANT_SLUG = '{slug}'")
        
        if create_shop:
            self.stdout.write("   USE_DEFAULT_SHOP = True")
        
        self.stdout.write("\n2. Run the development server:")
        self.stdout.write("   python manage.py runserver")
        
        self.stdout.write("\n3. Access the admin:")
        self.stdout.write("   http://127.0.0.1:8000/admin/")
        
        self.stdout.write(self.style.SUCCESS("\n✅ Development tenant ready!"))