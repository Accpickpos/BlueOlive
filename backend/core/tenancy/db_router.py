import logging
from django.conf import settings
from tenancy.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class TenantDatabaseRouter:
    def db_for_read(self, model, **hints):
        tenant = get_current_tenant()
        logger.debug(f"db_for_read: model={model._meta.label}, app_label={model._meta.app_label}, tenant={tenant}")
        if tenant and model._meta.app_label in settings.TENANT_APPS:
            return tenant.db_alias
        return "default"

    def db_for_write(self, model, **hints):
        tenant = get_current_tenant()
        logger.debug(f"db_for_write: model={model._meta.label}, app_label={model._meta.app_label}, tenant={tenant}")
        if tenant and model._meta.app_label in settings.TENANT_APPS:
            return tenant.db_alias
        return "default"

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        tenant = get_current_tenant()
        logger.debug(f"allow_migrate: app_label={app_label}, db={db}, tenant={tenant}, model_name={model_name}")

        # SHOP_APPS: Allow migration when tenant context is set and db matches
        shop_app_labels = [app.split('.')[-1] for app in settings.SHOP_APPS]
        if app_label in shop_app_labels:
            if tenant and db == tenant.db_alias:
                return True
            return False

        # TENANT_APPS: Allow migration when tenant context is set and db matches
        tenant_app_labels = [app.split('.')[-1] for app in settings.TENANT_APPS]
        if app_label in tenant_app_labels:
            if tenant and db == tenant.db_alias:
                return True
            return False

        # SHARED_APPS: Only migrate on default database, except auth, contenttypes, and shop_users which are needed per tenant
        shared_app_labels = [app.split('.')[-1] for app in settings.SHARED_APPS]
        if app_label in shared_app_labels:
            if app_label in ['auth', 'contenttypes', 'shop_users']:
                # Allow auth, contenttypes, and shop_users on tenant dbs
                tenant = get_current_tenant()
                if tenant and db == tenant.db_alias:
                    return True
            return db == "default"

        # All other apps: migrate on default database only
        return db == "default"