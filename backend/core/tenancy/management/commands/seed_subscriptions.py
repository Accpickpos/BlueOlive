# tenancy/management/commands/seed_subscriptions.py
"""
Management command to seed default subscription plans.
Plans are priced per shop to accommodate multi-shop tenants.
"""
from django.core.management.base import BaseCommand
from tenancy.models import SubscriptionPlan
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed default subscription plans (priced per shop)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without creating',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Plans priced per shop - tenants pay based on number of shops
        plans = [
            {
                'name': 'Starter',
                'slug': 'starter',
                'description': 'Perfect for small businesses with 1 shop. Includes POS, basic stock control, and reports.',
                'price': Decimal('299.00'),  # Per shop
                'setup_fee': Decimal('0.00'),
                'billing_period_days': 30,
                'max_shops': 1,
                'max_users': 3,
                'max_invoices_per_month': 50,
                'features': {
                    'pos': True,
                    'stock_control': True,
                    'basic_reports': True,
                    'debtors': False,
                    'creditors': False,
                    'cash_book': False,
                    'purchase_orders': False,
                    'api_access': False,
                },
                'is_active': True,
                'is_trial': False,
                'sort_order': 1,
            },
            {
                'name': 'Growth',
                'slug': 'growth',
                'description': 'For growing businesses with up to 3 shops. Includes debtors, creditors, and cash book.',
                'price': Decimal('599.00'),  # Per shop
                'setup_fee': Decimal('299.00'),
                'billing_period_days': 30,
                'max_shops': 3,
                'max_users': 8,
                'max_invoices_per_month': 150,
                'features': {
                    'pos': True,
                    'stock_control': True,
                    'basic_reports': True,
                    'debtors': True,
                    'creditors': True,
                    'cash_book': True,
                    'purchase_orders': True,
                    'api_access': False,
                },
                'is_active': True,
                'is_trial': False,
                'sort_order': 2,
            },
            {
                'name': 'Business',
                'slug': 'business',
                'description': 'For established businesses with up to 5 shops. Full features plus API access.',
                'price': Decimal('899.00'),  # Per shop
                'setup_fee': Decimal('499.00'),
                'billing_period_days': 30,
                'max_shops': 5,
                'max_users': 15,
                'max_invoices_per_month': 500,
                'features': {
                    'pos': True,
                    'stock_control': True,
                    'basic_reports': True,
                    'advanced_reports': True,
                    'debtors': True,
                    'creditors': True,
                    'cash_book': True,
                    'purchase_orders': True,
                    'api_access': True,
                },
                'is_active': True,
                'is_trial': False,
                'sort_order': 3,
            },
            {
                'name': 'Enterprise',
                'slug': 'enterprise',
                'description': 'Unlimited shops for large organizations. Priority support and custom branding.',
                'price': Decimal('1499.00'),  # Per shop
                'setup_fee': Decimal('999.00'),
                'billing_period_days': 30,
                'max_shops': 999,  # Unlimited
                'max_users': 50,
                'max_invoices_per_month': 9999,
                'features': {
                    'pos': True,
                    'stock_control': True,
                    'basic_reports': True,
                    'advanced_reports': True,
                    'debtors': True,
                    'creditors': True,
                    'cash_book': True,
                    'purchase_orders': True,
                    'api_access': True,
                    'custom_branding': True,
                    'priority_support': True,
                    'multi_currency': True,
                },
                'is_active': True,
                'is_trial': False,
                'sort_order': 4,
            },
            {
                'name': 'Free Trial',
                'slug': 'trial',
                'description': '14-day free trial to explore all features with 1 shop.',
                'price': Decimal('0.00'),
                'setup_fee': Decimal('0.00'),
                'billing_period_days': 30,
                'max_shops': 1,
                'max_users': 3,
                'max_invoices_per_month': 10,
                'features': {
                    'pos': True,
                    'stock_control': True,
                    'basic_reports': True,
                    'debtors': True,
                    'creditors': True,
                    'cash_book': True,
                    'purchase_orders': True,
                    'api_access': False,
                },
                'is_active': True,
                'is_trial': True,
                'sort_order': 0,
            },
        ]
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
            self.stdout.write('')
            for plan_data in plans:
                price = f"R{plan_data['price']}" if plan_data['price'] > 0 else "FREE"
                self.stdout.write(f"  Would create: {plan_data['name']} - {price}/shop/month")
                self.stdout.write(f"    - Max shops: {plan_data['max_shops']}")
                self.stdout.write(f"    - Max users: {plan_data['max_users']}")
            return
        
        created = 0
        for plan_data in plans:
            plan, was_created = SubscriptionPlan.objects.update_or_create(
                slug=plan_data['slug'],
                defaults=plan_data
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created plan: {plan.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Updated plan: {plan.name}"))
        
        self.stdout.write(self.style.SUCCESS(f"\nCompleted! Created {created} new plans."))
        
        # List all plans
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        self.stdout.write(self.style.HTTP_INFO('Subscription Plans (Priced Per Shop)'))
        self.stdout.write(self.style.HTTP_INFO('=' * 60))
        
        for plan in SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order'):
            price_display = f"R{plan.price}" if plan.price > 0 else "FREE"
            shops_display = f"Up to {plan.max_shops} shops" if plan.max_shops < 999 else "Unlimited shops"
            
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(f"{plan.sort_order}. {plan.name}"))
            self.stdout.write(f"   Price: {price_display} per shop/month")
            self.stdout.write(f"   Setup: R{plan.setup_fee} (one-time)")
            self.stdout.write(f"   Limits: {shops_display}, {plan.max_users} users")
            self.stdout.write(f"   {plan.description}")
            
            # Show key features
            features = []
            if plan.features.get('pos'):
                features.append('POS')
            if plan.features.get('debtors'):
                features.append('Debtors')
            if plan.features.get('creditors'):
                features.append('Creditors')
            if plan.features.get('api_access'):
                features.append('API')
            if plan.features.get('custom_branding'):
                features.append('Custom Branding')
            
            if features:
                self.stdout.write(f"   Features: {', '.join(features)}")
