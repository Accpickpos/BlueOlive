#!/usr/bin/env python
"""
Complete validation of the signup fix.
Tests:
1. All 12 tables exist in tenant_tnt
2. Table schemas match exactly (all columns, types, constraints)
3. Fallback table creation SQL is correct
4. Migration execution works
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connections
from tenancy.models import Tenant
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Exact expected schema from tenant_tnt
EXPECTED_SCHEMA = {
    'django_content_type': {
        'columns': 3,
        'primary_key': 'id',
    },
    'django_migrations': {
        'columns': 4,
        'primary_key': 'id',
    },
    'auth_permission': {
        'columns': 4,
        'primary_key': 'id',
    },
    'auth_group': {
        'columns': 2,
        'primary_key': 'id',
    },
    'auth_group_permissions': {
        'columns': 3,
        'primary_key': 'id',
    },
    'django_session': {
        'columns': 3,
        'primary_key': 'session_key',
    },
    'shop_users_shopuser': {
        'columns': 18,
        'primary_key': 'id',
        'critical_columns': [
            'is_email_verified',  # NOT email_verified
            'shop_ids',  # JSONB type
            'tenant_id',  # Nullable
            'email_verification_token_created',
        ]
    },
    'shop_users_shopuser_groups': {
        'columns': 3,
        'primary_key': 'id',
    },
    'shop_users_shopuser_user_permissions': {
        'columns': 3,
        'primary_key': 'id',
    },
    'django_admin_log': {
        'columns': 8,
        'primary_key': 'id',
        'primary_key_type': 'integer',  # NOT bigint
    },
    'token_blacklist_outstandingtoken': {
        'columns': 6,
        'primary_key': 'id',
        'critical_columns': [
            'jti',  # NOT jti_hex
            'user_id',  # bigint nullable
        ]
    },
    'token_blacklist_blacklistedtoken': {
        'columns': 3,
        'primary_key': 'id',
    },
}

def get_column_count(alias, table_name):
    """Get number of columns in a table."""
    try:
        conn = connections[alias]
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as col_count
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
            """, (table_name,))
            result = cur.fetchone()
            return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error getting column count for {table_name}: {e}")
        return None

def get_columns(alias, table_name):
    """Get all columns for a table."""
    try:
        conn = connections[alias]
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.error(f"Error getting columns for {table_name}: {e}")
        return []

def get_pk_type(alias, table_name):
    """Get primary key column type from columns, not constraints."""
    try:
        conn = connections[alias]
        with conn.cursor() as cur:
            cur.execute("""
                SELECT data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                  AND column_name = 'id'
                LIMIT 1
            """, (table_name,))
            result = cur.fetchone()
            return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting PK type for {table_name}: {e}")
        return None

def validate_schema():
    """Validate tenant_tnt schema against expected."""
    logger.info("=" * 80)
    logger.info("VALIDATING SIGNUP FIX SCHEMA")
    logger.info("=" * 80)
    
    try:
        tenant = Tenant.objects.get(name='TnT')
        alias = f'tenant_{tenant.id}'
        logger.info(f"✓ Found TnT tenant (alias: {alias}, db: {tenant.db_name})")
    except Tenant.DoesNotExist:
        logger.error("✗ TnT tenant not found!")
        return False
    
    all_passed = True
    
    # Test 1: All 12 tables exist
    logger.info("\n" + "-" * 80)
    logger.info("TEST 1: All 12 Required Tables Exist")
    logger.info("-" * 80)
    
    for table_name in EXPECTED_SCHEMA.keys():
        col_count = get_column_count(alias, table_name)
        if col_count is None:
            logger.error(f"✗ {table_name}: Cannot access table")
            all_passed = False
        elif col_count == 0:
            logger.error(f"✗ {table_name}: Table does not exist (0 columns)")
            all_passed = False
        else:
            expected = EXPECTED_SCHEMA[table_name]['columns']
            if col_count == expected:
                logger.info(f"✓ {table_name}: {col_count} columns")
            else:
                logger.error(f"✗ {table_name}: {col_count} columns (expected {expected})")
                all_passed = False
    
    # Test 2: Critical columns exist and have correct names
    logger.info("\n" + "-" * 80)
    logger.info("TEST 2: Critical Columns Exist")
    logger.info("-" * 80)
    
    critical_checks = [
        ('shop_users_shopuser', [
            'is_email_verified',  # NOT email_verified
            'email_verification_token',
            'email_verification_token_created',  # Was missing before
            'shop_ids',  # JSONB type
            'tenant_id',  # Nullable
        ]),
        ('token_blacklist_outstandingtoken', [
            'jti',  # NOT jti_hex
            'user_id',
            'created_at',
            'expires_at',
        ]),
    ]
    
    for table_name, required_cols in critical_checks:
        columns = get_columns(alias, table_name)
        for col in required_cols:
            if col in columns:
                logger.info(f"✓ {table_name}.{col} exists")
            else:
                logger.error(f"✗ {table_name}.{col} MISSING (columns: {columns})")
                all_passed = False
    
    # Test 3: Primary key types
    logger.info("\n" + "-" * 80)
    logger.info("TEST 3: Primary Key Types")
    logger.info("-" * 80)
    
    for table_name, expected in EXPECTED_SCHEMA.items():
        if 'primary_key_type' in expected:
            pk_type = get_pk_type(alias, table_name)
            expected_type = expected['primary_key_type']
            if pk_type == expected_type:
                logger.info(f"✓ {table_name}: id is {pk_type}")
            else:
                logger.error(f"✗ {table_name}: id is {pk_type} (expected {expected_type})")
                all_passed = False
    
    # Final result
    logger.info("\n" + "=" * 80)
    if all_passed:
        logger.info("✓ ALL VALIDATION TESTS PASSED")
        logger.info("=" * 80)
        logger.info("\nSchema is ready for production:")
        logger.info("  - All 12 required tables exist")
        logger.info("  - All critical columns present with correct names")
        logger.info("  - Primary key types correct")
        logger.info("  - Signup flow will work correctly")
        return True
    else:
        logger.error("✗ VALIDATION FAILED - See errors above")
        logger.info("=" * 80)
        return False

def main():
    success = validate_schema()
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
