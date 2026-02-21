"""
Debtors URL configuration.
Based on DMAST, DEBTRAN, DEBTOPEN, DPDC, DEBTORAUD table models.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .import_csv import list_tenants_and_shops, analyze_csv, import_csv

# Create router and register viewsets
router = DefaultRouter()
router.register(r'debtors', views.DebtorViewSet, basename='debtor')
router.register(r'transactions', views.DebtorTransactionViewSet, basename='debtor-transaction')
router.register(r'open-items', views.DebteopenViewSet, basename='debtopen')
router.register(r'post-dated-cheques', views.DpdcViewSet, basename='dpdc')
router.register(r'audit', views.DebtorAuditViewSet, basename='debtor-audit')
router.register(r'sales-areas', views.DareaViewSet, basename='darea')
router.register(r'documents', views.DocumentSearchViewSet, basename='document-search')

app_name = 'debtors'

urlpatterns = [
    path('', include(router.urls)),
    
    # Import endpoints
    path('import/tenants/', list_tenants_and_shops, name='import-tenants'),
    path('import/analyze/', analyze_csv, name='import-analyze'),
    path('import/execute/', import_csv, name='import-execute'),
]