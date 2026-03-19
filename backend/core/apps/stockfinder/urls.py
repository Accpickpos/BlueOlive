"""
URL Configuration for Stockfinder integration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    StockFinderConfigViewSet,
    StockFinderSyncLogViewSet,
    StockFinderWebhookView,
    StockFinderStockViewSet,
    StockFinderOrderViewSet,
    StockFinderPurchaseOrderViewSet,
    DocumentRetrievalView,
)

app_name = 'stockfinder'

router = DefaultRouter()
router.register(r'configs', StockFinderConfigViewSet, basename='config')
router.register(r'stock', StockFinderStockViewSet, basename='stock')
router.register(r'orders', StockFinderOrderViewSet, basename='order')
router.register(r'purchase-orders', StockFinderPurchaseOrderViewSet, basename='purchase-order')
router.register(r'sync-logs', StockFinderSyncLogViewSet, basename='sync-log')

urlpatterns = [
    # Webhook endpoint (no authentication - uses signature verification)
    path('webhook/', StockFinderWebhookView.as_view(), name='webhook'),
    
    # Document retrieval endpoint
    path('documents/', DocumentRetrievalView.as_view(), name='documents'),
    
    # Include router URLs
    path('', include(router.urls)),
]
