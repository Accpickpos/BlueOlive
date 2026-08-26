from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
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

urlpatterns = [
    # Webhook endpoint for receiving events from Stockfinder
    path("webhook/", StockFinderWebhookView.as_view(), name="webhook"),
] + router.urls
