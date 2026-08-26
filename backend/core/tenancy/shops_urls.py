# tenancy/shops_urls.py
# Separate URL configuration for root-level shops endpoint
# This allows /api/v1/shops/ to work correctly without path conflicts

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ShopViewSet

router = DefaultRouter()
router.register(r"", ShopViewSet, basename="shop")

urlpatterns = [
    path("", include(router.urls)),
]
