"""
Rentals Application Tests.

Covers the 4 failure-mode gaps flagged by /plan-eng-review's Test Review
(insufficient stock, double-submit, no-matching-rental, double-return) plus
the happy paths for all 4 reconciliation states and the GL-posting-failure
full-rollback behavior from /plan-eng-review's Test Review Issue 1.
"""
from decimal import Decimal

from django.test import TransactionTestCase
from django.contrib.auth.models import Group

from shop_users.models import ShopUser
from apps.debtors.models import Debtor
from apps.settings.models import SalesDepartment
from apps.stock_control.models import StockItem
from apps.general_ledger.models import GLMast, GLParam, GLTran

from .exceptions import RentalLedgerException, RentalStateException, RentalStockException
from .models import RentalSettings, RentalTransaction
from .services import RentalService


class RentalServiceTestCase(TransactionTestCase):
    """
    TransactionTestCase (not TestCase) because RentalService methods wrap
    themselves in @transaction.atomic — nested atomic blocks under
    TestCase's own wrapping transaction can mask rollback bugs.
    """

    def setUp(self):
        self.user = ShopUser.objects.create_user(username='cashier1', password='testpass123')
        Group.objects.get_or_create(name='Cashier')[0].user_set.add(self.user)

        self.accountant = ShopUser.objects.create_user(username='accountant1', password='testpass123')
        Group.objects.get_or_create(name='Accountant')[0].user_set.add(self.accountant)

        self.debtor = Debtor.objects.create(dno=1, dname='Test Customer')

        department = SalesDepartment.objects.create(number=1, name='LPG Gas')
        self.stock_item = StockItem.objects.create(
            stock_code='CYL9KG', description='9kg LPG Cylinder', department=department,
            quantity_on_hand=Decimal('20'),
        )

        GLParam.objects.get_or_create(pk=1, defaults=dict(curperiod=1, currentyr=2026, batchno=0))

        self.deposits_held = GLMast.objects.create(
            accno=21500000, name='Deposits Held', type='B', drorcr='C', repline=1,
        )
        self.cash = GLMast.objects.create(
            accno=10000000, name='Cash', type='B', drorcr='D', repline=1,
        )
        self.writeoff_income = GLMast.objects.create(
            accno=41000000, name='Deposit Write-offs', type='I', drorcr='C', repline=1,
        )
        self.sales_revenue = GLMast.objects.create(
            accno=40000000, name='Sales Revenue', type='I', drorcr='C', repline=1,
        )
        self.vat_output = GLMast.objects.create(
            accno=22000000, name='VAT Output', type='B', drorcr='C', repline=1,
        )

        settings_row = RentalSettings.get_solo()
        settings_row.deposits_held_accno = self.deposits_held.accno
        settings_row.cash_accno = self.cash.accno
        settings_row.writeoff_income_accno = self.writeoff_income.accno
        settings_row.sales_revenue_accno = self.sales_revenue.accno
        settings_row.vat_output_accno = self.vat_output.accno
        settings_row.overdue_threshold_days = 90
        settings_row.save()

    def _checkout(self, quantity=Decimal('2'), deposit=Decimal('500.00')):
        return RentalService.checkout_cylinder(
            debtor=self.debtor, stock_item=self.stock_item, quantity=quantity,
            deposit_amount=deposit, user=self.user,
        )

    # --- Checkout happy path -------------------------------------------------

    def test_checkout_happy_path(self):
        rental = self._checkout()

        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal('18'))
        self.assertEqual(rental.status, RentalTransaction.STATUS_OPEN)
        self.assertIsNotNone(rental.gl_batchno_checkout)

        self.deposits_held.refresh_from_db()
        self.cash.refresh_from_db()
        self.assertEqual(self.deposits_held.period1, Decimal('500.00'))  # credit, credit-normal -> increases
        self.assertEqual(self.cash.period1, Decimal('500.00'))  # debit, debit-normal -> increases

        self.assertEqual(
            GLTran.objects.filter(batchno=rental.gl_batchno_checkout).count(), 2,
        )

    def test_checkout_sets_due_date_from_tenant_threshold(self):
        rental = self._checkout()
        self.assertEqual((rental.due_date - rental.checkout_date).days, 90)

    # --- Gap 1: insufficient stock -------------------------------------------

    def test_checkout_insufficient_stock_raises(self):
        with self.assertRaises(RentalStockException):
            self._checkout(quantity=Decimal('999'))

        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal('20'))  # unchanged
        self.assertEqual(RentalTransaction.objects.count(), 0)

    # --- Gap 2: double-submit -------------------------------------------------

    def test_checkout_double_submit_raises(self):
        self._checkout(quantity=Decimal('1'), deposit=Decimal('250.00'))
        with self.assertRaises(RentalStateException):
            self._checkout(quantity=Decimal('1'), deposit=Decimal('250.00'))

        # Only the first checkout's stock decrement and GL post happened.
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal('19'))
        self.assertEqual(RentalTransaction.objects.count(), 1)

    def test_checkout_different_deposit_not_treated_as_double_submit(self):
        self._checkout(quantity=Decimal('1'), deposit=Decimal('250.00'))
        # A second, genuinely different checkout for the same customer is allowed.
        self._checkout(quantity=Decimal('1'), deposit=Decimal('300.00'))
        self.assertEqual(RentalTransaction.objects.count(), 2)

    # --- Gap 3: no matching rental ---------------------------------------------

    def test_return_no_matching_rental_raises(self):
        with self.assertRaises(RentalStateException):
            RentalService.return_cylinder(
                rental_id=999999, reconciliation_state=RentalTransaction.RECON_REFUNDED,
                user=self.user,
            )

    # --- Gap 4: double-return ---------------------------------------------------

    def test_return_already_returned_raises(self):
        rental = self._checkout()
        RentalService.return_cylinder(
            rental_id=rental.pk, reconciliation_state=RentalTransaction.RECON_REFUNDED,
            user=self.user,
        )
        with self.assertRaises(RentalStateException):
            RentalService.return_cylinder(
                rental_id=rental.pk, reconciliation_state=RentalTransaction.RECON_REFUNDED,
                user=self.user,
            )

    # --- Reconciliation state happy paths ---------------------------------------

    def test_return_refunded(self):
        rental = self._checkout(quantity=Decimal('2'), deposit=Decimal('500.00'))
        returned = RentalService.return_cylinder(
            rental_id=rental.pk, reconciliation_state=RentalTransaction.RECON_REFUNDED,
            user=self.user,
        )

        self.assertEqual(returned.status, RentalTransaction.STATUS_RETURNED)
        self.assertTrue(returned.is_reconciled)
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal('20'))  # back to original

        self.cash.refresh_from_db()
        self.assertEqual(self.cash.period1, Decimal('0.00'))  # +500 checkout, -500 refund

    def test_return_written_off_does_not_restore_stock(self):
        rental = self._checkout(quantity=Decimal('2'), deposit=Decimal('500.00'))
        returned = RentalService.return_cylinder(
            rental_id=rental.pk, reconciliation_state=RentalTransaction.RECON_WRITTEN_OFF,
            user=self.accountant,
        )

        self.assertTrue(returned.is_reconciled)
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal('18'))  # cylinder never came back

        self.writeoff_income.refresh_from_db()
        self.assertEqual(self.writeoff_income.period1, Decimal('500.00'))

    def test_return_disputed_posts_no_gl_and_stays_unreconciled(self):
        rental = self._checkout()
        returned = RentalService.return_cylinder(
            rental_id=rental.pk, reconciliation_state=RentalTransaction.RECON_DISPUTED,
            user=self.accountant,
        )

        self.assertFalse(returned.is_reconciled)
        self.assertIsNone(returned.gl_batchno_return)
        self.deposits_held.refresh_from_db()
        self.assertEqual(self.deposits_held.period1, Decimal('500.00'))  # unchanged from checkout

    def test_return_billed_for_replacement_charges_vat_and_does_not_double_decrement_stock(self):
        rental = self._checkout(quantity=Decimal('1'), deposit=Decimal('228.00'))
        self.stock_item.refresh_from_db()
        after_checkout_qty = self.stock_item.quantity_on_hand  # already decremented once

        returned = RentalService.return_cylinder(
            rental_id=rental.pk, reconciliation_state=RentalTransaction.RECON_BILLED_FOR_REPLACEMENT,
            user=self.user, replacement_unit_price=Decimal('200.00'),  # -> 228.00 incl. 14% VAT
        )

        self.assertTrue(returned.is_reconciled)
        self.stock_item.refresh_from_db()
        self.assertEqual(
            self.stock_item.quantity_on_hand, after_checkout_qty,
            "billed_for_replacement must not decrement stock again — the cylinder "
            "already left inventory at original checkout",
        )

        self.sales_revenue.refresh_from_db()
        self.vat_output.refresh_from_db()
        self.assertEqual(self.sales_revenue.period1, Decimal('200.00'))
        self.assertEqual(self.vat_output.period1, Decimal('28.00'))

    def test_return_requires_replacement_price_for_billed_for_replacement(self):
        rental = self._checkout()
        with self.assertRaises(RentalStateException):
            RentalService.return_cylinder(
                rental_id=rental.pk,
                reconciliation_state=RentalTransaction.RECON_BILLED_FOR_REPLACEMENT,
                user=self.user,
            )

    # --- Full rollback on GL posting failure -------------------------------------

    def test_checkout_rolls_back_everything_if_gl_account_missing(self):
        settings_row = RentalSettings.get_solo()
        settings_row.cash_accno = 99999999  # does not exist in GLMast
        settings_row.save()

        with self.assertRaises(RentalLedgerException):
            self._checkout()

        self.stock_item.refresh_from_db()
        self.assertEqual(
            self.stock_item.quantity_on_hand, Decimal('20'),
            "stock decrement must roll back when the GL post fails",
        )
        self.assertEqual(
            RentalTransaction.objects.count(), 0,
            "the RentalTransaction row must roll back when the GL post fails",
        )

    # --- is_overdue -------------------------------------------------------------

    def test_is_overdue_false_when_within_threshold(self):
        rental = self._checkout()
        self.assertFalse(rental.is_overdue)

    def test_is_overdue_false_once_returned(self):
        rental = self._checkout()
        rental.due_date = rental.checkout_date  # force overdue if still open
        rental.save()
        returned = RentalService.return_cylinder(
            rental_id=rental.pk, reconciliation_state=RentalTransaction.RECON_REFUNDED,
            user=self.user,
        )
        self.assertFalse(returned.is_overdue)
