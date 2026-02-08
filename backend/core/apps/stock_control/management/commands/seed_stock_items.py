"""
Seed Stock Items data for development/testing
Usage: python manage.py seed_stock_items
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.stock_control.models import StockItem
from apps.settings.models import SalesDepartment, TaxCode
from apps.creditors.models import Creditor
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed stock items data for development/testing'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Stock Items Data Seeding...'))
        
        try:
            user = User.objects.filter(is_staff=True).first()
            if not user:
                self.stdout.write(self.style.ERROR('No admin user found. Create one first.'))
                return
            
            # Ensure departments exist
            departments = SalesDepartment.objects.all()
            if not departments.exists():
                self.stdout.write(self.style.ERROR('No Sales Departments found. Run seed_settings first.'))
                return
            
            # Get tax code (code=1 is default 14%)
            tax_code = TaxCode.objects.filter(code=1).first()
            if not tax_code:
                self.stdout.write(self.style.ERROR('No Tax Code 1 (Standard) found. Run seed_settings first.'))
                return
            
            # Get creditors (optional)
            creditors = list(Creditor.objects.all())
            
            self._create_stock_items(user, departments, tax_code, creditors)
            self.stdout.write(self.style.SUCCESS('✓ Stock Items data seeded successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))

    def _create_stock_items(self, user, departments, tax_code, creditors):
        dept_list = list(departments)
        creditor_list = creditors if creditors else [None]
        
        stock_items_data = [
            # Electronics
            {
                'stock_code': 'ELEC001',
                'description': 'Laptop Computer 15inch',
                'department': 0,
                'cost_price': Decimal('450.00'),
                'average_cost': Decimal('450.00'),
                'selling_price_1': Decimal('699.99'),
                'selling_price_2': Decimal('679.99'),
                'selling_price_3': Decimal('659.99'),
                'markup_1': Decimal('55.56'),
                'markup_2': Decimal('51.11'),
                'markup_3': Decimal('46.67'),
                'quantity_on_hand': Decimal('15.00'),
                'reorder_quantity': Decimal('5.00'),
                'maximum_discount_percent': Decimal('10.00'),
            },
            {
                'stock_code': 'ELEC002',
                'description': 'Wireless Mouse',
                'department': 0,
                'cost_price': Decimal('12.50'),
                'average_cost': Decimal('12.50'),
                'selling_price_1': Decimal('24.99'),
                'selling_price_2': Decimal('22.99'),
                'selling_price_3': Decimal('20.99'),
                'markup_1': Decimal('99.92'),
                'markup_2': Decimal('83.92'),
                'markup_3': Decimal('67.92'),
                'quantity_on_hand': Decimal('50.00'),
                'reorder_quantity': Decimal('20.00'),
                'maximum_discount_percent': Decimal('15.00'),
            },
            {
                'stock_code': 'ELEC003',
                'description': 'USB-C Cable 2m',
                'department': 0,
                'cost_price': Decimal('2.50'),
                'average_cost': Decimal('2.50'),
                'selling_price_1': Decimal('7.99'),
                'selling_price_2': Decimal('6.99'),
                'selling_price_3': Decimal('5.99'),
                'markup_1': Decimal('219.60'),
                'markup_2': Decimal('179.60'),
                'markup_3': Decimal('139.60'),
                'quantity_on_hand': Decimal('200.00'),
                'reorder_quantity': Decimal('100.00'),
                'maximum_discount_percent': Decimal('20.00'),
            },
            # Furniture
            {
                'stock_code': 'FURN001',
                'description': 'Office Chair - Ergonomic',
                'department': 1,
                'cost_price': Decimal('120.00'),
                'average_cost': Decimal('120.00'),
                'selling_price_1': Decimal('249.99'),
                'selling_price_2': Decimal('229.99'),
                'selling_price_3': Decimal('209.99'),
                'markup_1': Decimal('108.32'),
                'markup_2': Decimal('91.66'),
                'markup_3': Decimal('75.00'),
                'quantity_on_hand': Decimal('20.00'),
                'reorder_quantity': Decimal('5.00'),
                'maximum_discount_percent': Decimal('5.00'),
            },
            {
                'stock_code': 'FURN002',
                'description': 'Desk Lamp LED',
                'department': 1,
                'cost_price': Decimal('25.00'),
                'average_cost': Decimal('25.00'),
                'selling_price_1': Decimal('49.99'),
                'selling_price_2': Decimal('44.99'),
                'selling_price_3': Decimal('39.99'),
                'markup_1': Decimal('99.96'),
                'markup_2': Decimal('79.96'),
                'markup_3': Decimal('59.96'),
                'quantity_on_hand': Decimal('40.00'),
                'reorder_quantity': Decimal('15.00'),
                'maximum_discount_percent': Decimal('10.00'),
            },
            # Clothing
            {
                'stock_code': 'CLTH001',
                'description': 'Cotton T-Shirt Medium',
                'department': 2,
                'cost_price': Decimal('8.00'),
                'average_cost': Decimal('8.00'),
                'selling_price_1': Decimal('17.99'),
                'selling_price_2': Decimal('15.99'),
                'selling_price_3': Decimal('13.99'),
                'markup_1': Decimal('124.88'),
                'markup_2': Decimal('99.88'),
                'markup_3': Decimal('74.88'),
                'quantity_on_hand': Decimal('100.00'),
                'reorder_quantity': Decimal('50.00'),
                'maximum_discount_percent': Decimal('25.00'),
            },
            {
                'stock_code': 'CLTH002',
                'description': 'Denim Jeans Size 32',
                'department': 2,
                'cost_price': Decimal('35.00'),
                'average_cost': Decimal('35.00'),
                'selling_price_1': Decimal('79.99'),
                'selling_price_2': Decimal('69.99'),
                'selling_price_3': Decimal('59.99'),
                'markup_1': Decimal('128.54'),
                'markup_2': Decimal('99.97'),
                'markup_3': Decimal('71.40'),
                'quantity_on_hand': Decimal('60.00'),
                'reorder_quantity': Decimal('20.00'),
                'maximum_discount_percent': Decimal('15.00'),
            },
            # Books
            {
                'stock_code': 'BOOK001',
                'description': 'Python Programming Guide',
                'department': 3,
                'cost_price': Decimal('18.00'),
                'average_cost': Decimal('18.00'),
                'selling_price_1': Decimal('34.99'),
                'selling_price_2': Decimal('32.99'),
                'selling_price_3': Decimal('29.99'),
                'markup_1': Decimal('94.39'),
                'markup_2': Decimal('83.28'),
                'markup_3': Decimal('66.61'),
                'quantity_on_hand': Decimal('30.00'),
                'reorder_quantity': Decimal('10.00'),
                'maximum_discount_percent': Decimal('5.00'),
            },
            # Hardware
            {
                'stock_code': 'HARD001',
                'description': '16oz Claw Hammer',
                'department': 4,
                'cost_price': Decimal('15.00'),
                'average_cost': Decimal('15.00'),
                'selling_price_1': Decimal('29.99'),
                'selling_price_2': Decimal('27.99'),
                'selling_price_3': Decimal('24.99'),
                'markup_1': Decimal('99.93'),
                'markup_2': Decimal('86.60'),
                'markup_3': Decimal('66.60'),
                'quantity_on_hand': Decimal('80.00'),
                'reorder_quantity': Decimal('30.00'),
                'maximum_discount_percent': Decimal('20.00'),
            },
            {
                'stock_code': 'HARD002',
                'description': 'Screwdriver Set 6pc',
                'department': 4,
                'cost_price': Decimal('12.00'),
                'average_cost': Decimal('12.00'),
                'selling_price_1': Decimal('24.99'),
                'selling_price_2': Decimal('22.99'),
                'selling_price_3': Decimal('19.99'),
                'markup_1': Decimal('108.25'),
                'markup_2': Decimal('91.58'),
                'markup_3': Decimal('66.58'),
                'quantity_on_hand': Decimal('120.00'),
                'reorder_quantity': Decimal('40.00'),
                'maximum_discount_percent': Decimal('15.00'),
            },
        ]
        
        for i, item_data in enumerate(stock_items_data):
            # Assign department and supplier
            dept_index = item_data['department']
            dept = dept_list[dept_index] if dept_index < len(dept_list) else dept_list[0]
            item_data['department'] = dept
            
            creditor = creditor_list[i % len(creditor_list)]
            item_data['supplier'] = creditor
            
            if tax_code:
                item_data['tax_code'] = tax_code
            
            obj, created = StockItem.objects.get_or_create(
                stock_code=item_data['stock_code'],
                defaults=item_data
            )
            
            if created:
                self.stdout.write(f'  ✓ Created Stock Item: {item_data["stock_code"]} - {item_data["description"]}')
            else:
                self.stdout.write(f'  - Stock Item already exists: {item_data["stock_code"]}')
