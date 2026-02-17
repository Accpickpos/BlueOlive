"""
Data migration script for migrating existing stock items to branch-based stock management.

This script:
1. Creates a default HQ branch for each tenant
2. Migrates existing StockItem.quantity_on_hand to BranchStock for the default branch
3. Sets the default branch as the primary branch for operations

Usage:
    python manage.py shell < migrate_to_branch_model.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.utils import timezone
from apps.stock_control.models import StockItem, Branch, BranchStock
from decimal import Decimal

def migrate_to_branch_model():
    """Main migration function"""
    print("=" * 80)
    print("Starting migration to branch-based stock management")
    print("=" * 80)
    
    # Step 1: Create default HQ branch
    print("\n[Step 1] Creating default HQ branch...")
    try:
        default_branch, created = Branch.objects.get_or_create(
            branch_code='HQ001',
            defaults={
                'branch_name': 'Headquarters',
                'branch_type': 'HQ',
                'address': '',
                'contact_phone': '',
                'is_active': True,
                'is_default': True,
                'created_by': 'System Migration',
            }
        )
        
        if created:
            print(f"✓ Created default branch: {default_branch.branch_code}")
        else:
            print(f"✓ Default branch already exists: {default_branch.branch_code}")
    except Exception as e:
        print(f"✗ Error creating default branch: {e}")
        return False
    
    # Step 2: Migrate stock items to branch stock
    print("\n[Step 2] Migrating stock items to BranchStock...")
    try:
        all_stock_items = StockItem.objects.all()
        migrated_count = 0
        skipped_count = 0
        
        print(f"Total stock items to process: {all_stock_items.count()}")
        
        for stock_item in all_stock_items:
            try:
                # Check if BranchStock already exists
                branch_stock, created = BranchStock.objects.get_or_create(
                    branch=default_branch,
                    stock_item=stock_item,
                    defaults={
                        'quantity': stock_item.quantity_on_hand,
                        'quantity_allocated': stock_item.quantity_allocated,
                        'reorder_level': stock_item.reorder_quantity,
                        'reorder_quantity': stock_item.reorder_quantity,
                    }
                )
                
                if created:
                    migrated_count += 1
                    print(f"  ✓ Migrated: {stock_item.stock_code} -> Qty: {stock_item.quantity_on_hand}")
                else:
                    skipped_count += 1
                    print(f"  ⊘ Already exists: {stock_item.stock_code}")
                    
            except Exception as e:
                print(f"  ✗ Error migrating {stock_item.stock_code}: {e}")
                continue
        
        print(f"\n✓ Migration complete:")
        print(f"  - Migrated: {migrated_count}")
        print(f"  - Skipped: {skipped_count}")
        print(f"  - Total: {migrated_count + skipped_count}")
        
    except Exception as e:
        print(f"✗ Error during stock item migration: {e}")
        return False
    
    # Step 3: Verify migration
    print("\n[Step 3] Verifying migration...")
    try:
        branch_stock_count = BranchStock.objects.filter(branch=default_branch).count()
        print(f"✓ BranchStock entries created: {branch_stock_count}")
        
        # Check for items not migrated
        not_migrated = all_stock_items.count() - branch_stock_count
        if not_migrated > 0:
            print(f"⚠ Warning: {not_migrated} items not migrated")
        
    except Exception as e:
        print(f"✗ Error during verification: {e}")
        return False
    
    print("\n" + "=" * 80)
    print("✓ Migration completed successfully!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Apply the migrations: python manage.py migrate stock_control")
    print("2. Test the API endpoints at /api/v1/stock-control/branches/")
    print("3. Test branch stock viewing at /api/v1/stock-control/branch-stock/")
    print()
    
    return True


def rollback_migration():
    """Rollback function to remove migrated branch stock entries"""
    print("\n" + "=" * 80)
    print("WARNING: This will remove all migrated BranchStock entries!")
    print("=" * 80)
    
    response = input("\nAre you sure you want to rollback? (yes/no): ").strip().lower()
    if response != 'yes':
        print("Rollback cancelled.")
        return False
    
    try:
        # Find and delete the default HQ branch's BranchStock entries
        default_branch = Branch.objects.get(branch_code='HQ001')
        count, _ = BranchStock.objects.filter(branch=default_branch).delete()
        print(f"✓ Deleted {count} BranchStock entries")
        
        # Optionally delete the default branch
        response = input("\nDelete the default HQ001 branch as well? (yes/no): ").strip().lower()
        if response == 'yes':
            default_branch.delete()
            print("✓ Deleted default branch")
        
        print("✓ Rollback completed")
        return True
        
    except Branch.DoesNotExist:
        print("Default branch not found, nothing to rollback")
        return False
    except Exception as e:
        print(f"✗ Error during rollback: {e}")
        return False


if __name__ == '__main__':
    # Check for command line argument
    if len(sys.argv) > 1 and sys.argv[1] == '--rollback':
        success = rollback_migration()
    else:
        success = migrate_to_branch_model()
    
    sys.exit(0 if success else 1)
