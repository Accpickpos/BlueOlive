"""
Enterprise URL routing for Creditors module
Organized with proper versioning and documentation endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CreditorViewSet, GoodsReceivedNoteViewSet, CreditorInvoiceViewSet,
    CreditorPaymentViewSet, CreditorJournalViewSet, OpenItemViewSet,
    RFCViewSet, CreditorsSummaryView
)

# Create router for automatic URL generation
router = DefaultRouter()

# Register creditor viewsets
router.register(r'creditors', CreditorViewSet, basename='creditor')
router.register(r'grn', GoodsReceivedNoteViewSet, basename='grn')
router.register(r'invoices', CreditorInvoiceViewSet, basename='invoice')
router.register(r'payments', CreditorPaymentViewSet, basename='payment')
router.register(r'journals', CreditorJournalViewSet, basename='journal')
router.register(r'open-items', OpenItemViewSet, basename='openitem')
router.register(r'rfc', RFCViewSet, basename='rfc')

# API endpoints
api_patterns = [
    path('summary/', CreditorsSummaryView.as_view(), name='creditors-summary'),
]

# API versioning
urlpatterns = [
    # API endpoints with default router
    path('', include(router.urls)),
    
    # Additional endpoints
    path('', include(api_patterns)),
]