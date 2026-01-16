# tenancy/shop_manager.py
from django.db import connections
from django.core.management import call_command
from django.apps import apps
from django.db.migrations.loader import MigrationLoader
from .tenant_context import set_current_tenant, clear_current_tenant


def fake_all_shared_migrations(database, shared_app_labels, tenant_app_labels):
    """
    Fake ALL migrations from shared and tenant apps in the migrations recorder.
    This prevents Django from trying to migrate them to the tenant schema.
    """
    from django.db.migrations.recorder import MigrationRecorder
    
    try:
        recorder = MigrationRecorder(connections[database])
        
        # Check if migration table exists
        if not recorder.has_table():
            return
        
        applied = set(recorder.applied_migrations())
        loader = MigrationLoader(None, ignore_no_migrations=True)
        
        # Get all migrations from shared and tenant apps, except auth, contenttypes, and shop_users which we migrate
        apps_to_fake = [app for app in shared_app_labels + tenant_app_labels if app not in ['auth', 'contenttypes', 'shop_users']]
        
        for app_label in apps_to_fake:
            if app_label not in loader.disk_migrations:
                continue
            
            app_migrations = loader.disk_migrations[app_label]
            
            # Fake all migrations for this shared/tenant app
            for migration_name in sorted(app_migrations.keys()):
                migration_key = (app_label, migration_name)
                
                if migration_key not in applied:
                    print(f"  Faking {app_label}.{migration_name}")
                    recorder.record_applied(app_label, migration_name)
    
    except Exception as e:
        print(f"  Warning: Could not fake shared migrations: {e}")
        import traceback
        traceback.print_exc()


def create_shop_schema(tenant, schema_name):
    """
    Create a schema in the tenant DB and run migrations that will create the shop tables in that schema.
    """
    from django.conf import settings
    alias = tenant.db_alias

    try:
        # Modify database connection settings to use this schema by default BEFORE creating schema
        original_options = settings.DATABASES[alias].get('OPTIONS', {}).copy()
        settings.DATABASES[alias]['OPTIONS'] = settings.DATABASES[alias].get('OPTIONS', {}).copy()
        settings.DATABASES[alias]['OPTIONS']['options'] = f'-c search_path="{schema_name}",public'

        # Force reload of connection settings
        connections.databases[alias] = settings.DATABASES[alias].copy()

        # Close any existing connections to ensure new settings take effect
        if hasattr(connections._connections, alias):
            getattr(connections._connections, alias).close()
            delattr(connections._connections, alias)

        conn = connections[alias]

        # Create the schema
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
            print(f"Schema '{schema_name}' created")

            # Create django_migrations table in this schema (search_path should be set by connection options)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS django_migrations (
                    id SERIAL PRIMARY KEY,
                    app VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    applied TIMESTAMP WITH TIME ZONE NOT NULL
                )
            """)
            print(f"Migration tracking table created in schema '{schema_name}'")

        # Set current tenant so router allows migration of shop apps
        set_current_tenant(tenant)

        try:
            # Get shared and tenant app labels
            shared_app_labels = [app.split('.')[-1] for app in settings.SHARED_APPS]
            tenant_app_labels = [app.split('.')[-1] for app in settings.TENANT_APPS]
            
            # Pre-fake all shared and tenant app migrations to prevent them from running
            print(f"\nPre-faking shared app migrations in {schema_name}...")
            fake_all_shared_migrations(alias, shared_app_labels, tenant_app_labels)
            
            # Run migrations with dependencies first
            # contenttypes, auth and shop_users must be migrated first
            migration_order = ['contenttypes', 'auth', 'shop_users'] + [
                app.split('.')[-1] for app in settings.SHOP_APPS if not app.endswith('shop_users')
            ]
            
            for app_label in migration_order:
                try:
                    app_config = apps.get_app_config(app_label)
                    print(f"Migrating {app_config.label} to schema {schema_name}...")

                    # Verify connection settings before migration
                    test_conn = connections[alias]
                    with test_conn.cursor() as cur:
                        cur.execute("SHOW search_path")
                        sp = cur.fetchone()
                        print(f"  search_path before migration: {sp[0]}")
                    
                    call_command("migrate", app_config.label, database=alias, verbosity=1)

                except LookupError:
                    print(f"Warning: App '{app_label}' not found in installed apps")

            # Verify tables were created
            with connections[alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{schema_name}"')  # Set to shop schema to check
                cur.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """, [schema_name])
                tables = cur.fetchall()

                if tables:
                    print(f"Tables created in schema '{schema_name}':")
                    for table in tables:
                        print(f"  - {table[0]}")
                else:
                    print(f"WARNING: No tables found in schema '{schema_name}'!")

                    # Debug: Check what tables exist in the database
                    cur.execute("SHOW search_path")
                    current_sp = cur.fetchone()
                    print(f"Current search_path: {current_sp[0]}")

                    cur.execute("""
                        SELECT schemaname, tablename
                        FROM pg_tables
                        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
                        ORDER BY schemaname, tablename
                    """)
                    all_tables = cur.fetchall()
                    print("All tables in database:")
                    for schema, table in all_tables:
                        print(f"  {schema}.{table}")

        finally:
            clear_current_tenant()

            # Close connection before restoring settings
            connections[alias].close()
            if hasattr(connections._connections, alias):
                delattr(connections._connections, alias)

            # Restore original database options
            if original_options:
                settings.DATABASES[alias]['OPTIONS'] = original_options
            else:
                settings.DATABASES[alias].pop('OPTIONS', None)

            # Force reload with original settings
            connections.databases[alias] = settings.DATABASES[alias].copy()

    except Exception as e:
        print(f"Error creating schema {schema_name}: {e}")
        import traceback
        traceback.print_exc()
        raise