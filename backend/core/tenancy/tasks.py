"""
Celery tasks for tenancy operations.
Handles async tenant database provisioning, signup completion, and
shop schema creation/migration.
"""
import logging
from datetime import timedelta
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from tenancy.models import Shop, Tenant
from tenancy.utils import register_tenant_connection
from tenancy.shop_manager import create_shop_schema

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, acks_late=True)
def setup_tenant_database_async(self, tenant_id):
    """
    Async task to create a tenant's physical database and run its core
    (public-schema) migrations. Triggered by Tenant's post_save signal for
    every tenant, regardless of which flow created it.

    acks_late=True: if the worker process dies mid-task (crash, OOM, deploy
    restart), the broker redelivers this task to another worker instead of
    losing it silently, leaving the tenant stuck at 'pending' forever. Safe
    to redeliver because every step here is idempotent (CREATE DATABASE
    checks existence first, migrations only apply what's pending).

    Sets tenant.setup_status to 'db_ready' on success or 'failed' on error.
    Does NOT create any shop or user - see complete_tenant_signup_async for
    the additional steps the self-serve signup flow needs.
    """
    from tenancy.shop_manager import migrate_tenant_database
    from tenancy.utils import create_tenant_database_postgres

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        logger.error(f"[CELERY] Tenant with id {tenant_id} not found")
        return f"Tenant {tenant_id} not found"

    logger.info(f"[CELERY] Setting up database for tenant: {tenant.name}")

    try:
        superuser_conn_info = {
            'host': tenant.db_host,
            'port': tenant.db_port,
            'user': tenant.db_user,
            'password': tenant.db_password,
            'dbname': 'postgres'
        }
        create_tenant_database_postgres(tenant, superuser_conn_info)
        register_tenant_connection(tenant)
        migrate_tenant_database(tenant)

        tenant.setup_status = 'db_ready'
        tenant.save(update_fields=['setup_status'])
        logger.info(f"[CELERY] ✅ Database ready for tenant: {tenant.name}")
        return tenant_id

    except Exception as e:
        logger.error(f"[CELERY] Failed to setup database for tenant {tenant.name}: {str(e)}", exc_info=True)
        try:
            self.retry(exc=e, countdown=5 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            tenant.setup_status = 'failed'
            tenant.save(update_fields=['setup_status'])
            logger.error(f"[CELERY] Max retries exceeded setting up tenant {tenant_id}")
            return f"Failed to setup tenant {tenant_id} after max retries"


@shared_task(bind=True, max_retries=5, acks_late=True)
def complete_tenant_signup_async(self, tenant_id, admin_password_hash,
                                  admin_username=None, first_name=None, last_name=None):
    """
    Async task completing self-serve tenant signup: creates the default
    "Main Office" shop and the tenant's first admin user, once the tenant's
    database is ready.

    admin_username/first_name/last_name are optional because different
    signup flows collect different fields - callers that only have an email
    (no separate username) can omit admin_username and it falls back to
    tenant.email.

    acks_late=True matters more here than on the other tasks: this task
    carries the admin_password_hash as an argument, which exists nowhere
    else (deliberately never persisted on the Tenant row). If the worker
    died mid-task with acks_late=False, that hash would be gone forever and
    the tenant would be stuck at 'db_ready' with no way to ever create its
    admin user - the subdomain is already taken, so the user couldn't even
    sign up again. With acks_late=True the broker redelivers the same
    message, hash included, to another worker. This is safe only because
    the shop/user creation below is now idempotent (get_or_create /
    existence-checked) - a redelivered task may run this body more than
    once against a partially-completed prior attempt.

    Dispatched independently of (and concurrently with)
    setup_tenant_database_async, so this retries with backoff until it sees
    setup_status == 'db_ready' rather than assuming ordering. Sets
    setup_status to 'ready' on success or 'failed' on error/timeout.
    """
    from shop_users.models import ShopUser

    try:
        tenant = Tenant.objects.get(id=tenant_id)
    except Tenant.DoesNotExist:
        logger.error(f"[CELERY] Tenant with id {tenant_id} not found")
        return f"Tenant {tenant_id} not found"

    if tenant.setup_status == 'pending':
        # The database provisioning task hasn't finished yet - wait for it.
        logger.info(f"[CELERY] Tenant {tenant.name} DB not ready yet, retrying signup completion")
        try:
            self.retry(countdown=5 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            tenant.setup_status = 'failed'
            tenant.save(update_fields=['setup_status'])
            logger.error(f"[CELERY] Tenant {tenant_id} database never became ready, giving up on signup completion")
            return f"Tenant {tenant_id} database never became ready"

    if tenant.setup_status == 'failed':
        logger.error(f"[CELERY] Tenant {tenant.name} database setup failed, aborting signup completion")
        return f"Tenant {tenant_id} database setup failed"

    logger.info(f"[CELERY] Completing signup for tenant: {tenant.name}")

    try:
        register_tenant_connection(tenant)

        # get_or_create rather than create: a redelivered task (acks_late,
        # see docstring) may be re-running this after a prior attempt
        # already created the shop but died before finishing the admin
        # user. A plain .create() here would hit unique_head_office_per_tenant
        # and turn a harmless retry into a permanent failure.
        shop, shop_created = Shop.objects.get_or_create(
            tenant=tenant,
            is_head_office=True,
            defaults={
                'name': 'Main Office',
                'schema_name': f"{tenant.slug}_main",
                'subdomain': 'main',
            }
        )
        if shop_created:
            logger.info(f"[CELERY] ✓ Default shop created for tenant {tenant.name}: {shop.name}")
        else:
            logger.info(f"[CELERY] Default shop already existed for tenant {tenant.name} (redelivered task), reusing")

        admin_user = ShopUser.objects.using(tenant.db_alias).filter(tenant_id=tenant.id, role='ADMIN').first()
        if admin_user:
            logger.info(f"[CELERY] Admin user already existed for tenant {tenant.name} (redelivered task), skipping creation")
        else:
            admin_user = ShopUser.objects.using(tenant.db_alias).create(
                username=admin_username or tenant.email,
                email=tenant.email,
                first_name=first_name or (tenant.name.split()[0] if tenant.name else ''),
                last_name=last_name or '',
                password=admin_password_hash,
                is_staff=True,
                is_superuser=False,
                role='ADMIN',
                tenant_id=tenant.id,
                is_active=True,
            )
            logger.info(f"[CELERY] ✓ Admin user created for tenant {tenant.name}: {admin_user.username}")

        tenant.setup_status = 'ready'
        tenant.save(update_fields=['setup_status'])
        logger.info(f"[CELERY] ✅ Signup complete for tenant: {tenant.name}")
        return tenant_id

    except Exception as e:
        logger.error(f"[CELERY] Failed to complete signup for tenant {tenant.name}: {str(e)}", exc_info=True)
        try:
            self.retry(exc=e, countdown=5 * (2 ** self.request.retries))
        except self.MaxRetriesExceededError:
            tenant.setup_status = 'failed'
            tenant.save(update_fields=['setup_status'])
            logger.error(f"[CELERY] Max retries exceeded completing signup for tenant {tenant_id}")
            return f"Failed to complete signup for tenant {tenant_id} after max retries"


@shared_task(bind=True, max_retries=3, acks_late=True)
def setup_shop_schema_async(self, shop_id):
    """
    Async task to create shop schema and run migrations.
    Updates shop status upon completion.

    acks_late=True: redelivers to another worker if this one dies mid-task
    instead of the shop being stuck at 'pending' forever. Safe because
    create_shop_schema/migrate_shop_apps are idempotent (CREATE SCHEMA IF
    NOT EXISTS, migrations only apply what's pending).

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


@shared_task
def sweep_stuck_tenant_provisioning(stuck_after_minutes=10):
    """
    Periodic safety net (see CELERY_BEAT_SCHEDULE) for tenants/shops whose
    provisioning task message was lost outright - e.g. the broker itself
    dropped it, or a task reached max_retries due to a bug before it could
    mark setup_status. acks_late on the provisioning tasks already handles
    the common case (a worker process dying mid-task), so this is a backstop
    for anything acks_late doesn't catch, not the primary mechanism.

    Does NOT cover complete_tenant_signup_async: that task carries the
    admin_password_hash as an argument, which is deliberately never
    persisted anywhere else, so a tenant stuck in 'db_ready' can't be safely
    re-queued from here - it relies on acks_late's message redelivery
    (the original hash travels with the redelivered message).
    """
    threshold = timezone.now() - timedelta(minutes=stuck_after_minutes)

    stuck_tenants = list(Tenant.objects.filter(setup_status='pending', created_at__lt=threshold))
    if stuck_tenants:
        logger.warning(
            f"[CELERY] Found {len(stuck_tenants)} tenant(s) stuck in 'pending' "
            f"past {stuck_after_minutes}m, re-queuing database setup"
        )
    for tenant in stuck_tenants:
        setup_tenant_database_async.delay(tenant.pk)

    stuck_shops = list(Shop.objects.filter(setup_status='pending', created_at__lt=threshold))
    if stuck_shops:
        logger.warning(
            f"[CELERY] Found {len(stuck_shops)} shop(s) stuck in 'pending' "
            f"past {stuck_after_minutes}m, re-queuing schema setup"
        )
    for shop in stuck_shops:
        setup_shop_schema_async.delay(shop.pk)

    return {'tenants_requeued': len(stuck_tenants), 'shops_requeued': len(stuck_shops)}
