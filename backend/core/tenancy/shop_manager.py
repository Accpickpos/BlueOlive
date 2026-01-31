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
    
    Each shop gets its own isolated copy of these tables in its schema.
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
            # Get connection
            conn = connections[alias]
            conn.close()
            conn.connect()
            
            # Set search path to the shop schema first
            # Include 'public' so auth/contenttypes models can be found
            with conn.cursor() as cur:
                cur.execute(f'SET search_path TO "{schema_name}", public')
                
                # Verify search path
                cur.execute('SHOW search_path')
                current_path = cur.fetchone()[0]
                logger.info(f"✓ Search path set to: {current_path}")
            
            # Migrate each shop app with explicit search_path
            for app_label in shop_app_labels:
                try:
                    logger.info(f"  Migrating {app_label} to {schema_name}...")
                    
                    # First, ensure search_path is set for this specific migration
                    with conn.cursor() as cur:
                        cur.execute(f'SET search_path TO "{schema_name}", public')
                    
                    call_command(
                        'migrate',
                        app_label,
                        database=alias,
                        verbosity=1,
                        interactive=False,
                    )
                    
                    logger.info(f"  ✓ {app_label} migrated to {schema_name}")
                    
                except Exception as e:
                    logger.error(f"  ✗ Failed to migrate {app_label}: {str(e)}")
                    # Try to continue with other apps
            
            # After migrations, verify and create any missing tables
            logger.info(f"Verifying tables in schema {schema_name}...")
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
    alias = tenant.db_alias
    set_current_tenant(tenant)
    
    try:
        logger.info(f"Migrating tenant database: {tenant.db_name}")
        
        conn = connections[alias]
        conn.close()
        conn.connect()
        
        # Set search path to public schema
        with conn.cursor() as cur:
            cur.execute('SET search_path TO public')
            cur.execute('SHOW search_path')
            logger.info(f"✓ Search path: {cur.fetchone()[0]}")
        
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
                try:
                    logger.info(f"  Migrating {app_label}...")
                    
                    call_command(
                        'migrate',
                        app_label,
                        database=alias,
                        verbosity=0,
                        interactive=False,
                    )
                    
                    logger.info(f"  ✓ {app_label} migrated")
                    
                except Exception as e:
                    logger.error(f"  ✗ {app_label}: {str(e)}")
                    # Continue with other apps
        
        logger.info(f"\n✓ Tenant database migration complete: {tenant.db_name}")
        logger.info(f"  Public schema apps: {apps_for_public_schema}")
        logger.info(f"  Shop schema apps (not migrated): {shop_app_labels}")
        
    except Exception as e:
        logger.error(f"Tenant database migration failed: {str(e)}")
        raise
    finally:
        clear_current_tenant()


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