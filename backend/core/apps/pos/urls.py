"""
Point of Sale URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'cash-sales', views.CashSaleViewSet, basename='cash-sale')
router.register(r'laybyes', views.LaybyeViewSet, basename='laybye')
router.register(r'quotations', views.QuotationViewSet, basename='quotation')
router.register(r'payouts', views.PayoutViewSet, basename='payout')
router.register(r'repairs', views.RepairViewSet, basename='repair')
router.register(r'job-cards', views.JobCardViewSet, basename='job-card')
router.register(r'cash-control', views.CashControlViewSet, basename='cash-control')
router.register(r'receipts-on-account', views.ReceiptOnAccountViewSet, basename='receipt-on-account')
router.register(r'credit-notes', views.CreditNoteViewSet, basename='credit-note')
router.register(r'cash-returns', views.CashReturnViewSet, basename='cash-return')
router.register(r'cash-a-cheque', views.CashAChequeViewSet, basename='cash-a-cheque')
router.register(r'transaction-queries', views.TransactionQueryViewSet, basename='transaction-query')

app_name = 'point_of_sale'

urlpatterns = [
    path('', include(router.urls)),
]
