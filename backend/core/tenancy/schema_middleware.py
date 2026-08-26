# tenancy/schema_middleware.py
"""
Middleware to set PostgreSQL search_path based on shop context.

When a shop is identified, this middleware sets the PostgreSQL search_path
to include the shop's schema. This allows Django ORM queries to find tables
in the shop-specific schema without explicit schema qualification.

Example:
- Shop "Downtown" has schema "volt_gray"
- Middleware sets: SET search_path TO volt_gray, public
- Django queries now look in volt_gray first, then public
"""

import logging

from django.db import connections
from tenancy.tenant_context import get_current_shop, get_current_tenant

logger = logging.getLogger(__name__)


class SchemaMiddleware:
    """
    Sets PostgreSQL search_path based on current shop context.

    Place this AFTER TenantMiddleware in MIDDLEWARE.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Get current shop from context set by TenantMiddleware
            shop_schema = get_current_shop()
            tenant = get_current_tenant()

            # DEBUG: Log what we found
            logger.debug(
                f"[SchemaMiddleware] shop_schema={shop_schema}, tenant={tenant.name if tenant else None}"
            )

            if shop_schema and tenant:
                # Get the tenant database connection
                db_alias = tenant.db_alias

                # DEBUG: Log the database configuration
                logger.debug(
                    f"[SchemaMiddleware] db_alias={db_alias}, available dbs={list(connections.databases.keys())}"
                )

                # Set the search_path to include shop schema
                try:
                    conn = connections[db_alias]
                    logger.debug(
                        f"[SchemaMiddleware] Connection found: {conn.settings_dict.get('NAME')}"
                    )
                    with conn.cursor() as cursor:
                        # Set search_path: shop schema first, then public schema
                        cursor.execute(f"SET search_path TO {shop_schema}, public")
                        logger.debug(f"Set search_path to: {shop_schema}, public")
                except Exception as e:
                    logger.warning(f"Failed to set search_path: {str(e)}")
                    logger.debug(
                        f"[SchemaMiddleware] Available database aliases: {list(connections.databases.keys())}"
                    )
            else:
                # DEBUG: Log why we're not setting search_path
                if not shop_schema:
                    logger.debug(
                        "[SchemaMiddleware] No shop_schema in context - search_path not set"
                    )
                if not tenant:
                    logger.debug(
                        "[SchemaMiddleware] No tenant in context - search_path not set"
                    )

        except Exception as e:
            logger.error(f"Error in schema middleware: {str(e)}")

        # Process request
        response = self.get_response(request)

        return response
