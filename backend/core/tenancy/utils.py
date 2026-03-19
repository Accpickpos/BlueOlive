# tenancy/utils.py
from django.conf import settings
from django.db import connections
from django.core.management import call_command
import psycopg2
from psycopg2 import extensions
import time

def register_tenant_connection(tenant, shop=None):
    """
    Register tenant database connection using credentials from Django settings.
    This ensures all tenants use the same PostgreSQL credentials as the main database.
    
    CRITICAL: We set search_path to the shop's schema at the connection level so that
    ALL queries (including migrations) default to the shop's schema, not public.
    
    Args:
        tenant: The Tenant object to connect to
        shop: Optional Shop object. If provided, uses this shop's schema.
              If not provided, falls back to tenant.shops.first() for backward compatibility.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    alias = tenant.db_alias
    # Use credentials from settings, not from tenant object
    # This allows old tenants with incorrect db_password to still work
    default_db = settings.DATABASES['default']
    
    # Get the shop's schema name - use provided shop or fall back to first shop
    # This ensures proper multi-shop data isolation within a tenant
    if shop is None:
        logger.debug(f"[register_tenant_connection] No shop provided, getting first shop for tenant {tenant.name}")
        shop = tenant.shops.first()
    
    if shop is None:
        logger.warning(f"[register_tenant_connection] No shop found for tenant {tenant.name}!")
    
    shop_schema = shop.schema_name if shop else "public"  # Fallback to public if no shop
    
    logger.debug(f"[register_tenant_connection] Tenant: {tenant.name}, Shop: {shop.name if shop else None}, Schema: {shop_schema}, DB: {tenant.db_name}")
    
    db_config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": tenant.db_name,
        "USER": default_db['USER'],  # Use settings USER, not tenant.db_user
        "PASSWORD": default_db['PASSWORD'],  # Use settings PASSWORD, not tenant.db_password
        "HOST": tenant.db_host,
        "PORT": tenant.db_port,
        "CONN_MAX_AGE": 60,
        # search_path: shop schema first so all shop tables (dmast, stock_items, etc.)
        # resolve without qualification. public second for shared tables (shop_users,
        # auth_*, django_*). Both are always found — order determines priority only.
        "OPTIONS": {
            'options': f'-c search_path="{shop_schema}",public -c statement_timeout=0'
        },
        "TIME_ZONE": settings.TIME_ZONE,
        "AUTOCOMMIT": True,
        "ATOMIC_REQUESTS": False,
        # IMPORTANT: must be True when CONN_MAX_AGE > 0.
        # Without health checks Django reuses persistent connections that may have been
        # opened before this schema was registered, causing "relation does not exist"
        # on tables that only exist in the shop schema (e.g. dmast).
        "CONN_HEALTH_CHECKS": True,
    }
    # Add to settings and ensure connections updated
    settings.DATABASES[alias] = db_config
    connections.databases[alias] = db_config

    # Force-close any existing physical connection for this alias so the next
    # query opens a fresh one with the new search_path OPTIONS above.
    # Without this, a persistent connection opened before register_tenant_connection
    # (e.g. from a previous request) would be reused and still point at the wrong schema.
    if alias in connections._connections.__dict__:
        try:
            connections[alias].close()
        except Exception:
            pass
    
    logger.debug(f"[register_tenant_connection] Connection registered: alias={alias}, db={tenant.db_name}, search_path=public,{shop_schema}")

def create_tenant_database_postgres(tenant, superuser_conn_info):
    """
    Create the actual tenant database in Postgres using superuser credentials.
    superuser_conn_info: dict with host, port, dbname, user, password
    """
    # Connect with superuser to create DB/user if necessary
    dsn = (
        f"host={superuser_conn_info['host']} "
        f"port={superuser_conn_info['port']} "
        f"user={superuser_conn_info['user']} "
        f"password={superuser_conn_info['password']} "
        f"dbname=postgres"
    )
    conn = psycopg2.connect(dsn)
    try:
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        # Create DB
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = %s", (tenant.db_name,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{tenant.db_name}"')
        # Optionally create user and grant privileges
        # cur.execute("CREATE USER ...")
        # cur.execute("GRANT ALL PRIVILEGES ON DATABASE ...")
    finally:
        conn.close()
    # small sleep or verify connectable
    time.sleep(0.5)

def provision_tenant(tenant, superuser_conn_info):
    """
    1) Create database in Postgres
    2) Register the DB alias in Django settings
    3) Migrate shop_users to public schema
    """
    from django.conf import settings
    from django.core.management import call_command
    from .tenant_context import set_current_tenant, clear_current_tenant

    create_tenant_database_postgres(tenant, superuser_conn_info)
    register_tenant_connection(tenant)

    # Migrate shop_users to public schema
    alias = tenant.db_alias
    original_options = settings.DATABASES[alias].get('OPTIONS', {})
    settings.DATABASES[alias]['OPTIONS'] = {
        **original_options,
        'options': '-c search_path=public'
    }
    connections.databases[alias] = settings.DATABASES[alias]

    try:
        set_current_tenant(tenant)
        try:
            call_command("migrate", "shop_users", database=alias, verbosity=1)
        finally:
            clear_current_tenant()
    finally:
        settings.DATABASES[alias]['OPTIONS'] = original_options
        connections.databases[alias] = settings.DATABASES[alias]