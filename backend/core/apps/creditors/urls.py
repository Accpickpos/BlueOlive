from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierViewSet, ExpenseCategoryViewSet, CreditorTransactionViewSet, RFCViewSet,
    OutstandingBalanceView
)

router = DefaultRouter()

# Register viewsets
router.register(r'suppliers', SupplierViewSet, basename='supplier')
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expensecategory')
router.register(r'transactions', CreditorTransactionViewSet, basename='transaction')
router.register(r'rfc', RFCViewSet, basename='rfc')

urlpatterns = [
    path('outstanding-balance/', OutstandingBalanceView.as_view(), name='outstanding-balance'),
    path('', include(router.urls)),
]