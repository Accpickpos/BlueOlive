"""
SaaS Admin URL configuration.
All endpoints require superuser (IsAdminUser) permission.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .import_views import list_tenants_and_shops, analyze_csv, import_csv
from .tenant_views import TenantViewSet, ShopViewSet, TenantStatsViewSet
from .user_views import (
    create_tenant_admin,
    list_tenant_users,
    toggle_user_status,
    reset_user_password,
    assign_user_shops,
)

app_name = 'saas_admin'

# Create router for tenant management API
router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'shops', ShopViewSet, basename='shop')
router.register(r'tenant-stats', TenantStatsViewSet, basename='tenant-stats')

urlpatterns = [
    # Tenant Management API (RESTful with ViewSets)
    path('', include(router.urls)),
    
    # CSV Import endpoints
    path('import/tenants/', list_tenants_and_shops, name='import-tenants'),
    path('import/analyze/', analyze_csv, name='import-analyze'),
    path('import/execute/', import_csv, name='import-execute'),
    
    # User Management endpoints
    path('users/create-admin/', create_tenant_admin, name='create-tenant-admin'),
    path('users/', list_tenant_users, name='list-tenant-users'),
    path('users/toggle-status/', toggle_user_status, name='toggle-user-status'),
    path('users/reset-password/', reset_user_password, name='reset-user-password'),
    path('users/assign-shops/', assign_user_shops, name='assign-user-shops'),
]
