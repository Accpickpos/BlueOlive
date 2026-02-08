"""
Seed Debtors (Customers) data for development/testing
Usage: 
    python manage.py seed_debtors                       # Seeds first tenant
    python manage.py seed_debtors --tenant-id 1         # Seeds specific tenant
    python manage.py seed_debtors --tenant-slug slug    # Seeds specific tenant by slug
    python manage.py seed_debtors --dry-run              # Show what would be seeded
"""
from apps.settings.management.commands.base_seed_command import BaseSeedCommand
from apps.debtors.models import Debtor
from apps.settings.models import SalesArea
from decimal import Decimal


class Command(BaseSeedCommand):
    COMMAND_TITLE = "Seeding Debtors Data"
    COMMAND_DESCRIPTION = "Debtors (customers)"
    STEP_NUMBER = "2/4"
    help = 'Seed debtors (customers) data for development/testing'

    def seed(self, user, tenant, shop, dry_run=False, **options):
        """Seed debtors data."""
        
        # Validate dependencies
        sales_areas = SalesArea.objects.all()
        if not sales_areas.exists():
            self.error("No Sales Areas found. Run 'seed_settings' first.")
            return
        
        self.print_section("Creating Debtors (Customers)")
        self._create_debtors(user, sales_areas, dry_run)

    def _create_debtors(self, user, sales_areas, dry_run=False):
        """Create debtor records."""
        debtors_data = [
            {
                'account_number': 'C001',
                'name': 'ABC Trading Company',
                'search_name': 'abc',
                'contact_person': 'John Smith',
                'telephone1': '555-0101',
                'email': 'john@abctrading.com',
                'postal_address_line1': '123 Main Street',
                'postal_address_line2': 'Suite 100',
                'postal_code': '12345',
                'credit_limit': Decimal('10000.00'),
                'account_category': 'O',
                'price_level': 1,
                'terms': 30,
            },
            {
                'account_number': 'C002',
                'name': 'XYZ Retailers Limited',
                'search_name': 'xyz',
                'contact_person': 'Sarah Johnson',
                'telephone1': '555-0102',
                'email': 'sarah@xyzretailers.com',
                'postal_address_line1': '456 Oak Avenue',
                'postal_code': '54321',
                'credit_limit': Decimal('25000.00'),
                'account_category': 'O',
                'price_level': 2,
                'terms': 60,
            },
            {
                'account_number': 'C003',
                'name': 'Quick Buy Store',
                'search_name': 'quick',
                'contact_person': 'Michael Brown',
                'telephone1': '555-0103',
                'email': 'michael@quickbuy.com',
                'postal_address_line1': '789 Pine Road',
                'postal_code': '99999',
                'credit_limit': Decimal('5000.00'),
                'account_category': 'C',
                'price_level': 1,
                'terms': 0,
            },
            {
                'account_number': 'C004',
                'name': 'Premium Goods Inc',
                'search_name': 'premium',
                'contact_person': 'Emily White',
                'telephone1': '555-0104',
                'email': 'emily@premiumgoods.com',
                'postal_address_line1': '321 Elm Street',
                'postal_code': '11111',
                'credit_limit': Decimal('50000.00'),
                'account_category': 'O',
                'price_level': 3,
                'terms': 90,
            },
            {
                'account_number': 'C005',
                'name': 'Corner Shop',
                'search_name': 'corner',
                'contact_person': 'David Green',
                'telephone1': '555-0105',
                'email': 'david@cornershop.com',
                'postal_address_line1': '654 Birch Lane',
                'postal_code': '22222',
                'credit_limit': Decimal('3000.00'),
                'account_category': 'C',
                'price_level': 1,
                'terms': 30,
            },
        ]
        
        sales_area_list = list(sales_areas)
        created = 0
        skipped = 0
        
        for i, debtor_data in enumerate(debtors_data):
            # Assign sales area in round-robin fashion
            sales_area = sales_area_list[i % len(sales_area_list)]
            debtor_data['sales_area'] = sales_area
            debtor_data['created_by'] = user
            
            if Debtor.objects.filter(account_number=debtor_data['account_number']).exists():
                self.skip(f"Debtor {debtor_data['account_number']}: {debtor_data['name']} (already exists)")
                skipped += 1
            else:
                if not dry_run:
                    Debtor.objects.create(**debtor_data)
                self.success(f"Debtor {debtor_data['account_number']}: {debtor_data['name']}")
                created += 1
        
        if dry_run:
            self.info(f"DRY RUN: Would create {created} debtors")
