"""
Targeted regression tests for the POS-module fixes from the Accpick
conformance audit: CashSale Subtotal Discount/Set Price parity, Cash Sale
-> Account Sale conversion, Quotation price_level enforcement, and the
DebtorService.post_debtran mechanism the Credit Note ledger-posting fix in
views.py relies on (the view itself needs full tenant/shop request context
that this test env doesn't have wired up, so that specific integration
point is verified by inspection + this lower-level mechanism check rather
than an end-to-end API test).
"""

from datetime import date, timedelta
from decimal import Decimal

from apps.debtors.models import Debtor
from apps.debtors.services import DebtorService
from apps.settings.models import SalesDepartment
from apps.stock_control.models import StockItem
from django.core.exceptions import ValidationError
from django.test import TestCase

from .exceptions import InvalidDocumentState
from .models import CashSale, CashSaleLine
from .serializers import QuotationCreateSerializer
from .services import CashSaleService


class CashSalePriceFacilityTests(TestCase):
    """CashSale.apply_subtotal_discount / apply_set_price parity with Invoice."""

    def setUp(self):
        self.department = SalesDepartment.objects.create(number=2, name="Parity Dept")
        self.stock_item = StockItem.objects.create(
            stock_code="PAR001",
            description="Parity Item",
            department=self.department,
            cost_price=Decimal("50.00"),
            maximum_discount_percent=Decimal("20.00"),
        )
        self.cash_sale = CashSale.objects.create(
            sale_number="CS-PARITY-0001",
            sale_date=date.today(),
            total_amount=Decimal("228.00"),
        )
        CashSaleLine.objects.create(
            cash_sale=self.cash_sale,
            line_number=1,
            stock_code="PAR001",
            description="Parity Item",
            quantity=Decimal("2.00"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("228.00"),
            vat_amount=Decimal("28.00"),
        )

    def test_apply_subtotal_discount_scales_unit_price(self):
        self.cash_sale.apply_subtotal_discount(Decimal("10"))
        line = self.cash_sale.lines.get(line_number=1)
        self.assertEqual(line.unit_price, Decimal("90.0000"))

    def test_apply_subtotal_discount_rejects_over_max_discount(self):
        with self.assertRaises(ValidationError):
            self.cash_sale.apply_subtotal_discount(Decimal("50"))

    def test_apply_set_price_rescales_to_target_total(self):
        self.cash_sale.apply_set_price(Decimal("456.00"))
        self.cash_sale.refresh_from_db()
        line = self.cash_sale.lines.get(line_number=1)
        # line_total is VAT-inclusive on CashSaleLine, so it should double
        # in step with the doubled target total.
        self.assertEqual(line.line_total, Decimal("456.00"))


class CashSaleToInvoiceConversionTests(TestCase):
    """CashSaleService.convert_cash_sale_to_invoice."""

    def setUp(self):
        self.department = SalesDepartment.objects.create(number=3, name="Conv Dept")
        self.stock_item = StockItem.objects.create(
            stock_code="CONV001",
            description="Convertible Item",
            department=self.department,
            cost_price=Decimal("40.00"),
        )
        self.debtor = Debtor.objects.create(dno=90001, dname="Convert Test Debtor")
        self.cash_sale = CashSale.objects.create(
            sale_number="CS-CONV-0001",
            sale_date=date.today(),
            customer_name="Walk-in",
            subtotal=Decimal("200.00"),
            vat_amount=Decimal("28.00"),
            total_amount=Decimal("228.00"),
        )
        CashSaleLine.objects.create(
            cash_sale=self.cash_sale,
            line_number=1,
            stock_code="CONV001",
            description="Convertible Item",
            quantity=Decimal("2.00"),
            unit_price=Decimal("100.00"),
            line_total=Decimal("228.00"),
            vat_amount=Decimal("28.00"),
        )

    def test_convert_creates_invoice_and_cancels_cash_sale(self):
        invoice = CashSaleService.convert_cash_sale_to_invoice(
            self.cash_sale, self.debtor
        )

        self.assertEqual(invoice.debtor_id, self.debtor.pk)
        self.assertEqual(invoice.total_amount, Decimal("228.00"))
        self.assertEqual(invoice.lines.count(), 1)

        line = invoice.lines.get(line_number=1)
        # CashSaleLine.line_total (228.00) is VAT-inclusive; InvoiceLine
        # stores the exclusive amount.
        self.assertEqual(line.line_total, Decimal("200.00"))

        self.cash_sale.refresh_from_db()
        self.assertTrue(self.cash_sale.is_cancelled)

    def test_convert_requires_debtor(self):
        with self.assertRaises(ValueError):
            CashSaleService.convert_cash_sale_to_invoice(self.cash_sale, None)

    def test_convert_rejects_already_posted_sale(self):
        self.cash_sale.is_posted = True
        self.cash_sale.save()
        with self.assertRaises(ValueError):
            CashSaleService.convert_cash_sale_to_invoice(self.cash_sale, self.debtor)


class QuotationPriceLevelEnforcementTests(TestCase):
    """QuotationLineCreateSerializer.validate now honors Quotation.price_level."""

    def setUp(self):
        self.department = SalesDepartment.objects.create(number=4, name="Price Dept")
        self.stock_item = StockItem.objects.create(
            stock_code="LVL001",
            description="Leveled Item",
            department=self.department,
            cost_price=Decimal("50.00"),
            selling_price_1=Decimal("100.00"),
            selling_price_2=Decimal("80.00"),
            maximum_discount_percent=Decimal("10.00"),
        )

    def _payload(self, price_level, unit_price):
        return {
            "quotation_number": f"QUO-TEST-{price_level}-{unit_price}",
            "quotation_date": date.today().isoformat(),
            "expiry_date": (date.today() + timedelta(days=30)).isoformat(),
            "customer_name": "Level Test Customer",
            "price_level": price_level,
            "lines": [
                {
                    "line_number": 1,
                    "stock_code": "LVL001",
                    "description": "Leveled Item",
                    "quantity": "1.00",
                    "unit_price": str(unit_price),
                    "tax_code": 1,
                }
            ],
        }

    def test_price_level_1_rejects_price_above_level_1_tolerance(self):
        # 150 is far above selling_price_1 (100) — should fail under level 1.
        serializer = QuotationCreateSerializer(data=self._payload(1, "150.00"))
        self.assertFalse(serializer.is_valid())

    def test_price_level_2_is_actually_used_for_validation(self):
        # Same unit_price validated against level 2 pricing context: still
        # priced far above selling_price_2 (80), should also fail — but the
        # point is level 2 was actually consulted (see below for the
        # positive case).
        serializer = QuotationCreateSerializer(data=self._payload(2, "150.00"))
        self.assertFalse(serializer.is_valid())

    def test_price_level_2_accepts_a_price_valid_at_that_level(self):
        # 80 matches selling_price_2 exactly — must pass when price_level=2
        # is actually threaded through instead of being hardcoded to 1.
        serializer = QuotationCreateSerializer(data=self._payload(2, "80.00"))
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_non_numeric_price_level_skips_enforcement_without_raising(self):
        serializer = QuotationCreateSerializer(data=self._payload("COST", "999.00"))
        self.assertTrue(serializer.is_valid(), serializer.errors)


class CreditNoteDebtorLedgerMechanismTests(TestCase):
    """
    Confirms the mechanism CreditNoteViewSet.post_credit's new debtor-ledger
    posting relies on: DebtorService.post_debtran(dtype="CN", ...) reduces
    the debtor's balance, and post_journal(journal_type="JD", ...) reverses
    it. The view itself is exercised through this exact call shape.
    """

    def setUp(self):
        self.debtor = Debtor.objects.create(
            dno=90002, dname="Credit Note Debtor", dcrnt=Decimal("500.00")
        )

    def test_post_debtran_cn_reduces_balance(self):
        DebtorService.post_debtran(
            debtor=self.debtor,
            dtype="CN",
            dttot=Decimal("100.00"),
            dtsub=Decimal("86.96"),
            dtgst=Decimal("13.04"),
            custref="CN-0001",
            transaction_date=date.today(),
            source_type="CREDIT_NOTE",
            source_reference="CN-0001",
        )
        self.debtor.refresh_from_db()
        self.assertEqual(self.debtor.dcrnt, Decimal("400.00"))

    def test_post_journal_jd_reverses_the_credit(self):
        DebtorService.post_debtran(
            debtor=self.debtor,
            dtype="CN",
            dttot=Decimal("100.00"),
            dtsub=Decimal("86.96"),
            dtgst=Decimal("13.04"),
            custref="CN-0002",
            transaction_date=date.today(),
            source_type="CREDIT_NOTE",
            source_reference="CN-0002",
        )
        DebtorService.post_journal(
            debtor=self.debtor,
            journal_type="JD",
            amount=Decimal("100.00"),
            custref="CANC-CN-0002"[:10],
        )
        self.debtor.refresh_from_db()
        self.assertEqual(self.debtor.dcrnt, Decimal("500.00"))


class OpenItemDebtorPostDebtranTests(TestCase):
    """
    post_debtran additionally creates a Debtopen row for Open Item accounts
    (acctype="O") — a second, separate type-choices list from
    DebtorTransaction's/DebtorAudit's that RCP (receipt) and INT (interest)
    fell outside of, the same bug class fixed for DebtorAudit above.
    """

    def setUp(self):
        self.debtor = Debtor.objects.create(
            dno=90003,
            dname="Open Item Debtor",
            acctype="O",
            dcrnt=Decimal("500.00"),
        )

    def test_post_debtran_rcp_creates_debtopen_row(self):
        from apps.debtors.models import Debtopen

        DebtorService.post_debtran(
            debtor=self.debtor,
            dtype="RCP",
            dttot=Decimal("100.00"),
            custref="RCT-0001",
            transaction_date=date.today(),
            source_type="POS",
            source_reference="RCT-0001",
        )
        self.assertTrue(Debtopen.objects.filter(dno=self.debtor, type="RCP").exists())

    def test_post_debtran_int_creates_debtopen_row(self):
        from apps.debtors.models import Debtopen

        DebtorService.post_debtran(
            debtor=self.debtor,
            dtype="INT",
            dttot=Decimal("15.00"),
            custref="INT-0001",
            transaction_date=date.today(),
            source_type="MANUAL",
            source_reference="INT-0001",
        )
        self.assertTrue(Debtopen.objects.filter(dno=self.debtor, type="INT").exists())
