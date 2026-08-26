from django.apps import AppConfig
from django.db.models.signals import post_migrate


class TenancyConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tenancy"
    verbose_name = "Multi-Tenancy"

    def ready(self):
        import tenancy.signals

        # Register database connections after migrations complete
        # This defers database access until apps are fully initialized
        post_migrate.connect(
            self._register_tenant_connections_after_migrate, sender=self, weak=False
        )

    @staticmethod
    def _register_tenant_connections_after_migrate(sender, **kwargs):
        """Register database connections after migrations are complete."""
        TenancyConfig._register_tenant_connections()

    @staticmethod
    def _register_tenant_connections():
        """Register database connections for all active tenants."""
        import logging

        from django.db import connection
        from django.db.utils import OperationalError, ProgrammingError
        from tenancy.models import Tenant
        from tenancy.utils import register_tenant_connection

        logger = logging.getLogger(__name__)

        try:
            # Check if the tenancy_tenant table exists before querying
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT 1 FROM information_schema.tables WHERE table_name='tenancy_tenant'"
                )
                if not cursor.fetchone():
                    # Table doesn't exist yet, skip registration
                    logger.debug(
                        "tenancy_tenant table does not exist yet, skipping tenant registration"
                    )
                    return

            tenants = Tenant.objects.filter(is_active=True)
            for tenant in tenants:
                try:
                    register_tenant_connection(tenant)
                except Exception as e:
                    logger.warning(
                        f"Failed to register connection for tenant {tenant.id}: {e}"
                    )
        except (ProgrammingError, OperationalError) as e:
            # Database not ready yet, this is normal during app initialization
            logger.debug(f"Database not ready for tenant registration: {e}")
        except Exception as e:
            # Log but don't fail app startup
            logger.warning(
                f"Unexpected error during tenant connection registration: {e}"
            )

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
