from django.apps import AppConfig


class PosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pos'
    label = 'pos'
    verbose_name = 'Point of Sale'

    def ready(self):
        """Register signals when app is ready."""
        import apps.pos.signals  # noqa

