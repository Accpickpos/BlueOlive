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
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help='Silently skip if tenant already exists (default: True, safe for Docker)'
        )

    def handle(self, *args, **options):
        name = options['name']
        slug = options['slug']
        db_name = options['db_name']
        create_shop = options['create_shop']
        skip_existing = options['skip_existing']

        self.stdout.write("\n" + "="*80)
        self.stdout.write("CREATE DEVELOPMENT TENANT")
        self.stdout.write("="*80 + "\n")

        # Check if tenant already exists
        if Tenant.objects.filter(slug=slug).exists():
            tenant = Tenant.objects.get(slug=slug)

            self.stdout.write(self.style.WARNING(
                f"Tenant with slug '{slug}' already exists, skipping creation."
            ))
            self.stdout.write(f"\nExisting tenant:")
            self.stdout.write(f"  Name: {tenant.name}")
            self.stdout.write(f"  Slug: {tenant.slug}")
            self.stdout.write(f"  Database: {tenant.db_name}")

            # Verify database exists and is accessible
            self.stdout.write("\nVerifying database exists...")
            import psycopg2
            from psycopg2 import OperationalError
            
            # Use default DB settings for verification (handles Docker vs local)
            default_db = settings.DATABASES['default']
            db_host = default_db['HOST']
            db_port = default_db['PORT']
            
            try:
                conn = psycopg2.connect(
                    host=db_host,
                    port=db_port,
                    user=default_db['USER'],
                    password=default_db['PASSWORD'],
                    dbname=tenant.db_name
                )
                conn.close()
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] Database '{tenant.db_name}' exists and is accessible."
                ))
            except OperationalError as e:
                self.stdout.write(self.style.ERROR(
                    f"[FAIL] Database '{tenant.db_name}' does not exist or is not accessible!"
                ))
                self.stdout.write(f"   Error: {str(e)}")
                self.stdout.write("   Creating database and setting up tenant...")
                
                # Create database
                from tenancy.utils import provision_tenant
                superuser_conn_info = {
                    'host': db_host,
                    'port': db_port,
                    'dbname': 'postgres',
                    'user': default_db['USER'],
                    'password': default_db['PASSWORD'],
                }
                try:
                    provision_tenant(tenant, superuser_conn_info)
                    self.stdout.write(self.style.SUCCESS(
                        f"[OK] Database '{tenant.db_name}' created and provisioned!"
                    ))
                except Exception as db_error:
                    self.stdout.write(self.style.ERROR(
                        f"Failed to create database: {str(db_error)}"
                    ))
                    return

            if not skip_existing:
                # Only prompt if explicitly running interactively
                try:
                    response = input("\nUse this existing tenant? [y/N]: ")
                    if response.lower() != 'y':
                        self.stdout.write(self.style.ERROR("Cancelled."))
                        return
                except EOFError:
                    # No TTY (e.g. Docker) — just continue
                    self.stdout.write("No TTY detected, continuing with existing tenant.")

        else:
            # Create tenant
            self.stdout.write("Creating tenant...")

            try:
                db_password = getattr(settings, 'DATABASES', {}).get('default', {}).get('PASSWORD', 'postgres')

                tenant = Tenant.objects.create(
                    name=name,
                    slug=slug,
                    db_name=db_name,
                    db_host=settings.DATABASES['default']['HOST'],
                    db_port=settings.DATABASES['default']['PORT'],
                    db_user=settings.DATABASES['default']['USER'],
                    db_password=db_password,
                    is_active=True
                )

                self.stdout.write(self.style.SUCCESS(
                    f"[OK] Tenant created: {tenant.name}"
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
            shop_code = "MS001"
            schema_name = "shop_main"

            if Shop.objects.filter(tenant=tenant, code=shop_code).exists():
                existing_shop = Shop.objects.filter(tenant=tenant, code=shop_code).first()
                self.stdout.write(self.style.WARNING(
                    f"Shop '{shop_code}' already exists for this tenant."
                ))
                # Check if schema needs to be created/migrated
                schema_name = existing_shop.schema_name
                from tenancy.shop_manager import create_shop_schema
                try:
                    self.stdout.write(f"Ensuring shop schema '{schema_name}' exists and is migrated...")
                    create_shop_schema(tenant, schema_name)
                    self.stdout.write(self.style.SUCCESS(
                        f"[OK] Shop schema verified and migrated"
                    ))
                except Exception as schema_error:
                    self.stdout.write(self.style.WARNING(
                        f"Schema may already exist or migration failed: {str(schema_error)}"
                    ))
            else:
                try:
                    shop = Shop.objects.create(
                        tenant=tenant,
                        name=shop_name,
                        code=shop_code,
                        schema_name=schema_name,
                        is_active=True,
                        is_head_office=True
                    )

                    self.stdout.write(self.style.SUCCESS(
                        f"[OK] Shop created: {shop.name}"
                    ))

                    # CRITICAL: Create the shop schema and migrate shop apps
                    from tenancy.shop_manager import create_shop_schema
                    self.stdout.write(f"Creating shop schema '{schema_name}' and migrating shop apps...")
                    create_shop_schema(tenant, schema_name)
                    self.stdout.write(self.style.SUCCESS(
                        f"[OK] Shop schema created and migrated"
                    ))

                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"Failed to create shop: {str(e)}"
                    ))

        # Create admin user for the tenant (required for login)
        self.stdout.write("\nCreating admin user...")
        from django.contrib.auth.hashers import make_password
        from shop_users.models import ShopUser
        from tenancy.utils import register_tenant_connection
        from tenancy.shop_manager import migrate_tenant_database
        
        # Ensure database exists and is accessible before proceeding
        import psycopg2
        from psycopg2 import OperationalError
        
        default_db = settings.DATABASES['default']
        db_host = default_db['HOST']
        db_port = default_db['PORT']
        
        try:
            conn = psycopg2.connect(
                host=db_host,
                port=db_port,
                user=default_db['USER'],
                password=default_db['PASSWORD'],
                dbname=tenant.db_name
            )
            conn.close()
        except OperationalError:
            self.stdout.write(self.style.WARNING(
                f"Database '{tenant.db_name}' not accessible. Creating and provisioning..."
            ))
            from tenancy.utils import provision_tenant
            superuser_conn_info = {
                'host': db_host,
                'port': db_port,
                'dbname': 'postgres',
                'user': default_db['USER'],
                'password': default_db['PASSWORD'],
            }
            try:
                provision_tenant(tenant, superuser_conn_info)
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"Failed to provision tenant database: {str(e)}"
                ))
                return
        
        try:
            # Register tenant connection
            register_tenant_connection(tenant)
            
            # Run migrations to ensure shop_users table exists
            migrate_tenant_database(tenant)
            
            # Check if user already exists
            admin_username = f"admin@{slug}"
            if ShopUser.objects.using(tenant.db_alias).filter(username=admin_username).exists():
                self.stdout.write(self.style.WARNING(
                    f"Admin user '{admin_username}' already exists, skipping."
                ))
            else:
                # Create admin user
                admin_user = ShopUser.objects.using(tenant.db_alias).create(
                    username=admin_username,
                    email=admin_username,
                    first_name='Admin',
                    password=make_password('admin123'),  # Default password - CHANGE IN PRODUCTION
                    is_staff=True,
                    is_superuser=False,
                    role='ADMIN',
                    tenant_id=tenant.id,
                    is_active=True,
                )
                self.stdout.write(self.style.SUCCESS(
                    f"[OK] Admin user created: {admin_username}"
                ))
                self.stdout.write(self.style.WARNING(
                    f"  Default password: admin123 (CHANGE IN PRODUCTION!)"
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f"Failed to create admin user: {str(e)}"
            ))
            import traceback
            traceback.print_exc()

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