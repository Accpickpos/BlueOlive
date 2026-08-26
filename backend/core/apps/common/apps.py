"""
Common App Configuration
Shared utilities across all business apps
"""

from django.apps import AppConfig


class CommonConfig(AppConfig):
    """Configuration for the common app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"
    verbose_name = "Common Utilities"

    def ready(self):
        """Initialize app when Django starts."""
        # Import signals if any
        # from . import signals
