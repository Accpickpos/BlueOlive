"""
Multi-tenant database utilities for FastAPI
Handles schema routing and dynamic database connections per tenant
"""
import logging
from typing import Optional, Generator
from sqlalchemy import text, event, pool
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool

from config import get_settings
from tenant_context import get_current_tenant

logger = logging.getLogger(__name__)

settings = get_settings()

# Base declarative for ORM models
Base = declarative_base()

# Cache for schema names - stores tenant_slug -> schema_name mappings
_schema_cache = {}

# Engine (created once, reused)
_engine = None


def get_engine() -> Engine:
    """Get or create the main database engine"""
    global _engine
    
    if _engine is None:
        # Create engine with connection pooling
        _engine = create_engine(
            settings.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=settings.debug,
        )
        
        # Add event listener to set schema on each connection
        @event.listens_for(Engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Set schema on connection based on current tenant"""
            tenant = get_current_tenant()
            if tenant:
                schema_name = get_tenant_schema_name(tenant)
                dbapi_conn.execute(f"SET search_path TO {schema_name}")
                logger.debug(f"Schema set to: {schema_name}")
    
    return _engine


def create_engine(database_url: str, **kwargs):
    """Create SQLAlchemy engine with multi-tenant support"""
    from sqlalchemy import create_engine as sa_create_engine
    return sa_create_engine(database_url, **kwargs)


def get_tenant_schema_name(tenant_slug: str) -> str:
    """
    Get schema name for tenant
    
    Schema naming convention: tenant_{slug}
    Example: tenant_acme -> schema 'tenant_acme'
    """
    if tenant_slug in _schema_cache:
        return _schema_cache[tenant_slug]
    
    schema_name = f"tenant_{tenant_slug.lower().replace('-', '_')}"
    _schema_cache[tenant_slug] = schema_name
    
    logger.debug(f"Mapped tenant {tenant_slug} to schema {schema_name}")
    return schema_name


def get_shared_schema_name() -> str:
    """Get the shared/public schema name"""
    return "public"


def create_tenant_schema(tenant_slug: str) -> bool:
    """
    Create a new tenant schema in the database
    
    This should be called when a new tenant is created
    """
    engine = get_engine()
    schema_name = get_tenant_schema_name(tenant_slug)
    
    try:
        with engine.connect() as conn:
            # Create schema if it doesn't exist
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            
            # Create all tables in the new schema
            Base.metadata.create_all(
                conn,
                tables=None,
                schema=schema_name
            )
            
            conn.commit()
            logger.info(f"Created schema {schema_name} for tenant {tenant_slug}")
            return True
    
    except Exception as e:
        logger.error(f"Error creating schema for tenant {tenant_slug}: {str(e)}")
        return False


def init_tenant_database(tenant_slug: str) -> bool:
    """Initialize database for tenant (create schema and tables)"""
    return create_tenant_schema(tenant_slug)


class TenantAwareDatabaseSession:
    """Session factory that's aware of current tenant context"""
    
    def __init__(self, engine: Engine):
        self.engine = engine
        self.session_factory = sessionmaker(bind=engine)
    
    def __call__(self) -> Session:
        """Create a new session"""
        return self.session_factory()
    
    def get_session(self) -> Session:
        """Get a new session"""
        return self()


# Create global session factory
_session_factory = None


def get_session_factory() -> TenantAwareDatabaseSession:
    """Get or create the session factory"""
    global _session_factory
    
    if _session_factory is None:
        engine = get_engine()
        _session_factory = TenantAwareDatabaseSession(engine)
    
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI routes to get database session
    Automatically handles schema routing for current tenant
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    tenant = get_current_tenant()
    
    if not tenant:
        raise ValueError("No tenant context set. Use set_current_tenant() before database operations.")
    
    session_factory = get_session_factory()
    session = session_factory()
    
    try:
        logger.debug(f"Creating database session for tenant: {tenant}")
        yield session
    finally:
        session.close()
        logger.debug(f"Closed database session for tenant: {tenant}")


def get_db_sync() -> Session:
    """Get synchronous database session (for non-async code)"""
    tenant = get_current_tenant()
    
    if not tenant:
        raise ValueError("No tenant context set")
    
    session_factory = get_session_factory()
    return session_factory()


async def get_db_async() -> Generator[Session, None, None]:
    """Async version of get_db"""
    return get_db()


def init_db(tenant_slug: Optional[str] = None) -> bool:
    """Initialize database (optionally for specific tenant)"""
    if tenant_slug:
        # Initialize for specific tenant
        return create_tenant_schema(tenant_slug)
    else:
        # Initialize public schema for shared tables
        engine = get_engine()
        try:
            Base.metadata.create_all(bind=engine, schema=get_shared_schema_name())
            logger.info("Initialized public schema")
            return True
        except Exception as e:
            logger.error(f"Error initializing public schema: {str(e)}")
            return False
