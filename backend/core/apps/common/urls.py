from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AccessGrantViewSet

router = DefaultRouter()
router.register(r"access-grants", AccessGrantViewSet, basename="access-grant")

app_name = "common"

urlpatterns = [
    path("", include(router.urls)),
]
