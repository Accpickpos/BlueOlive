"""
Seed Settings data for development/testing
Usage: 
    python manage.py seed_settings                      # Seeds first tenant
    python manage.py seed_settings --tenant-id 1        # Seeds specific tenant
    python manage.py seed_settings --tenant-slug slug
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.settings.models import (
    SalesDepartment, SalesArea, IncomeCategory, ExpenseCategory, 
    TaxCode, PaymentMethod, CreditTerms, SystemConfiguration
)
from tenancy.models import Tenant
from tenancy.tenant_context import set_current_tenant, clear_current
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed settings data for development/testing for a specific tenant'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant-id',
            type=int,
            help='Tenant ID to seed data for'
        )
        parser.add_argument(
            '--tenant-slug',
            type=str,
            help='Tenant slug to seed data for'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Settings Data Seeding...'))
        
        try:
            # Get the tenant to seed
            tenant = self._get_tenant(options)
            if not tenant:
                return
            
            # Set tenant context
            set_current_tenant(tenant)
            
            user = User.objects.filter(is_staff=True).first()
            if not user:
                self.stdout.write(self.style.WARNING('No admin user found. Create one first.'))
                return
            
            # Create Sales Departments
            self._create_sales_departments(user)
            
            # Create Sales Areas
            self._create_sales_areas(user)
            
            # Create Tax Codes
            self._create_tax_codes(user)
            
            # Create Payment Methods
            self._create_payment_methods(user)
            
            # Create Credit Terms
            self._create_credit_terms(user)
            
            # Create Income Categories
            self._create_income_categories(user)
            
            # Create Expense Categories
            self._create_expense_categories(user)
            
            self.stdout.write(self.style.SUCCESS('✓ Settings data seeded successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
        finally:
            clear_current()

    def _get_tenant(self, options):
        """Get the tenant to seed data for."""
        tenant_id = options.get('tenant_id')
        tenant_slug = options.get('tenant_slug')
        
        if tenant_id:
            try:
                return Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tenant with ID {tenant_id} not found'))
                return None
        
        if tenant_slug:
            try:
                return Tenant.objects.get(slug=tenant_slug)
            except Tenant.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Tenant with slug "{tenant_slug}" not found'))
                return None
        
        # Use first tenant by default
        tenant = Tenant.objects.first()
        if not tenant:
            self.stdout.write(self.style.ERROR('No tenants found in the system'))
            return None
        
        self.stdout.write(f'  Using tenant: {tenant.name}')
        return tenant

    def _create_sales_departments(self, user):
        departments = [
            {'number': 1, 'name': 'Electronics'},
            {'number': 2, 'name': 'Furniture'},
            {'number': 3, 'name': 'Clothing'},
            {'number': 4, 'name': 'Books'},
            {'number': 5, 'name': 'Hardware'},
        ]
        
        for dept in departments:
            obj, created = SalesDepartment.objects.get_or_create(
                number=dept['number'],
                defaults={
                    'name': dept['name'],
                    'created_by': user,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created Department: {dept["name"]}')
            else:
                self.stdout.write(f'  - Department already exists: {dept["name"]}')

    def _create_sales_areas(self, user):
        from tenancy.models import Shop
        
        # Get the first shop or create default
        shop = Shop.objects.first()
        if not shop:
            self.stdout.write(self.style.WARNING('  ⚠️  No shops found. Skipping sales areas.'))
            return
        
        areas = [
            {'number': 1, 'name': 'Metropolitan Area'},
            {'number': 2, 'name': 'Suburban Area'},
            {'number': 3, 'name': 'Rural Area'},
        ]
        
        for area in areas:
            obj, created = SalesArea.objects.get_or_create(
                number=area['number'],
                defaults={
                    'name': shop,  # ForeignKey to Shop
                    'created_by': user,
                    'is_active': True,
                    'commission_rate': Decimal('0.00')
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created Sales Area {area["number"]}: {area["name"]}')
            else:
                self.stdout.write(f'  - Sales Area {area["number"]} already exists')

    def _create_tax_codes(self, user):
        taxes = [
            {'code': 2, 'description': 'Zero Rated 0%', 'rate': Decimal('0.00')},
            {'code': 1, 'description': 'Standard Rate 14%', 'rate': Decimal('14.00')},
            {'code': 3, 'description': 'Reduced Rate 8%', 'rate': Decimal('8.00')},
        ]
        
        for tax in taxes:
            obj, created = TaxCode.objects.get_or_create(
                code=tax['code'],
                defaults={
                    'description': tax['description'],
                    'rate': tax['rate'],
                    'created_by': user,
                    'is_active': True,
                    'is_default': tax['code'] == 1  # Make code 1 default
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created Tax Code: {tax["code"]} - {tax["description"]}')
            else:
                self.stdout.write(f'  - Tax Code already exists: {tax["code"]}')

    def _create_payment_methods(self, user):
        methods = [
            {'code': 'CASH', 'name': 'Cash', 'requires_reference': False, 'is_electronic': False},
            {'code': 'CHQ', 'name': 'Cheque', 'requires_reference': True, 'is_electronic': False},
            {'code': 'CC', 'name': 'Credit Card', 'requires_reference': True, 'is_electronic': True},
            {'code': 'EFT', 'name': 'Electronic Transfer', 'requires_reference': True, 'is_electronic': True},
            {'code': 'OTHER', 'name': 'Other', 'requires_reference': False, 'is_electronic': False},
        ]
        
        for method in methods:
            obj, created = PaymentMethod.objects.get_or_create(
                code=method['code'],
                defaults={
                    'name': method['name'],
                    'requires_reference': method['requires_reference'],
                    'is_electronic': method['is_electronic'],
                    'created_by': user,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created Payment Method: {method["name"]}')
            else:
                self.stdout.write(f'  - Payment Method already exists: {method["name"]}')

    def _create_credit_terms(self, user):
        terms = [
            {'days': 0, 'description': 'Cash On Delivery'},
            {'days': 30, 'description': '30 Days'},
            {'days': 60, 'description': '60 Days'},
            {'days': 90, 'description': '90 Days'},
        ]
        
        for term in terms:
            obj, created = CreditTerms.objects.get_or_create(
                days=term['days'],
                defaults={
                    'description': term['description'],
                    'created_by': user,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created Credit Term: {term["description"]}')
            else:
                self.stdout.write(f'  - Credit Term already exists: {term["description"]}')

    def _create_income_categories(self, user):
        categories = [
            {'number': 1, 'name': 'Sales Income'},
            {'number': 2, 'name': 'Service Income'},
            {'number': 3, 'name': 'Interest Income'},
            {'number': 4, 'name': 'Other Income'},
        ]
        
        for cat in categories:
            obj, created = IncomeCategory.objects.get_or_create(
                number=cat['number'],
                defaults={
                    'name': cat['name'],
                    'created_by': user,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created Income Category: {cat["name"]}')
            else:
                self.stdout.write(f'  - Income Category already exists: {cat["name"]}')

    def _create_expense_categories(self, user):
        categories = [
            {'number': 1, 'name': 'Rent', 'category_type': 'BOTH'},
            {'number': 2, 'name': 'Utilities', 'category_type': 'BOTH'},
            {'number': 3, 'name': 'Salaries', 'category_type': 'BOTH'},
            {'number': 4, 'name': 'Maintenance', 'category_type': 'BOTH'},
            {'number': 5, 'name': 'Transport', 'category_type': 'BOTH'},
            {'number': 6, 'name': 'Other Expenses', 'category_type': 'BOTH'},
        ]
        
        for cat in categories:
            obj, created = ExpenseCategory.objects.get_or_create(
                number=cat['number'],
                defaults={
                    'name': cat['name'],
                    'category_type': cat['category_type'],
                    'created_by': user,
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✓ Created Expense Category: {cat["name"]}')
            else:
                self.stdout.write(f'  - Expense Category already exists: {cat["name"]}')
