# tenancy/management/commands/cleanup_schema.py
from django.core.management.base import BaseCommand
from tenancy.models import Tenant
from tenancy.shop_manager import cleanup_tables_in_wrong_schema, verify_schema_isolation


class Command(BaseCommand):
    help = "Clean up shop tables incorrectly placed in tenant public schemas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant-slug",
            type=str,
            help="Specific tenant slug to clean (default: all tenants)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned up without actually cleaning",
        )
        parser.add_argument(
            "--verify",
            action="store_true",
            help="Just verify schema isolation without cleaning",
        )

    def handle(self, *args, **options):
        tenant_slug = options.get("tenant_slug")
        dry_run = options.get("dry_run")
        verify_only = options.get("verify")

        # Get tenants to process
        if tenant_slug:
            tenants = Tenant.objects.filter(slug=tenant_slug)
            if not tenants.exists():
                self.stderr.write(self.style.ERROR(f"Tenant not found: {tenant_slug}"))
                return
        else:
            tenants = Tenant.objects.all()

        self.stdout.write(self.style.INFO(f"Processing {tenants.count()} tenant(s)..."))

        for tenant in tenants:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Tenant: {tenant.name} (slug: {tenant.slug})")
            self.stdout.write(f"{'='*60}")

            try:
                # First verify the current state
                result = verify_schema_isolation(tenant)

                if not result["is_valid"]:
                    self.stdout.write(self.style.WARNING("⚠️  Issues found:"))
                    for issue in result["issues"]:
                        self.stdout.write(f"   - {issue}")

                    if result["shop_tables_in_public"]:
                        self.stdout.write(
                            f"\nShop tables in public schema ({len(result['shop_tables_in_public'])}):"
                        )
                        for table in result["shop_tables_in_public"]:
                            self.stdout.write(f"   - {table}")
                else:
                    self.stdout.write(self.style.SUCCESS("✓ Schema isolation is valid"))

                if verify_only:
                    continue

                if dry_run:
                    self.stdout.write(
                        self.style.WARNING("\n⚠️  DRY RUN - No changes will be made")
                    )
                    continue

                # Perform cleanup
                self.stdout.write("\nCleaning up tables...")
                dropped = cleanup_tables_in_wrong_schema(tenant)

                if dropped:
                    self.stdout.write(
                        self.style.SUCCESS(f"\n✓ Dropped {len(dropped)} tables:")
                    )
                    for table in dropped:
                        self.stdout.write(f"   - {table}")
                else:
                    self.stdout.write("No tables needed cleanup")

                # Verify again after cleanup
                result = verify_schema_isolation(tenant)
                if result["is_valid"]:
                    self.stdout.write(
                        self.style.SUCCESS("✓ Schema isolation verified after cleanup")
                    )
                else:
                    self.stderr.write(
                        self.style.ERROR("⚠️  Still has issues after cleanup")
                    )
                    for issue in result["issues"]:
                        self.stderr.write(f"   - {issue}")

            except Exception as e:
                self.stderr.write(
                    self.style.ERROR(f"✗ Error processing tenant: {str(e)}")
                )
                import traceback

                traceback.print_exc()

        self.stdout.write(self.style.SUCCESS("\n✓ Done!"))
