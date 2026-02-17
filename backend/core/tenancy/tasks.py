"""
Celery tasks for tenancy operations.
Handles async shop schema creation and migration.
"""
import logging
from celery import shared_task
from django.db import transaction
from tenancy.models import Shop, Tenant
from tenancy.utils import register_tenant_connection
from tenancy.shop_manager import create_shop_schema

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def setup_shop_schema_async(self, shop_id):
    """
    Async task to create shop schema and run migrations.
    Updates shop status upon completion.
    
    Args:
        shop_id: ID of the Shop to set up
    """
    try:
        logger.info(f"[CELERY] Starting async shop schema setup for shop_id={shop_id}")
        
        # Get the shop
        try:
            shop = Shop.objects.get(id=shop_id)
        except Shop.DoesNotExist:
            logger.error(f"[CELERY] Shop with id {shop_id} not found")
            return f"Shop {shop_id} not found"
        
        tenant = shop.tenant
        
        logger.info(f"[CELERY] Setting up schema for shop: {shop.name} ({shop.schema_name})")
        
        try:
            # Ensure tenant connection is registered
            register_tenant_connection(tenant)
            logger.info(f"[CELERY] Tenant connection registered for {tenant.name}")
            
            # Create schema and migrate shop apps
            create_shop_schema(tenant, shop.schema_name)
            logger.info(f"[CELERY] Schema creation completed for {shop.schema_name}")
            
            # Update shop status to ready
            shop.setup_status = 'ready'
            shop.save(update_fields=['setup_status'])
            logger.info(f"[CELERY] ✅ Shop is now ready: {shop.name}")
            
            return f"Shop {shop_id} setup completed successfully"
            
        except Exception as e:
            logger.error(f"[CELERY] Error setting up schema: {str(e)}", exc_info=True)
            
            # Update shop status to failed
            shop.setup_status = 'failed'
            shop.save(update_fields=['setup_status'])
            
            # Retry the task with exponential backoff
            raise self.retry(exc=e, countdown=5 * (2 ** self.request.retries))
    
    except self.MaxRetriesExceededError:
        logger.error(f"[CELERY] Max retries exceeded for shop {shop_id}")
        try:
            shop = Shop.objects.get(id=shop_id)
            shop.setup_status = 'failed'
            shop.save(update_fields=['setup_status'])
        except:
            pass
        return f"Failed to setup shop {shop_id} after max retries"
    except Exception as e:
        logger.error(f"[CELERY] Unexpected error in setup_shop_schema_async: {str(e)}", exc_info=True)
        return f"Unexpected error: {str(e)}"
