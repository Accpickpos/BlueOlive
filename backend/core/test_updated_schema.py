#!/usr/bin/env python
"""
Test updated schema against tenant_tnt to verify exact match.
"""
import os
import sys
import django
import psycopg2
from psycopg2 import sql

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant
from tenancy.shop_manager import verify_and_create_missing_tables, create_missing_tables_manually
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_column_info(conn, table_name):
    """Get column info for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """, (table_name,))
        return cur.fetchall()

def compare_schemas(alias1, alias2, table_names):
    """Compare schemas between two databases."""
    conn1 = connections[alias1]
    conn2 = connections[alias2]
    
    mismatches = []
    
    for table_name in table_names:
        cols1 = get_column_info(conn1, table_name)
        cols2 = get_column_info(conn2, table_name)
        
        if len(cols1) != len(cols2):
            mismatches.append(f"{table_name}: Column count mismatch ({len(cols1)} vs {len(cols2)})")
            continue
        
        for (name1, type1, null1, default1), (name2, type2, null2, default2) in zip(cols1, cols2):
            if name1 != name2:
                mismatches.append(f"{table_name}: Column name mismatch - {name1} vs {name2}")
            elif type1 != type2:
                mismatches.append(f"{table_name}: {name1} type mismatch - {type1} vs {type2}")
            elif null1 != null2:
                mismatches.append(f"{table_name}: {name1} nullability mismatch - {null1} vs {null2}")
            elif default1 != default2:
                mismatches.append(f"{table_name}: {name1} default mismatch - {default1} vs {default2}")
    
    return mismatches

def main():
    """Test the updated schema."""
    logger.info("=" * 80)
    logger.info("Testing Updated Schema")
    logger.info("=" * 80)
    
    # Get reference tenant
    try:
        tenant_tnt = Tenant.objects.get(name='TnT')
        logger.info(f"Found reference tenant: {tenant_tnt.name}")
    except Tenant.DoesNotExist:
        logger.error("Reference tenant 'TnT' not found!")
        return False
    
    # Create a test tenant
    test_tenant = Tenant.objects.create(
        name='TestSchemaVerify',
        slug='test-schema-verify',
        subdomain='test-schema-verify',
        db_name='tenant_test_schema_verify'
    )
    logger.info(f"Created test tenant: {test_tenant.name}")
    
    # Get database aliases
    tnt_alias = f'tenant_{tenant_tnt.id}'
    test_alias = f'tenant_{test_tenant.id}'
    
    logger.info(f"Reference alias: {tnt_alias}")
    logger.info(f"Test alias: {test_alias}")
    
    # Critical 12 tables
    critical_tables = [
        'django_content_type',
        'django_migrations',
        'auth_permission',
        'auth_group',
        'auth_group_permissions',
        'django_session',
        'shop_users_shopuser',
        'shop_users_shopuser_groups',
        'shop_users_shopuser_user_permissions',
        'django_admin_log',
        'token_blacklist_outstandingtoken',
        'token_blacklist_blacklistedtoken',
    ]
    
    # Verify and create missing tables in test tenant
    logger.info("\n" + "="*80)
    logger.info("Verifying and Creating Missing Tables")
    logger.info("="*80)
    
    try:
        verify_and_create_missing_tables(test_tenant, test_alias)
        logger.info("✓ Tables verification/creation completed")
    except Exception as e:
        logger.error(f"✗ Table verification failed: {e}")
        test_tenant.delete()
        return False
    
    # Compare schemas
    logger.info("\n" + "="*80)
    logger.info("Comparing Schemas: test_schema_verify vs tnt (reference)")
    logger.info("="*80)
    
    try:
        mismatches = compare_schemas(test_alias, tnt_alias, critical_tables)
        
        if mismatches:
            logger.error(f"Found {len(mismatches)} schema mismatches:")
            for mismatch in mismatches:
                logger.error(f"  ✗ {mismatch}")
            test_tenant.delete()
            return False
        else:
            logger.info("✓ All 12 tables match tenant_tnt schema exactly!")
    except Exception as e:
        logger.error(f"✗ Schema comparison failed: {e}")
        test_tenant.delete()
        return False
    
    # Clean up test tenant
    test_tenant.delete()
    logger.info("\nTest tenant deleted")
    
    logger.info("\n" + "="*80)
    logger.info("SCHEMA UPDATE TEST PASSED ✓")
    logger.info("="*80)
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
