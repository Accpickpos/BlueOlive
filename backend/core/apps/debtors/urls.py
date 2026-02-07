"""
Debtors URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'', views.DebtorViewSet, basename='debtor')
router.register(r'transactions', views.DebtorTransactionViewSet, basename='debtor-transaction')
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')
router.register(r'post-dated-cheques', views.PostDatedChequeViewSet, basename='post-dated-cheque')

app_name = 'debtors'

urlpatterns = [
    path('', include(router.urls)),
]