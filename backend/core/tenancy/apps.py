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
        from django.db import connection
        from django.db.utils import ProgrammingError
        from tenancy.models import Tenant
        from tenancy.utils import register_tenant_connection

        try:
            # Check if the tenancy_tenant table exists before querying
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_name='tenancy_tenant'"
                )
                if not cursor.fetchone():
                    # Table doesn't exist yet, skip registration
                    return

            tenants = Tenant.objects.filter(is_active=True)
            for tenant in tenants:
                register_tenant_connection(tenant)
        except (ProgrammingError, Exception) as e:
            # Log but don't fail app startup
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Skipping tenant connection registration: {e}")
    
    def get_models(self, include_auto_created=False, include_swapped=False):
        """
        Override to exclude AuditLog from Django's makemigrations detection.
        AuditLog uses managed=False since the table is created manually in migration 0005.
        Note: Django admin and other features that use get_models() will still work
        because Django admin uses its own registry for registered models.
        """
        models = super().get_models(include_auto_created, include_swapped)
        # Exclude AuditLog from auto-migration detection only
        from tenancy.audit import AuditLog
        return [m for m in models if m is not AuditLog]
