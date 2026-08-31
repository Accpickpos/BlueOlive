from django.apps import AppConfig


class CreditorsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.creditors"
    label = "creditors"

    def ready(self):
        """
        Import signals when app is ready.

        FIX: this was previously missing entirely — apps/creditors/signals.py
        was never imported anywhere in the project, so none of its receivers
        were ever registered. In practice this meant NO creditors automatic
        business logic ever ran: open items were never created for GRNs,
        invoices, credit notes, payments or journals; GRN/invoice/credit-note
        header totals were never rolled up from their line items; aged
        balances were never recalculated. Every one of those behaviors only
        existed on paper in signals.py, never at runtime. Mirrors
        apps.stock_control.apps.StockControlConfig.ready() /
        apps.pos.apps.PosConfig.ready().
        """
        import apps.creditors.signals  # noqa
