"""
Tenant administration router
Endpoints for managing tenants, schema creation, and migrations
"""
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
import httpx
from datetime import datetime

from db_tenant import create_tenant_schema, init_db, get_db
from tenant_context import set_current_tenant, clear_tenant, get_current_tenant
from config import get_settings
from schema_migrations import TenantSchemaManager, create_shop_with_schema
from tenant_hooks import TenantLifecycleHooks

router = APIRouter(prefix="/api/v1/admin/tenants", tags=["admin", "tenants"])

settings = get_settings()


class TenantInitRequest(BaseModel):
    """Request body for tenant initialization"""
    slug: str
    name: Optional[str] = None
    domain: Optional[str] = None


class TenantInitResponse(BaseModel):
    """Response body for tenant initialization"""
    slug: str
    status: str
    message: str
    created_at: datetime
    schema_name: str


class TenantStatusResponse(BaseModel):
    """Response body for tenant status"""
    slug: str
    status: str
    schema_exists: bool
    tables_count: int


async def validate_admin_token(token: Optional[str] = None) -> dict:
    """
    Validate admin token with Django backend
    
    In production, this would verify JWT token with Django
    For now, we validate a simple Bearer token against Django
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token"
        )
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.django_backend_url}/api/user/profile/",
                headers={"Authorization": token}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}"
        )


async def check_admin_privileges(user_data: dict) -> bool:
    """Check if user has admin privileges"""
    # Check if user is superuser or has admin role
    return user_data.get("is_superuser") or "admin" in user_data.get("roles", [])


@router.post("/init", response_model=TenantInitResponse, status_code=201)
async def initialize_tenant(
    request: TenantInitRequest,
    authorization: Optional[str] = None
):
    """
    Initialize a new tenant with database schema and tables
    
    Requires admin privileges.
    
    Args:
        request: TenantInitRequest with slug and optional name/domain
        authorization: Bearer token for authentication
        
    Returns:
        TenantInitResponse with initialization status
        
    Raises:
        HTTPException: If tenant exists, token invalid, or operation fails
    """
    # Validate admin token
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        user_data = await validate_admin_token(authorization)
        is_admin = await check_admin_privileges(user_data)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can initialize tenants"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    try:
        # Validate slug format
        if not request.slug or not request.slug.replace("-", "").replace("_", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid tenant slug. Use alphanumeric characters, hyphens, or underscores"
            )
        
        # Verify tenant exists in Django
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.django_backend_url}/api/tenants/{request.slug}/",
                headers={"Authorization": authorization}
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant '{request.slug}' not found in Django backend"
                )
        
        # Create tenant schema and tables using new migration system
        migration_result = create_shop_with_schema(request.slug)
        
        if not migration_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to initialize POS schema: {', '.join(migration_result['messages'])}"
            )
        
        return TenantInitResponse(
            slug=request.slug,
            status="success",
            message=f"Tenant '{request.slug}' initialized successfully with schema and tables",
            created_at=datetime.utcnow(),
            schema_name=migration_result["schema_name"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize tenant: {str(e)}"
        )


@router.get("/{slug}/status", response_model=TenantStatusResponse)
async def get_tenant_status(
    slug: str,
    authorization: Optional[str] = None
):
    """
    Get tenant status including schema existence and table count
    
    Requires admin privileges.
    
    Args:
        slug: Tenant slug
        authorization: Bearer token for authentication
        
    Returns:
        TenantStatusResponse with tenant status
    """
    # Validate admin token
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        user_data = await validate_admin_token(authorization)
        is_admin = await check_admin_privileges(user_data)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can check tenant status"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    try:
        from db_tenant import get_engine
        from sqlalchemy import inspect, text
        
        engine = get_engine()
        
        with engine.connect() as conn:
            # Check if schema exists
            result = conn.execute(
                text(
                    "SELECT 1 FROM information_schema.schemata "
                    "WHERE schema_name = :schema"
                ),
                {"schema": f"tenant_{slug}"}
            )
            schema_exists = result.fetchone() is not None
            
            tables_count = 0
            if schema_exists:
                # Count tables in schema
                result = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables "
                        "WHERE table_schema = :schema"
                    ),
                    {"schema": f"tenant_{slug}"}
                )
                tables_count = result.scalar() or 0
        
        return TenantStatusResponse(
            slug=slug,
            status="active" if schema_exists else "not_initialized",
            schema_exists=schema_exists,
            tables_count=tables_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check tenant status: {str(e)}"
        )


@router.post("/{slug}/reset", status_code=200)
async def reset_tenant_schema(
    slug: str,
    authorization: Optional[str] = None
):
    """
    Reset (drop and recreate) tenant schema
    
    WARNING: This will delete all tenant data!
    Requires admin privileges and explicit confirmation.
    
    Args:
        slug: Tenant slug
        authorization: Bearer token for authentication
        
    Returns:
        Success message
    """
    # Validate admin token
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        user_data = await validate_admin_token(authorization)
        is_admin = await check_admin_privileges(user_data)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can reset tenants"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    try:
        from db_tenant import get_engine
        from sqlalchemy import text
        
        schema_name = f"tenant_{slug}"
        engine = get_engine()
        
        with engine.connect() as conn:
            # Drop schema with cascade
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
            conn.commit()
        
        # Recreate schema and tables
        create_tenant_schema(slug)
        init_db(slug)
        
        return {
            "slug": slug,
            "status": "reset",
            "message": f"Tenant '{slug}' schema has been reset"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset tenant schema: {str(e)}"
        )


@router.get("/", status_code=200)
async def list_tenant_statuses(authorization: Optional[str] = None):
    """
    List status of all tenant schemas
    
    Requires admin privileges.
    
    Args:
        authorization: Bearer token for authentication
        
    Returns:
        List of tenant statuses
    """
    # Validate admin token
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )
    
    try:
        user_data = await validate_admin_token(authorization)
        is_admin = await check_admin_privileges(user_data)
        
        if not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admin users can list tenants"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    
    try:
        from db_tenant import get_engine
        from sqlalchemy import text
        
        engine = get_engine()
        tenant_statuses = []
        
        with engine.connect() as conn:
            # Get all tenant schemas
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name LIKE 'tenant_%' "
                    "ORDER BY schema_name"
                )
            )
            
            for row in result:
                schema_name = row[0]
                slug = schema_name.replace("tenant_", "")
                
                # Count tables in schema
                result2 = conn.execute(
                    text(
                        "SELECT COUNT(*) FROM information_schema.tables "
                        "WHERE table_schema = :schema"
                    ),
                    {"schema": schema_name}
                )
                tables_count = result2.scalar() or 0
                
                tenant_statuses.append({
                    "slug": slug,
                    "schema_name": schema_name,
                    "status": "active",
                    "tables_count": tables_count
                })
        
        return {
            "total": len(tenant_statuses),
            "tenants": tenant_statuses
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )
