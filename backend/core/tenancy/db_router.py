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
        """
        Get list of tenant app labels from settings.
        These apps go to tenant DB public schema.
        """
        return getattr(settings, 'TENANT_APP_LABELS', [])

    def _get_shop_app_labels(self):
        """
        Get list of shop app labels from settings.
        These apps go to shop schemas within tenant DB.
        """
        return getattr(settings, 'SHOP_APP_LABELS', [])

    def _get_db_for_tenant(self, tenant):
        """
        Get database alias for a tenant, with validation.
        
        Returns the tenant's db_alias (e.g., 'tenant_acme').
        This points to the tenant's database, where queries will
        go to either public schema or shop schemas depending on context.
        """
        if not tenant:
            return None
            
        if not hasattr(tenant, 'db_alias') or not tenant.db_alias:
            logger.error(f"Tenant {tenant} has no db_alias attribute")
            return None
            
        return tenant.db_alias

    def db_for_read(self, model, **hints):
        """
        Route read operations to appropriate database.
        
        Logic:
        1. If model is a tenant app (shop_users, admin, etc.) → tenant DB
        2. If model is a shop app (cash_book, etc.) → tenant DB (router doesn't handle schemas)
        3. Otherwise → default DB
        
        Note: Schema routing (public vs shop schemas) is handled by
        set_search_path() in tenant_context.py, not by the router.
        """
        tenant = get_current_tenant()
        tenant_app_labels = self._get_tenant_app_labels()
        shop_app_labels = self._get_shop_app_labels()
        
        # Check if this is a tenant-level app
        if tenant and model._meta.app_label in tenant_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for {model._meta.app_label}. "
                f"Falling back to default."
            )
        
        # Check if this is a shop-level app
        # Shop apps also go to tenant DB, but PostgreSQL search_path determines schema
        if tenant and model._meta.app_label in shop_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for shop app {model._meta.app_label}. "
                f"Falling back to default."
            )
        
        # All other apps use default database
        return "default"

    def db_for_write(self, model, **hints):
        """
        Route write operations to appropriate database.
        Same logic as db_for_read().
        """
        tenant = get_current_tenant()
        tenant_app_labels = self._get_tenant_app_labels()
        shop_app_labels = self._get_shop_app_labels()
        
        # Tenant-level apps → tenant DB
        if tenant and model._meta.app_label in tenant_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for {model._meta.app_label}. "
                f"Falling back to default."
            )
        
        # Shop-level apps → tenant DB (schema determined by search_path)
        if tenant and model._meta.app_label in shop_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for shop app {model._meta.app_label}. "
                f"Falling back to default."
            )
        
        # All other apps → default database
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
        
        # If we can't determine the database, allow Django to decide
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Control which apps' migrations run on which databases and schemas.
        
        MIGRATION MATRIX:
        ================
        
        ┌─────────────────────┬─────────────┬──────────────┬──────────────┐
        │ App                 │ Default DB  │ Tenant DB    │ Shop Schema  │
        │                     │             │ (public)     │              │
        ├─────────────────────┼─────────────┼──────────────┼──────────────┤
        │ auth                │ ✓           │ ✓            │ ✗            │
        │ contenttypes        │ ✓           │ ✓            │ ✗            │
        │ sessions            │ ✓           │ ✗            │ ✗            │
        │ tenancy             │ ✓           │ ✗            │ ✗            │
        │ admin               │ ✗           │ ✓            │ ✗            │
        │ token_blacklist     │ ✗           │ ✓            │ ✗            │
        │ shop_users          │ ✗           │ ✓            │ ✗            │
        │ messaging           │ ✗           │ ✓            │ ✗            │
        │ cash_book           │ ✗           │ ✗            │ ✓            │
        │ creditors           │ ✗           │ ✗            │ ✓            │
        │ stock_control       │ ✗           │ ✗            │ ✓            │
        │ purchase_orders     │ ✗           │ ✗            │ ✓            │
        └─────────────────────┴─────────────┴──────────────┴──────────────┘
        
        MIGRATION COMMANDS:
        ==================
        
        1. Migrate default DB:
           python manage.py migrate --database=default
        
        2. Migrate tenant DB public schema:
           TENANT_DB_ALIAS=tenant_acme python manage.py migrate --database=tenant_acme
        
        3. Migrate shop schema:
           SHOP_SCHEMA=downtown python manage.py migrate_shop_apps --shop=downtown
           
        ENVIRONMENT VARIABLES:
        =====================
        
        TENANT_DB_ALIAS: Not required, router allows migration to any tenant DB
        SHOP_SCHEMA: Set by shop_manager.py during shop migrations
                     When set, indicates we're migrating a shop schema
        """
        tenant_app_labels = self._get_tenant_app_labels()
        shop_app_labels = self._get_shop_app_labels()
        
        # ================================================================
        # RULE 1: auth and contenttypes
        # ================================================================
        # These must exist in:
        # - Default DB (for superusers)
        # - Tenant DB public schema (for ShopUser)
        # But NOT in shop schemas (they inherit from public via search_path)
        
        if app_label in ['auth', 'contenttypes']:
            # Check if we're migrating a shop schema
            if self._is_shop_schema_migration():
                if settings.DEBUG and model_name:
                    logger.debug(
                        f"Blocking {app_label}.{model_name} migration to shop schema. "
                        f"Shop schemas inherit auth/contenttypes from public schema."
                    )
                return False
            
            # Allow migration to default and all tenant databases
            return True
        
        # ================================================================
        # RULE 2: Shop apps (cash_book, creditors, stock_control, etc.)
        # ================================================================
        # These should ONLY migrate to shop schemas, NEVER to:
        # - Default database
        # - Tenant DB public schema
        
        if app_label in shop_app_labels:
            # Block migration to default database
            if db == "default":
                if settings.DEBUG and model_name:
                    logger.debug(
                        f"Blocking {app_label}.{model_name} migration to default DB. "
                        f"Shop apps only migrate to shop schemas."
                    )
                return False
            
            # Check if we're in a shop schema migration context
            if self._is_shop_schema_migration():
                # We're migrating a shop schema - allow it
                if settings.DEBUG and model_name:
                    logger.debug(
                        f"Allowing {app_label}.{model_name} migration to shop schema."
                    )
                return True
            else:
                # We're migrating tenant DB public schema - block shop apps
                if settings.DEBUG and model_name:
                    logger.debug(
                        f"Blocking {app_label}.{model_name} migration to tenant public schema. "
                        f"Shop apps only migrate to shop schemas via shop_manager.py"
                    )
                return False
        
        # ================================================================
        # RULE 3: Tenant apps (admin, token_blacklist, shop_users, messaging)
        # ================================================================
        # These go to tenant DB public schema only, NOT to:
        # - Default database
        # - Shop schemas
        
        if app_label in tenant_app_labels:
            # Block migration to default database
            if db == "default":
                if settings.DEBUG and model_name:
                    logger.debug(
                        f"Blocking {app_label}.{model_name} migration to default DB. "
                        f"Use: TENANT_DB_ALIAS=<alias> python manage.py migrate --database=<alias>"
                    )
                else:
                    logger.warning(
                        f"Migration of {app_label} to default database blocked. "
                        f"Tenant apps must only migrate to tenant databases."
                    )
                return False
            
            # Block migration to shop schemas
            if self._is_shop_schema_migration():
                if settings.DEBUG and model_name:
                    logger.debug(
                        f"Blocking {app_label}.{model_name} migration to shop schema. "
                        f"This app belongs in tenant DB public schema."
                    )
                return False
            
            # Allow migration to tenant DB public schema
            if settings.DEBUG and model_name:
                logger.debug(
                    f"Allowing {app_label}.{model_name} migration to tenant DB public schema."
                )
            return True
        
        # ================================================================
        # RULE 4: All other apps (shared apps)
        # ================================================================
        # These include: sessions, messages, staticfiles, rest_framework,
        #                tenancy, corsheaders, etc.
        # These only go to default database.
        
        if db != "default":
            if settings.DEBUG and model_name:
                logger.debug(
                    f"Blocking {app_label}.{model_name} migration to {db}. "
                    f"Shared apps only migrate to default database."
                )
        
        return db == "default"

    def _is_shop_schema_migration(self):
        """
        Check if we're currently migrating a shop schema.
        
        This is determined by the SHOP_SCHEMA environment variable
        which is set by shop_manager.py during shop schema migrations.
        
        Example:
            SHOP_SCHEMA=downtown python manage.py migrate_shop_apps --shop=downtown
        
        Returns:
            bool: True if migrating a shop schema, False otherwise
        """
        shop_schema = os.environ.get('SHOP_SCHEMA')
        if shop_schema and settings.DEBUG:
            logger.debug(f"Shop schema migration detected: {shop_schema}")
        return shop_schema is not None


# ============================================================================
# ALTERNATIVE ROUTER (for reference - not used)
# ============================================================================
# This is an alternative implementation that requires explicit TENANT_DB_ALIAS
# Version 1 (above) is more flexible and recommended.

class StrictTenantDatabaseRouter:
    """
    Stricter version that requires TENANT_DB_ALIAS to be set.
    Use this if you want more explicit control over migrations.
    """
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        tenant_app_labels = getattr(settings, 'TENANT_APP_LABELS', [])
        
        if app_label in ['auth', 'contenttypes']:
            return True
        
        if app_label in tenant_app_labels:
            if db == "default":
                return False
            
            # Require explicit TENANT_DB_ALIAS
            tenant_db = getattr(settings, 'TENANT_DB_ALIAS', None)
            if tenant_db:
                return db == tenant_db
            
            # Without TENANT_DB_ALIAS, block migration
            logger.warning(
                f"Migration of {app_label} blocked. "
                f"Set TENANT_DB_ALIAS environment variable."
            )
            return False
        
        return db == "default"