# tenancy/db_router.py
import logging
import os
from django.conf import settings
from tenancy.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class TenantDatabaseRouter:
    """
    Routes database operations based on current tenant context.
    
    THREE-TIER ARCHITECTURE:
    ======================
    
    1. DEFAULT DATABASE (blue_olive):
       - Shared system tables across all tenants
       - Tables: Tenant, Shop, auth (superusers), contenttypes, sessions, 
                 messages, staticfiles, rest_framework, tenancy
       - Command: python manage.py migrate --database=default
    
    2. TENANT DATABASES (one per tenant):
       Public Schema:
       - Tenant-specific shared tables (shared across all shops in tenant)
       - Tables: ShopUser, admin (LogEntry), token_blacklist, messaging,
                 auth (duplicated), contenttypes (duplicated)
       - Command: TENANT_DB_ALIAS=tenant_acme python manage.py migrate --database=tenant_acme
    
    3. SHOP SCHEMAS (multiple per tenant database):
       - Shop-specific business data tables
       - Tables: cash_book, creditors, stock_control, purchase_orders, etc.
       - Command: SHOP_SCHEMA=downtown python manage.py migrate_shop_apps --shop=downtown
       - Note: Inherits auth/contenttypes from public schema via PostgreSQL search_path
    
    CRITICAL DESIGN DECISIONS:
    ========================
    
    Why auth/contenttypes are duplicated in tenant DBs:
    - ShopUser inherits from AbstractUser (requires auth tables)
    - Django's ContentType framework requires contenttypes in same DB
    - token_blacklist has ForeignKey to ShopUser (must be in same DB)
    - admin.LogEntry has ForeignKey to ShopUser (must be in same DB)
    
    Why shop apps DON'T go in tenant public schema:
    - Each tenant can have multiple shops
    - Shop data must be isolated from each other
    - PostgreSQL schemas provide efficient isolation within same DB
    - Allows easy shop-level backups and data management
    
    SETTINGS REQUIRED:
    ================
    
    In settings.py:
    
    TENANT_APP_LABELS = [
        'shop_users',     # Tenant public schema
        'admin',          # Tenant public schema
        'token_blacklist',# Tenant public schema
        'messaging',      # Tenant public schema
    ]
    
    SHOP_APP_LABELS = [
        'cash_book',      # Shop schemas only
        'creditors',      # Shop schemas only
        'stock_control',  # Shop schemas only
        'purchase_orders',# Shop schemas only
    ]
    """

    def _get_tenant_app_labels(self):
        return getattr(settings, 'TENANT_APP_LABELS', [])

    def _get_shop_app_labels(self):
        return getattr(settings, 'SHOP_APP_LABELS', [])

    def _get_db_for_tenant(self, tenant):
        if not tenant:
            return None
        if not hasattr(tenant, 'db_alias') or not tenant.db_alias:
            logger.error(f"Tenant {tenant} has no db_alias attribute")
            return None
        return tenant.db_alias

    def db_for_read(self, model, **hints):
        tenant = get_current_tenant()
        tenant_app_labels = self._get_tenant_app_labels()
        shop_app_labels = self._get_shop_app_labels()

        # Tenant-level app with active context → tenant DB
        if tenant and model._meta.app_label in tenant_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for {model._meta.app_label}. "
                f"Falling back to default."
            )

        # Shop-level app with active context → tenant DB
        if tenant and model._meta.app_label in shop_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for shop app {model._meta.app_label}. "
                f"Falling back to default."
            )

        # Shop-level app with NO tenant context → return None so that an
        # explicit .using(db_alias) on the queryset is honoured.
        # Returning "default" here would override .using() entirely, causing
        # shop queries (e.g. from the CSV importer) to hit the wrong database.
        if model._meta.app_label in shop_app_labels:
            return None

        return "default"

    def db_for_write(self, model, **hints):
        tenant = get_current_tenant()
        tenant_app_labels = self._get_tenant_app_labels()
        shop_app_labels = self._get_shop_app_labels()

        # Tenant-level app with active context → tenant DB
        if tenant and model._meta.app_label in tenant_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for {model._meta.app_label}. "
                f"Falling back to default."
            )

        # Shop-level app with active context → tenant DB
        if tenant and model._meta.app_label in shop_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for shop app {model._meta.app_label}. "
                f"Falling back to default."
            )

        # Shop-level app with NO tenant context → return None so that an
        # explicit .using(db_alias) on the queryset is honoured.
        if model._meta.app_label in shop_app_labels:
            return None

        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations only if both objects are in the same database.
        This prevents cross-database foreign keys.
        
        Note: This checks DATABASE, not schema. Relations between public schema
        and shop schemas within the same tenant DB are allowed (and common).
        """
        db1 = self.db_for_read(obj1.__class__)
        db2 = self.db_for_read(obj2.__class__)
        
        if db1 and db2:
            return db1 == db2
        
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Control which apps' migrations run on which databases and schemas.
        """
        tenant_app_labels = self._get_tenant_app_labels()
        shop_app_labels = self._get_shop_app_labels()
        
        if settings.DEBUG:
            logger.debug(f"[allow_migrate] db={db}, app_label={app_label}, model_name={model_name}")
        
        if app_label in ['auth', 'contenttypes']:
            if self._is_shop_schema_migration():
                return False
            return True
        
        if app_label in shop_app_labels:
            if db == "default":
                logger.warning(f"[allow_migrate] BLOCK {app_label}.{model_name} → default DB (shop app)")
                return False
            is_shop_migration = self._is_shop_schema_migration()
            if not is_shop_migration:
                logger.warning(f"[allow_migrate] BLOCK {app_label}.{model_name} → tenant public schema (SHOP_SCHEMA not set)")
                return False
            logger.debug(f"[allow_migrate] ALLOW {app_label}.{model_name} → shop schema (SHOP_SCHEMA={os.environ.get('SHOP_SCHEMA')})")
            return True
        
        if app_label in tenant_app_labels:
            if db == "default":
                logger.warning(f"Migration of {app_label} to default database blocked.")
                return False
            if self._is_shop_schema_migration():
                return False
            return True
        
        if db != "default":
            logger.warning(f"[allow_migrate] BLOCK {app_label}.{model_name} → {db}. Only default DB for shared apps.")
        
        return db == "default"

    def _is_shop_schema_migration(self):
        shop_schema = os.environ.get('SHOP_SCHEMA')
        tenant_db_alias = os.environ.get('TENANT_DB_ALIAS')
        if shop_schema:
            logger.warning(f"[_is_shop_schema_migration] SHOP_SCHEMA={shop_schema} (ACTIVE)")
        elif tenant_db_alias:
            logger.warning(f"[_is_shop_schema_migration] TENANT_DB_ALIAS={tenant_db_alias} (tenant migration)")
        else:
            logger.warning(f"[_is_shop_schema_migration] No migration context set")
        return shop_schema is not None


class StrictTenantDatabaseRouter:
    """
    Stricter version that requires TENANT_DB_ALIAS to be set.
    """
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        tenant_app_labels = getattr(settings, 'TENANT_APP_LABELS', [])
        
        if app_label in ['auth', 'contenttypes']:
            return True
        
        if app_label in tenant_app_labels:
            if db == "default":
                return False
            tenant_db = getattr(settings, 'TENANT_DB_ALIAS', None)
            if tenant_db:
                return db == tenant_db
            logger.warning(f"Migration of {app_label} blocked. Set TENANT_DB_ALIAS.")
            return False
        
        return db == "default"