"""
Shared throttle classes for cheap, non-sensitive public endpoints.

DEFAULT_THROTTLE_CLASSES (AnonRateThrottle/UserRateThrottle) put every
anonymous request — CSRF token fetch, subscription plan listing, login
attempts, signup — into one shared 100/hour-per-IP bucket unless a view
opts into its own scope. LoginThrottle (shop_users/views.py) already
carves login out into its own tight scope to stop brute force. This does
the same for read-only, no-side-effect public endpoints that have nothing
to do with account security, so normal page-load traffic on /auth doesn't
exhaust the same quota a brute-force guard is meant to protect.
"""
from rest_framework.throttling import AnonRateThrottle


class PublicReadThrottle(AnonRateThrottle):
    """For public, read-only, non-sensitive endpoints (subscription plan
    listing, CSRF token fetch). Generous rate — these carry no abuse risk
    beyond normal DB read load, so they shouldn't share a quota with
    security-sensitive actions."""
    scope = 'public_read'
    rate = '120/min'
