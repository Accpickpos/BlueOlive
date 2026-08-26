"""
Seed Creditors (Suppliers) data for development/testing
Usage:
    python manage.py seed_creditors                     # Seeds first tenant
    python manage.py seed_creditors --tenant-id 1       # Seeds specific tenant
    python manage.py seed_creditors --tenant-slug slug  # Seeds specific tenant by slug
    python manage.py seed_creditors --dry-run            # Show what would be seeded
"""

from decimal import Decimal

from apps.creditors.models import Creditor
from apps.settings.management.commands.base_seed_command import BaseSeedCommand
from apps.settings.models import CreditTerms, SalesArea


class Command(BaseSeedCommand):
    COMMAND_TITLE = "Seeding Creditors Data"
    COMMAND_DESCRIPTION = "Creditors (suppliers)"
    STEP_NUMBER = "3/4"
    help = "Seed creditors (suppliers) data for development/testing"

    def seed(self, user, tenant, shop, dry_run=False, **options):
        """Seed creditors data."""

        # Validate dependencies
        credit_terms = CreditTerms.objects.first()
        if not credit_terms:
            self.error("No Credit Terms found. Run 'seed_settings' first.")
            return

        sales_areas = list(SalesArea.objects.all())
        if not sales_areas:
            self.error("No Sales Areas found. Run 'seed_settings' first.")
            return

        self.print_section("Creating Creditors (Suppliers)")
        self._create_creditors(user, credit_terms, sales_areas, dry_run)

    def _create_creditors(self, user, credit_terms, sales_areas, dry_run=False):
        """Create creditor records."""
        creditors_data = [
            {
                "supplier_number": "S001",
                "name": "Global Supplies Ltd",
                "contact_person": "Robert Lee",
                "telephone": "555-1001",
                "email": "robert@globalsupplies.com",
                "physical_address_line1": "100 Industrial Avenue",
                "physical_city": "Commerce City",
                "physical_code": "12345",
                "our_account_number": "ACC-001",
                "account_category": "OI",
                "update_selling_price_on_receipt": True,
                "prompt_payment_discount_percent": Decimal("2.00"),
            },
            {
                "supplier_number": "S002",
                "name": "Quality Imports Inc",
                "contact_person": "Lisa Chen",
                "telephone": "555-1002",
                "email": "lisa@qualityimports.com",
                "physical_address_line1": "200 Trade Street",
                "physical_city": "Business Park",
                "physical_code": "54321",
                "our_account_number": "ACC-002",
                "account_category": "OI",
                "update_selling_price_on_receipt": True,
                "prompt_payment_discount_percent": Decimal("1.50"),
            },
            {
                "supplier_number": "S003",
                "name": "Direct Wholesale",
                "contact_person": "James Wilson",
                "telephone": "555-1003",
                "email": "james@directwholesale.com",
                "physical_address_line1": "300 Warehouse Road",
                "physical_city": "Industrial Zone",
                "physical_code": "99999",
                "our_account_number": "ACC-003",
                "account_category": "BBF",
                "update_selling_price_on_receipt": False,
                "prompt_payment_discount_percent": Decimal("0.00"),
            },
            {
                "supplier_number": "S004",
                "name": "Premium Distribution",
                "contact_person": "Angela Martinez",
                "telephone": "555-1004",
                "email": "angela@premiumdist.com",
                "physical_address_line1": "400 Commercial Way",
                "physical_city": "Trade Center",
                "physical_code": "11111",
                "our_account_number": "ACC-004",
                "account_category": "OI",
                "update_selling_price_on_receipt": True,
                "prompt_payment_discount_percent": Decimal("2.50"),
            },
            {
                "supplier_number": "S005",
                "name": "Local Producers Co",
                "contact_person": "Thomas Anderson",
                "telephone": "555-1005",
                "email": "thomas@localproducers.com",
                "physical_address_line1": "500 Factory Lane",
                "physical_city": "Manufacturing District",
                "physical_code": "22222",
                "our_account_number": "ACC-005",
                "account_category": "OI",
                "update_selling_price_on_receipt": False,
                "prompt_payment_discount_percent": Decimal("1.00"),
            },
        ]

        created = 0
        skipped = 0

        for i, creditor_data in enumerate(creditors_data):
            # Assign sales area in round-robin fashion
            sales_area = sales_areas[i % len(sales_areas)]
            creditor_data["sales_area"] = sales_area
            creditor_data["credit_terms"] = credit_terms
            creditor_data["created_by"] = user
            creditor_data["is_active"] = True

            if Creditor.objects.filter(
                supplier_number=creditor_data["supplier_number"]
            ).exists():
                self.skip(
                    f"Creditor {creditor_data['supplier_number']}: {creditor_data['name']} (already exists)"
                )
                skipped += 1
            else:
                if not dry_run:
                    Creditor.objects.create(**creditor_data)
                self.success(
                    f"Creditor {creditor_data['supplier_number']}: {creditor_data['name']}"
                )
                created += 1

        if dry_run:
            self.info(f"DRY RUN: Would create {created} creditors")
