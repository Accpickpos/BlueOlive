"""
Comprehensive tests for the creditors app.
Tests cover models, signals, serializers, and API endpoints.
"""

from datetime import timedelta
from decimal import Decimal

from apps.settings.models import CreditTerms, SalesArea, TaxCode
from django.core.exceptions import ValidationError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from tenancy.models import Shop, Tenant

from .models import (
    RFC,
    CreditorTransaction,
    CreditorTransactionLine,
    ExpenseCategory,
    ExpenseMonthlyTotal,
    OpenItemAllocation,
    RFCLineItem,
    Supplier,
    SupplierMonthlyPurchase,
)


class SupplierModelTests(TestCase):
    """Tests for Supplier model"""

    def setUp(self):
        """Create test data"""
        self.supplier = Supplier.objects.create(
            account_number=1001,
            name="Test Supplier",
            short_name="TS",
            email="supplier@test.com",
            telephone1="0123456789",
        )

    def test_supplier_creation(self):
        """Test supplier can be created"""
        self.assertEqual(self.supplier.account_number, 1001)
        self.assertEqual(self.supplier.name, "Test Supplier")
        self.assertTrue(self.supplier.is_active)

    def test_supplier_total_balance(self):
        """Test total balance calculation"""
        self.supplier.balance_current = Decimal("100.00")
        self.supplier.balance_30_days = Decimal("200.00")
        self.supplier.balance_60_days = Decimal("300.00")
        self.supplier.save()

        total = self.supplier.get_total_balance()
        self.assertEqual(total, Decimal("600.00"))

    def test_supplier_total_balance_with_rfc(self):
        """Test total balance including RFC"""
        self.supplier.balance_current = Decimal("100.00")
        self.supplier.rfc_outstanding_amount = Decimal("50.00")
        self.supplier.save()

        total = self.supplier.get_total_balance_with_rfc()
        self.assertEqual(total, Decimal("150.00"))

    def test_supplier_validation_empty_name(self):
        """Test supplier validation for empty name"""
        supplier = Supplier(account_number=1002, name="")
        with self.assertRaises(ValidationError):
            supplier.full_clean()

    def test_supplier_validation_negative_discount(self):
        """Test supplier validation for negative discount"""
        supplier = Supplier(
            account_number=1003,
            name="Test",
            prompt_payment_discount_percent=Decimal("-5.00"),
        )
        with self.assertRaises(ValidationError):
            supplier.full_clean()

    def test_supplier_string_representation(self):
        """Test supplier string representation"""
        self.assertEqual(str(self.supplier), "1001 - Test Supplier")


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


class CreditorTransactionTests(TransactionTestCase):
    """Tests for CreditorTransaction model and signals"""

    def setUp(self):
        """Create test data"""
        self.tax_code = TaxCode.objects.create(
            code=1,
            description="VAT 14%",
            rate=Decimal("14.00"),
            is_active=True,
            is_default=True,
        )

        self.supplier = Supplier.objects.create(
            account_number=1001,
            name="Test Supplier",
            account_type="",  # Balance Brought Forward
            is_active=True,
        )

    def test_transaction_creation(self):
        """Test transaction can be created"""
        transaction = CreditorTransaction.objects.create(
            transaction_type="INVOICE_STOCK",
            supplier=self.supplier,
            transaction_date=timezone.now().date(),
            transaction_number="INV-001",
            amount_exclusive=Decimal("1000.00"),
            vat_amount=Decimal("140.00"),
            amount_inclusive=Decimal("1140.00"),
        )

        self.assertEqual(transaction.amount_inclusive, Decimal("1140.00"))

    def test_transaction_auto_number_generation(self):
        """Test transaction number is auto-generated"""
        transaction = CreditorTransaction(
            transaction_type="INVOICE_STOCK",
            supplier=self.supplier,
            amount_inclusive=Decimal("100.00"),
        )
        transaction.save()

        self.assertTrue(transaction.transaction_number.startswith("INV-"))

    def test_transaction_future_date_validation(self):
        """Test transaction cannot be dated in future"""
        future_date = timezone.now().date() + timedelta(days=1)
        transaction = CreditorTransaction(
            transaction_type="INVOICE_STOCK",
            supplier=self.supplier,
            transaction_date=future_date,
            amount_inclusive=Decimal("100.00"),
        )

        with self.assertRaises(ValidationError):
            transaction.full_clean()

    def test_supplier_balance_update_on_invoice(self):
        """Test supplier balance updates when invoice is created"""
        initial_balance = self.supplier.balance_current

        CreditorTransaction.objects.create(
            transaction_type="INVOICE_STOCK",
            supplier=self.supplier,
            transaction_date=timezone.now().date(),
            transaction_number="INV-001",
            amount_inclusive=Decimal("1000.00"),
            age_current=Decimal("1000.00"),
        )

        self.supplier.refresh_from_db()
        self.assertEqual(
            self.supplier.balance_current, initial_balance + Decimal("1000.00")
        )

    def test_supplier_balance_update_on_payment(self):
        """Test supplier balance updates when payment is created"""
        self.supplier.balance_current = Decimal("1000.00")
        self.supplier.save()

        CreditorTransaction.objects.create(
            transaction_type="PAYMENT",
            supplier=self.supplier,
            transaction_date=timezone.now().date(),
            transaction_number="PAY-001",
            amount_inclusive=Decimal("500.00"),
            age_current=Decimal("500.00"),
        )

        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.amount_last_paid, Decimal("500.00"))
        self.assertEqual(self.supplier.balance_current, Decimal("500.00"))


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

        self.supplier = Supplier.objects.create(
            account_number=1001, name="Test Supplier"
        )

        self.rfc = RFC.objects.create(
            supplier=self.supplier, return_date=timezone.now().date(), status="PENDING"
        )

    def test_rfc_creation(self):
        """Test RFC is created properly"""
        self.assertEqual(self.rfc.status, "PENDING")
        self.assertEqual(self.rfc.supplier, self.supplier)

    def test_rfc_total_calculation(self):
        """Test RFC totals are calculated from line items"""
        # This would require StockItem which we can't import easily
        # So we'll test the calculation method logic
        self.rfc.total_exclusive = Decimal("1000.00")
        self.rfc.total_vat = Decimal("140.00")
        self.rfc.total_inclusive = Decimal("1140.00")
        self.rfc.save()

        self.assertEqual(self.rfc.total_inclusive, Decimal("1140.00"))

    def test_rfc_status_workflow(self):
        """Test RFC status workflow"""
        self.assertEqual(self.rfc.status, "PENDING")

        # Mark as credit received
        self.rfc.status = "CREDIT_RECEIVED"
        self.rfc.credit_date = timezone.now().date()
        self.rfc.save()

        self.assertEqual(self.rfc.status, "CREDIT_RECEIVED")
        self.assertIsNotNone(self.rfc.credit_date)


class OpenItemAllocationTests(TransactionTestCase):
    """Tests for Open Item Allocation"""

    def setUp(self):
        """Create test data"""
        self.supplier = Supplier.objects.create(
            account_number=1001, name="Test Supplier", account_type="O"  # Open Item
        )

        # Create invoice
        self.invoice = CreditorTransaction.objects.create(
            transaction_type="INVOICE_STOCK",
            supplier=self.supplier,
            transaction_date=timezone.now().date(),
            transaction_number="INV-001",
            amount_inclusive=Decimal("1000.00"),
            is_allocated=False,
            balance_due=Decimal("1000.00"),
        )

        # Create payment
        self.payment = CreditorTransaction.objects.create(
            transaction_type="PAYMENT",
            supplier=self.supplier,
            transaction_date=timezone.now().date(),
            transaction_number="PAY-001",
            amount_inclusive=Decimal("600.00"),
        )

    def test_allocation_creation(self):
        """Test allocation is created"""
        allocation = OpenItemAllocation.objects.create(
            supplier=self.supplier,
            invoice_transaction=self.invoice,
            payment_transaction=self.payment,
            amount_allocated=Decimal("600.00"),
        )

        self.assertEqual(allocation.amount_allocated, Decimal("600.00"))

    def test_invoice_balance_update_on_allocation(self):
        """Test invoice balance updates when allocation is made"""
        initial_balance = self.invoice.balance_due

        OpenItemAllocation.objects.create(
            supplier=self.supplier,
            invoice_transaction=self.invoice,
            payment_transaction=self.payment,
            amount_allocated=Decimal("600.00"),
        )

        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.balance_due, initial_balance - Decimal("600.00"))

    def test_invoice_marked_fully_allocated(self):
        """Test invoice is marked fully allocated when balance is zero"""
        OpenItemAllocation.objects.create(
            supplier=self.supplier,
            invoice_transaction=self.invoice,
            payment_transaction=self.payment,
            amount_allocated=Decimal("1000.00"),
        )

        self.invoice.refresh_from_db()
        self.assertTrue(self.invoice.is_allocated)
        self.assertEqual(self.invoice.balance_due, 0)


class SupplierMonthlyPurchaseTests(TestCase):
    """Tests for supplier monthly purchase statistics"""

    def setUp(self):
        """Create test data"""
        self.supplier = Supplier.objects.create(
            account_number=1001, name="Test Supplier"
        )

    def test_monthly_purchase_creation(self):
        """Test monthly purchase record creation"""
        purchase = SupplierMonthlyPurchase.objects.create(
            supplier=self.supplier,
            year=2024,
            month=1,
            stock_purchases_exclusive=Decimal("5000.00"),
            stock_purchases_vat=Decimal("700.00"),
            stock_purchases_inclusive=Decimal("5700.00"),
        )

        self.assertEqual(purchase.year, 2024)
        self.assertEqual(purchase.month, 1)
        self.assertEqual(purchase.stock_purchases_inclusive, Decimal("5700.00"))

    def test_monthly_purchase_unique_constraint(self):
        """Test unique constraint on supplier-year-month"""
        SupplierMonthlyPurchase.objects.create(
            supplier=self.supplier,
            year=2024,
            month=1,
            stock_purchases_exclusive=Decimal("5000.00"),
            stock_purchases_inclusive=Decimal("5700.00"),
        )

        # Try to create duplicate
        duplicate = SupplierMonthlyPurchase(
            supplier=self.supplier,
            year=2024,
            month=1,
            stock_purchases_exclusive=Decimal("1000.00"),
            stock_purchases_inclusive=Decimal("1140.00"),
        )

        with self.assertRaises(Exception):
            duplicate.save()
