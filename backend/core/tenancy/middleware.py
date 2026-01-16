# tenancy/middleware.py
import logging
from django.http import HttpResponseForbidden
from django.db import connections
from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current
from tenancy.models import Tenant, Shop

logger = logging.getLogger(__name__)

class TenantMiddleware:
    """
    1) Identify tenant from request (subdomain / header / api key)
    2) Set thread-local tenant
    3) Ensure tenant connection is registered in settings.connections (register dynamically if missing)
    4) Optionally set shop schema based on request (header or URL)
    5) Set search_path for the tenant DB connection to the requested schema
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow public endpoints without tenant check
        public_paths = ['/admin', '/favicon.ico', '/api/tenants/', '/api/current_tenant/']
        if (request.path == '/' or any(request.path.startswith(path) for path in public_paths)) and not request.path.startswith('/api/login/'):
            logger.debug(f"Skipping tenant middleware for public path: {request.path}")
            response = self.get_response(request)
            clear_current()
            return response

        # Log tenant setting for login requests
        if request.path.startswith('/api/login/'):
            logger.info(f"Processing login request for path: {request.path}, host: {request.get_host()}")

        host = request.get_host().split(":")[0]
        # Example: tenant is subdomain
        # extract subdomain e.g. tenant1.example.com -> tenant1
        # Also support localhost: tenant.localhost -> tenant
        parts = host.split(".")
        if len(parts) > 2:
            subdomain = parts[0]
        elif len(parts) == 2 and parts[1] == "localhost":
            subdomain = parts[0]
        else:
            subdomain = None

        # Or use header: X-Tenant or Authorization token
        tenant_key = request.headers.get("X-Tenant") or subdomain
        if not tenant_key:
            # If you allow public endpoints, skip; else block
            logger.warning(f"No tenant specified for path: {request.path}")
            return HttpResponseForbidden("Tenant not specified")

        tenant = None
        try:
            tenant = Tenant.objects.get(subdomain=tenant_key)
            logger.info(f"Resolved tenant: {tenant.name} for subdomain: {tenant_key}")
        except Tenant.DoesNotExist:
            logger.warning(f"Invalid subdomain: {tenant_key}")
            return HttpResponseForbidden("Invalid subdomain")

        # register tenant in thread-local
        set_current_tenant(tenant)
        logger.info(f"Set current tenant: {tenant.name} (id={tenant.id}) for request path: {request.path}")

        # Ensure connections registered (register_tenant_connection may be called on creation)
        from tenancy.utils import register_tenant_connection
        register_tenant_connection(tenant)

        # Determine shop schema: from user, header, or default
        shop_schema = None
        if hasattr(request, 'user') and request.user.is_authenticated and request.user.shop:
            # Use user's assigned shop
            shop_schema = request.user.shop.schema_name
        if not shop_schema:
            shop_schema = request.headers.get("X-Shop-Schema")  # e.g. 'shop_123'
        if not shop_schema:
            # Fallback to head office shop schema
            try:
                head_office = tenant.shops.get(is_head_office=True)
                shop_schema = head_office.schema_name
            except Shop.DoesNotExist:
                shop_schema = "public"  # fallback if no head office
        set_current_shop(shop_schema)
        logger.info(f"Set current shop schema: {shop_schema} for request path: {request.path}")

        # Set search_path for this tenant DB connection immediately
        alias = tenant.db_alias
        conn = connections[alias]
        # If connection isn't established yet, Django will connect on first use;
        # but we can force a cursor and set search_path now.
        with conn.cursor() as cur:
            cur.execute(f'SET search_path TO "{shop_schema}", public;')

        response = self.get_response(request)
        clear_current()
        return response
