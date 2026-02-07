# tenancy/db_router.py
import logging
from django.conf import settings
from tenancy.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class TenantDatabaseRouter:
    """
    Routes database operations based on current tenant context.
    
    Architecture:
    - Default database (blue_olive): Shared system tables only
      * auth (users, groups, permissions) - in ALL databases
      * contenttypes - in ALL databases  
      * sessions, messages, staticfiles
      * rest_framework, simplejwt
      * tenancy (Tenant, Shop models)
      
    - Tenant databases: Tenant-specific tables
      * auth (users, groups, permissions) - duplicated for tenant isolation
      * contenttypes - duplicated for tenant isolation
      * admin (LogEntry) - references ShopUser
      * token_blacklist - references ShopUser (must be in same DB)
      * shop_users (ShopUser model)
      * All business apps (cash_book, creditors, stock_control, purchase_orders)
    """

    def _get_tenant_app_labels(self):
        """Get list of tenant app labels from settings."""
        return getattr(settings, 'TENANT_APP_LABELS', [])

    def _get_db_for_tenant(self, tenant):
        """Get database alias for a tenant, with validation."""
        if not tenant:
            return None
            
        if not hasattr(tenant, 'db_alias') or not tenant.db_alias:
            logger.error(f"Tenant {tenant} has no db_alias attribute")
            return None
            
        return tenant.db_alias

    def db_for_read(self, model, **hints):
        """Route read operations to appropriate database."""
        tenant = get_current_tenant()
        tenant_app_labels = self._get_tenant_app_labels()
        
        if tenant and model._meta.app_label in tenant_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for {model._meta.app_label}. "
                f"Falling back to default."
            )
        
        return "default"

    def db_for_write(self, model, **hints):
        """Route write operations to appropriate database."""
        tenant = get_current_tenant()
        tenant_app_labels = self._get_tenant_app_labels()
        
        if tenant and model._meta.app_label in tenant_app_labels:
            db_alias = self._get_db_for_tenant(tenant)
            if db_alias:
                return db_alias
            logger.warning(
                f"Tenant context exists but no valid db_alias for {model._meta.app_label}. "
                f"Falling back to default."
            )
        
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations only if both objects are in the same database.
        This prevents cross-database foreign keys.
        """
        db1 = self.db_for_read(obj1.__class__)
        db2 = self.db_for_read(obj2.__class__)
        
        if db1 and db2:
            return db1 == db2
        
        # If we can't determine the database, allow Django to decide
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Control which apps' migrations run on which databases.
        
        Migration Matrix:
        ┌─────────────────────┬─────────────┬────────────────┐
        │ App                 │ Default DB  │ Tenant DBs     │
        ├─────────────────────┼─────────────┼────────────────┤
        │ auth                │ ✓           │ ✓              │
        │ contenttypes        │ ✓           │ ✓              │
        │ sessions            │ ✓           │ ✗              │
        │ messages            │ ✓           │ ✗              │
        │ staticfiles         │ ✓           │ ✗              │
        │ rest_framework      │ ✓           │ ✗              │
        │ tenancy             │ ✓           │ ✗              │
        │ corsheaders         │ ✓           │ ✗              │
        │ admin               │ ✗           │ ✓              │
        │ token_blacklist     │ ✗           │ ✓              │
        │ shop_users          │ ✗           │ ✓              │
        │ cash_book           │ ✗           │ ✓              │
        │ creditors           │ ✗           │ ✓              │
        │ stock_control       │ ✗           │ ✓              │
        │ purchase_orders     │ ✗           │ ✓              │
        └─────────────────────┴─────────────┴────────────────┘
        
        Usage:
        - Default DB: python manage.py migrate --database=default
        - Tenant DB:  TENANT_DB_ALIAS=tenant_acme python manage.py migrate --database=tenant_acme
        """
        tenant_app_labels = self._get_tenant_app_labels()
        
        # Auth and contenttypes must exist in ALL databases
        # Required because ShopUser inherits from AbstractUser
        if app_label in ['auth', 'contenttypes']:
            return True

        # Tenant apps should only migrate to tenant databases
        if app_label in tenant_app_labels:
            # STRICT: Tenant apps MUST NOT migrate to default database
            if db == "default":
                logger.warning(
                    f"Migration of {app_label} to default database blocked. "
                    f"Tenant apps must only migrate to tenant databases. "
                    f"Use: TENANT_DB_ALIAS=<alias> python manage.py migrate"
                )
                return False
            
            # Check if we're explicitly migrating a tenant database
            tenant_db = getattr(settings, 'TENANT_DB_ALIAS', None)
            if tenant_db:
                # We're migrating a specific tenant database
                return db == tenant_db
            
            # During normal migration (no TENANT_DB_ALIAS set), only migrate to explicit tenant DBs
            # This prevents accidental migrations to wrong databases
            return False

        # All other apps (shared apps) → default database only
        # This includes: sessions, messages, staticfiles, rest_framework, 
        # tenancy, corsheaders
        return db == "default"