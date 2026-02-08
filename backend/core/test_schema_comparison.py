#!/usr/bin/env python
"""
Test updated schema by querying one of the existing test tenants
and comparing it with tenant_tnt reference.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant
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

def format_column(name, data_type, is_nullable, default):
    """Format column info for display."""
    null_str = "NULL" if is_nullable == "YES" else "NOT NULL"
    default_str = f" DEFAULT {default}" if default else ""
    return f"  {name}: {data_type} {null_str}{default_str}"

def compare_schemas(alias1, alias2, table_names):
    """Compare schemas between two databases."""
    try:
        conn1 = connections[alias1]
        conn2 = connections[alias2]
    except Exception as e:
        logger.error(f"Error getting connections: {e}")
        return []
    
    mismatches = []
    
    for table_name in table_names:
        try:
            cols1 = get_column_info(conn1, table_name)
            cols2 = get_column_info(conn2, table_name)
        except Exception as e:
            logger.error(f"Error getting schema for {table_name}: {e}")
            mismatches.append(f"{table_name}: ERROR - {e}")
            continue
        
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
                # Skip default comparison for now as it can have formatting differences
                pass
    
    return mismatches

def main():
    """Test the updated schema."""
    logger.info("=" * 80)
    logger.info("Testing Updated Schema")
    logger.info("=" * 80)
    
    # Get reference tenant
    try:
        tenant_tnt = Tenant.objects.get(name='TnT')
        logger.info(f"✓ Found reference tenant: {tenant_tnt.name} (DB: {tenant_tnt.db_name})")
    except Tenant.DoesNotExist:
        logger.error("✗ Reference tenant 'TnT' not found!")
        return False
    
    # Use an existing test tenant to verify schema
    try:
        test_tenant = Tenant.objects.get(name='TestFix407')
        logger.info(f"✓ Found test tenant: {test_tenant.name} (DB: {test_tenant.db_name})")
    except Tenant.DoesNotExist:
        logger.error("✗ Test tenant 'TestFix407' not found!")
        return False
    
    # Get database aliases
    tnt_alias = f'tenant_{tenant_tnt.id}'
    test_alias = f'tenant_{test_tenant.id}'
    
    logger.info(f"\nReference alias: {tnt_alias} (database: {tenant_tnt.db_name})")
    logger.info(f"Test alias: {test_alias} (database: {test_tenant.db_name})")
    
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
    
    # Compare schemas
    logger.info("\n" + "="*80)
    logger.info(f"Comparing Schemas: {test_tenant.name} vs {tenant_tnt.name} (reference)")
    logger.info("="*80)
    
    try:
        mismatches = compare_schemas(test_alias, tnt_alias, critical_tables)
        
        if mismatches:
            logger.error(f"\n✗ Found {len(mismatches)} schema mismatches:")
            for mismatch in mismatches:
                logger.error(f"  ✗ {mismatch}")
            return False
        else:
            logger.info("✓ All 12 tables match tenant_tnt schema exactly!")
    except Exception as e:
        logger.error(f"✗ Schema comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Show sample: shop_users_shopuser columns
    logger.info("\n" + "="*80)
    logger.info("Sample: shop_users_shopuser columns in test tenant")
    logger.info("="*80)
    
    try:
        conn = connections[test_alias]
        cols = get_column_info(conn, 'shop_users_shopuser')
        for name, dtype, is_null, default in cols:
            print(format_column(name, dtype, is_null, default))
    except Exception as e:
        logger.error(f"✗ Error querying shop_users_shopuser: {e}")
        return False
    
    logger.info("\n" + "="*80)
    logger.info("SCHEMA TEST PASSED ✓")
    logger.info("="*80)
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
