"""
General Ledger tests.

TransactionTestCase (not TestCase) for anything that exercises
GLPostingService.post_batch, since it's wrapped in @transaction.atomic —
nested atomic blocks under TestCase's own wrapping transaction can mask
rollback bugs (see apps/gas/tests.py for the same reasoning).
"""

from decimal import Decimal

from django.test import TransactionTestCase

from .exceptions import GLPostingException
from .models import GLBatch, GLIntegrationLog, GLMast, GLParam, GLStJnl, GLTran
from .services import GLPostingService


def _make_account(accno, name, acc_type, drorcr, repline=1, balbfwd=Decimal("0.00")):
    return GLMast.objects.create(
        accno=accno,
        name=name,
        type=acc_type,
        drorcr=drorcr,
        repline=repline,
        balbfwd=balbfwd,
    )


class GLPostingServiceTestCase(TransactionTestCase):
    def setUp(self):
        GLParam.objects.get_or_create(
            pk=1, defaults=dict(curperiod=1, currentyr=2026, batchno=0)
        )
        self.bank = _make_account(1000, "Bank", "B", "D")
        self.sales = _make_account(4000, "Sales", "I", "C")
        self.expense = _make_account(5000, "Rent Expense", "I", "D")

    def test_post_entry_debit_normal_same_side_increases(self):
        """A debit posted to a debit-normal account increases its period balance."""
        GLPostingService.post_entry(
            debit_accno=1000,
            credit_accno=4000,
            amount=Decimal("100.00"),
            entry_date="2026-01-15",
            reference="TST1",
            details="Test sale",
        )
        self.bank.refresh_from_db()
        self.sales.refresh_from_db()
        self.assertEqual(self.bank.period1, Decimal("100.00"))
        # Sales is credit-normal; a credit leg increases it too.
        self.assertEqual(self.sales.period1, Decimal("100.00"))

    def test_post_entry_opposite_side_decreases(self):
        """A credit posted to a debit-normal account decreases its period balance."""
        GLPostingService.post_entry(
            debit_accno=5000,
            credit_accno=1000,
            amount=Decimal("40.00"),
            entry_date="2026-01-15",
            reference="TST2",
            details="Pay rent",
        )
        self.bank.refresh_from_db()
        self.expense.refresh_from_db()
        # Bank is debit-normal; the credit leg decreases it.
        self.assertEqual(self.bank.period1, Decimal("-40.00"))
        self.assertEqual(self.expense.period1, Decimal("40.00"))

    def test_post_batch_unbalanced_raises_and_writes_nothing(self):
        lines = [
            {"accno": 1000, "type": "D", "amount": Decimal("100.00")},
            {"accno": 4000, "type": "C", "amount": Decimal("90.00")},
        ]
        with self.assertRaises(GLPostingException):
            GLPostingService.post_batch(lines)

        self.assertEqual(GLTran.objects.count(), 0)
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.period1, Decimal("0.00"))

    def test_post_batch_balanced_multi_line(self):
        lines = [
            {"accno": 1000, "type": "D", "amount": Decimal("115.00")},
            {"accno": 4000, "type": "C", "amount": Decimal("100.00")},
            {"accno": 5000, "type": "C", "amount": Decimal("15.00")},
        ]
        batchno = GLPostingService.post_batch(lines)
        self.assertEqual(GLTran.objects.filter(batchno=batchno).count(), 3)
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.period1, Decimal("115.00"))

    def test_post_batch_requires_at_least_two_lines(self):
        with self.assertRaises(GLPostingException):
            GLPostingService.post_batch(
                [{"accno": 1000, "type": "D", "amount": Decimal("10.00")}]
            )

    def test_post_batch_unknown_account_raises(self):
        lines = [
            {"accno": 9999999, "type": "D", "amount": Decimal("10.00")},
            {"accno": 4000, "type": "C", "amount": Decimal("10.00")},
        ]
        with self.assertRaises(GLPostingException):
            GLPostingService.post_batch(lines)


class GLBatchPostingTestCase(TransactionTestCase):
    def setUp(self):
        GLParam.objects.get_or_create(
            pk=1, defaults=dict(curperiod=1, currentyr=2026, batchno=0)
        )
        self.bank = _make_account(1000, "Bank", "B", "D")
        self.sales = _make_account(4000, "Sales", "I", "C")

    def test_balanced_batch_posts_and_updates_balances(self):
        GLBatch.objects.create(
            accno=1000,
            batchno=55,
            capturedat="2026-01-10",
            date="2026-01-10",
            drorcr="D",
            amount=Decimal("50.00"),
            period=1,
        )
        GLBatch.objects.create(
            accno=4000,
            batchno=55,
            capturedat="2026-01-10",
            date="2026-01-10",
            drorcr="C",
            amount=Decimal("50.00"),
            period=1,
        )
        lines = [
            {"accno": r.accno, "type": r.drorcr, "amount": r.amount, "period": r.period}
            for r in GLBatch.objects.filter(batchno=55)
        ]
        GLPostingService.post_batch(lines)
        self.bank.refresh_from_db()
        self.assertEqual(self.bank.period1, Decimal("50.00"))

    def test_unbalanced_batch_lines_rejected_by_post_batch(self):
        GLBatch.objects.create(
            accno=1000,
            batchno=56,
            capturedat="2026-01-10",
            date="2026-01-10",
            drorcr="D",
            amount=Decimal("50.00"),
            period=1,
        )
        GLBatch.objects.create(
            accno=4000,
            batchno=56,
            capturedat="2026-01-10",
            date="2026-01-10",
            drorcr="C",
            amount=Decimal("30.00"),
            period=1,
        )
        lines = [
            {"accno": r.accno, "type": r.drorcr, "amount": r.amount, "period": r.period}
            for r in GLBatch.objects.filter(batchno=56)
        ]
        with self.assertRaises(GLPostingException):
            GLPostingService.post_batch(lines)


class StandingJournalPostDueLogicTestCase(TransactionTestCase):
    """
    Exercises the same math the post_due action applies, directly against
    GLStJnl rows, since the action itself requires an authenticated request
    context (covered at the view layer separately if/when API tests are
    added — this locks down the underlying timesbal/nextperiod arithmetic).
    """

    def setUp(self):
        GLParam.objects.get_or_create(
            pk=1, defaults=dict(curperiod=1, currentyr=2026, batchno=0)
        )
        self.rent = _make_account(5000, "Rent Expense", "I", "D")
        self.bank = _make_account(1000, "Bank", "B", "D")

    def test_timesbal_increments_and_nextperiod_wraps(self):
        GLStJnl.objects.create(
            accno=5000,
            details="Monthly rent",
            drorcr="D",
            amount=Decimal("100.00"),
            frequency=1,
            stperiod=1,
            times=12,
            timesbal=0,
            nextperiod=12,
            journalno=1,
        )
        GLStJnl.objects.create(
            accno=1000,
            details="Monthly rent",
            drorcr="C",
            amount=Decimal("100.00"),
            frequency=1,
            stperiod=1,
            times=12,
            timesbal=0,
            nextperiod=12,
            journalno=1,
        )
        rows = list(GLStJnl.objects.filter(journalno=1))
        lines = [{"accno": r.accno, "type": r.drorcr, "amount": r.amount} for r in rows]
        GLPostingService.post_batch(lines)
        for r in rows:
            r.timesbal += 1
            r.nextperiod = r.nextperiod % 12 + 1
            r.save(update_fields=["timesbal", "nextperiod"])

        row = GLStJnl.objects.get(accno=5000, journalno=1)
        self.assertEqual(row.timesbal, 1)
        self.assertEqual(row.nextperiod, 1)  # wraps 12 -> 1


class IntegrationLogIdempotencyTestCase(TransactionTestCase):
    def test_duplicate_source_record_rejected(self):
        GLIntegrationLog.objects.create(
            source_app="debtors",
            source_model="DebtorTransaction",
            source_pk=1,
            gl_batchno=1,
        )
        with self.assertRaises(Exception):
            GLIntegrationLog.objects.create(
                source_app="debtors",
                source_model="DebtorTransaction",
                source_pk=1,
                gl_batchno=2,
            )


class YearEndRolloverArithmeticTestCase(TransactionTestCase):
    """
    Locks down the year-end close math directly (same computation the
    year_end action performs) on a small synthetic chart of accounts, for
    both a profit and a loss scenario.
    """

    def setUp(self):
        GLParam.objects.get_or_create(
            pk=1,
            defaults=dict(curperiod=13, currentyr=2026, batchno=0, startper=1),
        )
        self.sales = _make_account(4000, "Sales", "I", "C")
        self.rent = _make_account(5000, "Rent Expense", "I", "D")
        self.retained_earnings = _make_account(3000, "Retained Earnings", "B", "C")
        param = GLParam.objects.get(pk=1)
        param.retained_earnings_accno = 3000
        param.save(update_fields=["retained_earnings_accno"])

    def _close_year(self):
        accounts = list(GLMast.objects.all())
        income_accounts = [a for a in accounts if a.type == "I"]
        closing_lines = []
        net_income = Decimal("0.00")
        for account in income_accounts:
            balance = sum(getattr(account, f"period{p}") for p in range(1, 14))
            if balance == 0:
                continue
            contribution = balance if account.drorcr == "C" else -balance
            net_income += contribution
            closing_lines.append(
                {
                    "accno": account.accno,
                    "type": "C" if account.drorcr == "D" else "D",
                    "amount": abs(balance),
                }
            )
        if closing_lines and net_income != 0:
            closing_lines.append(
                {
                    "accno": 3000,
                    "type": "C" if net_income > 0 else "D",
                    "amount": abs(net_income),
                }
            )
            GLPostingService.post_batch(closing_lines)
        return net_income

    def test_profit_scenario_closes_to_retained_earnings(self):
        self.sales.period1 = Decimal("1000.00")
        self.sales.save(update_fields=["period1"])
        self.rent.period1 = Decimal("300.00")
        self.rent.save(update_fields=["period1"])

        net_income = self._close_year()
        self.assertEqual(net_income, Decimal("700.00"))

        self.sales.refresh_from_db()
        self.rent.refresh_from_db()
        self.retained_earnings.refresh_from_db()
        # Closing entries land in whatever the current period is (13, per
        # setUp) — confirm the ledger fully offset each income account.
        self.assertEqual(
            sum(getattr(self.sales, f"period{p}") for p in range(1, 14)),
            Decimal("0.00"),
        )
        self.assertEqual(
            sum(getattr(self.rent, f"period{p}") for p in range(1, 14)),
            Decimal("0.00"),
        )
        self.assertEqual(self.retained_earnings.period13, Decimal("700.00"))

    def test_loss_scenario_closes_to_retained_earnings(self):
        self.sales.period1 = Decimal("300.00")
        self.sales.save(update_fields=["period1"])
        self.rent.period1 = Decimal("1000.00")
        self.rent.save(update_fields=["period1"])

        net_income = self._close_year()
        self.assertEqual(net_income, Decimal("-700.00"))

        self.retained_earnings.refresh_from_db()
        self.assertEqual(self.retained_earnings.period13, Decimal("-700.00"))
