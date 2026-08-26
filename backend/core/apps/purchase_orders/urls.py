from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BackOrderViewSet,
    PurchaseOrderReceiptViewSet,
    PurchaseOrderReportViewSet,
    PurchaseOrderTemplateViewSet,
    PurchaseOrderViewSet,
)

router = DefaultRouter()

# Register viewsets
router.register(r"orders", PurchaseOrderViewSet, basename="purchaseorder")
router.register(r"receipts", PurchaseOrderReceiptViewSet, basename="receipt")
router.register(r"back-orders", BackOrderViewSet, basename="backorder")
router.register(r"templates", PurchaseOrderTemplateViewSet, basename="template")
router.register(r"reports", PurchaseOrderReportViewSet, basename="report")

urlpatterns = [
    path("", include(router.urls)),
]
