from django.apps import AppConfig


class TenancyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tenancy'
    verbose_name = "Multi-Tenancy"

    def ready(self):
        import sys
        import tenancy.signals
        
        # Skip database access during migrations
        if 'migrate' not in sys.argv and 'makemigrations' not in sys.argv:
            self._register_tenant_connections()

    def _register_tenant_connections(self):
        """Register database connections for all active tenants."""
        from tenancy.models import Tenant
        from tenancy.utils import register_tenant_connection

        try:
            tenants = Tenant.objects.filter(is_active=True)
            for tenant in tenants:
                register_tenant_connection(tenant)
        except Exception as e:
            # Log but don't fail app startup
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to register tenant connections: {e}")
