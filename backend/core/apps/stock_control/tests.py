from datetime import timedelta
from decimal import Decimal

from apps.creditors.models import Creditor
from apps.debtors.models import Debtor
from apps.settings.models import SalesDepartment, TaxCode
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

from .models import (
    ContractPricing,
    FuturePricing,
    PackBundle,
    PackBundleIngredient,
    SpecialDeal,
    StockItem,
    StockMonthlyStatistic,
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

        cls.debtor = Debtor.objects.create(dno=1001, dname="Test Debtor")

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

    def test_contract_pricing_valid_date_range(self):
        """get_price() returns None outside valid_from/valid_until."""
        today = timezone.now().date()
        contract = ContractPricing.objects.create(
            debtor=self.debtor,
            stock_item=self.stock_item,
            pricing_method="ACTUAL",
            contract_price=Decimal("120.00"),
            valid_from=today - timedelta(days=1),
            valid_until=today + timedelta(days=1),
        )
        self.assertEqual(contract.get_price(), Decimal("120.00"))

        contract.valid_until = today - timedelta(days=1)
        contract.save()
        self.assertIsNone(contract.get_price())

    def test_contract_pricing_unbounded_dates_always_valid(self):
        """Null valid_from/valid_until means unbounded on that side."""
        contract = ContractPricing.objects.create(
            debtor=self.debtor,
            stock_item=self.stock_item,
            pricing_method="ACTUAL",
            contract_price=Decimal("120.00"),
        )
        self.assertEqual(contract.get_price(), Decimal("120.00"))


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class StockTransactionServiceEndpointTest(APITestCase):
    """
    API-level regression test for the bug this whole change fixes: posting
    an INCOMING transaction through /stock-transactions/ used to create
    the row without ever moving quantity_on_hand, and the endpoint had no
    IsStockMover gate at all.

    Overrides CACHES to locmem: DRF's throttle check reads through the
    default cache backend, which is Redis in this project's settings —
    not available in a plain test run, and unrelated to what these tests
    are actually verifying.
    """

    @classmethod
    def setUpTestData(cls):
        cls.department = SalesDepartment.objects.create(number=1, name="Groceries")

    def setUp(self):
        self.item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Product",
            department=self.department,
            cost_price=Decimal("100.00"),
            quantity_on_hand=Decimal("50"),
        )
        # is_superuser=True: ShopUser.save() requires an active tenant
        # context for any non-superuser, which isn't set up in this
        # single-DB test run (DISABLE_TENANT_ROUTER=1) — superuser status
        # only bypasses that save() guard here, it's unrelated to (and
        # doesn't satisfy on its own) the IsStockMover group check below.
        self.mover = User.objects.create_user(
            username="mover",
            email="mover@example.com",
            password="x",
            is_superuser=True,
        )
        self.mover.groups.add(Group.objects.create(name="Cashier"))
        self.plain_user = User.objects.create_user(
            username="plain",
            email="plain@example.com",
            password="x",
            is_superuser=True,
        )

    def test_non_mover_cannot_create_transaction(self):
        self.client.force_authenticate(self.plain_user)
        response = self.client.post(
            reverse("stocktransaction-list"),
            {
                "transaction_type": "INCOMING",
                "stock_item": self.item.stock_code,
                "quantity_in": "5",
                "unit_cost": "100.00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_incoming_transaction_moves_quantity_on_hand(self):
        self.client.force_authenticate(self.mover)
        response = self.client.post(
            reverse("stocktransaction-list"),
            {
                "transaction_type": "INCOMING",
                "stock_item": self.item.stock_code,
                "quantity_in": "5",
                "unit_cost": "100.00",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, Decimal("55"))


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class StockTakeUpdateStockModeTest(APITestCase):
    """
    Phase 2: StockTakeViewSet.update_stock previously always overwrote QOH
    with the counted quantity, with no additive mode and no branching on
    is_after_trading despite those fields existing on the model.
    """

    @classmethod
    def setUpTestData(cls):
        cls.department = SalesDepartment.objects.create(number=1, name="Groceries")

    def setUp(self):
        self.mover = User.objects.create_user(
            username="mover2",
            email="mover2@example.com",
            password="x",
            is_superuser=True,
        )
        self.mover.groups.add(Group.objects.create(name="Cashier"))
        self.client.force_authenticate(self.mover)

        self.item = StockItem.objects.create(
            stock_code="TAKE001",
            description="Take Test Product",
            department=self.department,
            cost_price=Decimal("100.00"),
            quantity_on_hand=Decimal("50"),
        )

    def _make_take(self, **kwargs):
        return StockTake.objects.create(
            stock_take_date=timezone.now().date(), status="IN_PROGRESS", **kwargs
        )

    def _make_item(self, take, counted):
        return StockTakeItem.objects.create(
            stock_take=take,
            stock_item=self.item,
            quantity_on_hand=self.item.quantity_on_hand,
            quantity_counted=counted,
            cost_price_at_count=self.item.cost_price,
            is_counted=True,
        )

    def _update_stock(self, take, **body):
        return self.client.post(
            reverse("stocktake-update-stock", args=[take.id]), body
        )

    def test_overwrite_mode_is_the_default_and_matches_prior_behavior(self):
        take = self._make_take()
        self._make_item(take, Decimal("48"))

        response = self._update_stock(take)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, Decimal("48"))

    def test_additive_mode_adds_counted_as_a_delta(self):
        take = self._make_take()
        self._make_item(take, Decimal("5"))

        response = self._update_stock(take, mode="additive")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, Decimal("55"))  # 50 + 5

    def test_additive_mode_two_counts_sum_correctly(self):
        take = self._make_take()
        item = self._make_item(take, Decimal("5"))

        self._update_stock(take, mode="additive")
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, Decimal("55"))

        # A second additive pass (e.g. a follow-up recount) adds again on
        # top of the now-updated QOH.
        item.quantity_counted = Decimal("3")
        item.save(update_fields=["quantity_counted"])
        take.status = "IN_PROGRESS"
        take.save(update_fields=["status"])
        self._update_stock(take, mode="additive")
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, Decimal("58"))  # 55 + 3

    def test_invalid_mode_rejected(self):
        take = self._make_take()
        self._make_item(take, Decimal("48"))
        response = self._update_stock(take, mode="bogus")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_additive_and_after_trading_together_rejected(self):
        take = self._make_take(
            is_after_trading=True, trading_start_date=timezone.now()
        )
        self._make_item(take, Decimal("48"))
        response = self._update_stock(take, mode="additive")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_after_trading_without_start_date_rejected(self):
        take = self._make_take(is_after_trading=True)
        self._make_item(take, Decimal("48"))
        response = self._update_stock(take)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_after_trading_preserves_movement_since_count_started(self):
        """
        An INCOMING transaction posted after trading_start_date must
        survive update_stock rather than being wiped out by the earlier
        physical count: target = counted + net movement since
        trading_start_date.
        """
        trading_start = timezone.now() - timedelta(hours=2)
        take = self._make_take(is_after_trading=True, trading_start_date=trading_start)
        # Physical count read 48 at count time (QOH was 50 then).
        self._make_item(take, Decimal("48"))

        # Real stock movement after the count started: +10 received.
        StockTransaction.objects.create(
            transaction_type="INCOMING",
            stock_item=self.item,
            quantity_in=Decimal("10"),
            unit_cost=Decimal("100.00"),
        )
        self.item.quantity_on_hand = Decimal("60")  # 50 + 10, as INCOMING would apply
        self.item.save(update_fields=["quantity_on_hand"])

        response = self._update_stock(take)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        # target = counted(48) + net_movement(+10) = 58
        self.assertEqual(self.item.quantity_on_hand, Decimal("58"))


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class SpecialDealBulkDepartmentTest(APITestCase):
    """Phase 3: bulk-department fans out one SpecialDeal per active item in a department."""

    @classmethod
    def setUpTestData(cls):
        cls.department = SalesDepartment.objects.create(number=2, name="Hardware")
        cls.other_department = SalesDepartment.objects.create(number=3, name="Other")

    def setUp(self):
        self.mover = User.objects.create_user(
            username="mover3",
            email="mover3@example.com",
            password="x",
            is_superuser=True,
        )
        self.mover.groups.add(Group.objects.create(name="Cashier"))
        self.client.force_authenticate(self.mover)

        self.item1 = StockItem.objects.create(
            stock_code="BD001",
            description="Item 1",
            department=self.department,
            cost_price=Decimal("50.00"),
            selling_price_1=Decimal("100.00"),
            selling_price_2=Decimal("110.00"),
            selling_price_3=Decimal("120.00"),
        )
        self.item2 = StockItem.objects.create(
            stock_code="BD002",
            description="Item 2",
            department=self.department,
            cost_price=Decimal("20.00"),
            selling_price_1=Decimal("40.00"),
            selling_price_2=Decimal("44.00"),
            selling_price_3=Decimal("48.00"),
        )
        self.inactive_item = StockItem.objects.create(
            stock_code="BD003",
            description="Inactive",
            department=self.department,
            cost_price=Decimal("10.00"),
            selling_price_1=Decimal("20.00"),
            is_active=False,
        )
        self.other_dept_item = StockItem.objects.create(
            stock_code="BD004",
            description="Other dept",
            department=self.other_department,
            cost_price=Decimal("10.00"),
            selling_price_1=Decimal("20.00"),
        )

    def test_percentage_decrease_creates_one_deal_per_active_item(self):
        response = self.client.post(
            reverse("specialdeal-bulk-department"),
            {
                "department": self.department.pk,
                "start_date": timezone.now().date().isoformat(),
                "end_date": (timezone.now().date() + timedelta(days=7)).isoformat(),
                "increase_decrease": "-",
                "percentage_rand": "P",
                "amount": "10",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["count"], 2)

        deal1 = SpecialDeal.objects.get(stock_item=self.item1)
        self.assertEqual(deal1.special_selling_price_1, Decimal("90.00"))  # 100 - 10%
        self.assertEqual(deal1.special_selling_price_2, Decimal("99.00"))  # 110 - 10%
        self.assertEqual(deal1.special_selling_price_3, Decimal("108.00"))  # 120 - 10%

        # Inactive item and items in other departments are excluded.
        self.assertFalse(SpecialDeal.objects.filter(stock_item=self.inactive_item).exists())
        self.assertFalse(SpecialDeal.objects.filter(stock_item=self.other_dept_item).exists())

    def test_flat_rand_increase(self):
        response = self.client.post(
            reverse("specialdeal-bulk-department"),
            {
                "department": self.department.pk,
                "start_date": timezone.now().date().isoformat(),
                "end_date": (timezone.now().date() + timedelta(days=7)).isoformat(),
                "increase_decrease": "+",
                "percentage_rand": "R",
                "amount": "5",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        deal2 = SpecialDeal.objects.get(stock_item=self.item2)
        self.assertEqual(deal2.special_selling_price_1, Decimal("45.00"))  # 40 + 5

    def test_missing_department_returns_400(self):
        response = self.client.post(
            reverse("specialdeal-bulk-department"),
            {
                "start_date": timezone.now().date().isoformat(),
                "end_date": (timezone.now().date() + timedelta(days=7)).isoformat(),
                "increase_decrease": "+",
                "percentage_rand": "P",
                "amount": "5",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class UsedInBundlesTest(APITestCase):
    """Phase 3: StockItemViewSet's used-in-bundles reverse lookup."""

    @classmethod
    def setUpTestData(cls):
        cls.department = SalesDepartment.objects.create(number=4, name="Bundles Dept")

    def setUp(self):
        self.mover = User.objects.create_user(
            username="mover4",
            email="mover4@example.com",
            password="x",
            is_superuser=True,
        )
        self.client.force_authenticate(self.mover)

        self.ingredient = StockItem.objects.create(
            stock_code="ING100",
            description="Shared Ingredient",
            department=self.department,
            cost_price=Decimal("5.00"),
        )
        self.bundle_item = StockItem.objects.create(
            stock_code="BUNDLEX",
            description="Bundle X",
            department=self.department,
            cost_price=Decimal("0"),
        )
        self.pack_bundle = PackBundle.objects.create(stock_item=self.bundle_item)
        PackBundleIngredient.objects.create(
            pack_bundle=self.pack_bundle,
            ingredient_stock=self.ingredient,
            quantity=Decimal("3.00"),
        )

    def test_used_in_bundles_lists_the_pack(self):
        response = self.client.get(
            reverse("stockitem-used-in-bundles", args=[self.ingredient.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["pack_bundle_stock_code"], "BUNDLEX")
        self.assertEqual(
            Decimal(str(response.data[0]["quantity_required"])), Decimal("3.00")
        )

    def test_used_in_bundles_empty_for_non_ingredient(self):
        standalone = StockItem.objects.create(
            stock_code="STANDALONE",
            description="Not in any bundle",
            department=self.department,
        )
        response = self.client.get(
            reverse("stockitem-used-in-bundles", args=[standalone.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class EnquiryAggregationTest(APITestCase):
    """Phase 4: net-new enquiry aggregations against seeded StockTransaction fixtures."""

    @classmethod
    def setUpTestData(cls):
        cls.dept_a = SalesDepartment.objects.create(number=10, name="Dept A")
        cls.dept_b = SalesDepartment.objects.create(number=11, name="Dept B")
        cls.supplier = Creditor.objects.create(
            supplier_number="S100", name="Test Supplier"
        )
        cls.debtor = Debtor.objects.create(dno=2001, dname="Enquiry Debtor")

    def setUp(self):
        self.mover = User.objects.create_user(
            username="mover5",
            email="mover5@example.com",
            password="x",
            is_superuser=True,
        )
        self.client.force_authenticate(self.mover)

        self.item_a = StockItem.objects.create(
            stock_code="ENQ001", description="Item A", department=self.dept_a
        )
        self.item_b = StockItem.objects.create(
            stock_code="ENQ002", description="Item B", department=self.dept_b
        )

        today = timezone.now().date()

        # Sales: item_a sells more (higher quantity), item_b higher value.
        StockTransaction.objects.create(
            transaction_type="SALE",
            stock_item=self.item_a,
            department=self.dept_a,
            debtor=self.debtor,
            transaction_date=today,
            transaction_time="09:00:00",
            quantity_out=Decimal("10"),
            value=Decimal("100.00"),
        )
        StockTransaction.objects.create(
            transaction_type="SALE",
            stock_item=self.item_b,
            department=self.dept_b,
            transaction_date=today,
            transaction_time="14:00:00",
            quantity_out=Decimal("2"),
            value=Decimal("400.00"),
        )
        # A sale return against item_a for the same debtor - nets down
        # the debtor's total quantity below the raw sale.
        StockTransaction.objects.create(
            transaction_type="SALE_RETURN",
            stock_item=self.item_a,
            department=self.dept_a,
            debtor=self.debtor,
            transaction_date=today,
            quantity_in=Decimal("3"),
            value=Decimal("30.00"),
        )
        # Incoming stock from the supplier.
        StockTransaction.objects.create(
            transaction_type="INCOMING",
            stock_item=self.item_a,
            supplier=self.supplier,
            transaction_date=today,
            quantity_in=Decimal("50"),
            unit_cost=Decimal("5.00"),
        )

    def test_debtor_breakdown_nets_sale_and_return(self):
        response = self.client.get(
            reverse("stockitem-debtor-breakdown", args=[self.item_a.pk])
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(row["debtor_id"], self.debtor.pk)
        self.assertEqual(Decimal(str(row["total_quantity"])), Decimal("7"))  # 10 - 3
        self.assertEqual(Decimal(str(row["total_value"])), Decimal("70.00"))  # 100 - 30

    def test_stock_contribution_percentages_sum_to_100(self):
        response = self.client.get(reverse("stocktransaction-stock-contribution"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        total_pct = sum(row["contribution_pct"] for row in response.data)
        self.assertAlmostEqual(total_pct, 100.0, places=1)
        # item_b has the higher value (400 vs 100) so should rank first.
        self.assertEqual(response.data[0]["stock_item_id"], self.item_b.pk)

    def test_sales_by_department(self):
        response = self.client.get(reverse("stocktransaction-sales-by-department"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_dept = {row["department_id"]: row for row in response.data}
        self.assertEqual(
            Decimal(str(by_dept[self.dept_a.pk]["total_value"])), Decimal("100.00")
        )
        self.assertEqual(
            Decimal(str(by_dept[self.dept_b.pk]["total_value"])), Decimal("400.00")
        )

    def test_hourly_analysis_buckets_by_hour(self):
        response = self.client.get(reverse("stocktransaction-hourly-analysis"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        hours = {row["hour"]: row for row in response.data}
        self.assertIn(9, hours)
        self.assertIn(14, hours)
        self.assertEqual(hours[9]["transaction_count"], 1)

    def test_purchase_history_lists_incoming_only(self):
        response = self.client.get(reverse("stocktransaction-purchase-history"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["transaction_type"], "INCOMING")
        self.assertEqual(results[0]["stock_item"], self.item_a.pk)

    def test_top_sellers_ordered_by_quantity(self):
        response = self.client.get(reverse("stocktransaction-top-sellers"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # item_a sold quantity 10 (higher than item_b's 2), so ranks first
        # despite item_b having the higher value.
        self.assertEqual(response.data[0]["stock_item_id"], self.item_a.pk)
        self.assertEqual(Decimal(str(response.data[0]["total_quantity"])), Decimal("10"))

    def test_stock_item_transactions_debtor_filter(self):
        response = self.client.get(
            reverse("stockitem-transactions", args=[self.item_a.pk]),
            {"debtor": self.debtor.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 2)  # the SALE and the SALE_RETURN
        self.assertTrue(all(r["debtor"] == self.debtor.pk for r in results))

    def test_stock_contribution_collapses_multiple_dated_transactions(self):
        """
        Regression guard: StockTransaction.Meta.ordering ("-transaction_date",
        "-id") must not leak into the GROUP BY of the aggregation below and
        fragment one item's sales into one row per transaction date.
        """
        StockTransaction.objects.create(
            transaction_type="SALE",
            stock_item=self.item_a,
            department=self.dept_a,
            transaction_date=timezone.now().date() - timedelta(days=1),
            quantity_out=Decimal("4"),
            value=Decimal("40.00"),
        )
        response = self.client.get(reverse("stocktransaction-stock-contribution"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item_a_rows = [r for r in response.data if r["stock_item_id"] == self.item_a.pk]
        self.assertEqual(len(item_a_rows), 1)
        # Original fixture SALE (10 @ value 100) + this one (4 @ value 40).
        self.assertEqual(Decimal(str(item_a_rows[0]["total_quantity"])), Decimal("14"))
        self.assertEqual(Decimal(str(item_a_rows[0]["total_value"])), Decimal("140.00"))

    def test_received_returned_report(self):
        StockTransaction.objects.create(
            transaction_type="RETURN",
            stock_item=self.item_a,
            supplier=self.supplier,
            transaction_date=timezone.now().date(),
            quantity_out=Decimal("5"),
        )
        response = self.client.get(
            reverse("stocktransaction-received-returned-report")
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        types = {r["transaction_type"] for r in results}
        self.assertEqual(types, {"INCOMING", "RETURN"})


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class StockItemReportTest(APITestCase):
    """Phase 5: StockItemViewSet report actions (code range, valuation, low-stock search/level)."""

    @classmethod
    def setUpTestData(cls):
        cls.dept_a = SalesDepartment.objects.create(number=20, name="Dept 20")
        cls.dept_b = SalesDepartment.objects.create(number=21, name="Dept 21")

    def setUp(self):
        self.mover = User.objects.create_user(
            username="mover6",
            email="mover6@example.com",
            password="x",
            is_superuser=True,
        )
        self.client.force_authenticate(self.mover)

        self.item_low = StockItem.objects.create(
            stock_code="RPT001",
            description="Critical low item",
            department=self.dept_a,
            cost_price=Decimal("10.00"),
            average_cost=Decimal("12.00"),
            quantity_on_hand=Decimal("-2"),
            reorder_quantity=Decimal("5"),
        )
        self.item_ok = StockItem.objects.create(
            stock_code="RPT002",
            description="Well stocked item",
            department=self.dept_b,
            cost_price=Decimal("20.00"),
            average_cost=Decimal("22.00"),
            quantity_on_hand=Decimal("100"),
            reorder_quantity=Decimal("5"),
        )
        self.item_outside_range = StockItem.objects.create(
            stock_code="ZZZ999",
            description="Outside code range",
            department=self.dept_a,
            cost_price=Decimal("5.00"),
            quantity_on_hand=Decimal("10"),
        )

    def test_code_range_filter_on_list(self):
        response = self.client.get(
            reverse("stockitem-list"), {"code_from": "RPT000", "code_to": "RPT999"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        codes = {r["stock_code"] for r in response.data["results"]}
        self.assertEqual(codes, {"RPT001", "RPT002"})

    def test_valuation_report_last_cost_basis(self):
        response = self.client.get(
            reverse("stockitem-valuation-report"),
            {"code_from": "RPT000", "code_to": "RPT999", "cost_basis": "last"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_code = {row["stock_code"]: row for row in response.data["items"]}
        # RPT001: -2 * 10.00 = -20.00; RPT002: 100 * 20.00 = 2000.00
        self.assertEqual(Decimal(str(by_code["RPT001"]["value"])), Decimal("-20.00"))
        self.assertEqual(Decimal(str(by_code["RPT002"]["value"])), Decimal("2000.00"))
        self.assertEqual(
            Decimal(str(response.data["total_value"])), Decimal("1980.00")
        )

    def test_valuation_report_average_cost_basis(self):
        response = self.client.get(
            reverse("stockitem-valuation-report"),
            {"code_from": "RPT000", "code_to": "RPT999", "cost_basis": "average"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_code = {row["stock_code"]: row for row in response.data["items"]}
        # RPT002: 100 * 22.00 = 2200.00
        self.assertEqual(Decimal(str(by_code["RPT002"]["value"])), Decimal("2200.00"))

    def test_low_stock_level_filter(self):
        response = self.client.get(reverse("stockitem-low-stock"), {"level": "critical"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        codes = {r["stock_code"] for r in results}
        self.assertEqual(codes, {"RPT001"})  # negative QOH -> critical

    def test_low_stock_search_filter(self):
        response = self.client.get(reverse("stockitem-low-stock"), {"search": "Critical"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["stock_code"], "RPT001")


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
)
class MonthlyStatisticReportTest(APITestCase):
    """Phase 5: StockMonthlyStatisticViewSet report actions."""

    @classmethod
    def setUpTestData(cls):
        cls.dept_a = SalesDepartment.objects.create(number=22, name="Dept 22")
        cls.dept_b = SalesDepartment.objects.create(number=23, name="Dept 23")

    def setUp(self):
        self.mover = User.objects.create_user(
            username="mover7",
            email="mover7@example.com",
            password="x",
            is_superuser=True,
        )
        self.client.force_authenticate(self.mover)

        self.item_a = StockItem.objects.create(
            stock_code="MS001", description="Fast Mover", department=self.dept_a
        )
        self.item_b = StockItem.objects.create(
            stock_code="MS002", description="Slow Mover", department=self.dept_b
        )
        self.item_c = StockItem.objects.create(
            stock_code="MS003", description="Slow Mover Two Months", department=self.dept_b
        )

        # item_a: strong sales across 2 months.
        StockMonthlyStatistic.objects.create(
            stock_item=self.item_a, year=2026, month=1,
            quantity_sold=Decimal("100"), value_sold=Decimal("1000.00"),
            profit_value=Decimal("400.00"),
        )
        StockMonthlyStatistic.objects.create(
            stock_item=self.item_a, year=2026, month=2,
            quantity_sold=Decimal("120"), value_sold=Decimal("1200.00"),
            profit_value=Decimal("480.00"),
        )
        # item_c: consistently slow across 2 months — the regression case
        # for the GROUP BY fragmentation bug (Meta.ordering leaking into
        # the aggregation, which would incorrectly split this into 2 rows
        # of "1 month, avg 2" instead of 1 row of "2 months, avg 2").
        StockMonthlyStatistic.objects.create(
            stock_item=self.item_c, year=2026, month=1,
            quantity_sold=Decimal("2"), value_sold=Decimal("40.00"),
            profit_value=Decimal("10.00"),
        )
        StockMonthlyStatistic.objects.create(
            stock_item=self.item_c, year=2026, month=2,
            quantity_sold=Decimal("2"), value_sold=Decimal("40.00"),
            profit_value=Decimal("10.00"),
        )
        # item_b: barely sells, only 1 month of data in the year.
        StockMonthlyStatistic.objects.create(
            stock_item=self.item_b, year=2026, month=1,
            quantity_sold=Decimal("2"), value_sold=Decimal("40.00"),
            profit_value=Decimal("10.00"),
        )

    def test_by_department_nets_cost_from_profit(self):
        response = self.client.get(
            reverse("stockmonthlystatistic-by-department"), {"year": 2026}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_dept = {row["department_id"]: row for row in response.data}
        dept_a_row = by_dept[self.dept_a.pk]
        # total_sales = 1000+1200=2200, total_profit=400+480=880, cost=2200-880=1320
        self.assertEqual(Decimal(str(dept_a_row["total_sales"])), Decimal("2200.00"))
        self.assertEqual(Decimal(str(dept_a_row["total_profit"])), Decimal("880.00"))
        self.assertEqual(Decimal(str(dept_a_row["total_cost"])), Decimal("1320.00"))

    def test_by_item_with_monthly_trend(self):
        response = self.client.get(
            reverse("stockmonthlystatistic-by-item"),
            {"year": 2026, "stock_item": self.item_a.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["by_item"]), 1)
        self.assertEqual(len(response.data["by_month"]), 2)
        months = {row["month"] for row in response.data["by_month"]}
        self.assertEqual(months, {1, 2})

    def test_slow_movers_uses_actual_months_not_fixed_12(self):
        # item_b: total_quantity=2 over 1 month of data -> avg=2.0, not 2/12=0.17
        response = self.client.get(
            reverse("stockmonthlystatistic-slow-movers"),
            {"year": 2026, "threshold": "3"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_item = {row["stock_item_id"]: row for row in response.data}
        self.assertIn(self.item_b.pk, by_item)
        self.assertNotIn(self.item_a.pk, by_item)  # avg 110/month, well above threshold
        self.assertEqual(by_item[self.item_b.pk]["avg_monthly_sales"], 2.0)
        self.assertEqual(by_item[self.item_b.pk]["months_with_data"], 1)

        # item_c: 2 months of quantity_sold=2 each must collapse into ONE
        # row (total_quantity=4, months_with_data=2, avg=2.0) — regression
        # guard for the GROUP BY fragmentation bug (StockMonthlyStatistic's
        # Meta.ordering leaking year/month into the aggregation, which
        # would otherwise produce two separate rows for this one item).
        self.assertIn(self.item_c.pk, by_item)
        self.assertEqual(len([r for r in response.data if r["stock_item_id"] == self.item_c.pk]), 1)
        self.assertEqual(Decimal(str(by_item[self.item_c.pk]["total_quantity"])), Decimal("4"))
        self.assertEqual(by_item[self.item_c.pk]["months_with_data"], 2)
        self.assertEqual(by_item[self.item_c.pk]["avg_monthly_sales"], 2.0)
