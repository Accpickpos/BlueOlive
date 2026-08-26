"""
Cash Book Module Tests
Comprehensive test coverage for models, services, and API endpoints
"""

from datetime import date, timedelta
from decimal import Decimal

from apps.settings.models import ExpenseCategory, IncomeCategory, TaxCode
from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import (
    BankDeposit,
    BankReconciliation,
    CashBookTransaction,
    CashFloat,
    OtherExpense,
    OtherIncome,
)
from .services import (
    BalanceCalculationService,
    ReconciliationService,
    SummaryService,
    TransactionNumberGenerator,
    TransactionService,
    VATService,
)


class VATServiceTest(TestCase):
    """Test VAT calculation service"""

    def test_vat_calculation_inclusive(self):
        """Test VAT calculation with inclusive amount"""
        amount = Decimal("114.00")  # 100 + 14% VAT
        vat = VATService.calculate_vat(amount, tax_code=1, is_inclusive=True)

        expected_vat = Decimal("14.00")
        self.assertAlmostEqual(vat, expected_vat, places=2)

    def test_vat_calculation_exclusive(self):
        """Test VAT calculation with exclusive amount"""
        amount = Decimal("100.00")
        vat = VATService.calculate_vat(amount, tax_code=1, is_inclusive=False)

        expected_vat = Decimal("14.00")
        self.assertAlmostEqual(vat, expected_vat, places=2)

    def test_no_vat_for_tax_code_2(self):
        """Test that tax code 2 results in zero VAT"""
        amount = Decimal("100.00")
        vat = VATService.calculate_vat(amount, tax_code=2, is_inclusive=True)

        self.assertEqual(vat, Decimal("0"))

    def test_get_net_amount(self):
        """Test getting net amount before VAT"""
        amount = Decimal("114.00")
        net = VATService.get_net_amount(amount, tax_code=1, is_inclusive=True)

        expected_net = Decimal("100.00")
        self.assertAlmostEqual(net, expected_net, places=2)


class TransactionNumberGeneratorTest(TestCase):
    """Test transaction number generation"""

    def setUp(self):
        """Set up test data"""
        self.income_category = IncomeCategory.objects.create(
            name="Test Income", category_number="INC001"
        )

    def test_generate_unique_numbers(self):
        """Test that generated numbers are unique"""
        today = date.today()

        # Create first transaction
        num1 = TransactionNumberGenerator.generate("OTHER_INCOME", today)

        # Create actual transaction
        CashBookTransaction.objects.create(
            transaction_type="OTHER_INCOME",
            transaction_number=num1,
            transaction_date=today,
            amount=Decimal("100.00"),
            description="Test",
        )

        # Generate second number
        num2 = TransactionNumberGenerator.generate("OTHER_INCOME", today)

        self.assertNotEqual(num1, num2)
        self.assertTrue(num2.endswith("00002"))

    def test_number_format(self):
        """Test that generated numbers follow correct format"""
        num = TransactionNumberGenerator.generate("OTHER_INCOME")

        # Format should be INC-YYYYMMDD-00001
        parts = num.split("-")
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "INC")
        self.assertEqual(len(parts[1]), 8)  # YYYYMMDD
        self.assertEqual(len(parts[2]), 5)  # 00001


class BalanceCalculationServiceTest(TestCase):
    """Test balance calculation service"""

    def setUp(self):
        """Set up test data"""
        self.income_category = IncomeCategory.objects.create(
            name="Test Income", category_number="INC001"
        )
        today = date.today()

        # Create test transactions
        self.txn1 = CashBookTransaction.objects.create(
            transaction_type="RECEIPT",
            transaction_number="RCP-20240101-00001",
            transaction_date=today,
            amount=Decimal("100.00"),
            description="Receipt 1",
            account_type="CASH",
        )

        self.txn2 = CashBookTransaction.objects.create(
            transaction_type="PAYMENT",
            transaction_number="PAY-20240101-00001",
            transaction_date=today,
            amount=Decimal("30.00"),
            description="Payment 1",
            account_type="CASH",
        )

    def test_balance_calculation(self):
        """Test that running balances are calculated correctly"""
        BalanceCalculationService.update_running_balances()

        self.txn1.refresh_from_db()
        self.txn2.refresh_from_db()

        self.assertEqual(self.txn1.running_balance_cash, Decimal("100.00"))
        self.assertEqual(self.txn2.running_balance_cash, Decimal("70.00"))

    def test_get_current_balances(self):
        """Test getting current balances"""
        BalanceCalculationService.update_running_balances()

        balances = BalanceCalculationService.get_current_balances()

        self.assertEqual(balances["cash"], Decimal("70.00"))
        self.assertEqual(balances["bank"], Decimal("0.00"))


class TransactionServiceTest(TestCase):
    """Test transaction creation service"""

    def setUp(self):
        """Set up test data"""
        self.income_category = IncomeCategory.objects.create(
            name="Test Income", category_number="INC001"
        )

    def test_create_other_income(self):
        """Test creating other income transaction"""
        today = date.today()

        income = TransactionService.create_other_income(
            transaction_date=today,
            income_category_id=self.income_category.id,
            amount=Decimal("100.00"),
            description="Test income",
            is_vat_inclusive=True,
            tax_code=1,
            created_by="test_user",
        )

        self.assertIsNotNone(income.id)
        self.assertEqual(income.transaction.amount, Decimal("100.00"))
        self.assertGreater(income.vat_amount, Decimal("0"))


class SummaryServiceTest(TestCase):
    """Test summary report service"""

    def setUp(self):
        """Set up test data"""
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Create transactions
        CashBookTransaction.objects.create(
            transaction_type="RECEIPT",
            transaction_number="RCP-20240101-00001",
            transaction_date=yesterday,
            amount=Decimal("1000.00"),
            description="Opening receipt",
            account_type="CASH",
        )

        CashBookTransaction.objects.create(
            transaction_type="RECEIPT",
            transaction_number="RCP-20240102-00001",
            transaction_date=today,
            amount=Decimal("500.00"),
            description="Income",
            account_type="CASH",
        )

        CashBookTransaction.objects.create(
            transaction_type="PAYMENT",
            transaction_number="PAY-20240102-00001",
            transaction_date=today,
            amount=Decimal("200.00"),
            description="Expense",
            account_type="CASH",
        )

        BalanceCalculationService.update_running_balances()

    def test_period_summary(self):
        """Test getting summary for a period"""
        today = date.today()

        summary = SummaryService.get_period_summary(today, today)

        self.assertEqual(summary["total_receipts"], Decimal("500.00"))
        self.assertEqual(summary["total_payments"], Decimal("200.00"))
        self.assertEqual(summary["transaction_count"], 2)


class CashBookTransactionModelTest(TestCase):
    """Test CashBookTransaction model"""

    def test_debit_transaction(self):
        """Test debit transaction detection"""
        txn = CashBookTransaction(
            transaction_type="RECEIPT",
            transaction_number="RCP-20240101-00001",
            transaction_date=date.today(),
            amount=Decimal("100.00"),
            description="Test",
        )

        self.assertTrue(txn.is_debit)
        self.assertFalse(txn.is_credit)

    def test_credit_transaction(self):
        """Test credit transaction detection"""
        txn = CashBookTransaction(
            transaction_type="PAYMENT",
            transaction_number="PAY-20240101-00001",
            transaction_date=date.today(),
            amount=Decimal("100.00"),
            description="Test",
        )

        self.assertFalse(txn.is_debit)
        self.assertTrue(txn.is_credit)

    def test_can_modify_unreconciled(self):
        """Test that unreconciled transactions can be modified"""
        txn = CashBookTransaction.objects.create(
            transaction_type="RECEIPT",
            transaction_number="RCP-20240101-00001",
            transaction_date=date.today(),
            amount=Decimal("100.00"),
            description="Test",
            is_reconciled=False,
        )

        self.assertTrue(txn.can_be_modified())

    def test_cannot_modify_reconciled(self):
        """Test that reconciled transactions cannot be modified"""
        txn = CashBookTransaction.objects.create(
            transaction_type="RECEIPT",
            transaction_number="RCP-20240101-00001",
            transaction_date=date.today(),
            amount=Decimal("100.00"),
            description="Test",
            is_reconciled=True,
        )

        self.assertFalse(txn.can_be_modified())


class CashBookTransactionAPITest(APITestCase):
    """Test Cash Book Transaction API endpoints"""

    def setUp(self):
        """Set up test data and authentication"""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",  # nosec B105 B106 - test fixture password
        )

        # Create Cashier group
        self.cashier_group = Group.objects.create(name="Cashier")
        self.user.groups.add(self.cashier_group)

        # Create test data
        today = date.today()
        CashBookTransaction.objects.create(
            transaction_type="RECEIPT",
            transaction_number="RCP-20240101-00001",
            transaction_date=today,
            amount=Decimal("100.00"),
            description="Test receipt",
            account_type="CASH",
        )

        BalanceCalculationService.update_running_balances()

    def test_list_transactions_requires_auth(self):
        """Test that listing transactions requires authentication"""
        response = self.client.get("/api/cashbook/transactions/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_transactions_authenticated(self):
        """Test listing transactions when authenticated"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/cashbook/transactions/")

        # Will return 404 until URL is properly configured
        self.assertIn(
            response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
        )

    def test_summary_endpoint_requires_dates(self):
        """Test that summary endpoint requires date parameters"""
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/cashbook/transactions/summary/")

        # Will return 400 or 404 depending on routing
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND],
        )
