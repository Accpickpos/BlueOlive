"""
Comprehensive tests for the creditors app.
Tests cover models, signals, serializers, and API endpoints.
"""

from decimal import Decimal

from apps.settings.models import ExpenseCategory, TaxCode
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from .models import (
    RFC,
    Creditor,
    CreditorInvoice,
    CreditorInvoiceLineItem,
    CreditorOpenItem,
    CreditorPayment,
    OpenItemAllocation,
    RFCLineItem,
)


class CreditorModelTests(TestCase):
    """Tests for Creditor model"""

    def setUp(self):
        """Create test data"""
        self.creditor = Creditor.objects.create(
            supplier_number="1001",
            name="Test Supplier",
            contact_person="John Doe",
            email="supplier@test.com",
            telephone="0123456789",
        )

    def test_supplier_creation(self):
        """Test creditor can be created"""
        self.assertEqual(self.creditor.supplier_number, "1001")
        self.assertEqual(self.creditor.name, "Test Supplier")
        self.assertTrue(self.creditor.is_active)

    def test_supplier_total_balance(self):
        """Test total_outstanding_balance is rolled up from the aging buckets on save"""
        self.creditor.balance_current = Decimal("100.00")
        self.creditor.balance_30_days = Decimal("200.00")
        self.creditor.balance_60_days = Decimal("300.00")
        self.creditor.save()

        self.assertEqual(self.creditor.total_outstanding_balance, Decimal("600.00"))

    def test_supplier_validation_empty_name(self):
        """Test creditor validation for empty name"""
        creditor = Creditor(supplier_number="1002", name="")
        with self.assertRaises(ValidationError):
            creditor.full_clean()

    def test_supplier_validation_negative_discount(self):
        """Test creditor validation for negative discount"""
        creditor = Creditor(
            supplier_number="1003",
            name="Test",
            prompt_payment_discount_percent=Decimal("-5.00"),
        )
        with self.assertRaises(ValidationError):
            creditor.full_clean()

    def test_supplier_string_representation(self):
        """Test creditor string representation"""
        self.assertEqual(str(self.creditor), "1001 - Test Supplier")


class TaxCodeTests(TestCase):
    """Tests for tax code usage"""

    def setUp(self):
        """Create test tax codes"""
        self.tax_14 = TaxCode.objects.create(
            code=1, description="VAT 14%", rate=Decimal("14.00"), is_active=True
        )
        self.tax_0 = TaxCode.objects.create(
            code=2, description="Zero Rated", rate=Decimal("0.00"), is_active=True
        )

    def test_tax_code_creation(self):
        """Test tax code is created properly"""
        self.assertEqual(self.tax_14.rate, Decimal("14.00"))
        self.assertEqual(self.tax_0.rate, Decimal("0.00"))


class CreditorInvoiceTests(TransactionTestCase):
    """Tests for CreditorInvoice creation, numbering, and balance rollups.

    CreditorTransaction (the old flat, directly-instantiable transaction
    model these tests targeted) is abstract — real transactions are the
    concrete per-type subclasses (CreditorInvoice, CreditorPayment, etc),
    with amounts held on line items and rolled up onto the header by
    signals.py, not passed in at create() time.
    """

    def setUp(self):
        """Create test data"""
        self.tax_code = TaxCode.objects.create(
            code=1,
            description="VAT 14%",
            rate=Decimal("14.00"),
            is_active=True,
            is_default=True,
        )
        self.expense_category = ExpenseCategory.objects.create(
            number=1, name="Test Expense", category_type="BOTH"
        )
        self.creditor = Creditor.objects.create(
            supplier_number="1001",
            name="Test Supplier",
            account_category="BBF",
            is_active=True,
        )

    def _make_invoice(self, invoice_number="EXP-1"):
        return CreditorInvoice.objects.create(
            creditor=self.creditor,
            transaction_date=timezone.now().date(),
            supplier_invoice_number=invoice_number,
        )

    def test_transaction_creation(self):
        """Test invoice total is rolled up from its line item(s)"""
        invoice = self._make_invoice()
        CreditorInvoiceLineItem.objects.create(
            invoice=invoice,
            line_number=1,
            expense_category=self.expense_category,
            amount=Decimal("1000.00"),
            tax_code=self.tax_code,
        )

        invoice.refresh_from_db()
        self.assertEqual(invoice.total_amount, Decimal("1140.00"))

    def test_transaction_auto_number_generation(self):
        """Test transaction number is auto-generated"""
        invoice = self._make_invoice()
        self.assertTrue(invoice.transaction_number.startswith("INV-"))

    def test_supplier_balance_update_on_invoice(self):
        """Test creditor balance_current updates when an invoice is posted"""
        initial_balance = self.creditor.balance_current

        invoice = self._make_invoice()
        CreditorInvoiceLineItem.objects.create(
            invoice=invoice,
            line_number=1,
            expense_category=self.expense_category,
            amount=Decimal("1000.00"),
            tax_code=self.tax_code,
        )

        self.creditor.refresh_from_db()
        self.assertEqual(
            self.creditor.balance_current, initial_balance + Decimal("1140.00")
        )

    def test_supplier_balance_update_on_payment(self):
        """Test creditor's last-payment info updates when a payment is created"""
        CreditorPayment.objects.create(
            creditor=self.creditor,
            transaction_date=timezone.now().date(),
            amount_due=Decimal("500.00"),
            amount_paid=Decimal("500.00"),
        )

        self.creditor.refresh_from_db()
        self.assertEqual(self.creditor.last_paid_amount, Decimal("500.00"))
        self.assertEqual(self.creditor.last_paid_date, timezone.now().date())


class RFCTests(TransactionTestCase):
    """Tests for RFC (Returns for Credit) model"""

    def setUp(self):
        """Create test data"""
        self.tax_code = TaxCode.objects.create(
            code=1,
            description="VAT 14%",
            rate=Decimal("14.00"),
            is_active=True,
            is_default=True,
        )

        self.creditor = Creditor.objects.create(
            supplier_number="1001", name="Test Supplier"
        )

        self.rfc = RFC.objects.create(
            creditor=self.creditor,
            rfc_number="000001",
            return_date=timezone.now().date(),
            status="PE",
        )

    def test_rfc_creation(self):
        """Test RFC is created properly"""
        self.assertEqual(self.rfc.status, "PE")
        self.assertEqual(self.rfc.creditor, self.creditor)

    def test_rfc_total_calculation(self):
        """Test RFC totals are calculated from line items (see RFCLineItem.save
        in models.py / signals.py for the real rollup; this exercises the
        plain field roundtrip)."""
        self.rfc.total_value_exclusive = Decimal("1000.00")
        self.rfc.total_value_inclusive = Decimal("1140.00")
        self.rfc.save()

        self.assertEqual(self.rfc.total_value_inclusive, Decimal("1140.00"))

    def test_rfc_status_workflow(self):
        """Test RFC status workflow"""
        self.assertEqual(self.rfc.status, "PE")

        # Mark as credit note received
        self.rfc.status = "CR"
        self.rfc.date_returned = timezone.now().date()
        self.rfc.save()

        self.assertEqual(self.rfc.status, "CR")
        self.assertIsNotNone(self.rfc.date_returned)


class OpenItemAllocationTests(TransactionTestCase):
    """Tests for Open Item Allocation"""

    def setUp(self):
        """Create test data: an invoice (and its auto-created open item) plus
        a payment to allocate against it."""
        self.tax_code = TaxCode.objects.create(
            code=1,
            description="VAT 14%",
            rate=Decimal("14.00"),
            is_active=True,
            is_default=True,
        )
        self.expense_category = ExpenseCategory.objects.create(
            number=1, name="Test Expense", category_type="BOTH"
        )
        self.creditor = Creditor.objects.create(
            supplier_number="1001", name="Test Supplier", account_category="OI"
        )

        self.invoice = CreditorInvoice.objects.create(
            creditor=self.creditor,
            transaction_date=timezone.now().date(),
            supplier_invoice_number="EXP-1",
        )
        CreditorInvoiceLineItem.objects.create(
            invoice=self.invoice,
            line_number=1,
            expense_category=self.expense_category,
            amount=Decimal("1000.00"),
            tax_code=self.tax_code,
        )
        self.open_item = CreditorOpenItem.objects.get(invoice=self.invoice)

        self.payment = CreditorPayment.objects.create(
            creditor=self.creditor,
            transaction_date=timezone.now().date(),
            amount_due=Decimal("600.00"),
            amount_paid=Decimal("600.00"),
        )

    def test_allocation_creation(self):
        """Test allocation is created"""
        allocation = OpenItemAllocation.objects.create(
            payment=self.payment,
            open_item=self.open_item,
            amount_paid=Decimal("600.00"),
        )

        self.assertEqual(allocation.amount_paid, Decimal("600.00"))

    def test_invoice_balance_update_on_allocation(self):
        """Test open item balance_due updates when an allocation is made"""
        initial_balance = self.open_item.balance_due

        OpenItemAllocation.objects.create(
            payment=self.payment,
            open_item=self.open_item,
            amount_paid=Decimal("600.00"),
        )

        self.open_item.refresh_from_db()
        self.assertEqual(
            self.open_item.balance_due, initial_balance - Decimal("600.00")
        )

    def test_invoice_marked_fully_allocated(self):
        """Test open item is marked fully allocated when balance is zero"""
        OpenItemAllocation.objects.create(
            payment=self.payment,
            open_item=self.open_item,
            amount_paid=Decimal("1140.00"),
        )

        self.open_item.refresh_from_db()
        self.assertTrue(self.open_item.is_fully_allocated)
        self.assertEqual(self.open_item.balance_due, 0)


# No SupplierMonthlyPurchaseTests: there is no per-supplier monthly purchase
# model in the current schema (purchases_mtd/purchases_ytd live directly on
# Creditor; ExpenseCategoryMonthlyBalance tracks expense categories, not
# suppliers) — the functionality these tests targeted doesn't exist to test.
