# tenancy/signals.py
"""
Signal handlers for automatic tenant database and shop schema setup.
"""
import logging
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.db import transaction
from tenancy.models import Tenant, Shop
from tenancy.utils import create_tenant_database_postgres, register_tenant_connection
from tenancy.shop_manager import (
    create_shop_schema, 
    migrate_tenant_database,
    delete_shop_schema
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Tenant)
def setup_tenant_database(sender, instance, created, **kwargs):
    """
    Automatically create and migrate tenant database when a new tenant is created.
    This runs AFTER the Tenant record is committed to the database.
    """
    if not created:
        return
    
    tenant = instance
    logger.info(f"🚀 Setting up database for new tenant: {tenant.name}")
    
    # Use transaction.on_commit to ensure this runs after tenant is saved
    def setup_database():
        try:
            # Step 1: Create the physical database
            logger.info(f"Step 1: Creating database '{tenant.db_name}'")
            superuser_conn_info = {
                'host': tenant.db_host,
                'port': tenant.db_port,
                'user': tenant.db_user,
                'password': tenant.db_password,
                'dbname': 'postgres'
            }
            create_tenant_database_postgres(tenant, superuser_conn_info)
            logger.info(f"✓ Database created: {tenant.db_name}")
            
            # Step 2: Register the connection in Django
            logger.info(f"Step 2: Registering database connection")
            register_tenant_connection(tenant)
            logger.info(f"✓ Connection registered: {tenant.db_alias}")
            
            # Step 3: Run migrations (excluding shop apps)
            logger.info(f"Step 3: Running migrations")
            migrate_tenant_database(tenant)
            logger.info(f"✓ Migrations complete")
            
            logger.info(f"✅ Tenant database setup complete for: {tenant.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup tenant database: {str(e)}")
            logger.exception(e)
            # Don't raise - allow tenant creation to succeed
            # You might want to set a flag on the tenant model indicating setup failed
    
    transaction.on_commit(setup_database)


@receiver(post_save, sender=Shop)
def setup_shop_schema(sender, instance, created, **kwargs):
    """
    Queue async schema setup when a new shop is created.
    This returns immediately without blocking, allowing the API to respond quickly.
    The actual schema creation happens asynchronously via Celery.
    """
    if not created:
        return
    
    shop = instance
    
    logger.info(f"🚀 Queueing async schema setup for shop: {shop.name} ({shop.schema_name})")
    
    # Queue the async task
    from tenancy.tasks import setup_shop_schema_async
    setup_shop_schema_async.delay(shop.id)
    
    logger.info(f"✅ Async setup task queued for shop: {shop.name}")



@receiver(pre_delete, sender=Shop)
def cleanup_shop_schema(sender, instance, **kwargs):
    """
    Optionally delete the schema when a shop is deleted.
    
    SECURITY NOTE: This is commented out by default to prevent accidental data loss.
    Uncomment only if you want automatic schema deletion.
    """
    shop = instance
    tenant = shop.tenant
    
    logger.warning(f"⚠️  Shop being deleted: {shop.name} ({shop.schema_name})")
    
    # UNCOMMENT BELOW TO ENABLE AUTOMATIC SCHEMA DELETION
    # WARNING: This will permanently delete ALL shop data!
    
    # try:
    #     delete_shop_schema(tenant, shop.schema_name, cascade=True)
    #     logger.info(f"✓ Schema deleted for shop: {shop.name}")
    # except Exception as e:
    #     logger.error(f"Failed to delete schema for shop {shop.name}: {str(e)}")
    #     # Don't raise - allow shop deletion to proceed
    
    logger.info(f"Schema '{shop.schema_name}' preserved (automatic deletion disabled)")