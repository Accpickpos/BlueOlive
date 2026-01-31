"""
FastAPI Point of Sale System
Main application entry point with Multi-Tenant Support
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from db_tenant import init_db, get_engine
from middleware import add_tenant_middleware
from schema_migrations import TenantSchemaManager

# Import all routers
from routers import invoices, cash_sales, credit_notes, receipts, cash_returns
from routers import laybyes, quotations, job_costing, repair_controls
from routers import payouts, cash_control, transaction_query, admin_tenants

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Initializing FastAPI POS System with Multi-Tenant Support...")
    
    # Initialize public schema (for shared tables)
    init_db()
    logger.info("Public schema initialized")
    
    # Initialize schema migrations utilities
    logger.info("Schema migration system ready for tenant initialization")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI POS System...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Point of Sale System with Multi-Tenant Support and Django DRF Integration",
    version=settings.app_version,
    lifespan=lifespan
)

# Add tenant detection middleware FIRST (before CORS)
add_tenant_middleware(app)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(invoices.router)
app.include_router(cash_sales.router)
app.include_router(credit_notes.router)
app.include_router(receipts.router)
app.include_router(cash_returns.router)
app.include_router(laybyes.router)
app.include_router(quotations.router)
app.include_router(job_costing.router)
app.include_router(repair_controls.router)
app.include_router(payouts.router)
app.include_router(cash_control.router)
app.include_router(transaction_query.router)
app.include_router(admin_tenants.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "endpoints": {
            "invoices": "/api/v1/invoices",
            "cash_sales": "/api/v1/cash-sales",
            "credit_notes": "/api/v1/credit-notes",
            "receipts": "/api/v1/receipts",
            "cash_returns": "/api/v1/cash-returns",
            "laybyes": "/api/v1/laybyes",
            "quotations": "/api/v1/quotations",
            "job_costing": "/api/v1/job-costing",
            "repair_controls": "/api/v1/repair-controls",
            "payouts": "/api/v1/payouts",
            "cash_control": "/api/v1/cash-control",
            "transaction_query": "/api/v1/transaction-query",
        }
    }


@app.get("/config")
async def get_config():
    """Get application configuration"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
        "drf_backend": settings.drf_base_url,
        "cors_origins": settings.allowed_origins,
    }


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.app_name} on {settings.fastapi_host}:{settings.fastapi_port}")
    uvicorn.run(
        "main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
