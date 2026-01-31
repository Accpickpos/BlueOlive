"""
Schema Migration and Initialization Utilities
Handles dynamic schema creation when new shops/tenants are created
Supports automatic table creation and schema management
"""
import logging
from sqlalchemy import text, inspect, create_engine
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from models_db import Base
from config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class TenantSchemaManager:
    """Manages tenant schemas and migrations"""
    
    @staticmethod
    def create_connection(tenant_slug: str = None):
        """Create a database connection (with optional schema context)"""
        engine = create_engine(settings.database_url, echo=False)
        return engine
    
    @staticmethod
    def get_public_connection():
        """Get connection for public schema"""
        engine = TenantSchemaManager.create_connection()
        return engine
    
    @staticmethod
    def create_tenant_schema(tenant_slug: str) -> bool:
        """
        Create a new schema for tenant
        Called when a new shop/tenant is created
        
        Args:
            tenant_slug: The tenant identifier (e.g., 'acme')
            
        Returns:
            bool: True if schema created successfully, False otherwise
        """
        schema_name = f"tenant_{tenant_slug.lower().replace('-', '_')}"
        
        try:
            engine = TenantSchemaManager.get_public_connection()
            
            with engine.connect() as conn:
                # Check if schema already exists
                inspector = inspect(engine)
                existing_schemas = inspector.get_schema_names()
                
                if schema_name in existing_schemas:
                    logger.info(f"Schema {schema_name} already exists for tenant {tenant_slug}")
                    return True
                
                # Create schema
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
                conn.commit()
                logger.info(f"Created schema {schema_name} for tenant {tenant_slug}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error creating schema {schema_name}: {str(e)}")
            return False
    
    @staticmethod
    def migrate_tenant_schema(tenant_slug: str) -> bool:
        """
        Initialize tables in tenant schema
        Called after schema is created
        
        Args:
            tenant_slug: The tenant identifier
            
        Returns:
            bool: True if migration successful, False otherwise
        """
        schema_name = f"tenant_{tenant_slug.lower().replace('-', '_')}"
        
        try:
            # Create engine that targets this schema
            engine = TenantSchemaManager.create_connection()
            
            # Set schema in connection
            with engine.connect() as conn:
                conn.execute(text(f"SET search_path TO {schema_name}"))
                conn.commit()
            
            # Create all tables in this schema
            Base.metadata.create_all(
                bind=engine,
                tables=None,
                checkfirst=True
            )
            
            logger.info(f"Successfully migrated schema {schema_name} for tenant {tenant_slug}")
            return True
            
        except Exception as e:
            logger.error(f"Error migrating schema {schema_name}: {str(e)}")
            return False
    
    @staticmethod
    def get_tenant_schema_name(tenant_slug: str) -> str:
        """Get the schema name for a tenant"""
        return f"tenant_{tenant_slug.lower().replace('-', '_')}"
    
    @staticmethod
    def list_tenant_schemas() -> list:
        """List all tenant schemas"""
        try:
            engine = TenantSchemaManager.get_public_connection()
            inspector = inspect(engine)
            schemas = inspector.get_schema_names()
            
            # Filter for tenant schemas only
            tenant_schemas = [s for s in schemas if s.startswith('tenant_')]
            return tenant_schemas
            
        except Exception as e:
            logger.error(f"Error listing tenant schemas: {str(e)}")
            return []
    
    @staticmethod
    def delete_tenant_schema(tenant_slug: str) -> bool:
        """
        Delete schema for a tenant (DANGEROUS - use with caution)
        
        Args:
            tenant_slug: The tenant identifier
            
        Returns:
            bool: True if deletion successful, False otherwise
        """
        schema_name = f"tenant_{tenant_slug.lower().replace('-', '_')}"
        
        try:
            engine = TenantSchemaManager.get_public_connection()
            
            with engine.connect() as conn:
                # Drop schema with cascade
                conn.execute(text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"))
                conn.commit()
                logger.warning(f"Deleted schema {schema_name} for tenant {tenant_slug}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error deleting schema {schema_name}: {str(e)}")
            return False
    
    @staticmethod
    def backup_tenant_schema(tenant_slug: str, backup_name: str) -> bool:
        """
        Backup tenant schema
        
        Args:
            tenant_slug: The tenant identifier
            backup_name: Name for the backup
            
        Returns:
            bool: True if backup successful, False otherwise
        """
        source_schema = f"tenant_{tenant_slug.lower().replace('-', '_')}"
        backup_schema = f"{source_schema}_backup_{backup_name}"
        
        try:
            engine = TenantSchemaManager.get_public_connection()
            
            with engine.connect() as conn:
                # Check if source schema exists
                inspector = inspect(engine)
                schemas = inspector.get_schema_names()
                
                if source_schema not in schemas:
                    logger.error(f"Source schema {source_schema} does not exist")
                    return False
                
                # Create backup schema
                conn.execute(text(f"CREATE SCHEMA {backup_schema}"))
                
                # Get all tables from source schema
                tables = inspector.get_table_names(schema=source_schema)
                
                # Copy tables
                for table in tables:
                    conn.execute(text(
                        f"CREATE TABLE {backup_schema}.{table} AS "
                        f"SELECT * FROM {source_schema}.{table}"
                    ))
                
                conn.commit()
                logger.info(f"Created backup {backup_schema} for tenant {tenant_slug}")
                return True
                
        except Exception as e:
            logger.error(f"Error backing up schema: {str(e)}")
            return False


def initialize_public_schema():
    """Initialize public schema with shared tables"""
    try:
        engine = TenantSchemaManager.get_public_connection()
        
        # Create public schema if not exists
        with engine.connect() as conn:
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
            conn.commit()
        
        logger.info("Public schema initialized")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing public schema: {str(e)}")
        return False


def create_shop_with_schema(tenant_slug: str) -> dict:
    """
    Create a new shop/tenant with complete schema setup
    This is called when a new shop is registered in Django
    
    Args:
        tenant_slug: The tenant identifier
        
    Returns:
        dict: Status of creation with success flag and messages
    """
    result = {
        "success": False,
        "messages": [],
        "tenant_slug": tenant_slug,
        "schema_name": TenantSchemaManager.get_tenant_schema_name(tenant_slug)
    }
    
    # Step 1: Create schema
    if not TenantSchemaManager.create_tenant_schema(tenant_slug):
        result["messages"].append("Failed to create schema")
        return result
    result["messages"].append("Schema created successfully")
    
    # Step 2: Migrate tables
    if not TenantSchemaManager.migrate_tenant_schema(tenant_slug):
        result["messages"].append("Failed to migrate tables")
        # Clean up schema if migration failed
        TenantSchemaManager.delete_tenant_schema(tenant_slug)
        return result
    result["messages"].append("Tables migrated successfully")
    
    result["success"] = True
    return result


def sync_tenant_schema(tenant_slug: str) -> dict:
    """
    Sync/update tenant schema with latest models
    Useful for migrations after code updates
    
    Args:
        tenant_slug: The tenant identifier
        
    Returns:
        dict: Status of sync operation
    """
    result = {
        "success": False,
        "messages": [],
        "tenant_slug": tenant_slug,
        "schema_name": TenantSchemaManager.get_tenant_schema_name(tenant_slug)
    }
    
    try:
        schema_name = result["schema_name"]
        engine = TenantSchemaManager.create_connection()
        
        with engine.connect() as conn:
            conn.execute(text(f"SET search_path TO {schema_name}"))
            conn.commit()
        
        # Update all tables based on current models
        Base.metadata.create_all(bind=engine, checkfirst=True)
        
        result["success"] = True
        result["messages"].append("Schema synced successfully")
        
    except Exception as e:
        result["messages"].append(f"Error syncing schema: {str(e)}")
    
    return result
