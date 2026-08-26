"""
Seed Settings data for development/testing
Usage:
    python manage.py seed_settings                      # Seeds first tenant
    python manage.py seed_settings --tenant-id 1        # Seeds specific tenant
    python manage.py seed_settings --tenant-slug slug   # Seeds specific tenant by slug
    python manage.py seed_settings --dry-run             # Show what would be seeded
"""

from decimal import Decimal

from apps.settings.management.commands.base_seed_command import BaseSeedCommand
from apps.settings.models import (
    CreditTerms,
    ExpenseCategory,
    IncomeCategory,
    PaymentMethod,
    SalesArea,
    SalesDepartment,
    SystemConfiguration,
    TaxCode,
)
from tenancy.models import Shop


class Command(BaseSeedCommand):
    COMMAND_TITLE = "Seeding Settings Data"
    COMMAND_DESCRIPTION = "Settings data"
    STEP_NUMBER = "1/4"
    help = "Seed reference/settings data for development/testing"

    def seed(self, user, tenant, shop, dry_run=False, **options):
        """Seed all settings data."""

        self.print_section("Creating Sales Departments")
        self._create_sales_departments(user, dry_run)

        self.print_section("Creating Sales Areas")
        self._create_sales_areas(shop, user, dry_run)

        self.print_section("Creating Tax Codes")
        self._create_tax_codes(user, dry_run)

        self.print_section("Creating Payment Methods")
        self._create_payment_methods(user, dry_run)

        self.print_section("Creating Credit Terms")
        self._create_credit_terms(user, dry_run)

        self.print_section("Creating Income Categories")
        self._create_income_categories(user, dry_run)

        self.print_section("Creating Expense Categories")
        self._create_expense_categories(user, dry_run)

    def _create_sales_departments(self, user, dry_run=False):
        """Create sales departments."""
        departments = [
            {"number": 1, "name": "Electronics"},
            {"number": 2, "name": "Furniture"},
            {"number": 3, "name": "Clothing"},
            {"number": 4, "name": "Books"},
            {"number": 5, "name": "Hardware"},
        ]

        created = 0
        skipped = 0

        for dept in departments:
            if SalesDepartment.objects.filter(number=dept["number"]).exists():
                self.skip(
                    f"Department {dept['number']}: {dept['name']} (already exists)"
                )
                skipped += 1
            else:
                if not dry_run:
                    SalesDepartment.objects.create(
                        number=dept["number"],
                        name=dept["name"],
                        created_by=user,
                        is_active=True,
                    )
                self.success(f"Department {dept['number']}: {dept['name']}")
                created += 1

        if dry_run:
            self.info(f"DRY RUN: Would create {created} departments")

    def _create_sales_areas(self, shop, user, dry_run=False):
        """Create sales areas."""
        if not shop:
            self.error("No shop found. Cannot create sales areas.")
            return

        areas = [
            {"number": 1, "name": "Metropolitan Area"},
            {"number": 2, "name": "Suburban Area"},
            {"number": 3, "name": "Rural Area"},
        ]

        created = 0
        skipped = 0

        for area in areas:
            if SalesArea.objects.filter(number=area["number"]).exists():
                self.skip(
                    f"Sales Area {area['number']}: {area['name']} (already exists)"
                )
                skipped += 1
            else:
                if not dry_run:
                    SalesArea.objects.create(
                        number=area["number"],
                        name=area["name"],
                        shop=shop,
                        created_by=user,
                        is_active=True,
                        commission_rate=Decimal("0.00"),
                    )
                self.success(f"Sales Area {area['number']}: {area['name']}")
                created += 1

        if dry_run:
            self.info(f"DRY RUN: Would create {created} sales areas")

    def _create_tax_codes(self, user, dry_run=False):
        """Create tax codes."""
        taxes = [
            {"code": 2, "description": "Zero Rated 0%", "rate": Decimal("0.00")},
            {"code": 1, "description": "Standard Rate 14%", "rate": Decimal("14.00")},
            {"code": 3, "description": "Reduced Rate 8%", "rate": Decimal("8.00")},
        ]

        created = 0
        skipped = 0

        for tax in taxes:
            if TaxCode.objects.filter(code=tax["code"]).exists():
                self.skip(
                    f"Tax Code {tax['code']}: {tax['description']} (already exists)"
                )
                skipped += 1
            else:
                if not dry_run:
                    TaxCode.objects.create(
                        code=tax["code"],
                        description=tax["description"],
                        rate=tax["rate"],
                        created_by=user,
                        is_active=True,
                        is_default=tax["code"] == 1,
                    )
                self.success(f"Tax Code {tax['code']}: {tax['description']}")
                created += 1

        if dry_run:
            self.info(f"DRY RUN: Would create {created} tax codes")

    def _create_payment_methods(self, user, dry_run=False):
        """Create payment methods."""
        methods = [
            {
                "code": "CASH",
                "name": "Cash",
                "requires_reference": False,
                "is_electronic": False,
            },
            {
                "code": "CHQ",
                "name": "Cheque",
                "requires_reference": True,
                "is_electronic": False,
            },
            {
                "code": "CC",
                "name": "Credit Card",
                "requires_reference": True,
                "is_electronic": True,
            },
            {
                "code": "EFT",
                "name": "Electronic Transfer",
                "requires_reference": True,
                "is_electronic": True,
            },
            {
                "code": "OTHER",
                "name": "Other",
                "requires_reference": False,
                "is_electronic": False,
            },
        ]

        created = 0
        skipped = 0

        for method in methods:
            if PaymentMethod.objects.filter(code=method["code"]).exists():
                self.skip(f"Payment Method: {method['name']} (already exists)")
                skipped += 1
            else:
                if not dry_run:
                    PaymentMethod.objects.create(
                        code=method["code"],
                        name=method["name"],
                        requires_reference=method["requires_reference"],
                        is_electronic=method["is_electronic"],
                        created_by=user,
                        is_active=True,
                    )
                self.success(f"Payment Method: {method['name']}")
                created += 1

        if dry_run:
            self.info(f"DRY RUN: Would create {created} payment methods")

    def _create_credit_terms(self, user, dry_run=False):
        """Create credit terms."""
        terms = [
            {"days": 0, "description": "Cash On Delivery"},
            {"days": 30, "description": "30 Days"},
            {"days": 60, "description": "60 Days"},
            {"days": 90, "description": "90 Days"},
        ]

        created = 0
        skipped = 0

        for term in terms:
            if CreditTerms.objects.filter(days=term["days"]).exists():
                self.skip(f"Credit Term: {term['description']} (already exists)")
                skipped += 1
            else:
                if not dry_run:
                    CreditTerms.objects.create(
                        days=term["days"],
                        description=term["description"],
                        created_by=user,
                        is_active=True,
                    )
                self.success(f"Credit Term: {term['description']}")
                created += 1

        if dry_run:
            self.info(f"DRY RUN: Would create {created} credit terms")

    def _create_income_categories(self, user, dry_run=False):
        """Create income categories."""
        categories = [
            {"number": 1, "name": "Sales Income"},
            {"number": 2, "name": "Service Income"},
            {"number": 3, "name": "Interest Income"},
            {"number": 4, "name": "Other Income"},
        ]

        created = 0
        skipped = 0

        for cat in categories:
            if IncomeCategory.objects.filter(number=cat["number"]).exists():
                self.skip(
                    f"Income Category {cat['number']}: {cat['name']} (already exists)"
                )
                skipped += 1
            else:
                if not dry_run:
                    IncomeCategory.objects.create(
                        number=cat["number"],
                        name=cat["name"],
                        created_by=user,
                        is_active=True,
                    )
                self.success(f"Income Category {cat['number']}: {cat['name']}")
                created += 1

        if dry_run:
            self.info(f"DRY RUN: Would create {created} income categories")

    def _create_expense_categories(self, user, dry_run=False):
        """Create expense categories."""
        categories = [
            {"number": 1, "name": "Rent", "category_type": "BOTH"},
            {"number": 2, "name": "Utilities", "category_type": "BOTH"},
            {"number": 3, "name": "Salaries", "category_type": "BOTH"},
            {"number": 4, "name": "Maintenance", "category_type": "BOTH"},
            {"number": 5, "name": "Transport", "category_type": "BOTH"},
            {"number": 6, "name": "Other Expenses", "category_type": "BOTH"},
        ]

        created = 0
        skipped = 0

        for cat in categories:
            if ExpenseCategory.objects.filter(number=cat["number"]).exists():
                self.skip(
                    f"Expense Category {cat['number']}: {cat['name']} (already exists)"
                )
                skipped += 1
            else:
                if not dry_run:
                    ExpenseCategory.objects.create(
                        number=cat["number"],
                        name=cat["name"],
                        category_type=cat["category_type"],
                        created_by=user,
                        is_active=True,
                    )
                self.success(f"Expense Category {cat['number']}: {cat['name']}")
                created += 1

        if dry_run:
            self.info(f"DRY RUN: Would create {created} expense categories")
