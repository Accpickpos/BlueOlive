from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    StockFinderConfigViewSet,
    StockFinderOrderViewSet,
    StockFinderPurchaseOrderViewSet,
    StockFinderWebhookView,
)

app_name = "stockfinder"

router = DefaultRouter()
router.register(r"orders", StockFinderOrderViewSet, basename="order")
router.register(
    r"purchase-orders", StockFinderPurchaseOrderViewSet, basename="purchase-order"
)
router.register(r"configs", StockFinderConfigViewSet, basename="config")

urlpatterns = [
    # Webhook endpoint for receiving events from Stockfinder
    path("webhook/", StockFinderWebhookView.as_view(), name="webhook"),
] + router.urls
