"""
Tenant context management for FastAPI
Handles detection and storage of current tenant for schema routing
"""
from typing import Optional
from contextvars import ContextVar
import logging

logger = logging.getLogger(__name__)

# Context variable to store current tenant
_tenant_context: ContextVar[Optional[str]] = ContextVar("tenant", default=None)


class TenantContext:
    """Manager for current tenant context"""
    
    @staticmethod
    def set_tenant(tenant_slug: str) -> None:
        """Set the current tenant"""
        logger.info(f"Setting tenant context to: {tenant_slug}")
        _tenant_context.set(tenant_slug)
    
    @staticmethod
    def get_tenant() -> Optional[str]:
        """Get the current tenant"""
        return _tenant_context.get()
    
    @staticmethod
    def clear_tenant() -> None:
        """Clear the current tenant"""
        _tenant_context.set(None)
    
    @staticmethod
    def is_tenant_set() -> bool:
        """Check if tenant is set"""
        return _tenant_context.get() is not None


def get_current_tenant() -> Optional[str]:
    """Get current tenant slug"""
    return TenantContext.get_tenant()


def set_current_tenant(tenant_slug: str) -> None:
    """Set current tenant slug"""
    TenantContext.set_tenant(tenant_slug)
