# examples/tenant_shop_setup.py
"""
Complete examples of creating tenants and shops with automatic schema setup.
"""
from tenancy.models import Tenant, Shop
from tenancy.shop_manager import get_schema_info
from django.db import transaction


# ============================================================================
# Example 1: Create a new tenant (automatic database setup)
# ============================================================================

def create_new_tenant():
    """
    Creates a new tenant. The signal will automatically:
    1. Create the physical PostgreSQL database
    2. Register the database connection in Django
    3. Migrate all TENANT_APP_LABELS (except SHOP_APP_LABELS) to public schema
    """
    tenant = Tenant.objects.create(
        name="Acme Corporation",
        slug="acme",
        db_name="tenant_acme",
        db_host="localhost",
        db_port=5432,
        db_user="postgres",
        db_password="your_password",
        db_alias="tenant_acme",  # Used in Django's DATABASES
        is_active=True
    )
    
    print(f"✓ Tenant created: {tenant.name}")
    print(f"  Database: {tenant.db_name}")
    print(f"  Alias: {tenant.db_alias}")
    print(f"  Public schema will contain: admin, token_blacklist, shop_users")
    
    return tenant


# ============================================================================
# Example 2: Create a shop (automatic schema setup)
# ============================================================================

def create_new_shop(tenant):
    """
    Creates a new shop. The signal will automatically:
    1. Create a PostgreSQL schema in the tenant's database
    2. Migrate SHOP_APP_LABELS to that schema
       (cash_book, creditors, stock_control, purchase_orders)
    """
    shop = Shop.objects.create(
        tenant=tenant,
        name="Downtown Store",
        slug="downtown",
        schema_name="shop_downtown",  # Must be unique across tenant DB
        is_active=True
    )
    
    print(f"✓ Shop created: {shop.name}")
    print(f"  Schema: {shop.schema_name}")
    print(f"  Schema will contain: cash_book, creditors, stock_control, purchase_orders")
    
    return shop


# ============================================================================
# Example 3: Create tenant with multiple shops
# ============================================================================

@transaction.atomic
def create_tenant_with_shops():
    """
    Complete example: Create a tenant and multiple shops.
    """
    # Step 1: Create tenant
    print("\n" + "="*80)
    print("Creating Tenant...")
    print("="*80)
    
    tenant = Tenant.objects.create(
        name="Retail Chain Inc",
        slug="retail-chain",
        db_name="tenant_retail",
        db_host="localhost",
        db_port=5432,
        db_user="postgres",
        db_password="your_password",
        db_alias="tenant_retail",
        is_active=True
    )
    
    print(f"✓ Tenant '{tenant.name}' created")
    print(f"  Database: {tenant.db_name}")
    
    # Step 2: Create shops
    shops = [
        {"name": "North Branch", "slug": "north", "schema": "shop_north"},
        {"name": "South Branch", "slug": "south", "schema": "shop_south"},
        {"name": "East Branch", "slug": "east", "schema": "shop_east"},
    ]
    
    created_shops = []
    
    for shop_data in shops:
        print(f"\n{'-'*80}")
        print(f"Creating Shop: {shop_data['name']}")
        print(f"{'-'*80}")
        
        shop = Shop.objects.create(
            tenant=tenant,
            name=shop_data['name'],
            slug=shop_data['slug'],
            schema_name=shop_data['schema'],
            is_active=True
        )
        
        created_shops.append(shop)
        print(f"✓ Shop '{shop.name}' created with schema '{shop.schema_name}'")
    
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    print(f"Tenant: {tenant.name}")
    print(f"Database: {tenant.db_name}")
    print(f"Shops created: {len(created_shops)}")
    
    for shop in created_shops:
        print(f"  - {shop.name} (schema: {shop.schema_name})")
    
    return tenant, created_shops


# ============================================================================
# Example 4: Verify shop schema setup
# ============================================================================

def verify_shop_setup(shop):
    """
    Verify that a shop's schema was created correctly.
    """
    print(f"\n{'='*80}")
    print(f"Verifying Shop: {shop.name}")
    print(f"{'='*80}")
    
    tenant = shop.tenant
    info = get_schema_info(tenant, shop.schema_name)
    
    if not info['exists']:
        print(f"✗ Schema '{shop.schema_name}' does not exist!")
        return False
    
    print(f"✓ Schema exists: {shop.schema_name}")
    print(f"✓ Tables: {info['table_count']}")
    
    print("\nTables:")
    for table in info['tables']:
        print(f"  - {table}")
    
    print("\nMigrations:")
    current_app = None
    for migration in info['migrations']:
        if migration['app'] != current_app:
            current_app = migration['app']
            print(f"\n  {current_app}:")
        print(f"    - {migration['name']} (applied: {migration['applied']})")
    
    return True


# ============================================================================
# Example 5: Working with shop data
# ============================================================================

def create_shop_data(shop):
    """
    Example of creating data in a shop's schema.
    This requires setting the tenant context.
    """
    from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current
    
    try:
        # Set context to route queries to the correct database and schema
        set_current_tenant(shop.tenant)
        set_current_shop(shop.schema_name)
        
        # Now import your models
        from apps.cash_book.models import CashTransaction
        from apps.creditors.models import Creditor
        
        # Create some data - it will go to the shop's schema
        transaction = CashTransaction.objects.create(
            description="Opening balance",
            amount=1000.00,
            # ... other fields
        )
        
        creditor = Creditor.objects.create(
            name="Supplier ABC",
            # ... other fields
        )
        
        print(f"✓ Created data in {shop.name} (schema: {shop.schema_name})")
        print(f"  - Cash transaction: {transaction.id}")
        print(f"  - Creditor: {creditor.id}")
        
    finally:
        # Always clear context when done
        clear_current()


# ============================================================================
# Example 6: Query across shops
# ============================================================================

def get_total_cash_across_shops(tenant):
    """
    Example of aggregating data across multiple shops.
    """
    from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current
    from apps.cash_book.models import CashTransaction
    from django.db.models import Sum
    
    shops = Shop.objects.filter(tenant=tenant, is_active=True)
    
    totals = {}
    
    for shop in shops:
        try:
            set_current_tenant(tenant)
            set_current_shop(shop.schema_name)
            
            # Query this shop's data
            total = CashTransaction.objects.aggregate(
                total=Sum('amount')
            )['total'] or 0
            
            totals[shop.name] = total
            
        finally:
            clear_current()
    
    print("\nCash totals by shop:")
    grand_total = 0
    for shop_name, total in totals.items():
        print(f"  {shop_name}: ${total:,.2f}")
        grand_total += total
    
    print(f"\nGrand Total: ${grand_total:,.2f}")
    
    return totals


# ============================================================================
# Example 7: Manual migration (if signal didn't run)
# ============================================================================

def manually_setup_shop(shop_id):
    """
    Manually setup a shop's schema if the automatic signal didn't work.
    """
    from tenancy.shop_manager import create_shop_schema
    
    shop = Shop.objects.get(id=shop_id)
    tenant = shop.tenant
    
    print(f"Manually setting up schema for: {shop.name}")
    
    try:
        create_shop_schema(tenant, shop.schema_name)
        print(f"✓ Schema setup complete")
        
        # Verify
        verify_shop_setup(shop)
        
    except Exception as e:
        print(f"✗ Failed: {str(e)}")
        raise


# ============================================================================
# Usage
# ============================================================================

if __name__ == "__main__":
    # Create a tenant with multiple shops
    tenant, shops = create_tenant_with_shops()
    
    # Verify each shop
    for shop in shops:
        verify_shop_setup(shop)
    
    # Create some data
    create_shop_data(shops[0])
    
    # Query across shops
    get_total_cash_across_shops(tenant)