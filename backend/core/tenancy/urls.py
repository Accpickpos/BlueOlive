# tenancy/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet, 
    ShopViewSet, 
    current_tenant, 
    tenant_shops, 
    all_shops,
    switch_shop,
    get_accessible_shops,
    get_current_shop
)

router = DefaultRouter()
# Register viewsets with empty prefixes since path() calls set the prefix
router.register(r'', TenantViewSet, basename='tenant')
router.register(r'shops', ShopViewSet, basename='shop')

urlpatterns = [
    # Specific paths MUST come BEFORE the router to avoid being caught as pk
    path('current_tenant/', current_tenant, name='current-tenant'),
    path('tenant_shops/', tenant_shops, name='tenant-shops'),
    path('all_shops/', all_shops, name='all-shops'),
    
    # Shop switching endpoints
    path('switch-shop/', switch_shop, name='switch-shop'),
    path('my-shops/', get_accessible_shops, name='accessible-shops'),
    path('current-shop/', get_current_shop, name='current-shop'),
    
    # Router must come LAST
    path('', include(router.urls)),
]

