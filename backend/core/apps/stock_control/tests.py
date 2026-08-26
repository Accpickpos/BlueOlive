from datetime import timedelta
from decimal import Decimal

from apps.creditors.models import Creditor
from apps.debtors.models import Debtor
from apps.settings.models import SalesDepartment, TaxCode
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from .models import (
    ContractPricing,
    FuturePricing,
    PackBundle,
    PackBundleIngredient,
    SpecialDeal,
    StockItem,
    StockTake,
    StockTakeItem,
    StockTransaction,
)


class StockItemModelTest(TestCase):
    """Test StockItem model calculations and methods"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.tax_code = TaxCode.objects.create(
            tax_code="14A", description="Standard VAT", tax_percent=Decimal("14.00")
        )

        cls.department = SalesDepartment.objects.create(number=1, name="Groceries")

        cls.supplier = Creditor.objects.create(
            account_number="SUP001", name="Test Supplier", contact_person="John Doe"
        )

    def setUp(self):
        """Set up test fixtures"""
        self.stock_item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Product",
            department=self.department,
            supplier=self.supplier,
            tax_code=self.tax_code,
            cost_price=Decimal("100.00"),
            selling_price_1=Decimal("150.00"),
            selling_price_2=Decimal("160.00"),
            selling_price_3=Decimal("170.00"),
            quantity_on_hand=Decimal("50.00"),
        )

    def test_calculate_markup(self):
        """Test markup calculation"""
        markup = self.stock_item.calculate_markup(1)
        expected = ((150 - 100) / 100) * 100  # 50%
        self.assertAlmostEqual(float(markup), expected, places=2)

    def test_calculate_markup_zero_cost(self):
        """Test markup calculation with zero cost price"""
        zero_cost_item = StockItem.objects.create(
            stock_code="FREE001",
            description="Free Item",
            department=self.department,
            cost_price=Decimal("0"),
            selling_price_1=Decimal("100.00"),
            quantity_on_hand=Decimal("10"),
        )
        markup = zero_cost_item.calculate_markup(1)
        self.assertEqual(markup, 0)

    def test_calculate_gross_profit(self):
        """Test gross profit calculation"""
        profit = self.stock_item.calculate_gross_profit(1)
        expected = ((150 - 100) / 150) * 100  # ~33.33%
        self.assertAlmostEqual(float(profit), expected, places=2)

    def test_stock_item_str_representation(self):
        """Test string representation"""
        expected = "TEST001 - Test Product"
        self.assertEqual(str(self.stock_item), expected)

    def test_stock_value_calculation(self):
        """Test total stock value"""
        stock_value = self.stock_item.quantity_on_hand * self.stock_item.cost_price
        expected = Decimal("5000.00")
        self.assertEqual(stock_value, expected)


class SpecialDealModelTest(TestCase):
    """Test SpecialDeal model"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.department = SalesDepartment.objects.create(number=1, name="Groceries")

        cls.stock_item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Product",
            department=cls.department,
            cost_price=Decimal("100.00"),
            selling_price_1=Decimal("150.00"),
            quantity_on_hand=Decimal("50.00"),
        )

    def setUp(self):
        """Set up test fixtures"""
        today = timezone.now().date()
        self.special_deal = SpecialDeal.objects.create(
            stock_item=self.stock_item,
            special_cost_price=Decimal("90.00"),
            special_selling_price_1=Decimal("140.00"),
            start_date=today,
            end_date=today + timedelta(days=7),
            is_active=True,
        )

    def test_is_valid_today(self):
        """Test if special deal is valid for today"""
        self.assertTrue(self.special_deal.is_valid_today())

    def test_is_not_valid_after_end_date(self):
        """Test special deal invalid after end date"""
        expired_deal = SpecialDeal.objects.create(
            stock_item=self.stock_item,
            special_cost_price=Decimal("90.00"),
            special_selling_price_1=Decimal("140.00"),
            start_date=timezone.now().date() - timedelta(days=10),
            end_date=timezone.now().date() - timedelta(days=3),
            is_active=True,
        )
        self.assertFalse(expired_deal.is_valid_today())

    def test_is_not_valid_when_inactive(self):
        """Test special deal invalid when inactive"""
        today = timezone.now().date()
        inactive_deal = SpecialDeal.objects.create(
            stock_item=self.stock_item,
            special_cost_price=Decimal("90.00"),
            special_selling_price_1=Decimal("140.00"),
            start_date=today,
            end_date=today + timedelta(days=7),
            is_active=False,
        )
        self.assertFalse(inactive_deal.is_valid_today())


class StockTransactionModelTest(TestCase):
    """Test StockTransaction model"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.department = SalesDepartment.objects.create(number=1, name="Groceries")

        cls.stock_item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Product",
            department=cls.department,
            cost_price=Decimal("100.00"),
            selling_price_1=Decimal("150.00"),
            quantity_on_hand=Decimal("50.00"),
        )

    def test_create_incoming_transaction(self):
        """Test creating an incoming stock transaction"""
        transaction = StockTransaction.objects.create(
            transaction_type="INCOMING",
            stock_item=self.stock_item,
            quantity_in=Decimal("20.00"),
            unit_cost=Decimal("100.00"),
            reference="PO-001",
        )

        self.assertEqual(transaction.transaction_type, "INCOMING")
        self.assertEqual(transaction.quantity_in, Decimal("20.00"))
        self.assertEqual(transaction.quantity_out, Decimal("0.00"))

    def test_create_sale_transaction(self):
        """Test creating a sale transaction"""
        transaction = StockTransaction.objects.create(
            transaction_type="SALE",
            stock_item=self.stock_item,
            quantity_out=Decimal("5.00"),
            unit_cost=Decimal("100.00"),
            unit_price=Decimal("150.00"),
            reference="INV-001",
        )

        self.assertEqual(transaction.transaction_type, "SALE")
        self.assertEqual(transaction.quantity_out, Decimal("5.00"))
        self.assertEqual(transaction.quantity_in, Decimal("0.00"))


class PackBundleModelTest(TestCase):
    """Test PackBundle model"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.department = SalesDepartment.objects.create(number=1, name="Groceries")

    def setUp(self):
        """Set up test fixtures"""
        self.ingredient1 = StockItem.objects.create(
            stock_code="ING001",
            description="Ingredient 1",
            department=self.department,
            cost_price=Decimal("10.00"),
            quantity_on_hand=Decimal("100"),
        )

        self.ingredient2 = StockItem.objects.create(
            stock_code="ING002",
            description="Ingredient 2",
            department=self.department,
            cost_price=Decimal("20.00"),
            quantity_on_hand=Decimal("100"),
        )

        self.bundle = StockItem.objects.create(
            stock_code="BUNDLE001",
            description="Bundle Product",
            department=self.department,
            cost_price=Decimal("30.00"),
            quantity_on_hand=Decimal("0"),
        )

        self.pack_bundle = PackBundle.objects.create(stock_item=self.bundle)

    def test_bundle_total_cost_calculation(self):
        """Test bundle total cost calculation"""
        PackBundleIngredient.objects.create(
            pack_bundle=self.pack_bundle,
            ingredient_stock=self.ingredient1,
            quantity=Decimal("2.00"),
        )

        PackBundleIngredient.objects.create(
            pack_bundle=self.pack_bundle,
            ingredient_stock=self.ingredient2,
            quantity=Decimal("1.00"),
        )

        total_cost = self.pack_bundle.calculate_total_cost()
        expected = (Decimal("2.00") * Decimal("10.00")) + (
            Decimal("1.00") * Decimal("20.00")
        )
        self.assertEqual(total_cost, expected)


class StockTakeTest(TestCase):
    """Test Stock Take functionality"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.department = SalesDepartment.objects.create(number=1, name="Groceries")

    def setUp(self):
        """Set up test fixtures"""
        self.stock_item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Product",
            department=self.department,
            cost_price=Decimal("100.00"),
            quantity_on_hand=Decimal("50.00"),
        )

        self.stock_take = StockTake.objects.create(
            stock_take_date=timezone.now().date(),
            status="IN_PROGRESS",
            created_by="admin",
        )

    def test_create_stock_take_item(self):
        """Test creating a stock take item"""
        take_item = StockTakeItem.objects.create(
            stock_take=self.stock_take,
            stock_item=self.stock_item,
            quantity_on_hand=Decimal("50.00"),
            quantity_counted=Decimal("48.00"),
            cost_price_at_count=Decimal("100.00"),
        )

        take_item.calculate_variance()
        self.assertEqual(take_item.variance_quantity, Decimal("-2.00"))
        self.assertEqual(take_item.variance_value, Decimal("-200.00"))

    def test_stock_take_string_representation(self):
        """Test stock take string representation"""
        expected = f"Stock Take - {self.stock_take.stock_take_date} (IN_PROGRESS)"
        self.assertEqual(str(self.stock_take), expected)


class ContractPricingTest(TestCase):
    """Test Contract Pricing functionality"""

    @classmethod
    def setUpTestData(cls):
        """Set up test data"""
        cls.department = SalesDepartment.objects.create(number=1, name="Groceries")

        cls.debtor = Debtor.objects.create(
            account_number="DEB001", name="Test Debtor", contact_person="Jane Doe"
        )

    def setUp(self):
        """Set up test fixtures"""
        self.stock_item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Product",
            department=self.department,
            cost_price=Decimal("100.00"),
            quantity_on_hand=Decimal("50"),
        )

    def test_contract_pricing_actual_price(self):
        """Test contract pricing with actual price method"""
        contract = ContractPricing.objects.create(
            debtor=self.debtor,
            stock_item=self.stock_item,
            pricing_method="ACTUAL",
            contract_price=Decimal("120.00"),
        )

        price = contract.get_price()
        self.assertEqual(price, Decimal("120.00"))

    def test_contract_pricing_cost_markup(self):
        """Test contract pricing with cost + markup method"""
        contract = ContractPricing.objects.create(
            debtor=self.debtor,
            stock_item=self.stock_item,
            pricing_method="COST_MARKUP",
            markup_percent=Decimal("20.00"),
        )

        price = contract.get_price(self.stock_item)
        expected = Decimal("100.00") * (1 + Decimal("20.00") / 100)
        self.assertEqual(price, expected)
