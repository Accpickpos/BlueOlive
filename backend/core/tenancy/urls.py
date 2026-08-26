# tenancy/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ShopConfigurationViewSet,
    ShopViewSet,
    SubscriptionPaymentViewSet,
    SubscriptionPlanViewSet,
    SubscriptionViewSet,
    TenantViewSet,
    all_shops,
    current_tenant,
    get_accessible_shops,
    get_current_shop,
    switch_shop,
    tenant_shops,
)

router = DefaultRouter()
# Register viewsets with empty prefixes since path() calls set the prefix
router.register(r"", TenantViewSet, basename="tenant")
router.register(r"shops", ShopViewSet, basename="shop")
router.register(r"shop-config", ShopConfigurationViewSet, basename="shop-config")

# Subscription routes
subscription_router = DefaultRouter()
subscription_router.register(
    r"plans", SubscriptionPlanViewSet, basename="subscription-plan"
)
subscription_router.register(
    r"subscriptions", SubscriptionViewSet, basename="subscription"
)
subscription_router.register(
    r"payments", SubscriptionPaymentViewSet, basename="subscription-payment"
)

urlpatterns = [
    # Specific paths MUST come BEFORE the router to avoid being caught as pk
    path("current_tenant/", current_tenant, name="current-tenant"),
    path("tenant_shops/", tenant_shops, name="tenant-shops"),
    path("all_shops/", all_shops, name="all-shops"),
    # Shop switching endpoints
    path("switch-shop/", switch_shop, name="switch-shop"),
    path("my-shops/", get_accessible_shops, name="accessible-shops"),
    path("current-shop/", get_current_shop, name="current-shop"),
    # Subscription endpoints
    path("subscription/", include(subscription_router.urls)),
    # Router must come LAST
    path("", include(router.urls)),
]
