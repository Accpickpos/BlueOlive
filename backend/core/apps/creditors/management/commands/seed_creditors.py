"""
Seed Creditors (Suppliers) data for development/testing
Usage: python manage.py seed_creditors
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.creditors.models import Creditor
from apps.settings.models import SalesArea, CreditTerms
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed creditors (suppliers) data for development/testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Creditors Data Seeding...'))
        
        try:
            user = User.objects.filter(is_staff=True).first()
            if not user:
                self.stdout.write(self.style.ERROR('No admin user found. Create one first.'))
                return
            
            # Ensure credit terms exist
            credit_terms = CreditTerms.objects.first()
            if not credit_terms:
                self.stdout.write(self.style.ERROR('No Credit Terms found. Run seed_settings first.'))
                return
            
            # Get sales areas
            sales_areas = list(SalesArea.objects.all())
            if not sales_areas:
                self.stdout.write(self.style.ERROR('No Sales Areas found. Run seed_settings first.'))
                return
            
            self._create_creditors(user, credit_terms, sales_areas)
            self.stdout.write(self.style.SUCCESS('✓ Creditors data seeded successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))

    def _create_creditors(self, user, credit_terms, sales_areas):
        creditors_data = [
            {
                'supplier_number': 'S001',
                'name': 'Global Supplies Ltd',
                'contact_person': 'Robert Lee',
                'telephone': '555-1001',
                'email': 'robert@globalsupplies.com',
                'physical_address_line1': '100 Industrial Avenue',
                'physical_city': 'Commerce City',
                'physical_code': '12345',
                'our_account_number': 'ACC-001',
                'account_category': 'OI',
                'update_selling_price_on_receipt': True,
                'prompt_payment_discount_percent': Decimal('2.00'),
            },
            {
                'supplier_number': 'S002',
                'name': 'Quality Imports Inc',
                'contact_person': 'Lisa Chen',
                'telephone': '555-1002',
                'email': 'lisa@qualityimports.com',
                'physical_address_line1': '200 Trade Street',
                'physical_city': 'Business Park',
                'physical_code': '54321',
                'our_account_number': 'ACC-002',
                'account_category': 'OI',
                'update_selling_price_on_receipt': True,
                'prompt_payment_discount_percent': Decimal('1.50'),
            },
            {
                'supplier_number': 'S003',
                'name': 'Direct Wholesale',
                'contact_person': 'James Wilson',
                'telephone': '555-1003',
                'email': 'james@directwholesale.com',
                'physical_address_line1': '300 Warehouse Road',
                'physical_city': 'Industrial Zone',
                'physical_code': '99999',
                'our_account_number': 'ACC-003',
                'account_category': 'BBF',
                'update_selling_price_on_receipt': False,
                'prompt_payment_discount_percent': Decimal('0.00'),
            },
            {
                'supplier_number': 'S004',
                'name': 'Premium Distribution',
                'contact_person': 'Angela Martinez',
                'telephone': '555-1004',
                'email': 'angela@premiumdist.com',
                'physical_address_line1': '400 Commercial Way',
                'physical_city': 'Trade Center',
                'physical_code': '11111',
                'our_account_number': 'ACC-004',
                'account_category': 'OI',
                'update_selling_price_on_receipt': True,
                'prompt_payment_discount_percent': Decimal('2.50'),
            },
            {
                'supplier_number': 'S005',
                'name': 'Local Producers Co',
                'contact_person': 'Thomas Anderson',
                'telephone': '555-1005',
                'email': 'thomas@localproducers.com',
                'physical_address_line1': '500 Factory Lane',
                'physical_city': 'Manufacturing District',
                'physical_code': '22222',
                'our_account_number': 'ACC-005',
                'account_category': 'OI',
                'update_selling_price_on_receipt': False,
                'prompt_payment_discount_percent': Decimal('1.00'),
            },
        ]
        
        sales_area_list = sales_areas
        
        for i, creditor_data in enumerate(creditors_data):
            # Assign sales area in round-robin fashion
            sales_area = sales_area_list[i % len(sales_area_list)]
            creditor_data['sales_area'] = sales_area
            creditor_data['credit_terms'] = credit_terms
            creditor_data['created_by'] = user
            creditor_data['is_active'] = True
            
            obj, created = Creditor.objects.get_or_create(
                supplier_number=creditor_data['supplier_number'],
                defaults=creditor_data
            )
            
            if created:
                self.stdout.write(f'  ✓ Created Creditor: {creditor_data["supplier_number"]} - {creditor_data["name"]}')
            else:
                self.stdout.write(f'  - Creditor already exists: {creditor_data["supplier_number"]}')
