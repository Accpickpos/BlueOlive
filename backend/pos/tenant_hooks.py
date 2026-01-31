"""
Integration module for tenant creation
This module provides hooks to be called when tenants are created/updated/deleted
"""
import logging
from typing import Optional

from schema_migrations import (
    TenantSchemaManager,
    create_shop_with_schema,
    sync_tenant_schema
)

logger = logging.getLogger(__name__)


class TenantLifecycleHooks:
    """Handles tenant lifecycle events"""
    
    @staticmethod
    async def on_tenant_created(tenant_slug: str, tenant_name: str = None) -> dict:
        """
        Called when a new tenant is created in Django
        
        Args:
            tenant_slug: Unique identifier for tenant
            tenant_name: Display name for tenant
            
        Returns:
            dict: Creation status
        """
        logger.info(f"Creating POS schema for new tenant: {tenant_slug}")
        
        result = create_shop_with_schema(tenant_slug)
        
        if result["success"]:
            logger.info(f"POS schema created for tenant: {tenant_slug}")
        else:
            logger.error(f"Failed to create POS schema for tenant {tenant_slug}: {result['messages']}")
        
        return result
    
    @staticmethod
    async def on_tenant_updated(tenant_slug: str) -> dict:
        """
        Called when a tenant is updated
        
        Args:
            tenant_slug: Tenant identifier
            
        Returns:
            dict: Update status
        """
        logger.info(f"Syncing POS schema for tenant: {tenant_slug}")
        
        result = sync_tenant_schema(tenant_slug)
        
        if result["success"]:
            logger.info(f"POS schema synced for tenant: {tenant_slug}")
        else:
            logger.error(f"Failed to sync POS schema for tenant {tenant_slug}: {result['messages']}")
        
        return result
    
    @staticmethod
    async def on_tenant_deleted(tenant_slug: str) -> dict:
        """
        Called when a tenant is deleted
        
        Args:
            tenant_slug: Tenant identifier
            
        Returns:
            dict: Deletion status
        """
        logger.warning(f"Deleting POS schema for tenant: {tenant_slug}")
        
        result = {
            "success": False,
            "messages": [],
            "tenant_slug": tenant_slug,
        }
        
        # Optional: Backup before deletion
        schema_name = TenantSchemaManager.get_tenant_schema_name(tenant_slug)
        
        if TenantSchemaManager.backup_tenant_schema(tenant_slug, "pre_deletion"):
            result["messages"].append(f"Backup created as {schema_name}_backup_pre_deletion")
        
        # Delete schema
        if TenantSchemaManager.delete_tenant_schema(tenant_slug):
            result["success"] = True
            result["messages"].append(f"Schema {schema_name} deleted successfully")
        else:
            result["messages"].append(f"Failed to delete schema {schema_name}")
        
        return result
    
    @staticmethod
    def get_tenant_status(tenant_slug: str) -> dict:
        """
        Get current status of tenant's POS schema
        
        Args:
            tenant_slug: Tenant identifier
            
        Returns:
            dict: Tenant status information
        """
        schema_name = TenantSchemaManager.get_tenant_schema_name(tenant_slug)
        
        result = {
            "tenant_slug": tenant_slug,
            "schema_name": schema_name,
            "schema_exists": False,
            "tables": [],
            "error": None
        }
        
        try:
            from sqlalchemy import inspect, create_engine
            from config import get_settings
            
            engine = create_engine(get_settings().database_url)
            inspector = inspect(engine)
            
            # Check if schema exists
            schemas = inspector.get_schema_names()
            result["schema_exists"] = schema_name in schemas
            
            # Get tables if schema exists
            if result["schema_exists"]:
                tables = inspector.get_table_names(schema=schema_name)
                result["tables"] = tables
            
        except Exception as e:
            result["error"] = str(e)
        
        return result


# For use in admin_tenants router
async def handle_tenant_creation(tenant_data: dict) -> dict:
    """
    Handle tenant creation with POS schema
    
    Called from admin_tenants router after tenant is created in Django
    
    Args:
        tenant_data: Tenant information from Django
        
    Returns:
        dict: Creation result
    """
    tenant_slug = tenant_data.get("slug")
    tenant_name = tenant_data.get("name")
    
    return await TenantLifecycleHooks.on_tenant_created(tenant_slug, tenant_name)


async def handle_tenant_deletion(tenant_slug: str) -> dict:
    """
    Handle tenant deletion with POS schema cleanup
    
    Called from admin_tenants router before tenant is deleted in Django
    
    Args:
        tenant_slug: Tenant identifier
        
    Returns:
        dict: Deletion result
    """
    return await TenantLifecycleHooks.on_tenant_deleted(tenant_slug)
