# shop_users/shops_urls.py
# Separate URL configuration for root-level users endpoint
# This allows /api/v1/users/ to work correctly at the root level

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ShopUserViewSet

router = DefaultRouter()
router.register(r'', ShopUserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
