# tenancy/signals.py
"""
Signal handlers for automatic tenant database and shop schema setup.
"""

import logging

from django.db import transaction
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from tenancy.models import Shop, Tenant
from tenancy.shop_manager import delete_shop_schema

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Tenant)
def setup_tenant_database(sender, instance, created, **kwargs):
    """
    Queue async physical database creation + core migrations when a new
    tenant is created. Runs via Celery (see
    tenancy.tasks.setup_tenant_database_async) so the request that created
    the tenant isn't blocked on CREATE DATABASE + migrations.
    Callers should poll Tenant.setup_status ('pending' -> 'db_ready'/'ready'/
    'failed') before relying on the tenant's database.
    """
    if not created:
        return

    tenant = instance
    logger.info(f"🚀 Queuing database setup for new tenant: {tenant.name}")

    from tenancy.tasks import setup_tenant_database_async

    transaction.on_commit(lambda: setup_tenant_database_async.delay(tenant.pk))


@receiver(post_save, sender=Shop)
def setup_shop_schema(sender, instance, created, **kwargs):
    """
    Queue async shop schema creation and migration when a new shop is created.
    Runs via Celery (see tenancy.tasks.setup_shop_schema_async) so the request
    that created the shop isn't blocked on schema creation + app migrations.
    Callers should poll Shop.setup_status ('pending' -> 'ready'/'failed') via
    the check_setup_status endpoint before relying on the shop's schema.
    """
    if not created:
        return

    shop = instance
    logger.info(f"🚀 Queuing schema setup for shop: {shop.name} ({shop.schema_name})")

    from tenancy.tasks import setup_shop_schema_async

    transaction.on_commit(lambda: setup_shop_schema_async.delay(shop.pk))


@receiver(pre_delete, sender=Shop)
def cleanup_shop_schema(sender, instance, **kwargs):
    """
    Optionally delete the schema when a shop is deleted.

    SECURITY NOTE: This is commented out by default to prevent accidental data loss.
    Uncomment only if you want automatic schema deletion.
    """
    shop = instance
    shop.tenant

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
