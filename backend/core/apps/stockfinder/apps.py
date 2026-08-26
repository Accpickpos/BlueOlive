from django.apps import AppConfig


class StockfinderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stockfinder"
    label = "stockfinder"
    verbose_name = "Stockfinder Integration"
