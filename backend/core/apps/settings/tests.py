"""
Tests for Settings App
Comprehensive test coverage for all settings models and views
"""

from decimal import Decimal

from apps.settings.models import (
    CostingCategory,
    CreditTerms,
    ExpenseCategory,
    IncomeCategory,
    PaymentMethod,
    SalesArea,
    SalesDepartment,
    SystemConfiguration,
    TaxCode,
)
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


# ═══════════════════════════════════════════════════════════════════════════
# Model Tests
# ═══════════════════════════════════════════════════════════════════════════


class SalesDepartmentModelTest(TestCase):
    """Test SalesDepartment model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

    def test_create_department(self):
        """Test creating a sales department"""
        dept = SalesDepartment.objects.create(
            number=1, name="Electronics", created_by=self.user
        )
        self.assertEqual(dept.number, 1)
        self.assertEqual(dept.name, "Electronics")
        self.assertTrue(dept.is_active)
        self.assertEqual(str(dept), "1 - Electronics")

    def test_gross_profit_calculation(self):
        """Test gross profit percentage calculation"""
        dept = SalesDepartment.objects.create(
            number=2,
            name="Furniture",
            sales_mtd=Decimal("10000.00"),
            profit_mtd=Decimal("2500.00"),
            created_by=self.user,
        )
        self.assertEqual(dept.gross_profit_percent_mtd, 25.0)

    def test_gross_profit_zero_sales(self):
        """Test gross profit calculation with zero sales"""
        dept = SalesDepartment.objects.create(
            number=3, name="Empty Dept", sales_mtd=0, profit_mtd=0, created_by=self.user
        )
        self.assertEqual(dept.gross_profit_percent_mtd, 0)


class SalesAreaModelTest(TestCase):
    """Test SalesArea model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

    def test_create_sales_area(self):
        """Test creating a sales area"""
        area = SalesArea.objects.create(
            number=1,
            name="John Smith",
            commission_rate=Decimal("5.00"),
            created_by=self.user,
        )
        self.assertEqual(area.number, 1)
        self.assertEqual(area.name, "John Smith")
        self.assertEqual(area.commission_rate, Decimal("5.00"))
        self.assertTrue(area.is_active)

    def test_commission_calculation(self):
        """Test commission tracking"""
        area = SalesArea.objects.create(
            number=2,
            name="Jane Doe",
            commission_rate=Decimal("10.00"),
            sales_mtd=Decimal("5000.00"),
            profit_mtd=Decimal("1000.00"),
            commission_mtd=Decimal("500.00"),
            created_by=self.user,
        )
        self.assertEqual(area.gross_profit_percent_mtd, 20.0)


class TaxCodeModelTest(TestCase):
    """Test TaxCode model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

    def test_create_tax_code(self):
        """Test creating a tax code"""
        tax = TaxCode.objects.create(
            code="V15",
            description="Standard VAT 15%",
            rate=Decimal("15.00"),
            created_by=self.user,
        )
        self.assertEqual(tax.code, "V15")
        self.assertEqual(tax.rate, Decimal("15.00"))

    def test_default_tax_code(self):
        """Test setting default tax code"""
        tax = TaxCode.objects.create(
            code="V0",
            description="Zero Rated",
            rate=Decimal("0.00"),
            is_default=True,
            created_by=self.user,
        )
        self.assertTrue(tax.is_default)


class PaymentMethodModelTest(TestCase):
    """Test PaymentMethod model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

    def test_create_payment_method(self):
        """Test creating a payment method"""
        method = PaymentMethod.objects.create(
            code="CASH",
            name="Cash",
            requires_reference=False,
            is_electronic=False,
            created_by=self.user,
        )
        self.assertEqual(method.code, "CASH")
        self.assertFalse(method.requires_reference)
        self.assertFalse(method.is_electronic)

    def test_electronic_payment(self):
        """Test electronic payment method"""
        method = PaymentMethod.objects.create(
            code="EFT",
            name="Electronic Funds Transfer",
            requires_reference=True,
            is_electronic=True,
            created_by=self.user,
        )
        self.assertTrue(method.is_electronic)
        self.assertTrue(method.requires_reference)


class CreditTermsModelTest(TestCase):
    """Test CreditTerms model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

    def test_create_credit_terms(self):
        """Test creating credit terms"""
        terms = CreditTerms.objects.create(
            days=30, description="Net 30", created_by=self.user
        )
        self.assertEqual(terms.days, 30)
        self.assertEqual(str(terms), "30 days - Net 30")


class SystemConfigurationTest(TestCase):
    """Test SystemConfiguration singleton"""

    def test_load_singleton(self):
        """Test loading the singleton instance"""
        config = SystemConfiguration.load()
        self.assertEqual(config.pk, 1)
        self.assertEqual(config.current_period, 1)

    def test_singleton_unique(self):
        """Test that only one config can exist"""
        config1 = SystemConfiguration.load()
        config2 = SystemConfiguration.load()
        self.assertEqual(config1.pk, config2.pk)

    def test_default_values(self):
        """Test default configuration values"""
        config = SystemConfiguration.load()
        self.assertEqual(config.currency_symbol, "R")
        self.assertEqual(config.decimal_places, 2)
        self.assertFalse(config.enable_negative_stock)


# ═══════════════════════════════════════════════════════════════════════════
# API View Tests
# ═══════════════════════════════════════════════════════════════════════════


class SalesDepartmentAPITest(APITestCase):
    """Test SalesDepartment API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_departments(self):
        """Test listing departments"""
        SalesDepartment.objects.create(
            number=1, name="Electronics", created_by=self.user
        )
        SalesDepartment.objects.create(number=2, name="Furniture", created_by=self.user)

        response = self.client.get("/api/v1/settings/departments/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_create_department(self):
        """Test creating a department"""
        data = {"number": 1, "name": "Electronics"}
        response = self.client.post("/api/v1/settings/departments/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SalesDepartment.objects.count(), 1)

    def test_department_validation(self):
        """Test department number validation"""
        # Create first department
        SalesDepartment.objects.create(
            number=1, name="Electronics", created_by=self.user
        )

        # Try to create duplicate
        data = {"number": 1, "name": "Duplicate"}
        response = self.client.post("/api/v1/settings/departments/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deactivate_department(self):
        """Test soft delete (deactivate)"""
        dept = SalesDepartment.objects.create(
            number=1, name="Electronics", created_by=self.user
        )
        response = self.client.post(
            f"/api/v1/settings/departments/{dept.id}/deactivate/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dept.refresh_from_db()
        self.assertFalse(dept.is_active)

    def test_activate_department(self):
        """Test reactivating a department"""
        dept = SalesDepartment.objects.create(
            number=1, name="Electronics", is_active=False, created_by=self.user
        )
        response = self.client.post(f"/api/v1/settings/departments/{dept.id}/activate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        dept.refresh_from_db()
        self.assertTrue(dept.is_active)

    def test_active_only_filter(self):
        """Test filtering active only"""
        SalesDepartment.objects.create(
            number=1, name="Active", is_active=True, created_by=self.user
        )
        SalesDepartment.objects.create(
            number=2, name="Inactive", is_active=False, created_by=self.user
        )

        response = self.client.get("/api/v1/settings/departments/active_only/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class SalesAreaAPITest(APITestCase):
    """Test SalesArea API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_list_sales_areas(self):
        """Test listing sales areas"""
        SalesArea.objects.create(number=1, name="John Smith", created_by=self.user)
        SalesArea.objects.create(number=2, name="Jane Doe", created_by=self.user)

        response = self.client.get("/api/v1/settings/sales-areas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_commission_rate_validation(self):
        """Test commission rate validation"""
        data = {"number": 1, "name": "Test", "commission_rate": 150}
        response = self.client.post("/api/v1/settings/sales-areas/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaxCodeAPITest(APITestCase):
    """Test TaxCode API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_default_tax_code(self):
        """Test getting default tax code"""
        TaxCode.objects.create(
            code="V15",
            description="Standard VAT",
            rate=Decimal("15.00"),
            is_default=True,
            created_by=self.user,
        )

        response = self.client.get("/api/v1/settings/tax-codes/default/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["code"], "V15")

    def test_set_default_tax_code(self):
        """Test setting a tax code as default"""
        tax1 = TaxCode.objects.create(
            code="V15",
            description="Standard VAT",
            rate=Decimal("15.00"),
            is_default=True,
            created_by=self.user,
        )
        tax2 = TaxCode.objects.create(
            code="V0",
            description="Zero Rated",
            rate=Decimal("0.00"),
            created_by=self.user,
        )

        # Set V0 as default
        response = self.client.post(
            f"/api/v1/settings/tax-codes/{tax2.id}/set_default/"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tax1.refresh_from_db()
        tax2.refresh_from_db()
        self.assertFalse(tax1.is_default)
        self.assertTrue(tax2.is_default)


class PaymentMethodAPITest(APITestCase):
    """Test PaymentMethod API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_electronic_methods(self):
        """Test filtering electronic payment methods"""
        PaymentMethod.objects.create(
            code="CASH", name="Cash", is_electronic=False, created_by=self.user
        )
        PaymentMethod.objects.create(
            code="EFT", name="EFT", is_electronic=True, created_by=self.user
        )

        response = self.client.get("/api/v1/settings/payment-methods/electronic/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_cash_based_methods(self):
        """Test filtering cash-based payment methods"""
        PaymentMethod.objects.create(
            code="CASH", name="Cash", is_electronic=False, created_by=self.user
        )

        response = self.client.get("/api/v1/settings/payment-methods/cash_based/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)


class SystemConfigurationAPITest(APITestCase):
    """Test SystemConfiguration API endpoints"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_configuration(self):
        """Test getting system configuration"""
        response = self.client.get("/api/v1/settings/system-config/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_configuration(self):
        """Test updating system configuration"""
        data = {
            "shop_name": "Test Shop",
            "shop_email": "test@shop.com",
            "currency_symbol": "R",
        }
        response = self.client.patch("/api/v1/settings/system-config/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cannot_create_second_config(self):
        """Test that singleton cannot be bypassed"""
        # Try to POST (create) - should fail
        data = {"shop_name": "Another Shop"}
        response = self.client.post("/api/v1/settings/system-config/", data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_delete_config(self):
        """Test that configuration cannot be deleted"""
        response = self.client.delete("/api/v1/settings/system-config/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_advance_period(self):
        """Test advancing accounting period"""
        response = self.client.post("/api/v1/settings/system-config/advance_period/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Period advanced", response.data["message"])


# ═══════════════════════════════════════════════════════════════════════════
# Authentication Tests
# ═══════════════════════════════════════════════════════════════════════════


class AuthenticationTest(APITestCase):
    """Test authentication requirements"""

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are rejected"""
        response = self.client.get("/api/v1/settings/departments/")
        # Might be 401 or 403 depending on configuration
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )
