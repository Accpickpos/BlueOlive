"""
FastAPI middleware for multi-tenant support
Detects tenant from subdomain or headers and sets context
"""
import logging
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import httpx

from tenant_context import set_current_tenant, clear_tenant
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TenantDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect tenant from request and set context
    
    Supports:
    1. Subdomain: acme.localhost -> tenant 'acme'
    2. Header: X-Tenant-Slug or X-Tenant
    3. Path parameter: /api/tenant/{slug}/...
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> any:
        """Process request and detect tenant"""
        tenant_slug = None
        
        # 1. Try to get tenant from X-Tenant header
        tenant_slug = request.headers.get("X-Tenant-Slug") or request.headers.get("X-Tenant")
        
        # 2. Try to get from subdomain
        if not tenant_slug:
            tenant_slug = self._extract_subdomain(request)
        
        # 3. Try to get from path parameter
        if not tenant_slug:
            tenant_slug = self._extract_from_path(request)
        
        # 4. Try to get from query parameter
        if not tenant_slug:
            tenant_slug = request.query_params.get("tenant")
        
        # If we found a tenant, validate it exists and set context
        if tenant_slug:
            logger.info(f"Detected tenant: {tenant_slug}")
            
            # Validate tenant exists in Django backend
            if await self._validate_tenant(tenant_slug):
                set_current_tenant(tenant_slug)
            else:
                clear_tenant()
                return JSONResponse(
                    status_code=404,
                    content={"detail": f"Tenant '{tenant_slug}' not found"}
                )
        else:
            logger.warning("No tenant detected in request")
            clear_tenant()
        
        try:
            response = await call_next(request)
        finally:
            # Clear tenant context after request
            clear_tenant()
        
        return response
    
    @staticmethod
    def _extract_subdomain(request: Request) -> str:
        """Extract subdomain from host header"""
        host = request.headers.get("host", "")
        
        # Remove port if present
        if ":" in host:
            host = host.split(":")[0]
        
        # Extract subdomain
        parts = host.split(".")
        
        # Localhost patterns: acme.localhost, shop.acme.localhost
        if "localhost" in host or "127.0.0.1" in host:
            if len(parts) >= 2 and parts[-1] == "localhost":
                # Could be: acme.localhost OR shop.acme.localhost
                if len(parts) == 2:
                    # acme.localhost
                    return parts[0]
                elif len(parts) == 3:
                    # shop.acme.localhost -> use 'acme' as tenant
                    return parts[1]
        
        # Production pattern: subdomain.yourdomain.com
        if len(parts) >= 3:
            return parts[0]
        
        return None
    
    @staticmethod
    def _extract_from_path(request: Request) -> str:
        """Extract tenant from path like /tenant/{slug}/api/..."""
        path_parts = request.url.path.split("/")
        
        # Look for /tenant/{slug}/ pattern
        try:
            if len(path_parts) > 2 and path_parts[1] == "tenant":
                return path_parts[2]
        except (IndexError, ValueError):
            pass
        
        return None
    
    @staticmethod
    async def _validate_tenant(tenant_slug: str) -> bool:
        """Validate tenant exists by calling Django backend"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                # Call Django backend to validate tenant
                response = await client.get(
                    f"{settings.drf_base_url.rstrip('/api')}/api/current_tenant/",
                    headers={"X-Tenant": tenant_slug},
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    logger.info(f"Tenant {tenant_slug} validated with Django backend")
                    return True
                else:
                    logger.warning(f"Tenant {tenant_slug} validation failed: {response.status_code}")
                    return False
        
        except Exception as e:
            logger.warning(f"Error validating tenant {tenant_slug}: {str(e)}")
            # Continue even if validation fails (Django might be down)
            # In production, you might want to fail here
            return True


def add_tenant_middleware(app):
    """Add tenant detection middleware to FastAPI app"""
    app.add_middleware(TenantDetectionMiddleware)
    logger.info("Added TenantDetectionMiddleware to application")
