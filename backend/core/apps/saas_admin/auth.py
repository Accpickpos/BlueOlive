"""
SaaS Admin — Platform Owner Authentication

The actual implementation lives in tenancy.platform_auth (shared with
shop_users.user_management_viewset, which manages Django superuser accounts
- a related but distinct concern). Re-exported here so existing
`from .auth import ...` imports across this app keep working unchanged.
"""

from tenancy.platform_auth import (  # noqa: F401
    ACCESS_COOKIE_NAME,
    PLATFORM_OWNER_CLAIM,
    REFRESH_COOKIE_NAME,
    PlatformOwnerJWTAuthentication,
)
