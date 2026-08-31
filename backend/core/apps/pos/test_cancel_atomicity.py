"""
Targeted regression tests for the atomic/locked stock reversal + audit
logging added to the POS cancel_* services (see services.py cancel_*
functions and tenancy/audit.py POSAuditLog). apps/pos/tests.py currently
fails to collect (pre-existing, unrelated StockCategory import drift), so
these live in their own module rather than depending on that file.
"""

from datetime import date
from decimal import Decimal

from apps.settings.models import SalesDepartment
from apps.stock_control.models import StockItem
from django.test import TestCase
from tenancy.audit import AuditLog

from .models import CashSale, CashSaleLine
from .services import CashSaleService


class CancelCashSaleTests(TestCase):
    """CashSaleService.cancel_cash_sale reverses stock and records an audit entry."""

    def setUp(self):
        self.department = SalesDepartment.objects.create(
            number=1, name="Test Department"
        )
        self.stock_item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Item",
            department=self.department,
            cost_price=Decimal("100.00"),
            quantity_on_hand=Decimal("10.00"),
            selling_price_1=Decimal("150.00"),
        )

        self.cash_sale = CashSale.objects.create(
            sale_number="CS-TEST-0001",
            sale_date=date.today(),
            is_posted=True,
            total_amount=Decimal("150.00"),
        )
        CashSaleLine.objects.create(
            cash_sale=self.cash_sale,
            line_number=1,
            stock_code="TEST001",
            description="Test Item",
            quantity=Decimal("2.00"),
            unit_price=Decimal("150.00"),
            line_total=Decimal("300.00"),
            vat_amount=Decimal("0.00"),
        )
        self.stock_item.quantity_on_hand = Decimal("8.00")
        self.stock_item.save()

    def test_cancel_reverses_stock_quantity(self):
        CashSaleService.cancel_cash_sale(self.cash_sale, reason="Customer return")

        self.stock_item.refresh_from_db()
        self.cash_sale.refresh_from_db()

        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("10.00"))
        self.assertTrue(self.cash_sale.is_cancelled)

    def test_cancel_is_idempotent_guard(self):
        CashSaleService.cancel_cash_sale(self.cash_sale, reason="Customer return")

        from .exceptions import InvalidDocumentState

        with self.assertRaises(InvalidDocumentState):
            CashSaleService.cancel_cash_sale(self.cash_sale, reason="Second attempt")

    def test_cancel_writes_audit_log_entry(self):
        before_count = AuditLog.objects.filter(action="POS_CANCELLED").count()

        CashSaleService.cancel_cash_sale(self.cash_sale, reason="Customer return")

        entries = AuditLog.objects.filter(action="POS_CANCELLED").order_by("-id")
        self.assertEqual(entries.count(), before_count + 1)
        latest = entries.first()
        self.assertEqual(latest.resource_type, "CashSale")
        self.assertEqual(latest.resource_id, "CS-TEST-0001")
        self.assertEqual(latest.details.get("reason"), "Customer return")
