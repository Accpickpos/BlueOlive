"""
Targeted regression tests for the Creditors-module fixes from the
priority-gap audit (Creditors.pdf):

- RFC line-item save crash (signals.py referenced a non-existent
  RFC.total_vat field in update_fields — every RFC line-item save raised
  ValueError).
- Stock quantity is now updated on GRN receipt, Credit Note return, and
  RFC send/replace/cancel ("updates Stock... simultaneously").
- GRN cost price flows to the stock item, and update_selling_price_on_receipt
  triggers a markup-based selling price recompute.
- Expense accumulation (ExpenseCategoryMonthlyBalance, purchases_mtd/ytd)
  is now live from actual invoice/GRN posting, not just the DBF importer.
- Open Item journals are pinned to a single ageing period instead of aging
  dynamically off a due date.

View-level actions (post_grn's surcharge apportionment, RFC update_status)
need full tenant/shop request context this test env doesn't have wired up,
so those two are covered indirectly by exercising the underlying pieces
directly — see apps.debtors.test_module_audit_fixes for the same convention.
"""

from datetime import date
from decimal import Decimal

from apps.settings.models import ExpenseCategory, SalesDepartment, TaxCode
from apps.stock_control.models import StockItem, StockTransaction
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from .models import (
    RFC,
    Creditor,
    CreditorCreditNote,
    CreditorCreditNoteLineItem,
    CreditorInvoice,
    CreditorInvoiceLineItem,
    CreditorJournal,
    CreditorPayment,
    ExpenseCategoryMonthlyBalance,
    ExpenseCategoryTransaction,
    GoodsReceivedNote,
    GRNLineItem,
    RFCLineItem,
)
from .views import _apportion_grn_surcharge, _resolve_rfc_stock


def _make_creditor(update_selling_price=False, **overrides):
    defaults = {
        "supplier_number": "1001",
        "name": "Test Supplier",
        "account_category": "OI",
        "update_selling_price_on_receipt": update_selling_price,
    }
    defaults.update(overrides)
    return Creditor.objects.create(**defaults)


class CreditorsAuditFixesTestBase(TestCase):
    def setUp(self):
        self.department = SalesDepartment.objects.create(number=1, name="Groceries")
        self.tax_code = TaxCode.objects.create(code=1, description="15% VAT", rate=Decimal("15.00"))
        self.stock_item = StockItem.objects.create(
            stock_code="TEST001",
            description="Test Product",
            department=self.department,
            cost_price=Decimal("100.00"),
            quantity_on_hand=Decimal("50"),
            markup_1=Decimal("50.00"),
        )
        self.creditor = _make_creditor()


class GRNStockMovementTests(CreditorsAuditFixesTestBase):
    """Manual §Transactions "GRN": updates Stock Quantity, Cost & Supplier
    Balance simultaneously."""

    def test_grn_line_creation_increases_qoh(self):
        grn = GoodsReceivedNote.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 1, 15),
            supplier_invoice_number="INV-1",
        )
        GRNLineItem.objects.create(
            grn=grn,
            line_number=1,
            stock_item=self.stock_item,
            quantity_received=Decimal("10"),
            unit_cost=Decimal("120.00"),
            tax_code=self.tax_code,
        )
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("60"))
        self.assertTrue(
            StockTransaction.objects.filter(
                stock_item=self.stock_item, transaction_type="INCOMING"
            ).exists()
        )

    def test_grn_line_updates_cost_price(self):
        grn = GoodsReceivedNote.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 1, 15),
            supplier_invoice_number="INV-1",
        )
        GRNLineItem.objects.create(
            grn=grn,
            line_number=1,
            stock_item=self.stock_item,
            quantity_received=Decimal("10"),
            unit_cost=Decimal("150.00"),
            tax_code=self.tax_code,
        )
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.cost_price, Decimal("150.00"))

    def test_grn_line_applies_markup_when_supplier_flagged(self):
        creditor = _make_creditor(supplier_number="1002", update_selling_price=True)
        grn = GoodsReceivedNote.objects.create(
            creditor=creditor,
            transaction_date=date(2026, 1, 15),
            supplier_invoice_number="INV-2",
        )
        GRNLineItem.objects.create(
            grn=grn,
            line_number=1,
            stock_item=self.stock_item,
            quantity_received=Decimal("10"),
            unit_cost=Decimal("200.00"),
            tax_code=self.tax_code,
        )
        self.stock_item.refresh_from_db()
        # markup_1 = 50% -> selling_price_1 = 200 * 1.5 = 300
        self.assertEqual(self.stock_item.selling_price_1, Decimal("300.00"))

    def test_grn_line_does_not_apply_markup_when_not_flagged(self):
        grn = GoodsReceivedNote.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 1, 15),
            supplier_invoice_number="INV-3",
        )
        GRNLineItem.objects.create(
            grn=grn,
            line_number=1,
            stock_item=self.stock_item,
            quantity_received=Decimal("10"),
            unit_cost=Decimal("200.00"),
            tax_code=self.tax_code,
        )
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.selling_price_1, Decimal("0.00"))

    def test_grn_updates_purchases_mtd_ytd_exactly_once(self):
        grn = GoodsReceivedNote.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 1, 15),
            supplier_invoice_number="INV-4",
        )
        GRNLineItem.objects.create(
            grn=grn,
            line_number=1,
            stock_item=self.stock_item,
            quantity_received=Decimal("10"),
            unit_cost=Decimal("100.00"),
            tax_code=self.tax_code,
        )
        second_item = StockItem.objects.create(
            stock_code="TEST002",
            description="Second Product",
            department=self.department,
            cost_price=Decimal("50.00"),
            quantity_on_hand=Decimal("0"),
        )
        GRNLineItem.objects.create(
            grn=grn,
            line_number=2,
            stock_item=second_item,
            quantity_received=Decimal("5"),
            unit_cost=Decimal("50.00"),
            tax_code=self.tax_code,
        )
        self.creditor.refresh_from_db()
        grn.refresh_from_db()
        # Two lines both contributed to header resaves — purchases must equal
        # the FINAL total exactly once, not be inflated by intermediate fires.
        self.assertEqual(self.creditor.purchases_ytd, grn.total_amount)


class CreditNoteStockMovementTests(CreditorsAuditFixesTestBase):
    def test_credit_note_line_creation_decreases_qoh(self):
        cn = CreditorCreditNote.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 1, 15),
            supplier_credit_note_number="CN-1",
        )
        CreditorCreditNoteLineItem.objects.create(
            credit_note=cn,
            line_number=1,
            stock_item=self.stock_item,
            quantity_returned=Decimal("5"),
            unit_cost=Decimal("100.00"),
            tax_code=self.tax_code,
        )
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("45"))
        self.assertTrue(
            StockTransaction.objects.filter(
                stock_item=self.stock_item, transaction_type="RETURN"
            ).exists()
        )


class RFCStockMovementTests(CreditorsAuditFixesTestBase):
    """Manual: RFC crash fix + stock movement between normal stock and the
    RFC bucket."""

    def test_rfc_line_item_save_does_not_crash(self):
        rfc = RFC.objects.create(creditor=self.creditor, rfc_number="000001")
        # Previously raised ValueError: RFC has no field named "total_vat".
        line = RFCLineItem.objects.create(
            rfc=rfc,
            line_number=1,
            stock_item=self.stock_item,
            quantity_returned=Decimal("3"),
            tax_code=self.tax_code,
        )
        rfc.refresh_from_db()
        self.assertGreater(rfc.total_value_inclusive, Decimal("0"))
        self.assertEqual(line.line_value_exclusive, Decimal("300.00"))

    def test_rfc_line_creation_decreases_qoh(self):
        rfc = RFC.objects.create(creditor=self.creditor, rfc_number="000002")
        RFCLineItem.objects.create(
            rfc=rfc,
            line_number=1,
            stock_item=self.stock_item,
            quantity_returned=Decimal("5"),
            tax_code=self.tax_code,
        )
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("45"))
        self.assertTrue(
            StockTransaction.objects.filter(
                stock_item=self.stock_item, transaction_type="RFC_IN"
            ).exists()
        )


class GRNSurchargeApportionmentTests(CreditorsAuditFixesTestBase):
    """Manual §Transactions "GRN": surcharge must be apportioned across
    lines by value and folded into landed stock cost."""

    def test_surcharge_apportioned_by_line_value_share(self):
        second_item = StockItem.objects.create(
            stock_code="TEST003",
            description="Third Product",
            department=self.department,
            cost_price=Decimal("0.00"),
            quantity_on_hand=Decimal("0"),
        )
        grn = GoodsReceivedNote.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 1, 15),
            supplier_invoice_number="INV-SUR",
            surcharge_amount=Decimal("30.00"),
        )
        # Line 1: 100.00 (25% of 400 subtotal) -> surcharge share 7.50 / 10 qty = 0.75/unit
        GRNLineItem.objects.create(
            grn=grn,
            line_number=1,
            stock_item=self.stock_item,
            quantity_received=Decimal("10"),
            unit_cost=Decimal("10.00"),
            tax_code=self.tax_code,
        )
        # Line 2: 300.00 (75% of 400 subtotal) -> surcharge share 22.50 / 10 qty = 2.25/unit
        GRNLineItem.objects.create(
            grn=grn,
            line_number=2,
            stock_item=second_item,
            quantity_received=Decimal("10"),
            unit_cost=Decimal("30.00"),
            tax_code=self.tax_code,
        )
        grn.refresh_from_db()
        _apportion_grn_surcharge(grn)

        self.stock_item.refresh_from_db()
        second_item.refresh_from_db()
        self.assertEqual(self.stock_item.cost_price, Decimal("10.75"))
        self.assertEqual(second_item.cost_price, Decimal("32.25"))


class RFCResolutionStockTests(CreditorsAuditFixesTestBase):
    """RFC resolution-side stock movement (RE=replaced, CA=cancelled)."""

    def test_rfc_replaced_brings_stock_back_in(self):
        rfc = RFC.objects.create(creditor=self.creditor, rfc_number="000003")
        line = RFCLineItem.objects.create(
            rfc=rfc,
            line_number=1,
            stock_item=self.stock_item,
            quantity_returned=Decimal("5"),
            quantity_credited=Decimal("5"),
            tax_code=self.tax_code,
        )
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("45"))  # left on RFC send

        _resolve_rfc_stock(rfc, "RE")
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("50"))  # replacement received

    def test_rfc_cancelled_reverses_original_movement(self):
        rfc = RFC.objects.create(creditor=self.creditor, rfc_number="000004")
        RFCLineItem.objects.create(
            rfc=rfc,
            line_number=1,
            stock_item=self.stock_item,
            quantity_returned=Decimal("5"),
            tax_code=self.tax_code,
        )
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("45"))

        _resolve_rfc_stock(rfc, "CA")
        self.stock_item.refresh_from_db()
        self.assertEqual(self.stock_item.quantity_on_hand, Decimal("50"))


class JournalAgePeriodTests(CreditorsAuditFixesTestBase):
    """Open Item journals must be pinned to a single ageing period rather
    than aging dynamically from a due date."""

    def test_journal_pins_open_item_to_chosen_bucket(self):
        journal = CreditorJournal.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 1, 15),
            journal_type="DJ",
            journal_amount=Decimal("500.00"),
            age_period="3",  # 90 days
        )
        open_item = self.creditor.open_items.get(journal=journal)
        self.assertEqual(open_item.ageing_flag, "3")
        self.assertIsNone(open_item.due_date)

        self.creditor.recalculate_aged_balances()
        self.creditor.refresh_from_db()
        self.assertEqual(self.creditor.balance_90_days, Decimal("500.00"))
        self.assertEqual(self.creditor.balance_current, Decimal("0.00"))

    def test_journal_defaults_to_current_period(self):
        journal = CreditorJournal.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 1, 15),
            journal_type="CJ",
            journal_amount=Decimal("100.00"),
        )
        open_item = self.creditor.open_items.get(journal=journal)
        self.assertEqual(open_item.ageing_flag, "0")


class ExpenseAccumulationTests(CreditorsAuditFixesTestBase):
    """ExpenseCategoryMonthlyBalance and creditor purchases must accumulate
    from real invoice posting, not just the DBF importer."""

    def setUp(self):
        super().setUp()
        self.expense_category = ExpenseCategory.objects.create(
            number=1, name="Electricity", category_type="CREDITORS"
        )

    def test_invoice_line_creates_expense_transaction_and_monthly_balance(self):
        invoice = CreditorInvoice.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 3, 10),
            supplier_invoice_number="EXP-1",
        )
        CreditorInvoiceLineItem.objects.create(
            invoice=invoice,
            line_number=1,
            expense_category=self.expense_category,
            amount=Decimal("1000.00"),
            tax_code=self.tax_code,
        )

        self.assertTrue(
            ExpenseCategoryTransaction.objects.filter(
                expense_category=self.expense_category, creditor=self.creditor
            ).exists()
        )
        balance = ExpenseCategoryMonthlyBalance.objects.get(
            expense_category=self.expense_category, year=2026
        )
        self.assertEqual(balance.exp_month_3, Decimal("1000.00"))
        self.assertEqual(balance.expense_mtd, Decimal("1000.00"))


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class ReportsEnquiriesSmokeTests(CreditorsAuditFixesTestBase):
    """
    Every one of these routes previously 404'd (unregistered). Exercises
    each through the actual DRF request/response cycle — not just direct
    Python calls — since query-shape bugs (e.g. the Meta.ordering-leaking-
    into-GROUP-BY pattern found elsewhere in this codebase) only surface
    once the ORM actually executes the query. CACHES is overridden to
    locmem because DRF's request throttling reads through the configured
    cache backend, which in this project's local .env is real Redis — not
    available/relevant in a unit test.
    """

    def setUp(self):
        super().setUp()
        User = get_user_model()
        # ShopUser.save() requires tenant context unless is_superuser=True —
        # these are read-only reporting endpoints, no tenant-scoped
        # permission behavior under test, so a superuser sidesteps that
        # requirement cleanly.
        self.user = User.objects.create_user(
            username="reportuser", password="testpass123", is_superuser=True  # nosec B106
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.expense_category = ExpenseCategory.objects.create(
            number=2, name="Rent", category_type="CREDITORS"
        )

        grn = GoodsReceivedNote.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 3, 5),
            supplier_invoice_number="SMOKE-GRN",
        )
        GRNLineItem.objects.create(
            grn=grn, line_number=1, stock_item=self.stock_item,
            quantity_received=Decimal("2"), unit_cost=Decimal("50.00"),
            tax_code=self.tax_code,
        )

        invoice = CreditorInvoice.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 3, 5),
            supplier_invoice_number="SMOKE-INV",
        )
        CreditorInvoiceLineItem.objects.create(
            invoice=invoice, line_number=1,
            expense_category=self.expense_category,
            amount=Decimal("200.00"), tax_code=self.tax_code,
        )

        cn = CreditorCreditNote.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 3, 6),
            supplier_credit_note_number="SMOKE-CN",
        )
        CreditorCreditNoteLineItem.objects.create(
            credit_note=cn, line_number=1, stock_item=self.stock_item,
            quantity_returned=Decimal("1"), unit_cost=Decimal("50.00"),
            tax_code=self.tax_code,
        )

        payment = CreditorPayment.objects.create(
            creditor=self.creditor,
            transaction_date=date(2026, 3, 7),
            amount_due=Decimal("100.00"), amount_paid=Decimal("100.00"),
        )
        from .models import CreditorOpenItem, OpenItemAllocation

        open_item = CreditorOpenItem.objects.filter(
            creditor=self.creditor, grn__isnull=False, balance_due__gt=0
        ).first()
        if open_item:
            OpenItemAllocation.objects.create(
                payment=payment, open_item=open_item,
                amount_paid=open_item.balance_due, settlement_discount=Decimal("0"),
            )

        CreditorJournal.objects.create(
            creditor=self.creditor, transaction_date=date(2026, 3, 8),
            journal_type="DJ", journal_amount=Decimal("25.00"),
        )

        rfc = RFC.objects.create(creditor=self.creditor, rfc_number="900001")
        RFCLineItem.objects.create(
            rfc=rfc, line_number=1, stock_item=self.stock_item,
            quantity_returned=Decimal("1"), tax_code=self.tax_code,
        )

    def _get(self, path, **params):
        response = self.client.get(f"/api/creditors/{path}", params)
        self.assertEqual(
            response.status_code, 200, f"{path} -> {response.status_code}: {response.content[:500]}"
        )
        return response.json()

    def test_account_details_report(self):
        self._get("reports/account_details/", include_banking="true")

    def test_age_analysis_report(self):
        self._get("reports/age_analysis/", include_zero="true", print_last_paid="true", print_banking="true")

    def test_remittance_advices_report(self):
        self._get("reports/remittance_advices/", include_zero="true")

    def test_transactions_report(self):
        data = self._get("reports/transactions/", start_date="2026-01-01", end_date="2026-12-31")
        self.assertGreaterEqual(len(data["transactions"]), 4)

    def test_expense_tax_report_monthly_and_ytd(self):
        self._get("reports/expense_tax/", report_type="monthly_tax", report_date="2026-03-15")
        self._get("reports/expense_tax/", report_type="ytd", report_date="2026-03-15")

    def test_payouts_report(self):
        self._get("reports/payouts/", start_date="2026-01-01", end_date="2026-12-31")

    def test_transaction_scroll_enquiry_both_modes(self):
        scroll = self._get(
            "enquiries/transaction_scroll/",
            start_date="2026-01-01", end_date="2026-12-31", enquiry_type="scroll",
        )
        self.assertGreaterEqual(scroll["grand_total"]["count"], 4)
        totals = self._get(
            "enquiries/transaction_scroll/",
            start_date="2026-01-01", end_date="2026-12-31", enquiry_type="totals",
        )
        self.assertIn("totals", totals)

    def test_expenditure_totals_enquiry(self):
        data = self._get("enquiries/expenditure_totals/", year=2026, month=3)
        self.assertEqual(float(data["expenditure"]["total_exclusive"]), 200.0)

    def test_expense_category_totals_enquiry(self):
        self._get("enquiries/expense_category_totals/", year=2026, month=3)

    def test_expense_category_details_enquiry(self):
        data = self._get(
            "enquiries/expense_category_details/",
            category_id=self.expense_category.id, year=2026, month=3,
        )
        self.assertEqual(len(data["details"]), 1)

    def test_monthly_expense_details_enquiry(self):
        data = self._get(
            "enquiries/monthly_expense_details/",
            category_id=self.expense_category.id, year=2026,
        )
        self.assertEqual(len(data["monthly_data"]), 12)

    def test_purchase_history_enquiry(self):
        data = self._get("enquiries/purchase_history/", year=2026, sort_by="total_purchases")
        self.assertEqual(data["supplier_count"], 1)

    def test_individual_account_enquiry(self):
        data = self._get("enquiries/individual_account/", supplier_id=self.creditor.id)
        self.assertEqual(data["supplier"]["account_number"], "1001")
        self.assertGreaterEqual(len(data["recent_transactions"]), 4)

    def test_expense_categories_list(self):
        data = self._get("expense-categories/")
        self.assertIn("results", data)
        self.assertTrue(any(r["category_name"] == "Rent" for r in data["results"]))
