"""
POS Application Tests.
Comprehensive test suite for POS models, services, and views.
"""

from datetime import date
from decimal import Decimal

from apps.settings.models import SalesArea, SalesDepartment
from apps.stock_control.models import StockItem
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase

from .calculation_service import CalculationService
from .exceptions import InsufficientStock, InvalidDocumentState, POSValidationException
from .models import (
    CashACheque,
    CashControl,
    CashReturn,
    CashReturnLine,
    CashSale,
    CashSaleLine,
    CreditNote,
    CreditNoteLine,
    JobCard,
    JobCardLine,
    Laybye,
    LaybyeLine,
    LaybyePayment,
    Payout,
    Quotation,
    QuotationLine,
    ReceiptOnAccount,
    Repair,
    Tender,
    TransactionQuery,
)
from .services import CashSaleService, LaybyeService, QuotationService

User = get_user_model()


class CalculationServiceTestCase(TestCase):
    """Test CalculationService methods."""

    def test_calculate_line_totals_basic(self):
        """Test basic line total calculation."""
        result = CalculationService.calculate_line_totals(
            quantity=Decimal("10"),
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("10"),
            tax_code=1,
            cost_price=Decimal("50.00"),
        )

        self.assertEqual(result["subtotal"], Decimal("1000.00"))
        self.assertEqual(result["discount_amount"], Decimal("100.00"))
        self.assertEqual(result["line_total_before_vat"], Decimal("900.00"))
        self.assertEqual(result["vat_amount"], Decimal("126.00"))  # 900 * 0.14
        self.assertEqual(result["line_total"], Decimal("1026.00"))
        self.assertEqual(result["line_cost"], Decimal("500.00"))
        self.assertEqual(result["line_profit"], Decimal("400.00"))

    def test_calculate_line_totals_zero_quantity_fails(self):
        """Test that zero quantity raises error."""
        with self.assertRaises(ValidationError):
            CalculationService.calculate_line_totals(
                quantity=Decimal("0"), unit_price=Decimal("100.00")
            )

    def test_calculate_line_totals_negative_price_fails(self):
        """Test that negative price raises error."""
        with self.assertRaises(ValidationError):
            CalculationService.calculate_line_totals(
                quantity=Decimal("10"), unit_price=Decimal("-100.00")
            )

    def test_calculate_document_totals(self):
        """Test document totals calculation."""
        lines = [
            {
                "line_total_before_vat": Decimal("900.00"),
                "vat_amount": Decimal("126.00"),
                "line_cost": Decimal("500.00"),
                "discount_amount": Decimal("100.00"),
            },
            {
                "line_total_before_vat": Decimal("500.00"),
                "vat_amount": Decimal("70.00"),
                "line_cost": Decimal("300.00"),
                "discount_amount": Decimal("50.00"),
            },
        ]

        result = CalculationService.calculate_document_totals(lines)

        self.assertEqual(result["subtotal"], Decimal("1400.00"))
        self.assertEqual(result["vat_amount"], Decimal("196.00"))
        self.assertEqual(result["total_amount"], Decimal("1596.00"))
        self.assertEqual(result["total_cost"], Decimal("800.00"))
        self.assertEqual(result["gross_profit"], Decimal("600.00"))

    def test_calculate_change(self):
        """Test change calculation."""
        change = CalculationService.calculate_change(
            tendered=Decimal("1000.00"), total=Decimal("750.00")
        )

        self.assertEqual(change, Decimal("250.00"))

    def test_calculate_tender_balance(self):
        """Test tender balance verification."""
        tenders = [{"amount": Decimal("600.00")}, {"amount": Decimal("400.00")}]

        balance, is_balanced = CalculationService.calculate_tender_balance(
            tenders, Decimal("1000.00")
        )

        self.assertEqual(balance, Decimal("0.00"))
        self.assertTrue(is_balanced)

    def test_calculate_laybye_balance(self):
        """Test laybye balance calculation."""
        result = CalculationService.calculate_laybye_balance(
            total_amount=Decimal("1000.00"),
            deposit_amount=Decimal("200.00"),
            amount_paid=Decimal("300.00"),
        )

        self.assertEqual(result["total_amount"], Decimal("1000.00"))
        self.assertEqual(result["amount_paid"], Decimal("300.00"))
        self.assertEqual(result["balance_due"], Decimal("700.00"))


class CashSaleModelTestCase(TestCase):
    """Test CashSale model."""

    def setUp(self):
        """Set up test data."""
        # is_superuser=True bypasses ShopUser.save()'s tenant-context guard,
        # which isn't set up in this single-DB test run (DISABLE_TENANT_ROUTER=1).
        self.user = User.objects.create_user(
            username="cashier1",
            password="testpass123",  # nosec B105 B106 - test fixture password
            is_superuser=True,
        )
        self.sales_area = SalesArea.objects.create(number=1, name="Main")

    def test_create_cash_sale(self):
        """Test creating a cash sale."""
        sale = CashSale.objects.create(
            sale_number="SALE-001",
            sale_date=date.today(),
            customer_name="John Doe",
            cashier=self.user,
            station_number=1,
            sales_area=self.sales_area,
            cash_tendered=Decimal("1000.00"),
        )

        self.assertEqual(sale.sale_number, "SALE-001")
        self.assertFalse(sale.is_posted)
        self.assertFalse(sale.is_cancelled)

    def test_cash_sale_string_representation(self):
        """Test cash sale string representation."""
        sale = CashSale.objects.create(
            sale_number="SALE-001",
            sale_date=date.today(),
            cashier=self.user,
            station_number=1,
        )

        self.assertEqual(str(sale), "Cash Sale SALE-001")


class LaybyeModelTestCase(TestCase):
    """Test Laybye model."""

    def setUp(self):
        """Set up test data."""
        self.sales_area = SalesArea.objects.create(number=1, name="Main")

    def test_create_laybye(self):
        """Test creating a laybye."""
        laybye = Laybye.objects.create(
            laybye_number="LB-001",
            customer_name="Jane Doe",
            telephone="0712345678",
            laybye_date=date.today(),
            expiry_date=date(2026, 3, 5),
            total_amount=Decimal("1000.00"),
            deposit_amount=Decimal("200.00"),
            balance_due=Decimal("800.00"),
            sales_area=self.sales_area,
        )

        self.assertEqual(laybye.status, "ACTIVE")
        self.assertEqual(laybye.amount_paid, Decimal("0.00"))


class LaybyeServiceTestCase(TransactionTestCase):
    """Test LaybyeService operations."""

    def setUp(self):
        """Set up test data."""
        self.sales_area = SalesArea.objects.create(number=1, name="Main")

    def test_make_payment_on_laybye(self):
        """Test making a payment on laybye."""
        laybye = Laybye.objects.create(
            laybye_number="LB-001",
            customer_name="Jane Doe",
            telephone="0712345678",
            laybye_date=date.today(),
            expiry_date=date(2026, 3, 5),
            total_amount=Decimal("1000.00"),
            deposit_amount=Decimal("200.00"),
            balance_due=Decimal("800.00"),
            amount_paid=Decimal("200.00"),
            sales_area=self.sales_area,
        )

        payment, _invoice = LaybyeService.make_payment(
            laybye, Decimal("300.00"), self.sales_area
        )

        laybye.refresh_from_db()

        self.assertEqual(payment.amount, Decimal("300.00"))
        self.assertEqual(laybye.amount_paid, Decimal("500.00"))
        self.assertEqual(laybye.balance_due, Decimal("500.00"))
        self.assertEqual(laybye.status, "ACTIVE")

    def test_make_payment_completes_laybye(self):
        """Test that final payment marks laybye as completed."""
        laybye = Laybye.objects.create(
            laybye_number="LB-001",
            customer_name="Jane Doe",
            telephone="0712345678",
            laybye_date=date.today(),
            expiry_date=date(2026, 3, 5),
            total_amount=Decimal("1000.00"),
            deposit_amount=Decimal("200.00"),
            balance_due=Decimal("800.00"),
            amount_paid=Decimal("200.00"),
            sales_area=self.sales_area,
        )

        LaybyeService.make_payment(laybye, Decimal("800.00"), self.sales_area)

        laybye.refresh_from_db()

        self.assertEqual(laybye.status, "COMPLETED")

    def test_payment_exceeds_balance_fails(self):
        """Test that payment exceeding balance raises error."""
        laybye = Laybye.objects.create(
            laybye_number="LB-001",
            customer_name="Jane Doe",
            telephone="0712345678",
            laybye_date=date.today(),
            expiry_date=date(2026, 3, 5),
            total_amount=Decimal("1000.00"),
            deposit_amount=Decimal("200.00"),
            balance_due=Decimal("800.00"),
            amount_paid=Decimal("200.00"),
            sales_area=self.sales_area,
        )

        with self.assertRaises(POSValidationException):
            LaybyeService.make_payment(laybye, Decimal("900.00"))

    def test_cancel_laybye_with_retention(self):
        """Test cancelling a laybye with retention."""
        laybye = Laybye.objects.create(
            laybye_number="LB-001",
            customer_name="Jane Doe",
            telephone="0712345678",
            laybye_date=date.today(),
            expiry_date=date(2026, 3, 5),
            total_amount=Decimal("1000.00"),
            deposit_amount=Decimal("200.00"),
            balance_due=Decimal("800.00"),
            amount_paid=Decimal("200.00"),
            sales_area=self.sales_area,
        )

        LaybyeService.cancel_laybye(laybye, retention_percentage=Decimal("10"))

        laybye.refresh_from_db()

        self.assertEqual(laybye.status, "CANCELLED")
        self.assertEqual(laybye.retention_percentage, Decimal("10"))
        self.assertEqual(laybye.refund_amount, Decimal("180.00"))  # 200 - 20


class CashSaleServiceTestCase(TransactionTestCase):
    """Test CashSaleService operations."""

    def setUp(self):
        """Set up test data."""
        # is_superuser=True bypasses ShopUser.save()'s tenant-context guard,
        # which isn't set up in this single-DB test run (DISABLE_TENANT_ROUTER=1).
        self.user = User.objects.create_user(
            username="cashier1",
            password="testpass123",  # nosec B105 B106 - test fixture password
            is_superuser=True,
        )
        self.sales_area = SalesArea.objects.create(number=1, name="Main")

        # Create stock item
        department = SalesDepartment.objects.create(number=1, name="General Items")
        self.stock_item = StockItem.objects.create(
            stock_code="SKU001",
            description="Test Item",
            department=department,
            quantity_on_hand=Decimal("100"),
            reorder_quantity=Decimal("10"),
        )

    def test_post_cash_sale_updates_stock(self):
        """Test that posting sale updates stock."""
        sale = CashSale.objects.create(
            sale_number="SALE-001",
            sale_date=date.today(),
            customer_name="John Doe",
            cashier=self.user,
            station_number=1,
            sales_area=self.sales_area,
            cash_tendered=Decimal("1000.00"),
        )

        CashSaleLine.objects.create(
            cash_sale=sale,
            line_number=1,
            stock_code="SKU001",
            description="Test Item",
            quantity=Decimal("10"),
            unit_price=Decimal("100.00"),
            discount_percentage=Decimal("0"),
            tax_code=1,
            line_total=Decimal("1140.00"),
            vat_amount=Decimal("140.00"),
            cost_price=Decimal("50.00"),
            line_profit=Decimal("500.00"),
        )

        CashSaleService.post_cash_sale(sale)

        self.stock_item.refresh_from_db()

        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("90"))

    def test_post_already_posted_sale_fails(self):
        """Test that posting already-posted sale raises error."""
        sale = CashSale.objects.create(
            sale_number="SALE-001",
            sale_date=date.today(),
            customer_name="John Doe",
            cashier=self.user,
            station_number=1,
            is_posted=True,
        )

        with self.assertRaises(InvalidDocumentState):
            CashSaleService.post_cash_sale(sale)
