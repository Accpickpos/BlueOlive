from decimal import Decimal

from apps.settings.models import SalesDepartment
from django.test import TestCase

from .models import PackBundle, PackBundleIngredient, StockItem, StockTransaction
from .services import StockTransactionService


class StockTransactionServiceTest(TestCase):
    """
    Covers the bug this service fixes: posting an INCOMING/RETURN/MANUFACTURE
    StockTransaction previously created the record but never moved
    quantity_on_hand (see signals.py's update_stock_item_after_transaction,
    which only ever touched metadata fields).
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
            average_cost=Decimal("100.00"),
            quantity_on_hand=Decimal("50"),
        )

    def test_create_incoming_transaction_increases_qoh(self):
        tx = StockTransactionService.create_incoming_transaction(
            stock_item=self.item, quantity=Decimal("10"), unit_cost=Decimal("120.00")
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, Decimal("60"))
        self.assertEqual(tx.transaction_type, "INCOMING")
        self.assertEqual(tx.quantity_in, Decimal("10"))

    def test_create_incoming_transaction_updates_average_cost(self):
        # Weighted average: (50*100 + 10*120) / 60 = 103.33...
        StockTransactionService.create_incoming_transaction(
            stock_item=self.item, quantity=Decimal("10"), unit_cost=Decimal("120.00")
        )
        self.item.refresh_from_db()
        expected = (
            Decimal("50") * Decimal("100.00") + Decimal("10") * Decimal("120.00")
        ) / Decimal("60")
        self.assertAlmostEqual(float(self.item.average_cost), float(expected), places=2)

    def test_create_incoming_transaction_rejects_non_positive_quantity(self):
        with self.assertRaises(ValueError):
            StockTransactionService.create_incoming_transaction(
                stock_item=self.item, quantity=Decimal("0"), unit_cost=Decimal("10")
            )

    def test_create_return_transaction_decreases_qoh(self):
        tx = StockTransactionService.create_return_transaction(
            stock_item=self.item, quantity=Decimal("15"), unit_cost=Decimal("100.00")
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity_on_hand, Decimal("35"))
        self.assertEqual(tx.transaction_type, "RETURN")
        self.assertEqual(tx.quantity_out, Decimal("15"))

    def test_create_manufacture_transaction_moves_bundle_and_ingredients(self):
        ingredient1 = StockItem.objects.create(
            stock_code="ING001",
            description="Ingredient 1",
            department=self.department,
            cost_price=Decimal("10.00"),
            quantity_on_hand=Decimal("100"),
        )
        ingredient2 = StockItem.objects.create(
            stock_code="ING002",
            description="Ingredient 2",
            department=self.department,
            cost_price=Decimal("20.00"),
            quantity_on_hand=Decimal("100"),
        )
        bundle = StockItem.objects.create(
            stock_code="BUNDLE001",
            description="Bundle Product",
            department=self.department,
            cost_price=Decimal("30.00"),
            quantity_on_hand=Decimal("0"),
        )
        pack_bundle = PackBundle.objects.create(stock_item=bundle)
        PackBundleIngredient.objects.create(
            pack_bundle=pack_bundle,
            ingredient_stock=ingredient1,
            quantity=Decimal("2.00"),
        )
        PackBundleIngredient.objects.create(
            pack_bundle=pack_bundle,
            ingredient_stock=ingredient2,
            quantity=Decimal("1.00"),
        )

        tx = StockTransactionService.create_manufacture_transaction(
            bundle_stock_item=bundle, quantity=Decimal("5")
        )

        bundle.refresh_from_db()
        ingredient1.refresh_from_db()
        ingredient2.refresh_from_db()

        self.assertEqual(tx.transaction_type, "MANUFACTURE")
        self.assertEqual(bundle.quantity_on_hand, Decimal("5"))
        self.assertEqual(ingredient1.quantity_on_hand, Decimal("90"))  # 100 - 2*5
        self.assertEqual(ingredient2.quantity_on_hand, Decimal("95"))  # 100 - 1*5

        bundle_use_txns = StockTransaction.objects.filter(transaction_type="BUNDLE_USE")
        self.assertEqual(bundle_use_txns.count(), 2)
        ing1_txn = bundle_use_txns.get(stock_item=ingredient1)
        self.assertEqual(ing1_txn.quantity_out, Decimal("10"))

    def test_create_manufacture_transaction_rejects_non_bundle_item(self):
        plain_item = StockItem.objects.create(
            stock_code="PLAIN001",
            description="Not a bundle",
            department=self.department,
            quantity_on_hand=Decimal("0"),
        )
        with self.assertRaises(ValueError):
            StockTransactionService.create_manufacture_transaction(
                bundle_stock_item=plain_item, quantity=Decimal("1")
            )
