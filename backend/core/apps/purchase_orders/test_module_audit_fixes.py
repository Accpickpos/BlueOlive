"""
Targeted regression tests for the Purchase Orders module fixes from the
priority-gap audit (POrders.pdf):

- PurchaseOrderReceiptViewSet.queryset.select_related() referenced a
  non-existent `creditor_transaction` field (the real FK is `creditor_grn`) —
  every GET to /purchase-orders/receipts/ raised FieldError.
- Cancel Order had a "Reason for Cancellation" field with nowhere to store
  it — cancellation_reason is now a real PurchaseOrder field, and
  cancel_order/PurchaseOrder.cancel() persist it.
- Manual line entry had no way to record a per-line comment or expense
  category — both now round-trip through create().
- "Reset Purchase Order Quantities" utility only existed as a management
  command requiring shell access — services.resync_stock_on_order() is now
  shared by the command and the resync_on_order_quantities API action.

View-level permission/tenant wiring isn't available in this test env (see
apps.creditors.test_module_audit_fixes for the same convention), so the
queryset/model/service layers are exercised directly instead of through
APIClient requests.
"""

from datetime import date, timedelta
from decimal import Decimal

from apps.creditors.models import Creditor
from apps.settings.models import ExpenseCategory, SalesDepartment
from apps.stock_control.models import StockItem
from django.test import TestCase
from django.utils import timezone

from .models import PurchaseOrder, PurchaseOrderLine, PurchaseOrderReceipt
from .services import resync_stock_on_order
from .views import PurchaseOrderReceiptViewSet


def _make_supplier(**overrides):
    defaults = {
        "supplier_number": "2001",
        "name": "Test Supplier",
        "account_category": "OI",
    }
    defaults.update(overrides)
    return Creditor.objects.create(**defaults)


class PurchaseOrdersAuditFixesTestBase(TestCase):
    def setUp(self):
        self.department = SalesDepartment.objects.create(number=1, name="Groceries")
        self.stock_item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Product",
            department=self.department,
            cost_price=Decimal("100.00"),
            quantity_on_hand=Decimal("50"),
            quantity_on_order=Decimal("0"),
        )
        self.supplier = _make_supplier()

    def _make_order(self, quantity=Decimal("10"), status="O"):
        order = PurchaseOrder.objects.create(
            supplier=self.supplier,
            delivery_date=date.today() + timedelta(days=7),
            status=status,
        )
        line = PurchaseOrderLine.objects.create(
            purchase_order=order,
            line_number=1,
            stock_item=self.stock_item,
            stock_code=self.stock_item.stock_code,
            quantity=quantity,
            base_price=Decimal("100.00"),
        )
        line.calculate_totals()
        order.calculate_totals()
        if order.status != status:
            # calculate_totals() derives status from delivered quantities
            # (O/P/F), which would overwrite an explicit "C" override — set
            # it directly afterwards, the same way cancel_order()/cancel()
            # apply status without re-deriving it from quantities.
            order.status = status
            order.save(update_fields=["status"])
        return order, line


class ReceiptViewSetQuerysetTests(PurchaseOrdersAuditFixesTestBase):
    """The receipts list queryset's select_related() must reference real
    field names — creditor_grn, not the never-existed creditor_transaction."""

    def test_receipt_queryset_evaluates_without_field_error(self):
        order, _line = self._make_order()
        PurchaseOrderReceipt.objects.create(
            purchase_order=order,
            receipt_date=date.today(),
            invoice_number="INV-1",
        )
        # Evaluating the queryset compiles the SQL, which is where an invalid
        # select_related() field name previously raised FieldError.
        results = list(PurchaseOrderReceiptViewSet.queryset)
        self.assertEqual(len(results), 1)


class CancelReasonTests(PurchaseOrdersAuditFixesTestBase):
    def test_cancel_stores_reason_and_reverses_on_order_quantity(self):
        order, line = self._make_order(quantity=Decimal("10"))
        self.stock_item.quantity_on_order = line.quantity_outstanding
        self.stock_item.save(update_fields=["quantity_on_order"])

        order.cancel(reason="Supplier discontinued the item")

        order.refresh_from_db()
        self.assertEqual(order.status, "C")
        self.assertEqual(order.cancellation_reason, "Supplier discontinued the item")
        self.assertIsNotNone(order.cancelled_at)

        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_order, Decimal("0"))

    def test_cancel_without_reason_leaves_it_blank(self):
        order, _line = self._make_order()
        order.cancel()
        order.refresh_from_db()
        self.assertEqual(order.cancellation_reason, "")

    def test_cancel_blocks_fully_received_order(self):
        order, _line = self._make_order(status="F")
        with self.assertRaises(ValueError):
            order.cancel(reason="too late")


class LineCommentsAndExpenseCategoryTests(PurchaseOrdersAuditFixesTestBase):
    def test_line_persists_comments_and_expense_category(self):
        category = ExpenseCategory.objects.create(
            number=1, name="Freight", category_type="CREDITORS"
        )
        order, _existing_line = self._make_order()
        line = PurchaseOrderLine.objects.create(
            purchase_order=order,
            line_number=2,
            stock_item=self.stock_item,
            stock_code=self.stock_item.stock_code,
            quantity=Decimal("5"),
            base_price=Decimal("50.00"),
            comments="Urgent — customer waiting",
            expense_category=category,
        )
        line.refresh_from_db()
        self.assertEqual(line.comments, "Urgent — customer waiting")
        self.assertEqual(line.expense_category_id, category.id)


class ResyncStockOnOrderTests(PurchaseOrdersAuditFixesTestBase):
    """Exercises the shared logic behind both the resync_po_quantities
    management command and the resync_on_order_quantities API action."""

    def test_resync_corrects_drifted_quantity(self):
        order, line = self._make_order(quantity=Decimal("10"))
        # Simulate drift: quantity_on_order out of sync with reality.
        self.stock_item.quantity_on_order = Decimal("999")
        self.stock_item.save(update_fields=["quantity_on_order"])

        result = resync_stock_on_order()

        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_order, line.quantity_outstanding)
        self.assertEqual(result["items_updated"], 1)
        self.assertEqual(result["changes"][0]["stock_code"], self.stock_item.stock_code)

    def test_resync_excludes_cancelled_orders(self):
        order, line = self._make_order(quantity=Decimal("10"), status="C")
        self.stock_item.quantity_on_order = Decimal("50")
        self.stock_item.save(update_fields=["quantity_on_order"])

        resync_stock_on_order()

        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_order, Decimal("0"))

    def test_resync_is_a_noop_when_already_correct(self):
        order, line = self._make_order(quantity=Decimal("10"))
        self.stock_item.quantity_on_order = line.quantity_outstanding
        self.stock_item.save(update_fields=["quantity_on_order"])

        result = resync_stock_on_order()

        self.assertEqual(result["items_updated"], 0)
        self.assertEqual(result["changes"], [])
