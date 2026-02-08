# shop_users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ShopUserViewSet, ProfileView, TenantTokenView, LogoutView, GetCSRFTokenView, UnifiedLoginView, SignupView, CookieTokenRefreshView
from .user_management_viewset import UserManagementViewSet

router = DefaultRouter()
router.register(r'users', ShopUserViewSet, basename='shopuser')
router.register(r'admin/superusers', UserManagementViewSet, basename='superuser')

urlpatterns = [
    path('', include(router.urls)),
    # Authentication endpoints
    path('auth/csrf/', GetCSRFTokenView.as_view(), name='csrf_token'),
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('auth/login/', TenantTokenView.as_view(), name='token_obtain_pair'),
    path('auth/unified-login/', UnifiedLoginView.as_view(), name='unified_login'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('auth/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', ProfileView.as_view(), name='profile'),
]