"""
Shared utilities for data seeding across all apps.
Provides common functions to reduce code duplication and ensure consistency.
"""
from django.core.management.base import CommandError
from django.db import transaction
from tenancy.models import Tenant, Shop
from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current
from django.contrib.auth import get_user_model

User = get_user_model()


class SeedingException(Exception):
    """Custom exception for seeding operations."""
    pass


def get_tenant(tenant_id=None, tenant_slug=None):
    """
    Get a tenant by ID or slug. Returns first tenant if neither specified.
    
    Args:
        tenant_id (int, optional): Tenant ID
        tenant_slug (str, optional): Tenant slug
        
    Returns:
        Tenant: The requested tenant
        
    Raises:
        SeedingException: If tenant not found
    """
    try:
        if tenant_id:
            return Tenant.objects.get(id=tenant_id)
        elif tenant_slug:
            return Tenant.objects.get(slug=tenant_slug)
        else:
            tenant = Tenant.objects.first()
            if not tenant:
                raise SeedingException("No tenants exist. Create a tenant first using create_dev_tenant command.")
            return tenant
    except Tenant.DoesNotExist:
        if tenant_id:
            raise SeedingException(f"Tenant with ID {tenant_id} not found")
        else:
            raise SeedingException(f"Tenant with slug '{tenant_slug}' not found")


def get_shop(tenant, shop_id=None, shop_slug=None):
    """
    Get a shop for a tenant. Returns first active shop if neither specified.
    
    Args:
        tenant (Tenant): The tenant object
        shop_id (int, optional): Shop ID
        shop_slug (str, optional): Shop slug
        
    Returns:
        Shop: The requested shop
        
    Raises:
        SeedingException: If shop not found
    """
    try:
        if shop_id:
            return Shop.objects.get(id=shop_id, tenant=tenant)
        elif shop_slug:
            return Shop.objects.get(slug=shop_slug, tenant=tenant)
        else:
            shop = Shop.objects.filter(tenant=tenant, is_active=True).first()
            if not shop:
                raise SeedingException(f"No active shops found for tenant '{tenant.name}'. Create a shop first.")
            return shop
    except Shop.DoesNotExist:
        if shop_id:
            raise SeedingException(f"Shop with ID {shop_id} not found for tenant '{tenant.name}'")
        else:
            raise SeedingException(f"Shop with slug '{shop_slug}' not found for tenant '{tenant.name}'")


def get_or_create_admin_user():
    """
    Get or create an admin user for seeding.
    
    Returns:
        User: An active admin/staff user
        
    Raises:
        SeedingException: If no admin user exists and can't be created
    """
    admin = User.objects.filter(is_staff=True, is_active=True).first()
    if not admin:
        raise SeedingException(
            "No active admin/staff user found. Create an admin user first:\n"
            "  python manage.py createsuperuser"
        )
    return admin


def set_seeding_context(tenant, shop=None):
    """
    Set the current tenant and shop context for seeding.
    
    Args:
        tenant (Tenant): The tenant to set
        shop (Shop or str, optional): The shop to set (Shop object or schema name)
    """
    set_current_tenant(tenant)
    if shop:
        if isinstance(shop, Shop):
            set_current_shop(shop.schema_name)
        else:
            set_current_shop(shop)


def clear_seeding_context():
    """Clear the current tenant and shop context."""
    clear_current()


def bulk_create_with_feedback(model, objects, batch_size=1000, verbose=True):
    """
    Bulk create objects with progress feedback.
    
    Args:
        model: Django model class
        objects (list): List of model instances to create
        batch_size (int): Number of objects to create per batch
        verbose (bool): Whether to print progress
        
    Returns:
        int: Number of objects created
    """
    if not objects:
        return 0
    
    created_count = 0
    total = len(objects)
    
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        model.objects.bulk_create(batch, ignore_conflicts=True)
        created_count += len(batch)
        
        if verbose:
            progress = min(created_count, total)
            print(f"  Progress: {progress}/{total} objects created...")
    
    return created_count


def get_or_create_batch(model, defaults_list, unique_field, verbose=True):
    """
    Get or create multiple objects efficiently.
    
    Args:
        model: Django model class
        defaults_list (list): List of dicts with unique_field and other fields
        unique_field (str): Field name used for uniqueness
        verbose (bool): Whether to print progress
        
    Returns:
        tuple: (created_count, existing_count)
    """
    created_count = 0
    existing_count = 0
    
    for item_data in defaults_list:
        lookup_value = item_data.pop(unique_field)
        obj, created = model.objects.get_or_create(
            **{unique_field: lookup_value},
            defaults=item_data
        )
        
        if created:
            created_count += 1
        else:
            existing_count += 1
    
    if verbose:
        print(f"  Created: {created_count}, Already existed: {existing_count}")
    
    return created_count, existing_count


@transaction.atomic
def safe_seed_operation(operation_name, operation_func, *args, **kwargs):
    """
    Execute a seeding operation within a transaction.
    Rolls back on failure.
    
    Args:
        operation_name (str): Name of the operation for logging
        operation_func: Callable to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
        
    Returns:
        The return value of operation_func
        
    Raises:
        SeedingException: If the operation fails
    """
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        raise SeedingException(f"Failed during {operation_name}: {str(e)}") from e


def validate_seed_dependencies(required_models):
    """
    Validate that required models have data before seeding dependent data.
    
    Args:
        required_models (dict): Dict of {model: minimum_count} to validate
        
    Raises:
        SeedingException: If validation fails
    """
    for model, min_count in required_models.items():
        count = model.objects.count()
        if count < min_count:
            app_label = model._meta.app_label
            model_name = model._meta.model_name
            raise SeedingException(
                f"Validation failed: Expected at least {min_count} "
                f"{model_name} records in '{app_label}', but found {count}. "
                f"Seed dependent data first."
            )


def seed_status_report(command_output, status_data):
    """
    Print a formatted status report of what was seeded.
    
    Args:
        command_output: Django command self.stdout
        status_data (dict): Dict with 'created', 'skipped', 'errors' keys
    """
    created = status_data.get('created', 0)
    skipped = status_data.get('skipped', 0)
    errors = status_data.get('errors', [])
    
    command_output.write("\n" + "="*70)
    command_output.write("SEEDING SUMMARY")
    command_output.write("="*70)
    command_output.write(f"\n✓ Created: {created}")
    command_output.write(f"⊘ Skipped: {skipped}")
    
    if errors:
        command_output.write(f"✗ Errors: {len(errors)}\n")
        for error in errors:
            command_output.write(f"  - {error}\n")
    else:
        command_output.write("\n")
