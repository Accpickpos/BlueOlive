# tenancy/management/commands/rerun_shop_migrations.py
"""
Management command to re-run shop app migrations for all shops in all tenants.

This is needed because shop-specific migrations (debtors, creditors, etc.) are only
applied when a shop is first created. If new migrations are added later, they need
to be manually re-run using this command.

Usage:
    python manage.py rerun_shop_migrations
    python manage.py rerun_shop_migrations --tenant-slug=acme
    python manage.py rerun_shop_migrations --tenant-slug=acme --shop-code=MS001
    python manage.py rerun_shop_migrations --dry-run
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from tenancy.models import Shop, Tenant
from tenancy.shop_manager import migrate_shop_apps

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-run shop app migrations for all shops in all tenants"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-slug",
            type=str,
            help="Specific tenant slug to process (default: all tenants)",
        )
        parser.add_argument(
            "--shop-code",
            type=str,
            help="Specific shop code to process (requires --tenant-slug)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be migrated without actually migrating",
        )
        parser.add_argument(
            "--apps",
            type=str,
            help="Comma-separated list of apps to migrate (default: all shop apps)",
        )

    def handle(self, *args, **options):
        tenant_slug = options.get("tenant_slug")
        shop_code = options.get("shop_code")
        dry_run = options.get("dry_run")
        apps_arg = options.get("apps")

        # Get shop apps to migrate
        shop_app_labels = getattr(settings, "SHOP_APP_LABELS", [])

        if apps_arg:
            # Filter to only specified apps
            requested_apps = [app.strip() for app in apps_arg.split(",")]
            shop_app_labels = [app for app in shop_app_labels if app in requested_apps]
            if not shop_app_labels:
                self.stderr.write(
                    self.style.ERROR(
                        f"None of the specified apps {requested_apps} are in SHOP_APP_LABELS"
                    )
                )
                return

        # Get tenants to process
        if tenant_slug:
            tenants = Tenant.objects.filter(slug=tenant_slug)
            if not tenants.exists():
                self.stderr.write(self.style.ERROR(f"Tenant not found: {tenant_slug}"))
                return
            self.stdout.write(f"Processing tenant: {tenant_slug}")
        else:
            tenants = Tenant.objects.all()

        total_shops = 0
        processed_shops = 0
        failed_shops = 0

        # Count total shops first
        for tenant in tenants:
            if shop_code:
                total_shops += tenant.shops.filter(
                    code=shop_code, is_active=True
                ).count()
            else:
                total_shops += tenant.shops.filter(is_active=True).count()

        self.stdout.write(
            self.style.NOTICE(
                f"Found {total_shops} shop(s) to process across {tenants.count()} tenant(s)"
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("⚠️  DRY RUN - No migrations will be applied")
            )

        self.stdout.write(f"Apps to migrate: {', '.join(shop_app_labels)}")

        # Process each tenant
        for tenant in tenants:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Tenant: {tenant.name} (slug: {tenant.slug})")
            self.stdout.write(f"Database: {tenant.db_alias}")
            self.stdout.write(f"{'='*60}")

            # Get shops for this tenant
            if shop_code:
                shops = tenant.shops.filter(code=shop_code, is_active=True)
            else:
                shops = tenant.shops.filter(is_active=True)

            if not shops.exists():
                self.stdout.write("  No active shops found")
                continue

            for shop in shops:
                processed_shops += 1
                self.stdout.write(
                    f"\n  Shop: {shop.name} (code: {shop.code}, schema: {shop.schema_name})"
                )

                if dry_run:
                    self.stdout.write(self.style.WARNING("    → Would run migrations"))
                    continue

                try:
                    # Run migrations for this shop
                    logger.info(
                        f"Running migrations for shop {shop.schema_name} in tenant {tenant.slug}"
                    )

                    # The migrate_shop_apps function will apply any pending migrations
                    migrate_shop_apps(
                        tenant, shop.schema_name, app_labels=shop_app_labels
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"    ✓ Migrations completed for {shop.name}"
                        )
                    )

                except Exception as e:
                    failed_shops += 1
                    self.stderr.write(self.style.ERROR(f"    ✗ Failed: {str(e)}"))
                    logger.exception(f"Migration failed for shop {shop.schema_name}")

        # Summary
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write("SUMMARY")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"Total shops processed: {processed_shops}")

        if failed_shops > 0:
            self.stdout.write(self.style.ERROR(f"Failed: {failed_shops}"))
        else:
            self.stdout.write(
                self.style.SUCCESS("All migrations completed successfully!")
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n⚠️  This was a dry run - no changes were made")
            )
