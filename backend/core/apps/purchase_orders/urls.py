from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PurchaseOrderViewSet, PurchaseOrderReceiptViewSet, BackOrderViewSet,
    PurchaseOrderTemplateViewSet, PurchaseOrderReportViewSet
)

router = DefaultRouter()

# Register viewsets
router.register(r'orders', PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'receipts', PurchaseOrderReceiptViewSet, basename='receipt')
router.register(r'back-orders', BackOrderViewSet, basename='backorder')
router.register(r'templates', PurchaseOrderTemplateViewSet, basename='template')
router.register(r'reports', PurchaseOrderReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
]