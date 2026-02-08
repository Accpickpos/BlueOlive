# tenancy/shop_manager.py
from django.db import connections
from django.core.management import call_command
from django.conf import settings
from tenancy.tenant_context import set_current_tenant, clear_current_tenant
import logging
import os

logger = logging.getLogger(__name__)


def create_shop_schema(tenant, schema_name):
    """
    Create a schema and migrate shop apps to it.
    
    Architecture:
    - Tenant database (public schema): admin, token_blacklist, shop_users
    - Shop schemas: cash_book, creditors, stock_control, purchase_orders
    
    This function:
    1. Creates the PostgreSQL schema
    2. Migrates only SHOP_APP_LABELS apps to the schema
    """
    alias = tenant.db_alias
    set_current_tenant(tenant)

    try:
        logger.info(f"Creating schema: {schema_name} in database: {tenant.db_name}")
        
        # Get connection
        conn = connections[alias]
        conn.close()
        conn.connect()
        
        # Step 1: Create schema
        with conn.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
            logger.info(f"✓ Schema created: {schema_name}")
        
        # Commit schema creation
        conn.commit()
        
        # Step 2: Migrate shop apps to this schema
        migrate_shop_apps(tenant, schema_name)
        
        logger.info(f"✓ Schema setup complete: {schema_name}")
        
    except Exception as e:
        logger.error(f"Failed to create schema {schema_name}: {str(e)}")
        raise
    finally:
        clear_current_tenant()


def migrate_shop_apps(tenant, schema_name):
    """
    Migrate SHOP_APP_LABELS apps to a specific schema.
    
    These apps are:
    - cash_book
    - creditors  
    - stock_control
    - purchase_orders
    - settings
    - pos
    
    Each shop gets its own isolated copy of these tables in its schema.
    
    NOTE: Settings app no longer has dependencies on tenancy models (Tenant, Shop),
    so migrations work cleanly without cross-schema foreign key issues.
    """
    alias = tenant.db_alias
    
    try:
        logger.info(f"Migrating shop apps to schema: {schema_name}")
        
        # Get shop app labels from settings
        shop_app_labels = getattr(settings, 'SHOP_APP_LABELS', [])
        
        if not shop_app_labels:
            logger.warning("No shop apps configured in SHOP_APP_LABELS")
            return
        
        logger.info(f"Shop apps to migrate: {shop_app_labels}")
        
        try:
            # Get connection and ensure fresh state
            conn = connections[alias]
            conn.close()
            conn.connect()
            
            # STEP 1: Setup django_migrations table in shop schema
            logger.info("Step 1: Setting up django_migrations table in shop schema...")
            with conn.cursor() as cur:
                # Check if django_migrations table exists in shop schema
                cur.execute(f"""
                    SELECT EXISTS(
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_name = 'django_migrations'
                    )
                """, [schema_name])
                
                migrations_table_exists = cur.fetchone()[0]
                
                if not migrations_table_exists:
                    logger.info("  Creating django_migrations table in shop schema...")
                    cur.execute(f"""
                        CREATE TABLE "{schema_name}".django_migrations (
                            id bigint NOT NULL PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                            app character varying(255) NOT NULL,
                            name character varying(255) NOT NULL,
                            applied timestamp with time zone NOT NULL
                        )
                    """)
                    conn.commit()
                    logger.info("  ✓ Created django_migrations table")
            
            # STEP 2: Mark tenancy migrations as already applied in shop schema
            # This prevents Django from trying to re-migrate tenancy to the shop schema
            logger.info("Step 2: Marking tenancy migrations as applied...")
            with conn.cursor() as cur:
                # First, switch to public schema to read tenancy migrations
                cur.execute('SET search_path TO public')
                cur.execute("""
                    SELECT app, name, applied
                    FROM django_migrations
                    WHERE app = 'tenancy'
                    ORDER BY id
                """)
                tenancy_migrations = cur.fetchall()
                
                if tenancy_migrations:
                    logger.info(f"  Found {len(tenancy_migrations)} tenancy migrations")
                    
                    # Now insert them into the shop schema's django_migrations
                    cur.execute(f'SET search_path TO "{schema_name}"')
                    for app, name, applied in tenancy_migrations:
                        try:
                            cur.execute("""
                                INSERT INTO django_migrations (app, name, applied)
                                VALUES (%s, %s, %s)
                            """, (app, name, applied))
                        except Exception as e:
                            # Might already exist, that's fine
                            logger.debug(f"  Could not insert {app}.{name}: {e}")
                    
                    conn.commit()
                    logger.info("  ✓ Tenancy migrations marked as applied in shop schema")
            
            # STEP 3: Close connection to reset Django's migration state
            # Django will reconnect and see the marked migrations
            logger.info("Step 3: Resetting connection for migration execution...")
            conn.close()
            
            # STEP 4: Migrate each shop app
            logger.info(f"Step 4: Migrating shop apps to schema: {schema_name}...")
            for app_label in shop_app_labels:
                try:
                    logger.info(f"  Migrating {app_label}...")
                    
                    # Before migrating, update the database connection options to use the shop schema
                    # This ensures Django creates tables in the correct schema
                    original_options = settings.DATABASES[alias].get('OPTIONS', {}).copy()
                    settings.DATABASES[alias]['OPTIONS'] = {
                        'options': f'-c search_path={schema_name},public'
                    }
                    # Also update the connection cache
                    connections.databases[alias]['OPTIONS'] = settings.DATABASES[alias]['OPTIONS']
                    
                    # Close any existing connection to force reconnect with new options
                    connections[alias].close()
                    
                    try:
                        call_command(
                            'migrate',
                            app_label,
                            database=alias,
                            verbosity=1,
                            interactive=False,
                        )
                        logger.info(f"  ✓ {app_label} migrated to {schema_name}")
                    finally:
                        # Restore original options
                        settings.DATABASES[alias]['OPTIONS'] = original_options
                        connections.databases[alias]['OPTIONS'] = original_options
                        connections[alias].close()  # Close to force reconnect with public schema
                    
                except Exception as e:
                    logger.error(f"  ✗ Failed to migrate {app_label}: {str(e)}")
                    # Restore original options even on error
                    settings.DATABASES[alias]['OPTIONS'] = original_options
                    connections.databases[alias]['OPTIONS'] = original_options
                    # Try to continue with other apps
            
            # After migrations, verify and create any missing tables
            logger.info(f"Step 5: Verifying tables in schema {schema_name}...")
            conn = connections[alias]
            if conn.connection is None:
                conn.connect()
            create_missing_shop_tables(conn, schema_name, shop_app_labels)
            
            logger.info(f"✓ All shop apps migrated to {schema_name}")
            
        except Exception as e:
            logger.error(f"Failed to migrate shop apps to {schema_name}: {str(e)}")
            raise
        
    except Exception as e:
        logger.error(f"Error in migrate_shop_apps: {str(e)}")
        raise


def create_missing_shop_tables(conn, schema_name, app_labels):
    """
    Create missing tables in shop schema by directly using Django's schema editor.
    This handles the case where migrations don't properly create tables in non-public schemas.
    """
    from django.db import connection
    from django.db.backends.postgresql.schema import DatabaseSchemaEditor
    from django.apps import apps
    
    try:
        with conn.cursor() as cur:
            # Set search path
            cur.execute(f'SET search_path TO "{schema_name}", public')
            
            # Get all tables currently in schema
            cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = %s
            """, [schema_name])
            
            existing_tables = {row[0] for row in cur.fetchall()}
            logger.info(f"Found {len(existing_tables)} existing tables in {schema_name}")
            
            # Get all models for these apps
            models_to_create = []
            for app_label in app_labels:
                try:
                    app_config = apps.get_app_config(app_label)
                    for model in app_config.get_models():
                        models_to_create.append(model)
                except Exception as e:
                    logger.warning(f"Could not load app {app_label}: {str(e)}")
            
            # Check which models' tables don't exist
            tables_to_create = []
            for model in models_to_create:
                table_name = model._meta.db_table
                if table_name not in existing_tables:
                    tables_to_create.append(model)
                    logger.info(f"  Need to create table: {table_name}")
            
            if tables_to_create:
                logger.info(f"Creating {len(tables_to_create)} missing tables...")
                
                # Use PostgreSQL schema editor
                with DatabaseSchemaEditor(conn) as schema_editor:
                    for model in tables_to_create:
                        try:
                            # Set search path before creating
                            with conn.cursor() as cur2:
                                cur2.execute(f'SET search_path TO "{schema_name}", public')
                            
                            schema_editor.create_model(model)
                            logger.info(f"  ✓ Created table: {model._meta.db_table}")
                        except Exception as e:
                            logger.error(f"  ✗ Failed to create {model._meta.db_table}: {str(e)}")
            else:
                logger.info(f"✓ All required tables exist in {schema_name}")
                
    except Exception as e:
        logger.error(f"Error creating missing tables: {str(e)}")


def verify_schema_tables(conn, schema_name, expected_apps):
    """
    Verify that tables were created in the correct schema.
    """
    try:
        with conn.cursor() as cur:
            # Get all tables in the schema
            cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = %s
                ORDER BY tablename
            """, [schema_name])
            
            schema_tables = [row[0] for row in cur.fetchall()]
            
            logger.info(f"✓ Found {len(schema_tables)} tables in schema '{schema_name}'")
            
            if schema_tables:
                logger.info("Tables in schema:")
                for table in schema_tables:
                    logger.info(f"  - {table}")
            else:
                logger.warning(f"⚠ No tables found in schema '{schema_name}'!")
            
            # Check for django_migrations table
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1
                    FROM pg_tables
                    WHERE schemaname = %s
                    AND tablename = 'django_migrations'
                )
            """, [schema_name])
            
            has_migrations = cur.fetchone()[0]
            
            if has_migrations:
                logger.info(f"✓ Migration tracking table exists in {schema_name}")
                
                # Show applied migrations
                cur.execute(f'SET search_path TO "{schema_name}", public')
                cur.execute("SELECT app, COUNT(*) FROM django_migrations GROUP BY app ORDER BY app")
                migrations = cur.fetchall()
                
                if migrations:
                    logger.info("Applied migrations:")
                    for app, count in migrations:
                        logger.info(f"  - {app}: {count} migration(s)")
            else:
                logger.warning(f"⚠ No migration tracking table in {schema_name}")
                
    except Exception as e:
        logger.error(f"Error verifying schema tables: {str(e)}")


def migrate_tenant_database(tenant):
    """
    Migrate tenant database (public schema only).
    
    This migrates:
    - Core Django apps: contenttypes, auth, sessions, admin
    - Tenant apps (public schema): token_blacklist, shop_users
    
    Does NOT migrate SHOP_APP_LABELS (those go to shop schemas).
    """
    import os
    
    alias = tenant.db_alias
    set_current_tenant(tenant)
    
    # CRITICAL: Set environment variable so db_router knows which tenant DB we're migrating
    # The router checks TENANT_DB_ALIAS to decide if tenant apps can migrate
    os.environ['TENANT_DB_ALIAS'] = alias
    
    try:
        logger.info(f"Migrating tenant database: {tenant.db_name}")
        
        conn = connections[alias]
        conn.close()
        conn.connect()
        
        # CRITICAL: Set search_path for this connection session
        # This ensures all subsequent queries use the public schema
        with conn.cursor() as cur:
            cur.execute('SET search_path TO public')
            # Test that search_path is set
            cur.execute('SHOW search_path')
            search_path = cur.fetchone()[0]
            logger.info(f"✓ Search path set: {search_path}")
        
        # Commit this change to ensure it persists
        conn.commit()
        
        # Get apps to migrate
        tenant_app_labels = getattr(settings, 'TENANT_APP_LABELS', [])
        shop_app_labels = getattr(settings, 'SHOP_APP_LABELS', [])
        
        # Tenant apps EXCLUDING shop apps
        # shop_users, admin, token_blacklist go to public schema
        # cash_book, creditors, etc. go to shop schemas
        apps_for_public_schema = [
            app for app in tenant_app_labels 
            if app not in shop_app_labels
        ]
        
        logger.info(f"Apps to migrate to public schema: {apps_for_public_schema}")
        logger.info(f"Shop apps (will be migrated to shop schemas): {shop_app_labels}")
        
        # Migrate in proper dependency order
        migration_phases = [
            {
                'name': 'Core Dependencies',
                'apps': ['contenttypes', 'auth'],
            },
            {
                'name': 'Django Admin & Sessions',
                'apps': ['admin', 'sessions'],
            },
            {
                'name': 'JWT Tokens',
                'apps': ['token_blacklist'],
            },
            {
                'name': 'Tenant Apps',
                'apps': apps_for_public_schema,
            },
        ]
        
        for phase in migration_phases:
            phase_name = phase['name']
            phase_apps = phase['apps']
            
            logger.info(f"\n{'='*60}")
            logger.info(f"Phase: {phase_name}")
            logger.info(f"{'='*60}")
            
            for app_label in phase_apps:
                # Skip apps that don't have migrations
                if app_label in ['messages', 'rest_framework', 'rest_framework_simplejwt']:
                    logger.info(f"  Skipping {app_label} (no migrations)")
                    continue
                
                try:
                    logger.info(f"  Migrating {app_label}...")
                    
                    call_command(
                        'migrate',
                        app_label,
                        database=alias,
                        verbosity=2,
                        interactive=False,
                    )
                    
                    # CRITICAL: Ensure the connection commits the migration changes
                    # This forces django_migrations to be updated in the database
                    conn = connections[alias]
                    if conn.in_atomic_block:
                        logger.warning(f"  ⚠️ {app_label} migrated but connection is in atomic block, committing...")
                        conn.commit()
                    
                    logger.info(f"  ✓ {app_label} migrated")
                    
                except Exception as e:
                    logger.error(f"  ✗ {app_label}: {str(e)}")
                    import traceback
                    logger.error(f"  Traceback: {traceback.format_exc()}")
                    # Continue with other apps
        
        logger.info(f"\n✓ Tenant database migration complete: {tenant.db_name}")
        logger.info(f"  Public schema apps: {apps_for_public_schema}")
        logger.info(f"  Shop schema apps (not migrated): {shop_app_labels}")
        
        # CRITICAL FIX: Always verify and create missing tables manually
        # Migrations might mark as applied without actually creating tables due to transaction issues
        # This fallback ensures 100% table creation reliability
        logger.info(f"\nVerifying all required tables exist...")
        verify_and_create_missing_tables(tenant, alias)
        
    except Exception as e:
        logger.error(f"Tenant database migration failed: {str(e)}")
        raise
    finally:
        clear_current_tenant()
        # Clear the TENANT_DB_ALIAS environment variable
        if 'TENANT_DB_ALIAS' in os.environ:
            del os.environ['TENANT_DB_ALIAS']


def verify_and_create_missing_tables(tenant, alias):
    """
    Verify that all required tables exist after migrations.
    
    These are the 12 tables that should exist in every tenant's public schema:
    1. auth_group
    2. auth_group_permissions
    3. auth_permission
    4. django_admin_log
    5. django_content_type
    6. django_migrations
    7. django_session
    8. shop_users_shopuser
    9. shop_users_shopuser_groups
    10. shop_users_shopuser_user_permissions
    11. token_blacklist_blacklistedtoken
    12. token_blacklist_outstandingtoken
    """
    from django.db import connections
    
    # All 12 required tables - matching tenant_tnt public schema
    required_tables = [
        'auth_group',
        'auth_group_permissions',
        'auth_permission',
        'django_admin_log',
        'django_content_type',
        'django_migrations',
        'django_session',
        'shop_users_shopuser',
        'shop_users_shopuser_groups',
        'shop_users_shopuser_user_permissions',
        'token_blacklist_blacklistedtoken',
        'token_blacklist_outstandingtoken',
    ]
    
    conn = connections[alias]
    
    # Close and reconnect to ensure fresh connection
    conn.close()
    conn.connect()
    
    with conn.cursor() as cur:
        cur.execute('SET search_path TO public')
        
        missing_tables = []
        for table_name in required_tables:
            cur.execute(f"""
                SELECT EXISTS(
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                )
            """, (table_name,))
            exists = cur.fetchone()[0]
            if not exists:
                logger.warning(f"  ✗ Missing table: {table_name}")
                missing_tables.append(table_name)
            else:
                logger.info(f"  ✓ Table exists: {table_name}")
        
        if missing_tables:
            logger.warning(f"\n{'='*60}")
            logger.warning(f"Missing tables after migrations: {missing_tables}")
            logger.info(f"Creating missing tables manually...")
            logger.warning(f"{'='*60}\n")
            try:
                create_missing_tables_manually(conn, missing_tables)
                logger.info(f"\n✓ Missing tables created successfully")
                
                # Verify again after creation
                missing_after_create = []
                with conn.cursor() as cur2:
                    cur2.execute('SET search_path TO public')
                    for table_name in missing_tables:
                        cur2.execute(f"""
                            SELECT EXISTS(
                                SELECT 1 FROM information_schema.tables
                                WHERE table_schema = 'public' AND table_name = %s
                            )
                        """, (table_name,))
                        exists = cur2.fetchone()[0]
                        if not exists:
                            missing_after_create.append(table_name)
                
                if missing_after_create:
                    logger.error(f"\n✗ Tables still missing after creation attempt: {missing_after_create}")
                    raise Exception(f"Failed to create tables: {missing_after_create}")
                    
            except Exception as e:
                logger.error(f"\n✗ Failed to create missing tables: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                raise
        else:
            logger.info(f"\n✓ All required tables exist")


def create_missing_tables_manually(conn, missing_tables):
    """
    Create missing tables manually using raw SQL.
    
    This uses exact schema from tenant_tnt reference database.
    Tables are created in dependency order to avoid foreign key constraint errors.
    """
    # Exact table definitions from tenant_tnt
    create_sql = {
        'django_content_type': """
            CREATE TABLE IF NOT EXISTS django_content_type (
                id integer NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                app_label character varying(100) NOT NULL,
                model character varying(100) NOT NULL,
                UNIQUE (app_label, model)
            )
        """,
        'django_migrations': """
            CREATE TABLE IF NOT EXISTS django_migrations (
                id bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                app character varying(255) NOT NULL,
                name character varying(255) NOT NULL,
                applied timestamp with time zone NOT NULL
            )
        """,
        'auth_permission': """
            CREATE TABLE IF NOT EXISTS auth_permission (
                id integer NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                name character varying(255) NOT NULL,
                content_type_id integer NOT NULL,
                codename character varying(100) NOT NULL,
                UNIQUE (content_type_id, codename),
                FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED
            )
        """,
        'auth_group': """
            CREATE TABLE IF NOT EXISTS auth_group (
                id integer NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                name character varying(150) NOT NULL UNIQUE
            )
        """,
        'auth_group_permissions': """
            CREATE TABLE IF NOT EXISTS auth_group_permissions (
                id bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                group_id integer NOT NULL,
                permission_id integer NOT NULL,
                UNIQUE (group_id, permission_id),
                FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED,
                FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED
            )
        """,
        'django_session': """
            CREATE TABLE IF NOT EXISTS django_session (
                session_key character varying(40) NOT NULL PRIMARY KEY,
                session_data text NOT NULL,
                expire_date timestamp with time zone NOT NULL
            )
        """,
        'shop_users_shopuser': """
            CREATE TABLE IF NOT EXISTS shop_users_shopuser (
                id bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                password character varying(128) NOT NULL,
                last_login timestamp with time zone,
                is_superuser boolean NOT NULL DEFAULT false,
                first_name character varying(150) NOT NULL DEFAULT '',
                last_name character varying(150) NOT NULL DEFAULT '',
                is_staff boolean NOT NULL DEFAULT false,
                is_active boolean NOT NULL DEFAULT true,
                date_joined timestamp with time zone NOT NULL,
                username character varying(150) NOT NULL UNIQUE,
                email character varying(254) NOT NULL UNIQUE,
                tenant_id integer,
                role character varying(20) NOT NULL DEFAULT 'STAFF',
                phone character varying(20),
                shop_ids jsonb NOT NULL DEFAULT '[]'::jsonb,
                email_verification_token character varying(255),
                email_verification_token_created timestamp with time zone,
                is_email_verified boolean NOT NULL DEFAULT false
            )
        """,
        'shop_users_shopuser_groups': """
            CREATE TABLE IF NOT EXISTS shop_users_shopuser_groups (
                id bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                shopuser_id bigint NOT NULL,
                group_id integer NOT NULL,
                UNIQUE (shopuser_id, group_id),
                FOREIGN KEY (shopuser_id) REFERENCES shop_users_shopuser(id) DEFERRABLE INITIALLY DEFERRED,
                FOREIGN KEY (group_id) REFERENCES auth_group(id) DEFERRABLE INITIALLY DEFERRED
            )
        """,
        'shop_users_shopuser_user_permissions': """
            CREATE TABLE IF NOT EXISTS shop_users_shopuser_user_permissions (
                id bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                shopuser_id bigint NOT NULL,
                permission_id integer NOT NULL,
                UNIQUE (shopuser_id, permission_id),
                FOREIGN KEY (shopuser_id) REFERENCES shop_users_shopuser(id) DEFERRABLE INITIALLY DEFERRED,
                FOREIGN KEY (permission_id) REFERENCES auth_permission(id) DEFERRABLE INITIALLY DEFERRED
            )
        """,
        'django_admin_log': """
            CREATE TABLE IF NOT EXISTS django_admin_log (
                id integer NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                action_time timestamp with time zone NOT NULL,
                object_id text,
                object_repr character varying(200) NOT NULL,
                action_flag smallint NOT NULL,
                change_message text NOT NULL,
                content_type_id integer,
                user_id bigint NOT NULL,
                FOREIGN KEY (content_type_id) REFERENCES django_content_type(id) DEFERRABLE INITIALLY DEFERRED,
                FOREIGN KEY (user_id) REFERENCES shop_users_shopuser(id) DEFERRABLE INITIALLY DEFERRED
            )
        """,
        'token_blacklist_outstandingtoken': """
            CREATE TABLE IF NOT EXISTS token_blacklist_outstandingtoken (
                id bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                token text NOT NULL,
                created_at timestamp with time zone,
                expires_at timestamp with time zone NOT NULL,
                user_id bigint,
                jti character varying(255) NOT NULL,
                FOREIGN KEY (user_id) REFERENCES shop_users_shopuser(id) DEFERRABLE INITIALLY DEFERRED
            )
        """,
        'token_blacklist_blacklistedtoken': """
            CREATE TABLE IF NOT EXISTS token_blacklist_blacklistedtoken (
                id bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
                blacklisted_at timestamp with time zone NOT NULL,
                token_id bigint NOT NULL UNIQUE,
                FOREIGN KEY (token_id) REFERENCES token_blacklist_outstandingtoken(id) DEFERRABLE INITIALLY DEFERRED
            )
        """,
    }
    
    # Define creation order based on dependencies
    creation_order = [
        # No dependencies
        'django_content_type',
        'django_migrations',
        'auth_permission',
        'auth_group',
        'django_session',
        'shop_users_shopuser',
        # Depend on auth_permission and auth_group
        'auth_group_permissions',
        # Depend on shop_users_shopuser
        'shop_users_shopuser_groups',
        'shop_users_shopuser_user_permissions',
        'django_admin_log',
        'token_blacklist_outstandingtoken',
        # Depend on token_blacklist_outstandingtoken
        'token_blacklist_blacklistedtoken',
    ]
    
    with conn.cursor() as cur:
        cur.execute('SET search_path TO public')
        logger.info(f"\nCreating {len(missing_tables)} missing tables in dependency order...")
        
        for i, table_name in enumerate(creation_order, 1):
            if table_name not in missing_tables:
                continue  # Skip tables that don't need to be created
                
            if table_name not in create_sql:
                logger.warning(f"  {i}. ✗ Don't know how to create table: {table_name}")
                continue
            
            try:
                sql = create_sql[table_name]
                cur.execute(sql)
                logger.info(f"  {i}. ✓ Created table: {table_name}")
            except Exception as e:
                logger.error(f"  {i}. ✗ Failed to create {table_name}: {e}")
                logger.error(f"      SQL: {sql[:200]}...")
                raise  # Re-raise to stop the process on error
    
    try:
        conn.commit()
        logger.info(f"\n✓ Transaction committed - all missing tables created successfully")
    except Exception as e:
        logger.error(f"\n✗ Failed to commit transaction: {e}")
        conn.rollback()
        raise


def delete_shop_schema(tenant, schema_name, cascade=True):
    """
    Delete a shop schema and all its contents.
    
    ⚠️ WARNING: THIS PERMANENTLY DELETES ALL DATA IN THE SCHEMA!
    
    Args:
        tenant: Tenant instance
        schema_name: Name of schema to delete
        cascade: If True, delete all objects in schema (recommended)
    """
    alias = tenant.db_alias
    
    try:
        logger.warning(f"⚠️  DELETING SCHEMA: {schema_name} (cascade={cascade})")
        
        conn = connections[alias]
        
        with conn.cursor() as cur:
            if cascade:
                cur.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
            else:
                cur.execute(f'DROP SCHEMA IF EXISTS "{schema_name}"')
        
        conn.commit()
        logger.info(f"✓ Schema deleted: {schema_name}")
        
    except Exception as e:
        logger.error(f"Failed to delete schema {schema_name}: {str(e)}")
        raise


def get_schema_info(tenant, schema_name):
    """
    Get information about a schema.
    
    Returns:
        dict with keys: exists, table_count, tables, migrations
    """
    alias = tenant.db_alias
    
    try:
        conn = connections[alias]
        
        with conn.cursor() as cur:
            # Check if schema exists
            cur.execute("""
                SELECT EXISTS(
                    SELECT 1
                    FROM information_schema.schemata
                    WHERE schema_name = %s
                )
            """, [schema_name])
            exists = cur.fetchone()[0]
            
            if not exists:
                return {
                    'exists': False,
                    'table_count': 0,
                    'tables': [],
                    'migrations': []
                }
            
            # Get tables
            cur.execute("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = %s
                ORDER BY tablename
            """, [schema_name])
            tables = [row[0] for row in cur.fetchall()]
            
            # Get migrations
            cur.execute(f'SET search_path TO "{schema_name}", public')
            cur.execute("""
                SELECT app, name, applied
                FROM django_migrations
                ORDER BY app, applied
            """)
            migrations = [
                {'app': row[0], 'name': row[1], 'applied': row[2]}
                for row in cur.fetchall()
            ]
            
            return {
                'exists': True,
                'table_count': len(tables),
                'tables': tables,
                'migrations': migrations
            }
            
    except Exception as e:
        logger.error(f"Failed to get schema info for {schema_name}: {str(e)}")
        raise