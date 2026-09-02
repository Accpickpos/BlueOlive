"""
Platform Owner Authentication

Completely separate cookie/token namespace from tenant authentication
(tenancy.jwt_authentication.TenantJWTAuthentication), by design:

- Tenant auth reads `access_token`/`refresh_token` cookies and always looks
  the user up in a *tenant* database (tenant.db_alias) — see
  TenantJWTAuthentication.get_user(). A platform superuser's ShopUser row
  lives only in the `default` database (see ShopUserBackend.authenticate,
  Strategy 1), so that lookup never finds them: superuser sessions issued by
  the tenant login views authenticate once, then fail on every subsequent
  request. Platform-owner auth never touches a tenant database at all.
- Using distinct cookie names (`po_access_token`/`po_refresh_token`) and a
  distinct token claim (`is_platform_owner`) means a tenant user's session
  can never be mistaken for a platform-owner session, and vice versa — the
  two can even be logged in simultaneously in the same browser without
  colliding.

Lives in `tenancy` (rather than `apps.saas_admin`, the only app that used to
own it) because `shop_users.user_management_viewset` — which manages Django
superuser accounts, a related but distinct concern from tenant management —
needs it too, and both `apps.saas_admin` and `shop_users` already depend on
`tenancy`. Putting it here avoids `shop_users` reaching into an app-level
package.
"""

import logging

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from shop_users.models import ShopUser

logger = logging.getLogger(__name__)

ACCESS_COOKIE_NAME = "po_access_token"
REFRESH_COOKIE_NAME = "po_refresh_token"
PLATFORM_OWNER_CLAIM = "is_platform_owner"


class PlatformOwnerJWTAuthentication(BaseAuthentication):
    """
    Authenticates requests using the platform-owner-only JWT cookie.
    Only ever resolves users from the `default` database, and only ever
    accepts users with is_superuser=True.
    """

    SAFE_METHODS = ("GET", "HEAD", "OPTIONS")

    def authenticate(self, request):
        raw_token = request.COOKIES.get(ACCESS_COOKIE_NAME)
        if not raw_token:
            return None

        try:
            validated_token = AccessToken(raw_token)
        except Exception:
            # Invalid/expired token - treat as anonymous, let permission
            # classes reject rather than raising here.
            return None

        if not validated_token.get(PLATFORM_OWNER_CLAIM):
            return None

        if not self._validate_csrf(request):
            raise AuthenticationFailed("CSRF validation failed")

        user_id = validated_token.get("user_id")
        try:
            user = ShopUser.objects.using("default").get(id=user_id, is_superuser=True)
        except ShopUser.DoesNotExist:
            raise AuthenticationFailed("Platform owner account not found")

        if not user.is_active:
            raise AuthenticationFailed("Account is inactive")

        return (user, validated_token)

    def _validate_csrf(self, request):
        if request.method in self.SAFE_METHODS:
            return True

        csrf_token = request.headers.get("X-CSRFToken") or request.COOKIES.get(
            "csrftoken"
        )
        expected_csrf = request.META.get("CSRF_COOKIE") or request.COOKIES.get(
            "csrftoken"
        )

        if not csrf_token or not expected_csrf:
            logger.warning("Platform owner request missing CSRF token")
            return False

        return self._constant_time_compare(csrf_token, expected_csrf)

    @staticmethod
    def _constant_time_compare(val1, val2):
        val1 = val1.encode("utf-8") if isinstance(val1, str) else val1
        val2 = val2.encode("utf-8") if isinstance(val2, str) else val2
        if len(val1) != len(val2):
            return False
        result = 0
        for c1, c2 in zip(val1, val2):
            result |= c1 ^ c2
        return result == 0
