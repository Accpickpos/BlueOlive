"""
Seed Debtors (Customers) data for development/testing
Usage: python manage.py seed_debtors
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.debtors.models import Debtor
from apps.settings.models import SalesArea
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed debtors (customers) data for development/testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Debtors Data Seeding...'))
        
        try:
            user = User.objects.filter(is_staff=True).first()
            if not user:
                self.stdout.write(self.style.ERROR('No admin user found. Create one first.'))
                return
            
            # Ensure sales areas exist
            sales_areas = SalesArea.objects.all()
            if not sales_areas.exists():
                self.stdout.write(self.style.ERROR('No Sales Areas found. Run seed_settings first.'))
                return
            
            self._create_debtors(user, sales_areas)
            self.stdout.write(self.style.SUCCESS('✓ Debtors data seeded successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))

    def _create_debtors(self, user, sales_areas):
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
        
        for i, debtor_data in enumerate(debtors_data):
            # Assign sales area in round-robin fashion
            sales_area = sales_area_list[i % len(sales_area_list)]
            debtor_data['sales_area'] = sales_area
            debtor_data['created_by'] = user
            
            obj, created = Debtor.objects.get_or_create(
                account_number=debtor_data['account_number'],
                defaults=debtor_data
            )
            
            if created:
                self.stdout.write(f'  ✓ Created Debtor: {debtor_data["account_number"]} - {debtor_data["name"]}')
            else:
                self.stdout.write(f'  - Debtor already exists: {debtor_data["account_number"]}')
