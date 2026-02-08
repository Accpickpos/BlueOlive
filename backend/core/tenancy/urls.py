# tenancy/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, ShopViewSet, current_tenant, tenant_shops, all_shops

router = DefaultRouter()
# Register viewsets with empty prefixes since path() calls set the prefix
router.register(r'', TenantViewSet, basename='tenant')
router.register(r'shops', ShopViewSet, basename='shop')

urlpatterns = [
    path('', include(router.urls)),
    path('current_tenant/', current_tenant, name='current-tenant'),
    path('tenant_shops/', tenant_shops, name='tenant-shops'),
    path('all_shops/', all_shops, name='all-shops'),
]

