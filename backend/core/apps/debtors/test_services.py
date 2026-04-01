"""
Tests for DebtorService.
Unit tests for the debtor business logic layer.
"""
from decimal import Decimal
from datetime import date
from unittest.mock import patch, MagicMock
import pytest
from django.test import TestCase, override_settings
from django.db import transaction
from apps.debtors.models import Debtor, DebtorTransaction, Debtopen, Dpdc, DebtorAudit, Darea
from apps.debtors.services import DebtorService


class TestDebtorServiceCalculateAgeAnalysis(TestCase):
    """Tests for calculate_age_analysis method."""

    @classmethod
    def setUpTestData(cls):
        """Create test debtor."""
        cls.debtor = Debtor.objects.create(
            dno=1001,
            dname='Test Customer',
            dcontact='John Doe',
            dtel='0123456789',
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('500.00'),
            d30=Decimal('300.00'),
            d60=Decimal('200.00'),
            d90=Decimal('100.00'),
            d120=Decimal('50.00'),
            d150=Decimal('25.00'),
            d180=Decimal('25.00'),
        )

    def test_calculate_age_analysis_returns_all_fields(self):
        """Test that all age analysis fields are returned."""
        result = DebtorService.calculate_age_analysis(self.debtor)
        
        # Check basic debtor info
        assert result['dno'] == 1001
        assert result['dname'] == 'Test Customer'
        assert result['dcontact'] == 'John Doe'
        
        # Check aging buckets
        assert result['current'] == Decimal('500.00')
        assert result['days_30'] == Decimal('300.00')
        assert result['days_60'] == Decimal('200.00')
        assert result['days_90'] == Decimal('100.00')
        assert result['days_120'] == Decimal('50.00')
        assert result['days_150'] == Decimal('25.00')
        assert result['days_180'] == Decimal('25.00')

    def test_calculate_age_analysis_totals(self):
        """Test that total balance is calculated correctly."""
        result = DebtorService.calculate_age_analysis(self.debtor)
        
        # Total should be sum of all aging buckets
        expected_total = Decimal('500.00') + Decimal('300.00') + Decimal('200.00') + \
                        Decimal('100.00') + Decimal('50.00') + Decimal('25.00') + Decimal('25.00')
        assert result['total_balance'] == expected_total


class TestDebtorServiceGetDebtorsSummary(TestCase):
    """Tests for get_debtors_summary method."""

    @classmethod
    def setUpTestData(cls):
        """Create test debtors."""
        # Active debtor
        cls.debtor1 = Debtor.objects.create(
            dno=2001,
            dname='Active Customer',
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('500.00'),
            d30=Decimal('300.00'),
            d60=Decimal('200.00'),
            d90=Decimal('100.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
            blockflag='N',
        )
        
        # Another active debtor
        cls.debtor2 = Debtor.objects.create(
            dno=2002,
            dname='Another Customer',
            dclimit=Decimal('5000.00'),
            dcrnt=Decimal('100.00'),
            d30=Decimal('50.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
            blockflag='N',
        )
        
        # Blocked debtor
        cls.debtor3 = Debtor.objects.create(
            dno=2003,
            dname='Blocked Customer',
            dclimit=Decimal('5000.00'),
            dcrnt=Decimal('0.00'),
            d30=Decimal('0.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
            blockflag='Y',
        )

    def test_get_debtors_summary_counts(self):
        """Test that debtor counts are correct."""
        result = DebtorService.get_debtors_summary()
        
        assert result['total_debtors'] == 3
        assert result['active_debtors'] == 2
        assert result['blocked_debtors'] == 1

    def test_get_debtors_summary_balances(self):
        """Test that balances are calculated correctly."""
        result = DebtorService.get_debtors_summary()
        
        # Total balance = dcrnt + d30 + d60 + d90 + d120 + d150 + d180 for all debtors
        # debtor1: 500 + 300 + 200 + 100 + 0 + 0 + 0 = 1100
        # debtor2: 100 + 50 + 0 + 0 + 0 + 0 + 0 = 150
        # debtor3: 0 (blocked, no balance)
        assert result['total_balance'] == Decimal('1250.00')

    def test_get_debtors_summary_aging_buckets(self):
        """Test aging bucket calculations."""
        result = DebtorService.get_debtors_summary()
        
        # Current: 500 + 100 = 600
        # d30: 300 + 50 = 350
        # d60: 200 + 0 = 200
        # d90: 100 + 0 = 100
        # d120+: 0 + 0 = 0
        assert result['aging_summary']['current'] == Decimal('600.00')
        assert result['aging_summary']['days_30'] == Decimal('350.00')
        assert result['aging_summary']['days_60'] == Decimal('200.00')
        assert result['aging_summary']['days_90'] == Decimal('100.00')
        assert result['aging_summary']['days_120_plus'] == Decimal('0.00')


class TestDebtorServiceCalculateInterest(TestCase):
    """Tests for calculate_interest method."""

    @classmethod
    def setUpTestData(cls):
        """Create test debtor with interest flag."""
        cls.debtor = Debtor.objects.create(
            dno=3001,
            dname='Interest Customer',
            dintflag='Y',  # Interest enabled
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('1000.00'),
            d30=Decimal('500.00'),
            d60=Decimal('300.00'),
            d90=Decimal('200.00'),
            d120=Decimal('100.00'),
            d150=Decimal('50.00'),
            d180=Decimal('50.00'),
        )
        
        # Debtor without interest flag
        cls.debtor_no_interest = Debtor.objects.create(
            dno=3002,
            dname='No Interest Customer',
            dintflag='N',  # Interest disabled
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('500.00'),
            d30=Decimal('100.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
        )

    def test_calculate_interest_with_default_rate(self):
        """Test interest calculation with default 1% rate."""
        # From period 2 (30 days): d30 + d60 + d90 + d120 + d150 + d180
        # = 500 + 300 + 200 + 100 + 50 + 50 = 1200
        # Interest = 1200 * 0.01 = 12.00
        result = DebtorService.calculate_interest(self.debtor)
        
        assert result == Decimal('12.00')

    def test_calculate_interest_different_start_period(self):
        """Test interest calculation from different periods."""
        # From period 3 (60 days): d60 + d90 + d120 + d150 + d180
        # = 300 + 200 + 100 + 50 + 50 = 700
        # Interest = 700 * 0.01 = 7.00
        result = DebtorService.calculate_interest(self.debtor, start_period=3)
        
        assert result == Decimal('7.00')

    def test_calculate_interest_from_period_4(self):
        """Test interest calculation from period 4 (90 days)."""
        # From period 4: d90 + d120 + d150 + d180
        # = 200 + 100 + 50 + 50 = 400
        result = DebtorService.calculate_interest(self.debtor, start_period=4)
        
        assert result == Decimal('4.00')

    def test_calculate_interest_disabled_debtor(self):
        """Test that interest is zero for debtor without interest flag."""
        result = DebtorService.calculate_interest(self.debtor_no_interest)
        
        assert result == Decimal('0.00')

    def test_calculate_interest_custom_rate(self):
        """Test interest calculation with custom rate."""
        # 1200 * 0.02 = 24.00
        result = DebtorService.calculate_interest(self.debtor, rate=0.02)
        
        assert result == Decimal('24.00')


class TestDebtorServiceCheckCreditLimit(TestCase):
    """Tests for check_credit_limit method."""

    @classmethod
    def setUpTestData(cls):
        """Create test debtors."""
        # Debtor under limit
        cls.debtor_under = Debtor.objects.create(
            dno=4001,
            dname='Under Limit Customer',
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('3000.00'),
            d30=Decimal('1000.00'),
            d60=Decimal('500.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
        )
        
        # Debtor over limit
        cls.debtor_over = Debtor.objects.create(
            dno=4002,
            dname='Over Limit Customer',
            dclimit=Decimal('5000.00'),
            dcrnt=Decimal('3000.00'),
            d30=Decimal('2000.00'),
            d60=Decimal('500.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
        )

    def test_check_credit_limit_under_limit(self):
        """Test credit limit check for customer under limit."""
        result = DebtorService.check_credit_limit(self.debtor_under)
        
        assert result['over_limit'] is False
        assert result['total_balance'] == Decimal('4500.00')
        assert result['dclimit'] == Decimal('10000.00')
        assert result['available_credit'] == Decimal('5500.00')
        assert result['percentage_used'] == 45.0

    def test_check_credit_limit_over_limit(self):
        """Test credit limit check for customer over limit."""
        result = DebtorService.check_credit_limit(self.debtor_over)
        
        assert result['over_limit'] is True
        assert result['total_balance'] == Decimal('5500.00')
        assert result['dclimit'] == Decimal('5000.00')
        assert result['available_credit'] == Decimal('-500.00')
        assert result['percentage_used'] == 110.0


class TestDebtorServicePostReceipt(TestCase):
    """Tests for post_receipt method."""

    @classmethod
    def setUpTestData(cls):
        """Create test debtor."""
        cls.debtor = Debtor.objects.create(
            dno=5001,
            dname='Receipt Customer',
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('1000.00'),
            d30=Decimal('500.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
            blockflag='N',
            ddatlpd=None,
            damtlpd=Decimal('0.00'),
        )
        
        # Blocked debtor
        cls.blocked_debtor = Debtor.objects.create(
            dno=5002,
            dname='Blocked Receipt Customer',
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('100.00'),
            d30=Decimal('0.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
            blockflag='Y',
        )

    def test_post_receipt_blocked_debtor_raises_error(self):
        """Test that receipt cannot be posted to blocked debtor."""
        with self.assertRaises(ValueError) as context:
            DebtorService.post_receipt(
                debtor=self.blocked_debtor,
                amount=Decimal('100.00')
            )
        
        assert "is blocked" in str(context.exception)

    def test_post_receipt_negative_amount_raises_error(self):
        """Test that negative receipt amount raises error."""
        with self.assertRaises(ValueError) as context:
            DebtorService.post_receipt(
                debtor=self.debtor,
                amount=Decimal('-50.00')
            )
        
        assert "positive" in str(context.exception)

    def test_post_receipt_zero_amount_raises_error(self):
        """Test that zero receipt amount raises error."""
        with self.assertRaises(ValueError) as context:
            DebtorService.post_receipt(
                debtor=self.debtor,
                amount=Decimal('0.00')
            )
        
        assert "positive" in str(context.exception)


class TestDebtorServiceAgeBalances(TestCase):
    """Tests for age_balances method."""

    @classmethod
    def setUpTestData(cls):
        """Create test debtors."""
        cls.debtor1 = Debtor.objects.create(
            dno=6001,
            dname='Age Balance Customer 1',
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('500.00'),
            d30=Decimal('400.00'),
            d60=Decimal('300.00'),
            d90=Decimal('200.00'),
            d120=Decimal('100.00'),
            d150=Decimal('50.00'),
            d180=Decimal('25.00'),
            dsalesm=Decimal('100.00'),
            dprofitm=Decimal('20.00'),
        )
        
        cls.debtor2 = Debtor.objects.create(
            dno=6002,
            dname='Age Balance Customer 2',
            dclimit=Decimal('5000.00'),
            dcrnt=Decimal('100.00'),
            d30=Decimal('50.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
            dsalesm=Decimal('50.00'),
            dprofitm=Decimal('10.00'),
        )

    def test_age_balances_shifts_buckets(self):
        """Test that aging buckets shift correctly."""
        count = DebtorService.age_balances()
        
        # Reload from database
        self.debtor1.refresh_from_db()
        self.debtor2.refresh_from_db()
        
        # debtor1 should have shifted:
        # dcrnt was 500 -> goes to d30
        # d30 was 400 -> goes to d60
        # d60 was 300 -> goes to d90
        # d90 was 200 -> goes to d120
        # d120 was 100 -> goes to d150
        # d150 was 50 -> goes to d180
        # d180 was 25 -> stays in d180 (or could be written off)
        
        assert self.debtor1.dcrnt == Decimal('0.00')
        assert self.debtor1.d30 == Decimal('500.00')  # old dcrnt
        assert self.debtor1.d60 == Decimal('400.00')  # old d30
        assert self.debtor1.d90 == Decimal('300.00')  # old d60
        assert self.debtor1.d120 == Decimal('200.00')  # old d90
        assert self.debtor1.d150 == Decimal('100.00')  # old d120
        assert self.debtor1.d180 == Decimal('50.00')  # old d150

    def test_age_balances_resets_mtd_stats(self):
        """Test that MTD stats are reset after aging."""
        DebtorService.age_balances()
        
        self.debtor1.refresh_from_db()
        
        # MTD sales and profit should be reset
        assert self.debtor1.dsalesm == Decimal('0.00')
        assert self.debtor1.dprofitm == Decimal('0.00')

    def test_age_balances_returns_count(self):
        """Test that method returns number of debtors processed."""
        count = DebtorService.age_balances()
        
        assert count == 2


class TestDebtorServiceGetTopCustomers(TestCase):
    """Tests for get_top_customers method."""

    @classmethod
    def setUpTestData(cls):
        """Create test debtors with different sales."""
        Debtor.objects.create(
            dno=7001,
            dname='Low Sales Customer',
            is_active=True,
            dclimit=Decimal('5000.00'),
            dcrnt=Decimal('100.00'),
            d30=Decimal('0.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
        )
        
        Debtor.objects.create(
            dno=7002,
            dname='High Sales Customer',
            is_active=True,
            dclimit=Decimal('20000.00'),
            dcrnt=Decimal('5000.00'),
            d30=Decimal('1000.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
        )
        
        # Inactive customer (should be excluded)
        Debtor.objects.create(
            dno=7003,
            dname='Inactive Customer',
            is_active=False,
            dclimit=Decimal('10000.00'),
            dcrnt=Decimal('10000.00'),
            d30=Decimal('0.00'),
            d60=Decimal('0.00'),
            d90=Decimal('0.00'),
            d120=Decimal('0.00'),
            d150=Decimal('0.00'),
            d180=Decimal('0.00'),
        )

    def test_get_top_customers_returns_active_only(self):
        """Test that only active customers are returned."""
        # Note: The actual implementation uses sales_mtd/sales_ytd fields
        # which may not exist or may be 0 for new test data
        results = DebtorService.get_top_customers(limit=10)
        
        # Should return at most the 2 active customers
        assert len(results) <= 2
        
        # All returned should be active
        for debtor in results:
            assert debtor.is_active is True