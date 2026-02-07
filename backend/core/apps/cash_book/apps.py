from django.apps import AppConfig


class CashBookConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cash_book'
    label = 'cash_book'
    
    def ready(self):
        """Register signals when app is ready"""
        import apps.cash_book.signals  # noqa
