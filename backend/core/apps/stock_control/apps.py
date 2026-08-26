from django.apps import AppConfig


class StockControlConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stock_control"
    label = "stock_control"

    def ready(self):
        """Import signals when app is ready"""
        import apps.stock_control.signals
