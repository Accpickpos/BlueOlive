# tenancy/management/commands/populate_shop_subdomains.py
"""
Management command to populate subdomain field for existing shops that don't have one.
Run with: python manage.py populate_shop_subdomains
"""

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from tenancy.models import Shop


class Command(BaseCommand):
    help = 'Populate subdomain field for shops that are missing it'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # Find shops without subdomains
        shops_without_subdomain = Shop.objects.filter(subdomain__isnull=True) | Shop.objects.filter(subdomain='')
        total_count = shops_without_subdomain.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('All shops already have subdomains!'))
            return
        
        self.stdout.write(f'Found {total_count} shops without subdomains')
        
        updated_count = 0
        for shop in shops_without_subdomain:
            # Generate subdomain from shop name
            new_subdomain = slugify(shop.name)
            
            # Handle empty slugs (e.g., shop names with only special characters)
            if not new_subdomain:
                new_subdomain = f"shop-{shop.id}"
            
            # Check for duplicates within the same tenant
            counter = 1
            original_subdomain = new_subdomain
            while Shop.objects.filter(tenant=shop.tenant, subdomain=new_subdomain).exclude(id=shop.id).exists():
                new_subdomain = f"{original_subdomain}-{counter}"
                counter += 1
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'[DRY RUN] Would update Shop "{shop.name}" (ID: {shop.id}) with subdomain: {new_subdomain}'
                    )
                )
            else:
                shop.subdomain = new_subdomain
                shop.save(update_fields=['subdomain'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated Shop "{shop.name}" (ID: {shop.id}) with subdomain: {new_subdomain}'
                    )
                )
                updated_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\n[DRY RUN] Would update {total_count} shops. Run without --dry-run to apply changes.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccessfully updated {updated_count} shops with subdomains!'
                )
            )