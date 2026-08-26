# shop_users/urls.py
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .user_management_viewset import UserManagementViewSet
from .views import (
    CookieTokenRefreshView,
    GetCSRFTokenView,
    LogoutView,
    ProfileView,
    ShopUserViewSet,
    SignupView,
    SubdomainValidationView,
    TenantTokenView,
    UnifiedLoginView,
)

router = DefaultRouter()
router.register(r"users", ShopUserViewSet, basename="shopuser")
router.register(r"admin/superusers", UserManagementViewSet, basename="superuser")

urlpatterns = [
    path("", include(router.urls)),
    # Authentication endpoints (already under /api/v1/users/auth/ in main urls.py)
    path("csrf/", GetCSRFTokenView.as_view(), name="csrf_token"),
    path("signup/", SignupView.as_view(), name="signup"),
    path(
        "signup/validate-subdomain/",
        SubdomainValidationView.as_view(),
        name="validate_subdomain",
    ),
    path("login/", TenantTokenView.as_view(), name="token_obtain_pair"),
    path("unified-login/", UnifiedLoginView.as_view(), name="unified_login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
]
