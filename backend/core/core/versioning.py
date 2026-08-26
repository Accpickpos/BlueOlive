"""
API versioning utilities for managing multiple API versions.
Supports /api/v1/, /api/v2/, etc. with backward compatibility.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter


class VersionedRouter(DefaultRouter):
    """
    Router that supports API versioning.
    Automatically prefixes routes with version.

    Usage:
        router = VersionedRouter(version='v1')
        router.register('users', UserViewSet)
    """

    def __init__(self, version="v1", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = version

    def get_urls(self):
        """Override to include version in URL patterns."""
        urls = super().get_urls()
        # URLs are already built with version prefix in urls.py
        return urls


class APIVersioning:
    """
    Centralized API versioning configuration.
    Tracks supported versions and handles deprecation.
    """

    CURRENT_VERSION = "v1"
    SUPPORTED_VERSIONS = ["v1"]
    DEPRECATED_VERSIONS = []

    VERSION_CHANGES = {
        "v1": {
            "released": "2026-02-07",
            "description": "Initial API version with core endpoints",
            "endpoints": [
                "/api/v1/tenants/",
                "/api/v1/shops/",
                "/api/v1/users/",
                "/api/v1/debtors/",
                "/api/v1/creditors/",
                "/api/v1/cash-book/",
                "/api/v1/stock-control/",
                "/api/v1/purchase-orders/",
                "/api/v1/pos/",
            ],
        },
    }

    @classmethod
    def is_supported(cls, version):
        """Check if version is supported."""
        return version in cls.SUPPORTED_VERSIONS

    @classmethod
    def is_deprecated(cls, version):
        """Check if version is deprecated."""
        return version in cls.DEPRECATED_VERSIONS

    @classmethod
    def get_version_info(cls, version):
        """Get version information."""
        return cls.VERSION_CHANGES.get(version)

    @classmethod
    def add_version(cls, version, description, endpoints):
        """Register a new API version."""
        cls.SUPPORTED_VERSIONS.append(version)
        cls.VERSION_CHANGES[version] = {
            "released": __import__("datetime").datetime.now().isoformat(),
            "description": description,
            "endpoints": endpoints,
        }


def extract_version(request):
    """
    Extract API version from request.
    Supports multiple strategies:
    - URL path: /api/v1/...
    - Header: X-API-Version: v1
    - Query param: ?api_version=v1

    Returns default version if not specified.
    """
    # Try to get from URL (set by middleware)
    version = getattr(request, "api_version", None)

    # Try header
    if not version:
        version = request.META.get("HTTP_X_API_VERSION")

    # Try query param (use GET instead of query_params to work at middleware level)
    if not version:
        version = request.GET.get("api_version")

    # Default to current version
    if not version:
        version = APIVersioning.CURRENT_VERSION

    return version


class APIVersioningMiddleware:
    """
    Middleware to extract and validate API version from request.
    Sets request.api_version for use in views.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract version from URL path if /api/vX/...
        path_parts = request.path.strip("/").split("/")
        if len(path_parts) >= 2 and path_parts[0] == "api":
            version = path_parts[1]
            # Check if it matches version pattern (v1, v2, etc.)
            if version.startswith("v") and version[1:].isdigit():
                request.api_version = version
                request.path_version = version
            else:
                request.api_version = extract_version(request)
        else:
            request.api_version = extract_version(request)

        response = self.get_response(request)

        # Add version info to response headers
        response["X-API-Version"] = request.api_version

        if APIVersioning.is_deprecated(request.api_version):
            response["X-API-Deprecation-Warning"] = (
                f"API version {request.api_version} is deprecated. "
                f"Please upgrade to {APIVersioning.CURRENT_VERSION}"
            )

        return response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_version_info(request):
    """
    Get information about API versions.
    Endpoint: /api/
    """
    version = extract_version(request)

    return Response(
        {
            "current_version": APIVersioning.CURRENT_VERSION,
            "requested_version": version,
            "supported_versions": APIVersioning.SUPPORTED_VERSIONS,
            "deprecated_versions": APIVersioning.DEPRECATED_VERSIONS,
            "versions": APIVersioning.VERSION_CHANGES,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def version_detail(request, version):
    """
    Get detailed information about a specific API version.
    Endpoint: /api/versions/{version}/
    """
    if not APIVersioning.is_supported(version):
        return Response(
            {"error": f"API version {version} is not supported"}, status=404
        )

    info = APIVersioning.get_version_info(version)
    is_deprecated = APIVersioning.is_deprecated(version)

    return Response(
        {
            "version": version,
            "is_current": version == APIVersioning.CURRENT_VERSION,
            "is_deprecated": is_deprecated,
            "info": info,
        }
    )
