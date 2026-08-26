from django.core.management.base import BaseCommand
from tenancy.models import Shop, Tenant


class Command(BaseCommand):
    help = "List all tenants and their associated shops"

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant", type=str, help="Show shops for a specific tenant"
        )

    def handle(self, *args, **options):
        if options.get("tenant"):
            # Show shops for specific tenant
            try:
                tenant = int(options["tenant"])
                tenant = Tenant.objects.get(id=tenant)
            except (ValueError, Tenant.DoesNotExist):
                tenant = Tenant.objects.filter(name=options["tenant"]).first()

            if not tenant:
                self.stdout.write(
                    self.style.ERROR(f"Tenant '{options['tenant']}' not found")
                )
                return

            self.stdout.write(
                self.style.SUCCESS(f"\nTenant: {tenant.name} (ID: {tenant.id})")
            )
            shops = tenant.shops.all()
            if shops:
                self.stdout.write("  Shops:")
                for shop in shops:
                    self.stdout.write(
                        f"    - {shop.name} (code: {shop.code}, schema: {shop.schema_name})"
                    )
            else:
                self.stdout.write("  No shops found")
        else:
            # Show all tenants and shops
            tenants = Tenant.objects.all()
            if not tenants:
                self.stdout.write(self.style.WARNING("No tenants found"))
                return

            for tenant in tenants:
                self.stdout.write(
                    self.style.SUCCESS(f"\nTenant: {tenant.name} (ID: {tenant.id})")
                )
                shops = tenant.shops.all()
                if shops:
                    self.stdout.write("  Shops:")
                    for shop in shops:
                        self.stdout.write(
                            f"    - {shop.name} (code: {shop.code}, schema: {shop.schema_name})"
                        )
                else:
                    self.stdout.write("  No shops found")
