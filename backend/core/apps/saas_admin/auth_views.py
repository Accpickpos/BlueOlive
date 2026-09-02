"""
SaaS Admin — Platform Owner Authentication Views

Login/logout/profile/refresh for platform superusers only. Deliberately
independent of the tenant login flow (shop_users.views.TenantTokenView) —
see auth.py module docstring for why. No tenant_slug/subdomain is ever
required or accepted here.
"""

import logging

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from shop_users.models import ShopUser

from .auth import (
    ACCESS_COOKIE_NAME,
    PLATFORM_OWNER_CLAIM,
    REFRESH_COOKIE_NAME,
    PlatformOwnerJWTAuthentication,
)
from .permissions import IsPlatformSuperuser

logger = logging.getLogger(__name__)


class PlatformLoginThrottle(AnonRateThrottle):
    scope = "login"


def _issue_tokens(user):
    refresh = RefreshToken()
    refresh["user_id"] = user.id
    refresh["username"] = user.username
    refresh[PLATFORM_OWNER_CLAIM] = True
    access = refresh.access_token
    access[PLATFORM_OWNER_CLAIM] = True
    return str(access), str(refresh)


def _set_auth_cookies(response, access_token, refresh_token):
    is_secure = not settings.DEBUG
    samesite = "Lax" if settings.DEBUG else "None"

    response.set_cookie(
        key=ACCESS_COOKIE_NAME,
        value=access_token,
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        secure=is_secure,
        httponly=True,
        samesite=samesite,
        path="/",
    )
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        secure=is_secure,
        httponly=True,
        samesite=samesite,
        path="/",
    )


class PlatformLoginView(APIView):
    """
    POST /api/v1/saas-admin/auth/login/
    { "username": "...", "password": "..." }

    Authenticates only against ShopUser rows in the `default` database with
    is_superuser=True. No tenant/subdomain involved.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [PlatformLoginThrottle]

    @method_decorator(csrf_exempt)
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"detail": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = ShopUser.objects.using("default").get(
                username=username, is_superuser=True
            )
        except ShopUser.DoesNotExist:
            # Dummy password hash for timing-attack resistance, matching the
            # pattern used by ShopUserBackend._perform_dummy_password_check.
            ShopUser().set_password(password)
            logger.warning(f"Platform login failed: unknown username {username}")
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.check_password(password) or not user.is_active:
            logger.warning(f"Platform login failed for {username}")
            return Response(
                {"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        access_token, refresh_token = _issue_tokens(user)

        response = Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_superuser": True,
                }
            }
        )
        _set_auth_cookies(response, access_token, refresh_token)

        logger.info(f"Platform owner login: {username}")
        return response


class PlatformLogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt)
    def post(self, request):
        response = Response({"detail": "Logged out"})
        response.delete_cookie(ACCESS_COOKIE_NAME, path="/")
        response.delete_cookie(REFRESH_COOKIE_NAME, path="/")
        return response


class PlatformTokenRefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @method_decorator(csrf_exempt)
    def post(self, request):
        raw_refresh = request.COOKIES.get(REFRESH_COOKIE_NAME)
        if not raw_refresh:
            return Response(
                {"detail": "No refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            refresh = RefreshToken(raw_refresh)
        except TokenError:
            return Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not refresh.get(PLATFORM_OWNER_CLAIM):
            return Response(
                {"detail": "Invalid refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user_id = refresh.get("user_id")
        try:
            ShopUser.objects.using("default").get(
                id=user_id, is_superuser=True, is_active=True
            )
        except ShopUser.DoesNotExist:
            return Response(
                {"detail": "Account no longer valid"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access = refresh.access_token
        access[PLATFORM_OWNER_CLAIM] = True

        response = Response({"detail": "Token refreshed"})
        is_secure = not settings.DEBUG
        samesite = "Lax" if settings.DEBUG else "None"
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=str(access),
            max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
            secure=is_secure,
            httponly=True,
            samesite=samesite,
            path="/",
        )
        return response


class PlatformProfileView(APIView):
    """GET /api/v1/saas-admin/auth/profile/"""

    authentication_classes = [PlatformOwnerJWTAuthentication]
    permission_classes = [IsPlatformSuperuser]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_superuser": True,
            }
        )
