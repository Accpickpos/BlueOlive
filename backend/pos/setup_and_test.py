#!/usr/bin/env python
"""
POS System Setup and Testing Script
Tests schema creation, model initialization, and API integration
"""
import asyncio
import logging
from datetime import datetime
from schema_migrations import (
    TenantSchemaManager,
    create_shop_with_schema,
    initialize_public_schema,
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_schema_creation():
    """Test schema creation for a tenant"""
    logger.info("=" * 60)
    logger.info("TEST 1: Schema Creation")
    logger.info("=" * 60)
    
    tenant_slug = "test_acme"
    
    try:
        # Create schema
        result = create_shop_with_schema(tenant_slug)
        
        if result["success"]:
            logger.info(f"✓ Schema creation successful")
            logger.info(f"  Schema name: {result['schema_name']}")
            logger.info(f"  Messages: {', '.join(result['messages'])}")
            return True
        else:
            logger.error(f"✗ Schema creation failed")
            logger.error(f"  Messages: {', '.join(result['messages'])}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Exception during schema creation: {str(e)}")
        return False


async def test_list_schemas():
    """Test listing all tenant schemas"""
    logger.info("=" * 60)
    logger.info("TEST 2: List Tenant Schemas")
    logger.info("=" * 60)
    
    try:
        schemas = TenantSchemaManager.list_tenant_schemas()
        
        if schemas:
            logger.info(f"✓ Found {len(schemas)} tenant schema(s):")
            for schema in schemas:
                logger.info(f"  - {schema}")
            return True
        else:
            logger.warning("⚠ No tenant schemas found")
            return True  # Not necessarily a failure
            
    except Exception as e:
        logger.error(f"✗ Exception listing schemas: {str(e)}")
        return False


async def test_tenant_status():
    """Test getting tenant status"""
    logger.info("=" * 60)
    logger.info("TEST 3: Get Tenant Status")
    logger.info("=" * 60)
    
    tenant_slug = "test_acme"
    
    try:
        status = TenantSchemaManager.get_tenant_schema_name(tenant_slug)
        logger.info(f"✓ Tenant schema name: {status}")
        
        # Try to get more detailed status
        try:
            from sqlalchemy import inspect, create_engine
            from config import get_settings
            
            engine = create_engine(get_settings().database_url)
            inspector = inspect(engine)
            schemas = inspector.get_schema_names()
            
            if status in schemas:
                tables = inspector.get_table_names(schema=status)
                logger.info(f"✓ Schema exists with {len(tables)} tables:")
                for table in sorted(tables):
                    logger.info(f"  - {table}")
                return True
            else:
                logger.warning(f"⚠ Schema {status} not found in database")
                return False
                
        except Exception as e:
            logger.warning(f"⚠ Could not inspect schema: {str(e)}")
            return True
            
    except Exception as e:
        logger.error(f"✗ Exception getting tenant status: {str(e)}")
        return False


async def test_public_schema():
    """Test public schema initialization"""
    logger.info("=" * 60)
    logger.info("TEST 4: Public Schema Initialization")
    logger.info("=" * 60)
    
    try:
        success = initialize_public_schema()
        
        if success:
            logger.info("✓ Public schema initialized successfully")
            return True
        else:
            logger.error("✗ Failed to initialize public schema")
            return False
            
    except Exception as e:
        logger.error(f"✗ Exception initializing public schema: {str(e)}")
        return False


async def test_backup_and_cleanup():
    """Test backup and cleanup of tenant schema"""
    logger.info("=" * 60)
    logger.info("TEST 5: Backup and Cleanup")
    logger.info("=" * 60)
    
    tenant_slug = "test_acme"
    
    try:
        # Backup schema before cleanup
        logger.info(f"Creating backup of {tenant_slug}...")
        backup_success = TenantSchemaManager.backup_tenant_schema(
            tenant_slug, 
            f"test_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if backup_success:
            logger.info("✓ Backup created successfully")
        else:
            logger.warning("⚠ Backup creation failed, continuing with cleanup")
        
        # Clean up test schema
        logger.info(f"Deleting test schema {tenant_slug}...")
        delete_success = TenantSchemaManager.delete_tenant_schema(tenant_slug)
        
        if delete_success:
            logger.info("✓ Schema deleted successfully")
            return True
        else:
            logger.error("✗ Failed to delete schema")
            return False
            
    except Exception as e:
        logger.error(f"✗ Exception during backup/cleanup: {str(e)}")
        return False


async def run_all_tests():
    """Run all tests"""
    logger.info("\n" + "=" * 60)
    logger.info("POS SYSTEM MIGRATION TESTS")
    logger.info("=" * 60 + "\n")
    
    results = {
        "Schema Creation": await test_schema_creation(),
        "List Schemas": await test_list_schemas(),
        "Tenant Status": await test_tenant_status(),
        "Public Schema": await test_public_schema(),
        "Backup & Cleanup": await test_backup_and_cleanup(),
    }
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 60 + "\n")
    
    return passed == total


def print_usage_examples():
    """Print usage examples"""
    logger.info("\n" + "=" * 60)
    logger.info("USAGE EXAMPLES")
    logger.info("=" * 60 + "\n")
    
    examples = """
1. CREATE A NEW TENANT SCHEMA (Python):
   from schema_migrations import create_shop_with_schema
   result = create_shop_with_schema("my_shop")
   print(result)

2. CREATE A NEW TENANT SCHEMA (cURL):
   curl -X POST http://localhost:8001/api/v1/admin/tenants/init \\
     -H "Content-Type: application/json" \\
     -H "Authorization: Bearer <admin_token>" \\
     -d '{
       "slug": "my_shop",
       "name": "My Shop",
       "domain": "myshop.example.com"
     }'

3. LIST ALL TENANT SCHEMAS (Python):
   from schema_migrations import TenantSchemaManager
   schemas = TenantSchemaManager.list_tenant_schemas()
   print(schemas)

4. GET TENANT STATUS (Python):
   from tenant_hooks import TenantLifecycleHooks
   status = TenantLifecycleHooks.get_tenant_status("my_shop")
   print(status)

5. CHECK SCHEMA IN POSTGRESQL:
   psql -U postgres -d blue_olive
   \\dn                    # List all schemas
   SET search_path TO tenant_my_shop;
   \\dt                    # List all tables in tenant schema

6. SYNC SCHEMA WITH LATEST MODELS (Python):
   from schema_migrations import sync_tenant_schema
   result = sync_tenant_schema("my_shop")
   print(result)

7. DELETE TENANT SCHEMA (Python):
   from schema_migrations import TenantSchemaManager
   TenantSchemaManager.delete_tenant_schema("my_shop")

8. START FASTAPI SERVER:
   cd backend/pos
   python -m uvicorn main:app --reload --port 8001

9. START FRONTEND:
   cd frontend
   npm run dev
   # Access: http://localhost:3000

10. TEST INVOICE CREATION:
    1. Login to http://localhost:3000
    2. Navigate to: Dashboard > POS > Invoices > Create
    3. Select debtor account
    4. Add line items
    5. Save and post invoice
"""
    
    logger.info(examples)
    logger.info("=" * 60 + "\n")


if __name__ == "__main__":
    # Run async tests
    success = asyncio.run(run_all_tests())
    
    # Print usage examples
    print_usage_examples()
    
    # Exit with appropriate code
    exit(0 if success else 1)
