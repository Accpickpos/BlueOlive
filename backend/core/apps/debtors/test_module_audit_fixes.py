"""
Targeted regression tests for the Debtors-module fixes from the priority-gap
audit: single-ageing-period allocation for Open Item journals, Account
Category Conversion touching Debtopen, and the DebtorService.get_debtor_statement
field-name/None-arithmetic bugs. View-level actions (age_analysis_detail,
statement, charge_interest, DebteopenViewSet.allocate/allocate_receipt) need
full tenant/shop request context this test env doesn't have wired up, so
they're covered at the DebtorService layer instead — see
apps.pos.test_module_audit_fixes for the same convention.
"""

from datetime import date
from decimal import Decimal

from apps.debtors.models import Debtopen, Debtor, DebtorTransaction
from apps.debtors.services import DebtorService
from django.test import TestCase


class PostJournalAgePeriodTests(TestCase):
    """
    Manual §2.2 "Debit/Credit Journal for Open Item Debtors": "The total
    value of the journal may only be allocated to ONE ageing period."
    """

    def setUp(self):
        self.open_item_debtor = Debtor.objects.create(
            dno=70001, dname="Open Item Journal Debtor", acctype="O"
        )
        self.bbf_debtor = Debtor.objects.create(
            dno=70002, dname="BBF Journal Debtor", acctype=""
        )

    def test_debit_journal_creates_debtopen_row_in_chosen_period(self):
        DebtorService.post_journal(
            debtor=self.open_item_debtor,
            journal_type="JD",
            amount=Decimal("150.00"),
            custref="TestJrnl",
            age_period="2",
        )
        open_items = Debtopen.objects.filter(dno=self.open_item_debtor)
        self.assertEqual(open_items.count(), 1)
        item = open_items.first()
        self.assertEqual(item.ageflag, "2")
        self.assertEqual(item.type, "JD")
        self.assertEqual(item.total, Decimal("150.00"))
        self.assertEqual(item.balancedue, Decimal("150.00"))

    def test_credit_journal_defaults_to_current_period(self):
        DebtorService.post_journal(
            debtor=self.open_item_debtor,
            journal_type="JC",
            amount=Decimal("50.00"),
            custref="TestCrJrnl",
        )
        item = Debtopen.objects.get(dno=self.open_item_debtor)
        self.assertEqual(item.ageflag, "0")
        self.assertEqual(item.type, "JC")

    def test_invalid_age_period_rejected(self):
        with self.assertRaises(ValueError):
            DebtorService.post_journal(
                debtor=self.open_item_debtor,
                journal_type="JD",
                amount=Decimal("10.00"),
                custref="BadPeriod",
                age_period="9",
            )
        self.assertFalse(Debtopen.objects.filter(dno=self.open_item_debtor).exists())

    def test_bbf_debtor_journal_creates_no_debtopen_row(self):
        """
        BBF accounts track balance purely via the aging buckets, never via
        Debtopen — age_period is meaningless for them and should not create
        a row regardless of what's passed.
        """
        DebtorService.post_journal(
            debtor=self.bbf_debtor,
            journal_type="JD",
            amount=Decimal("75.00"),
            custref="BBFJrnl",
            age_period="3",
        )
        self.assertFalse(Debtopen.objects.filter(dno=self.bbf_debtor).exists())
        self.bbf_debtor.refresh_from_db()
        self.assertEqual(self.bbf_debtor.dcrnt, Decimal("75.00"))

    def test_journal_requires_reference(self):
        with self.assertRaises(ValueError):
            DebtorService.post_journal(
                debtor=self.open_item_debtor,
                journal_type="JD",
                amount=Decimal("10.00"),
                custref="   ",
            )


class ConvertAccountCategoryTests(TestCase):
    """
    Manual "Account Category Conversions": Open Item -> BBF clears all open
    item transactions; BBF -> Open Item takes on one Debtopen row per
    non-zero aged bucket.
    """

    def test_open_item_to_bbf_clears_debtopen(self):
        debtor = Debtor.objects.create(dno=70101, dname="Convert O to BBF", acctype="O")
        Debtopen.objects.create(
            dno=debtor,
            dtrano="000001",
            type="IN",
            date=date.today(),
            total=Decimal("200.00"),
            balancedue=Decimal("200.00"),
            ageflag="0",
            posted="Y",
        )
        Debtopen.objects.create(
            dno=debtor,
            dtrano="000002",
            type="IN",
            date=date.today(),
            total=Decimal("50.00"),
            balancedue=Decimal("50.00"),
            ageflag="1",
            posted="Y",
        )

        DebtorService.convert_account_category(debtor, "")

        debtor.refresh_from_db()
        self.assertEqual(debtor.acctype, "")
        self.assertFalse(Debtopen.objects.filter(dno=debtor).exists())

    def test_bbf_to_open_item_takes_on_nonzero_buckets(self):
        debtor = Debtor.objects.create(
            dno=70102,
            dname="Convert BBF to O",
            acctype="",
            dcrnt=Decimal("100.00"),
            d30=Decimal("0.00"),
            d60=Decimal("50.00"),
            d120=Decimal("25.00"),
            d150=Decimal("0.00"),
            d180=Decimal("10.00"),
        )

        DebtorService.convert_account_category(debtor, "O")

        debtor.refresh_from_db()
        self.assertEqual(debtor.acctype, "O")

        items = Debtopen.objects.filter(dno=debtor).order_by("dtrano")
        # d30 and d150 are zero, so only 4 buckets take on a row
        self.assertEqual(items.count(), 4)
        by_ageflag = {item.ageflag: item.balancedue for item in items}
        self.assertEqual(by_ageflag["0"], Decimal("100.00"))
        self.assertEqual(by_ageflag["2"], Decimal("50.00"))
        # d120 and d180 both collapse into ageflag "4" (120+ Days)
        self.assertEqual(
            sorted(item.balancedue for item in items if item.ageflag == "4"),
            [Decimal("10.00"), Decimal("25.00")],
        )
        # Every take-on row needs a unique journal number for this debtor.
        dtranos = [item.dtrano for item in items]
        self.assertEqual(len(dtranos), len(set(dtranos)))

    def test_converting_to_same_category_is_a_noop(self):
        debtor = Debtor.objects.create(
            dno=70103, dname="Same Category", acctype="O", dcrnt=Decimal("100.00")
        )
        Debtopen.objects.create(
            dno=debtor,
            dtrano="000001",
            type="IN",
            date=date.today(),
            total=Decimal("100.00"),
            balancedue=Decimal("100.00"),
            ageflag="0",
            posted="Y",
        )

        DebtorService.convert_account_category(debtor, "O")

        self.assertEqual(Debtopen.objects.filter(dno=debtor).count(), 1)


class GetDebtorStatementTests(TestCase):
    """
    DebtorService.get_debtor_statement previously filtered on
    dno/dtdate/dttot (not real DebtorTransaction field names) and could
    crash on `Decimal + None` when a debtor had no prior transactions.
    """

    def setUp(self):
        self.debtor = Debtor.objects.create(dno=70201, dname="Statement Debtor")

    def test_statement_splits_opening_and_period_transactions(self):
        DebtorService.post_debtran(
            debtor=self.debtor,
            dtype="IN",
            dttot=Decimal("100.00"),
            transaction_date=date(2026, 1, 15),
        )
        DebtorService.post_debtran(
            debtor=self.debtor,
            dtype="IN",
            dttot=Decimal("40.00"),
            transaction_date=date(2026, 2, 10),
        )

        statement = DebtorService.get_debtor_statement(
            self.debtor, start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)
        )

        self.assertEqual(statement["opening_balance"], Decimal("100.00"))
        self.assertEqual(statement["closing_balance"], Decimal("140.00"))
        self.assertEqual(
            list(statement["transactions"]),
            list(
                DebtorTransaction.objects.filter(
                    debtor=self.debtor, transaction_date=date(2026, 2, 10)
                )
            ),
        )

    def test_statement_with_no_transactions_does_not_crash(self):
        statement = DebtorService.get_debtor_statement(
            self.debtor, start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)
        )
        self.assertEqual(statement["opening_balance"], Decimal("0.00"))
        self.assertEqual(statement["closing_balance"], Decimal("0.00"))
        self.assertEqual(list(statement["transactions"]), [])
