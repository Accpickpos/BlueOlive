"""
Point of Sale services.
Business logic for POS operations based on PointOfSale.pdf
"""

import logging
from datetime import date
from decimal import Decimal

from apps.debtors.models import Debtor
from apps.stock_control.models import StockItem, StockTransaction
from django.db import transaction
from django.db.models import F, Q, Sum
from django.utils import timezone

from .calculation_service import CalculationService
from .exceptions import InsufficientStock, InvalidDocumentState, POSValidationException
from .models import (
    CashControl,
    CashSale,
    CashSaleLine,
    Invoice,
    InvoiceLine,
    JobCard,
    JobCardLine,
    Laybye,
    LaybyeLine,
    LaybyePayment,
    Quotation,
    QuotationLine,
    Repair,
    Tender,
)
from .price_validation_service import PriceValidationService

logger = logging.getLogger(__name__)


class CashControlService:
    """
    Shared helper for updating the daily CashControl totals for a cashier.
    CashSaleService.update_cash_control() handles cash sales directly; every
    other till-affecting transaction (returns, receipts, credits, payouts,
    cashed cheques, laybyes) should post through here so the till reconciles.
    """

    @staticmethod
    def _get_or_create(control_date, cashier, station_number=1):
        control, _ = CashControl.objects.get_or_create(
            control_date=control_date, cashier=cashier, station_number=station_number
        )
        return control

    @staticmethod
    def record_cash_return(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(
            control_date, cashier, station_number
        )
        control.cash_refunds_count += 1
        control.cash_refunds_total += amount
        control.cash_refunds += amount
        control.save()
        return control

    @staticmethod
    def record_receipt(
        control_date, cashier, station_number, amount, tender_type="CASH"
    ):
        control = CashControlService._get_or_create(
            control_date, cashier, station_number
        )
        control.receipts_count += 1
        control.receipts_total += amount
        if tender_type == "CASH":
            control.cash_takings += amount
        elif tender_type == "CHEQUE":
            control.cheque_takings += amount
        elif tender_type == "SPEEDPOINT":
            control.speedpoint_takings += amount
        control.save()
        return control

    @staticmethod
    def record_credit_note(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(
            control_date, cashier, station_number
        )
        control.credits_count += 1
        control.credits_total += amount
        control.save()
        return control

    @staticmethod
    def record_payout(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(
            control_date, cashier, station_number
        )
        control.payouts_count += 1
        control.payouts_total += amount
        control.save()
        return control

    @staticmethod
    def record_cashed_cheque(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(
            control_date, cashier, station_number
        )
        control.cashed_cheques_count += 1
        control.cashed_cheques_total += amount
        control.save()
        return control

    @staticmethod
    def record_new_laybye(control_date, cashier, station_number, deposit_amount):
        control = CashControlService._get_or_create(
            control_date, cashier, station_number
        )
        control.new_laybyes_count += 1
        control.new_laybyes_total += deposit_amount
        control.cash_takings += deposit_amount
        control.save()
        return control

    @staticmethod
    def record_laybye_receipt(control_date, cashier, station_number, amount):
        control = CashControlService._get_or_create(
            control_date, cashier, station_number
        )
        control.laybye_receipts_count += 1
        control.laybye_receipts_total += amount
        control.cash_takings += amount
        control.save()
        return control

    @staticmethod
    def record_laybye_cancel(control_date, cashier, station_number, refund_amount):
        control = CashControlService._get_or_create(
            control_date, cashier, station_number
        )
        control.cancelled_laybyes_count += 1
        control.cancelled_laybyes_total += refund_amount
        control.save()
        return control

    # ------------------------------------------------------------------
    # Reversal helpers — undo exactly what the matching record_*() call
    # above added, for the generic transaction reverse/void gaps (Credit
    # Note, Cash Return, Receipt on Account, Cash A Cheque, and Cash Sale's
    # own cancel_cash_sale, which previously reversed stock but never the
    # till). Each is a no-op if no CashControl row exists for that
    # date/cashier/station (nothing was ever recorded to undo).
    # ------------------------------------------------------------------

    @staticmethod
    def _get_existing(control_date, cashier, station_number):
        return CashControl.objects.filter(
            control_date=control_date, cashier=cashier, station_number=station_number
        ).first()

    @staticmethod
    def reverse_cash_sale(cash_sale):
        control = CashControlService._get_existing(
            cash_sale.sale_date, cash_sale.cashier, cash_sale.station_number
        )
        if not control:
            return None
        control.cash_sales_count = max(0, control.cash_sales_count - 1)
        control.cash_sales_total -= cash_sale.total_amount
        for tender in cash_sale.tenders.all():
            if tender.tender_type == "CASH":
                control.cash_takings -= tender.amount
            elif tender.tender_type == "CHEQUE":
                control.cheque_takings -= tender.amount
            elif tender.tender_type == "VOUCHER":
                control.voucher_takings -= tender.amount
            elif tender.tender_type == "SPEEDPOINT":
                control.speedpoint_takings -= tender.amount
        control.save()
        return control

    @staticmethod
    def reverse_receipt(
        control_date, cashier, station_number, amount, tender_type="CASH"
    ):
        control = CashControlService._get_existing(
            control_date, cashier, station_number
        )
        if not control:
            return None
        control.receipts_count = max(0, control.receipts_count - 1)
        control.receipts_total -= amount
        if tender_type == "CASH":
            control.cash_takings -= amount
        elif tender_type == "CHEQUE":
            control.cheque_takings -= amount
        elif tender_type == "SPEEDPOINT":
            control.speedpoint_takings -= amount
        control.save()
        return control

    @staticmethod
    def reverse_credit_note(control_date, cashier, station_number, amount):
        control = CashControlService._get_existing(
            control_date, cashier, station_number
        )
        if not control:
            return None
        control.credits_count = max(0, control.credits_count - 1)
        control.credits_total -= amount
        control.save()
        return control

    @staticmethod
    def reverse_cash_return(control_date, cashier, station_number, amount):
        control = CashControlService._get_existing(
            control_date, cashier, station_number
        )
        if not control:
            return None
        control.cash_refunds_count = max(0, control.cash_refunds_count - 1)
        control.cash_refunds_total -= amount
        control.cash_refunds -= amount
        control.save()
        return control

    @staticmethod
    def reverse_cashed_cheque(control_date, cashier, station_number, amount):
        control = CashControlService._get_existing(
            control_date, cashier, station_number
        )
        if not control:
            return None
        control.cashed_cheques_count = max(0, control.cashed_cheques_count - 1)
        control.cashed_cheques_total -= amount
        control.save()
        return control


class CashSaleService:
    """Service class for cash sale operations."""

    @staticmethod
    @transaction.atomic
    def post_cash_sale(cash_sale):
        """
        Post a cash sale - update stock and create movements.

        Args:
            cash_sale: CashSale instance

        Returns:
            CashSale: Updated cash sale

        Raises:
            InvalidDocumentState: If sale is already posted or cancelled
            InsufficientStock: If stock is insufficient
        """
        if cash_sale.is_posted:
            raise InvalidDocumentState(
                "Cash Sale", cash_sale.sale_number, "POSTED", "post"
            )

        if cash_sale.is_cancelled:
            raise InvalidDocumentState(
                "Cash Sale", cash_sale.sale_number, "CANCELLED", "post"
            )

        # Update stock for each line
        for line in cash_sale.lines.all():
            if line.stock_code:
                try:
                    stock_item = StockItem.objects.get(stock_code=line.stock_code)

                    # Check stock availability — manual §3.1 [311.htm]:
                    # "If No is selected [Allow Negative Quantities],
                    # Accpick will not allow a stock item with zero
                    # quantity on hand to be processed at Point of Sale."
                    # Previously this block ran unconditionally regardless
                    # of the per-item flag.
                    if (
                        not stock_item.allow_negative_quantities
                        and stock_item.quantity_on_hand < line.quantity
                    ):
                        raise InsufficientStock(
                            stock_code=line.stock_code,
                            required=float(line.quantity),
                            available=float(stock_item.quantity_on_hand),
                        )

                    # Update quantity on hand
                    stock_item.quantity_on_hand -= line.quantity

                    # Update sales statistics
                    stock_item.sales_mtd_quantity += line.quantity
                    stock_item.sales_mtd_value += line.line_total
                    stock_item.sales_ytd_quantity += line.quantity
                    stock_item.sales_ytd_value += line.line_total
                    stock_item.last_sale_date = cash_sale.sale_date
                    stock_item.save()

                    # Create stock movement. transaction_number is an
                    # IntegerField (legacy TRANO) — sale_number is a string
                    # like "CS-A1B2C3D4" and doesn't fit it; use comments
                    # instead so this doesn't raise on every posted sale.
                    StockTransaction.objects.create(
                        stock_item=stock_item,
                        transaction_type="SALE",
                        transaction_date=cash_sale.sale_date,
                        comments=cash_sale.sale_number[:30],
                        quantity_out=line.quantity,
                        quantity_balance=stock_item.quantity_on_hand,
                        unit_cost=line.cost_price,
                        unit_price=line.unit_price,
                        station_number=cash_sale.station_number,
                    )

                    logger.info(
                        f"Posted cash sale {cash_sale.sale_number}: "
                        f"stock {line.stock_code} reduced by {line.quantity}"
                    )

                except StockItem.DoesNotExist:
                    logger.warning(
                        f"Stock item {line.stock_code} not found for sale {cash_sale.sale_number}"
                    )
                    # Non-stock item - continue without stock update

        # Mark as posted
        cash_sale.is_posted = True
        cash_sale.save()

        # Update cash control
        CashSaleService.update_cash_control(cash_sale)

        logger.info(f"Successfully posted cash sale {cash_sale.sale_number}")
        return cash_sale

    @staticmethod
    @transaction.atomic
    def cancel_cash_sale(cash_sale, reason=""):
        """
        Cancel a cash sale.

        Args:
            cash_sale: CashSale instance
            reason: Cancellation reason

        Returns:
            CashSale: Updated cash sale

        Raises:
            InvalidDocumentState: If already cancelled
        """
        if cash_sale.is_cancelled:
            raise InvalidDocumentState(
                "Cash Sale", cash_sale.sale_number, "CANCELLED", "cancel"
            )

        if cash_sale.is_posted:
            # Reverse stock movements
            for line in cash_sale.lines.all():
                if line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=line.stock_code)

                        # Reverse quantity
                        stock_item.quantity_on_hand += line.quantity
                        stock_item.save()

                        # Create reversing movement. transaction_number is an
                        # IntegerField and there's no separate `reference`
                        # field on this model — both the sale number and
                        # cancellation reason need to go in `comments`.
                        StockTransaction.objects.create(
                            stock_item=stock_item,
                            transaction_type="RETURN",
                            transaction_date=date.today(),
                            comments=f"CANC-{cash_sale.sale_number}"[:30],
                            quantity_in=line.quantity,
                            quantity_balance=stock_item.quantity_on_hand,
                            unit_cost=line.cost_price,
                            unit_price=line.unit_price,
                            station_number=cash_sale.station_number,
                        )

                        logger.info(
                            f"Reversed stock for cancelled sale {cash_sale.sale_number}: "
                            f"{line.stock_code} increased by {line.quantity}"
                        )
                    except StockItem.DoesNotExist:
                        logger.warning(
                            f"Stock item {line.stock_code} not found for reversal"
                        )

            # Also reverse the till totals update_cash_control() made when
            # this sale was posted — previously only stock was reversed,
            # leaving CashControl permanently overstated after a cancel.
            CashControlService.reverse_cash_sale(cash_sale)

        cash_sale.is_cancelled = True
        cash_sale.save()

        logger.info(f"Cancelled cash sale {cash_sale.sale_number}. Reason: {reason}")
        return cash_sale

    @staticmethod
    def update_cash_control(cash_sale):
        """Update daily cash control for cashier."""
        control, created = CashControl.objects.get_or_create(
            control_date=cash_sale.sale_date,
            cashier=cash_sale.cashier,
            station_number=cash_sale.station_number,
        )

        control.cash_sales_count += 1
        control.cash_sales_total += cash_sale.total_amount

        # Update tender-specific totals
        for tender in cash_sale.tenders.all():
            if tender.tender_type == "CASH":
                control.cash_takings += tender.amount
            elif tender.tender_type == "CHEQUE":
                control.cheque_takings += tender.amount
            elif tender.tender_type == "VOUCHER":
                control.voucher_takings += tender.amount
            elif tender.tender_type == "SPEEDPOINT":
                control.speedpoint_takings += tender.amount

        control.save()
        return control

    @staticmethod
    def get_daily_summary(control_date, cashier=None, station_number=None):
        """Get daily sales summary."""
        filters = Q(control_date=control_date)
        if cashier:
            filters &= Q(cashier=cashier)
        if station_number:
            filters &= Q(station_number=station_number)

        controls = CashControl.objects.filter(filters)

        summary = controls.aggregate(
            total_sales=Sum("cash_sales_total"),
            total_refunds=Sum("cash_refunds_total"),
            total_receipts=Sum("receipts_total"),
            total_payouts=Sum("payouts_total"),
            total_credits=Sum("credits_total"),
            total_cashed_cheques=Sum("cashed_cheques_total"),
            total_new_laybyes=Sum("new_laybyes_total"),
            total_laybye_receipts=Sum("laybye_receipts_total"),
            total_cancelled_laybyes=Sum("cancelled_laybyes_total"),
            cash_takings=Sum("cash_takings"),
            cheque_takings=Sum("cheque_takings"),
            speedpoint_takings=Sum("speedpoint_takings"),
        )

        zero = Decimal("0.00")
        return {
            "control_date": control_date,
            "total_sales": summary["total_sales"] or zero,
            "total_refunds": summary["total_refunds"] or zero,
            "total_receipts": summary["total_receipts"] or zero,
            "total_payouts": summary["total_payouts"] or zero,
            "total_credits": summary["total_credits"] or zero,
            "total_cashed_cheques": summary["total_cashed_cheques"] or zero,
            "total_new_laybyes": summary["total_new_laybyes"] or zero,
            "total_laybye_receipts": summary["total_laybye_receipts"] or zero,
            "total_cancelled_laybyes": summary["total_cancelled_laybyes"] or zero,
            "cash_expected": (
                (summary["total_sales"] or zero)
                + (summary["total_new_laybyes"] or zero)
                + (summary["total_laybye_receipts"] or zero)
                - (summary["total_refunds"] or zero)
                - (summary["total_payouts"] or zero)
                - (summary["total_cashed_cheques"] or zero)
            ),
            "cash_takings": summary["cash_takings"] or zero,
            "cheque_takings": summary["cheque_takings"] or zero,
            "speedpoint_takings": summary["speedpoint_takings"] or zero,
        }


class CreditNoteService:
    """Service class for credit note operations."""

    @staticmethod
    @transaction.atomic
    def cancel_credit_note(credit_note, reason=""):
        """
        Cancel a credit note — reverses exactly what post_credit did: the
        stock increment per line (a credit note returns stock, so cancelling
        removes it again) and the CashControl credits total.
        """
        if credit_note.is_cancelled:
            raise InvalidDocumentState(
                "Credit Note", credit_note.credit_number, "CANCELLED", "cancel"
            )

        if credit_note.is_posted:
            for line in credit_note.lines.all():
                if line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=line.stock_code)
                        stock_item.quantity_on_hand -= line.quantity
                        stock_item.save()
                        StockTransaction.objects.create(
                            stock_item=stock_item,
                            transaction_type="SALE",
                            transaction_date=date.today(),
                            comments=f"CANC-{credit_note.credit_number}"[:30],
                            quantity_out=line.quantity,
                            quantity_balance=stock_item.quantity_on_hand,
                            unit_price=line.unit_price,
                            station_number=credit_note.station_number,
                        )
                    except StockItem.DoesNotExist:
                        logger.warning(
                            f"Stock item {line.stock_code} not found for reversal"
                        )

            CashControlService.reverse_credit_note(
                credit_note.credit_date,
                credit_note.cashier,
                credit_note.station_number,
                credit_note.total_amount,
            )

        credit_note.is_cancelled = True
        credit_note.cancel_reason = reason
        credit_note.cancelled_at = timezone.now()
        credit_note.save()

        logger.info(
            f"Cancelled credit note {credit_note.credit_number}. Reason: {reason}"
        )
        return credit_note


class CashReturnService:
    """Service class for cash return operations."""

    @staticmethod
    @transaction.atomic
    def cancel_cash_return(cash_return, reason=""):
        """
        Cancel a cash return — reverses exactly what post_return did: the
        stock increment per line and the CashControl cash-refunds total.
        """
        if cash_return.is_cancelled:
            raise InvalidDocumentState(
                "Cash Return", cash_return.return_number, "CANCELLED", "cancel"
            )

        if cash_return.is_posted:
            for line in cash_return.lines.all():
                if line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=line.stock_code)
                        stock_item.quantity_on_hand -= line.quantity
                        stock_item.save()
                        StockTransaction.objects.create(
                            stock_item=stock_item,
                            transaction_type="SALE",
                            transaction_date=date.today(),
                            comments=f"CANC-{cash_return.return_number}"[:30],
                            quantity_out=line.quantity,
                            quantity_balance=stock_item.quantity_on_hand,
                            unit_price=line.unit_price,
                            station_number=cash_return.station_number,
                        )
                    except StockItem.DoesNotExist:
                        logger.warning(
                            f"Stock item {line.stock_code} not found for reversal"
                        )

            CashControlService.reverse_cash_return(
                cash_return.return_date,
                cash_return.cashier,
                cash_return.station_number,
                cash_return.total_amount,
            )

        cash_return.is_cancelled = True
        cash_return.cancel_reason = reason
        cash_return.cancelled_at = timezone.now()
        cash_return.save()

        logger.info(
            f"Cancelled cash return {cash_return.return_number}. Reason: {reason}"
        )
        return cash_return


class ReceiptOnAccountService:
    """Service class for receipt-on-account operations."""

    @staticmethod
    @transaction.atomic
    def cancel_receipt(receipt, reason=""):
        """
        Cancel a receipt on account — reverses the CashControl receipts
        total, and if the receipt was actually posted to the debtor's
        ledger (apps.debtors.DebtorService.post_receipt via
        ReceiptOnAccountViewSet.post_receipt), reverses that too with an
        equal-and-opposite journal debit rather than mutating history,
        matching DebtorService.post_journal's existing JD/JC pattern.
        """
        if receipt.is_cancelled:
            raise InvalidDocumentState(
                "Receipt", receipt.receipt_number, "CANCELLED", "cancel"
            )

        if receipt.is_posted:
            CashControlService.reverse_receipt(
                receipt.receipt_date,
                receipt.cashier,
                receipt.station_number,
                receipt.total_amount,
                receipt.tender_type,
            )

            if receipt.debtor_transaction_id:
                from apps.debtors.services import DebtorService

                try:
                    DebtorService.post_journal(
                        debtor=receipt.debtor_transaction.debtor,
                        journal_type="JD",
                        amount=receipt.total_amount,
                        custref=f"CANC-{receipt.receipt_number}"[:10],
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to reverse debtor ledger for cancelled receipt "
                        f"{receipt.receipt_number}: {e}"
                    )

        receipt.is_cancelled = True
        receipt.cancel_reason = reason
        receipt.cancelled_at = timezone.now()
        receipt.save()

        logger.info(f"Cancelled receipt {receipt.receipt_number}. Reason: {reason}")
        return receipt


class CashAChequeService:
    """Service class for cash-a-cheque operations."""

    @staticmethod
    @transaction.atomic
    def cancel_cash_a_cheque(cheque, reason=""):
        """Cancel a cash-a-cheque transaction — reverses the CashControl cashed-cheques total."""
        if cheque.is_cancelled:
            raise InvalidDocumentState(
                "Cash A Cheque", cheque.transaction_number, "CANCELLED", "cancel"
            )

        if cheque.is_processed:
            CashControlService.reverse_cashed_cheque(
                cheque.transaction_date,
                cheque.cashier,
                cheque.station_number,
                cheque.cash_paid,
            )

        cheque.is_cancelled = True
        cheque.cancel_reason = reason
        cheque.cancelled_at = timezone.now()
        cheque.save()

        logger.info(
            f"Cancelled cash-a-cheque {cheque.transaction_number}. Reason: {reason}"
        )
        return cheque


class LaybyeService:
    """Service class for laybye operations."""

    @staticmethod
    @transaction.atomic
    def create_laybye(laybye_data, lines_data):
        """
        Create a new laybye with lines.

        Args:
            laybye_data: Dictionary with laybye header data
            lines_data: List of line item dictionaries

        Returns:
            Laybye: Created laybye instance

        Raises:
            POSValidationException: If validation fails
        """
        # total_amount/balance_due have no default and aren't nullable —
        # seed placeholders now, the real values get computed from lines and
        # saved a few lines down. Without this the initial create() raises
        # an IntegrityError before a single line is even processed.
        laybye = Laybye.objects.create(
            **laybye_data,
            total_amount=Decimal("0.00"),
            balance_due=Decimal("0.00"),
        )

        total_amount = Decimal("0.00")

        for idx, line_data in enumerate(lines_data, start=1):
            line_data["line_number"] = idx

            # Validate price/discount against configured pricing before
            # committing the line — previously laybye lines had no price
            # validation at all, unlike CashSale/Invoice/Quotation lines.
            # A stock_code that isn't found is treated as a manual entry
            # and skipped, matching the serializer-level checks elsewhere.
            stock_code = line_data.get("stock_code")
            if stock_code and line_data.get("unit_price") is not None:
                try:
                    PriceValidationService.validate_line_item_price(
                        stock_code=stock_code,
                        quantity=line_data["quantity"],
                        unit_price=line_data["unit_price"],
                        discount_percent=line_data.get(
                            "discount_percentage", Decimal("0.00")
                        ),
                        price_level=1,
                        transaction_date=laybye_data.get("laybye_date") or date.today(),
                        enforce=True,
                    )
                except POSValidationException as e:
                    if "not found" in str(e):
                        pass
                    else:
                        raise POSValidationException(f"Line {idx}: {e}")

            # Calculate line totals using service
            try:
                line_calcs = CalculationService.calculate_line_totals(
                    quantity=line_data["quantity"],
                    unit_price=line_data["unit_price"],
                    discount_percentage=line_data.get(
                        "discount_percentage", Decimal("0.00")
                    ),
                    tax_code=line_data.get("tax_code", 1),
                )

                # line_total is excl-VAT here (LaybyeLine has its own separate
                # vat_amount field, same convention as InvoiceLine) — use
                # line_total_before_vat, not the VAT-inclusive line_total key.
                line_data["line_total"] = line_calcs["line_total_before_vat"]
                line_data["vat_amount"] = line_calcs["vat_amount"]

                line = LaybyeLine.objects.create(laybye=laybye, **line_data)
                total_amount += line_calcs[
                    "line_total"
                ]  # VAT-inclusive, correct for the laybye total

            except Exception as e:
                logger.error(f"Error creating laybye line {idx}: {str(e)}")
                raise POSValidationException(
                    f"Error creating laybye line {idx}: {str(e)}"
                )

            # Move sale-type lines into "laybye stock" — same LAYBYE_IN/OUT
            # transaction pair the model already defines but nothing posted
            # to. Goods leave general inventory now, not at final payment
            # (mirrors how rentals/PO receiving avoid double-counting stock).
            if line.transaction_type == "SP" and line.stock_code:
                LaybyeService._move_stock_for_line(line, direction="out")

        # Update laybye totals
        laybye.total_amount = total_amount
        laybye.balance_due = total_amount - laybye.deposit_amount
        laybye.amount_paid = laybye.deposit_amount
        laybye.save()

        logger.info(
            f"Created laybye {laybye.laybye_number} with {len(lines_data)} lines"
        )
        return laybye

    @staticmethod
    def _move_stock_for_line(line, direction):
        """
        Move one laybye sale-line's quantity between general inventory and
        "laybye stock". direction='out' takes it out of inventory (laybye
        created); direction='in' returns it (laybye cancelled).
        """
        try:
            stock_item = StockItem.objects.select_for_update().get(
                stock_code=line.stock_code
            )
        except StockItem.DoesNotExist:
            logger.warning(
                f"Stock item {line.stock_code} not found for laybye line — "
                f"skipping stock movement (non-stock item)"
            )
            return

        if direction == "out":
            if (
                not stock_item.allow_negative_quantities
                and stock_item.quantity_on_hand < line.quantity
            ):
                raise InsufficientStock(
                    stock_code=line.stock_code,
                    required=float(line.quantity),
                    available=float(stock_item.quantity_on_hand),
                )
            stock_item.quantity_on_hand -= line.quantity
            transaction_type = "LAYBYE_IN"  # into laybye stock == out of inventory
        else:
            stock_item.quantity_on_hand += line.quantity
            transaction_type = "LAYBYE_OUT"  # out of laybye stock == back to inventory

        stock_item.save()

        # transaction_number is an IntegerField (legacy TRANO) — laybye_number
        # is a string like "LAY-1234567890" and doesn't fit it; use comments.
        StockTransaction.objects.create(
            stock_item=stock_item,
            transaction_type=transaction_type,
            transaction_date=line.transaction_date,
            comments=line.laybye.laybye_number[:30],
            quantity_out=line.quantity if direction == "out" else Decimal("0"),
            quantity_in=line.quantity if direction == "in" else Decimal("0"),
            quantity_balance=stock_item.quantity_on_hand,
            unit_cost=line.cost_price,
            unit_price=line.unit_price,
            station_number=line.station_number,
        )

    @staticmethod
    @transaction.atomic
    def make_payment(laybye, amount, sales_area=None):
        """
        Make a payment on a laybye.

        Args:
            laybye: Laybye instance
            amount: Payment amount
            sales_area: Sales area (optional)

        Returns:
            LaybyePayment: Created payment record

        Raises:
            InvalidDocumentState: If laybye is not active
            POSValidationException: If payment amount is invalid
        """
        if laybye.status != "ACTIVE":
            raise InvalidDocumentState(
                "Laybye", laybye.laybye_number, laybye.status, "make_payment"
            )

        try:
            amount = Decimal(str(amount))
        except Exception:
            raise POSValidationException(f"Invalid payment amount: {amount}")

        if amount <= 0:
            raise POSValidationException("Payment amount must be positive")

        if amount > laybye.balance_due:
            raise POSValidationException(
                f"Payment amount {amount} exceeds balance due {laybye.balance_due}"
            )

        # Create payment record
        payment = LaybyePayment.objects.create(
            laybye=laybye,
            payment_date=date.today(),
            amount=amount,
            sales_area=sales_area,
        )

        # Update laybye
        laybye.amount_paid += amount
        laybye.balance_due -= amount

        invoice = None
        # Check if fully paid
        if laybye.balance_due <= 0:
            laybye.status = "COMPLETED"
            laybye.save()

            # Manual §"Laybye Stock": goods already left inventory at
            # creation, so completion auto-generates the invoice rather than
            # requiring a separate manual conversion step. If there's no
            # linked debtor account (manual/cash customer entry) or the
            # conversion fails for some other reason, leave the laybye
            # COMPLETED and let staff convert it by hand — the payment
            # itself must not be rolled back over this.
            if laybye.debtor_account_number:
                try:
                    debtor = Debtor.objects.get(dno=laybye.debtor_account_number)
                    invoice = QuotationService.convert_laybye_to_invoice(laybye, debtor)
                    logger.info(
                        f"Laybye {laybye.laybye_number} fully paid — "
                        f"auto-converted to invoice {invoice.invoice_number}"
                    )
                except Debtor.DoesNotExist:
                    logger.warning(
                        f"Laybye {laybye.laybye_number} fully paid but debtor account "
                        f"{laybye.debtor_account_number} not found — invoice not auto-generated"
                    )
                except Exception as e:
                    logger.error(
                        f"Laybye {laybye.laybye_number} fully paid but auto-invoice failed: {e}"
                    )
            else:
                logger.info(
                    f"Laybye {laybye.laybye_number} fully paid but has no linked debtor "
                    f"account — invoice not auto-generated"
                )
        else:
            laybye.save()

        logger.info(f"Payment of {amount} recorded on laybye {laybye.laybye_number}")
        return payment, invoice

    @staticmethod
    @transaction.atomic
    def cancel_laybye(laybye, retention_percentage=0):
        """
        Cancel a laybye and calculate refund.

        Args:
            laybye: Laybye instance
            retention_percentage: Percentage to retain (default 0%)

        Returns:
            Laybye: Updated laybye

        Raises:
            InvalidDocumentState: If already cancelled
            POSValidationException: If retention percentage is invalid
        """
        if laybye.status == "CANCELLED":
            raise InvalidDocumentState(
                "Laybye", laybye.laybye_number, "CANCELLED", "cancel"
            )

        if laybye.status == "CONVERTED_TO_INVOICE":
            raise InvalidDocumentState(
                "Laybye", laybye.laybye_number, "CONVERTED_TO_INVOICE", "cancel"
            )

        try:
            retention_percentage = Decimal(str(retention_percentage))
        except Exception:
            raise POSValidationException(
                f"Invalid retention percentage: {retention_percentage}"
            )

        if not (0 <= retention_percentage <= 100):
            raise POSValidationException(
                "Retention percentage must be between 0 and 100"
            )

        # Calculate refund using service
        retention_amount = laybye.amount_paid * (retention_percentage / 100)
        refund_amount = laybye.amount_paid - retention_amount

        laybye.status = "CANCELLED"
        laybye.retention_percentage = retention_percentage
        laybye.refund_amount = refund_amount
        laybye.save()

        # Return the goods from laybye stock back to general inventory.
        for line in laybye.lines.filter(transaction_type="SP"):
            if line.stock_code:
                LaybyeService._move_stock_for_line(line, direction="in")

        logger.info(f"Cancelled laybye {laybye.laybye_number}. Refund: {refund_amount}")
        return laybye

    @staticmethod
    def check_expired_laybyes():
        """Check for and mark expired laybyes."""
        today = date.today()
        expired = Laybye.objects.filter(status="ACTIVE", expiry_date__lt=today)

        count = expired.update(status="EXPIRED")
        return count


class QuotationService:
    """Service class for quotation operations."""

    # NOTE: the real quotation->invoice conversion is convert_quotation_to_invoice
    # below (used by the API). A dead stub convert_to_invoice() previously lived
    # here too — same method name, different signature, never called anywhere
    # — removed to eliminate the two-competing-implementations trap.

    @staticmethod
    @transaction.atomic
    def convert_to_job_card(quotation):
        """Convert quotation to job card."""
        if quotation.status == "JOB":
            raise ValueError("Quotation already converted to job card")

        # Create job card from quotation
        job_card = JobCard.objects.create(
            job_number=f"JOB-{quotation.quotation_number}",
            job_date=date.today(),
            customer_name=quotation.customer_name,
            address=quotation.address_line1,
            telephone=quotation.telephone,
            sales_area=quotation.sales_area,
        )

        # Copy lines
        for q_line in quotation.lines.all():
            JobCardLine.objects.create(
                job_card=job_card,
                line_number=q_line.line_number,
                stock_code=q_line.stock_code,
                description=q_line.description,
                quantity=q_line.quantity,
                unit_price=q_line.unit_price,
                discount_percentage=q_line.discount_percentage,
                tax_code=q_line.tax_code,
                line_total=q_line.line_total,
                vat_amount=q_line.vat_amount,
                cost_price=q_line.cost_price,
            )

        # Update quotation
        quotation.status = "JOB"
        quotation.save()

        return job_card

    @staticmethod
    @transaction.atomic
    def convert_job_card_to_invoice(job_card, debtor):
        """
        Convert job card to customer invoice.

        Args:
            job_card: JobCard instance to convert
            debtor: Debtor instance (customer)

        Returns:
            Invoice: Created invoice

        Raises:
            ValueError: If job card cannot be converted
        """
        if job_card.status == "CONVERTED_TO_INVOICE":
            raise ValueError("Job card already converted to invoice")

        if job_card.status == "CANCELLED":
            raise ValueError("Cannot convert cancelled job card to invoice")

        if not debtor:
            raise ValueError(
                "Debtor is required to create invoice. Please select a debtor."
            )

        # Generate invoice number (format: INV-YYYYMMDD-XXXXX)
        from django.utils import timezone

        today = timezone.now().date()
        invoice_count = Invoice.objects.filter(invoice_date=today).count() + 1
        invoice_number = (
            f"INV-{today.year}{today.month:02d}{today.day:02d}-{invoice_count:05d}"
        )

        # Handle sales_area - get the code string (not the ForeignKey object)
        # Invoice.sales_area is a CharField(max_length=2), not a ForeignKey
        sales_area_code = "01"  # Default fallback
        if job_card.sales_area:
            # Convert the SalesArea number to a 2-digit string (e.g., 1 -> "01")
            sales_area_code = str(job_card.sales_area.number).zfill(2)
        else:
            # Try to get default sales area
            try:
                from apps.settings.models import SalesArea

                default_sales_area = SalesArea.objects.filter(is_active=True).first()
                if default_sales_area:
                    sales_area_code = str(default_sales_area.number).zfill(2)
            except Exception as e:
                logger.warning(f"Could not fetch default SalesArea: {e}")

        logger.debug(
            f"Using sales_area_code: {sales_area_code} for job card {job_card.job_number}"
        )

        # Create invoice
        invoice = Invoice.objects.create(
            debtor=debtor,
            invoice_number=invoice_number,
            invoice_date=today,
            delivery_name=job_card.customer_name,
            delivery_address_line1=job_card.address,
            delivery_telephone=job_card.telephone,
            order_number=job_card.order_number,
            job_card_number=job_card.job_number,
            sales_area=sales_area_code,
            subtotal=(
                round(job_card.subtotal, 2) if job_card.subtotal else Decimal("0.00")
            ),
            vat_amount=(
                round(job_card.vat_amount, 2)
                if job_card.vat_amount
                else Decimal("0.00")
            ),
            total_amount=(
                round(job_card.total_amount, 2)
                if job_card.total_amount
                else Decimal("0.00")
            ),
            total_cost=(
                round(job_card.total_cost, 2)
                if job_card.total_cost
                else Decimal("0.00")
            ),
            gross_profit=(
                round(job_card.gross_profit, 2)
                if job_card.gross_profit
                else Decimal("0.00")
            ),
            status="DRAFT",
            is_posted=False,
        )

        # Copy job card lines to invoice lines
        for job_line in job_card.lines.all():
            # Calculate line_cost from quantity * cost_price (if available)
            line_cost = (
                (job_line.quantity * job_line.cost_price)
                if job_line.cost_price
                else Decimal("0.00")
            )

            # Create invoice line - validation is now skipped in the model's save method
            InvoiceLine.objects.create(
                invoice=invoice,
                line_number=job_line.line_number,
                stock_code=job_line.stock_code,
                description=job_line.description,
                quantity=job_line.quantity,
                unit_price=job_line.unit_price,
                discount_percentage=job_line.discount_percentage,
                tax_code=job_line.tax_code,
                line_total=job_line.line_total,
                vat_amount=job_line.vat_amount,
                cost_price=job_line.cost_price,
                line_cost=line_cost,
                line_profit=job_line.line_profit,
            )

        # Update job card status
        # Log all field lengths for debugging
        logger.debug("Job card field lengths before update:")
        logger.debug(
            f"  job_number: {len(job_card.job_number) if job_card.job_number else 0} (max 20)"
        )
        logger.debug(
            f"  customer_name: {len(job_card.customer_name) if job_card.customer_name else 0} (max 200)"
        )
        logger.debug(
            f"  address: {len(job_card.address) if job_card.address else 0} (max 1000)"
        )
        logger.debug(
            f"  telephone: {len(job_card.telephone) if job_card.telephone else 0} (max 50)"
        )
        logger.debug(
            f"  contact_person: {len(job_card.contact_person) if job_card.contact_person else 0} (max 100)"
        )
        logger.debug(
            f"  order_number: {len(job_card.order_number) if job_card.order_number else 0} (max 50)"
        )
        logger.debug(
            f"  registration_number: {len(job_card.registration_number) if job_card.registration_number else 0} (max 50)"
        )
        logger.debug(
            f"  job_description: {len(job_card.job_description) if job_card.job_description else 0} (max ?)"
        )
        logger.debug(
            f"  debtor_account_number: {len(job_card.debtor_account_number) if job_card.debtor_account_number else 0} (max 20)"
        )
        logger.debug(
            f"  status: {len(job_card.status) if job_card.status else 0} (max 25)"
        )
        logger.debug(
            f"  cancellation_reason: {len(job_card.cancellation_reason) if job_card.cancellation_reason else 0} (max ?)"
        )

        # Truncate all string fields to their max_length to prevent database errors
        status_value = "CONVERTED_TO_INVOICE"[:25]  # max_length is 25
        job_card.status = status_value

        # Truncate any potentially long string fields
        if job_card.job_number and len(job_card.job_number) > 20:
            job_card.job_number = job_card.job_number[:20]
        if job_card.customer_name and len(job_card.customer_name) > 200:
            job_card.customer_name = job_card.customer_name[:200]
        if job_card.address and len(job_card.address) > 1000:
            job_card.address = job_card.address[:1000]
        if job_card.telephone and len(job_card.telephone) > 50:
            job_card.telephone = job_card.telephone[:50]
        if job_card.contact_person and len(job_card.contact_person) > 100:
            job_card.contact_person = job_card.contact_person[:100]
        if job_card.order_number and len(job_card.order_number) > 50:
            job_card.order_number = job_card.order_number[:50]
        if job_card.registration_number and len(job_card.registration_number) > 50:
            job_card.registration_number = job_card.registration_number[:50]
        if job_card.job_description and len(job_card.job_description) > 2000:
            job_card.job_description = job_card.job_description[:2000]
        if job_card.debtor_account_number and len(job_card.debtor_account_number) > 20:
            job_card.debtor_account_number = job_card.debtor_account_number[:20]
        if job_card.cancellation_reason and len(job_card.cancellation_reason) > 500:
            job_card.cancellation_reason = job_card.cancellation_reason[:500]

        logger.debug(
            f"Updating job card {job_card.job_number} status to: {status_value}"
        )

        try:
            # Use update_fields to avoid triggering full save signals that might cause issues
            job_card.save(update_fields=["status", "updated_at"])
        except Exception as e:
            logger.error(f"Error updating job card status: {e}")
            logger.error(
                f"Job card fields: job_number={job_card.job_number}, status={job_card.status}"
            )
            # Re-raise to maintain original error behavior
            raise

        logger.info(
            f"Converted job card {job_card.job_number} to invoice {invoice.invoice_number} "
            f"for debtor {debtor.dno}"
        )

        return invoice

    @transaction.atomic
    def convert_laybye_to_invoice(laybye, debtor):
        """
        Convert laybye to customer invoice.

        Args:
            laybye: Laybye instance to convert
            debtor: Debtor instance (customer)

        Returns:
            Invoice: Created invoice

        Raises:
            ValueError: If laybye cannot be converted
        """
        from apps.pos.models import LaybyeLine

        if laybye.status == "CONVERTED_TO_INVOICE":
            raise ValueError("Laybye already converted to invoice")

        if laybye.status == "CANCELLED":
            raise ValueError("Cannot convert cancelled laybye to invoice")

        if laybye.status == "EXPIRED":
            raise ValueError("Cannot convert expired laybye to invoice")

        if not debtor:
            raise ValueError(
                "Debtor is required to create invoice. Please select a debtor."
            )

        # Generate invoice number (format: INV-YYYYMMDD-XXXXX)
        from apps.settings.models import SalesArea
        from django.utils import timezone

        today = timezone.now().date()
        invoice_count = Invoice.objects.filter(invoice_date=today).count() + 1
        invoice_number = (
            f"INV-{today.year}{today.month:02d}{today.day:02d}-{invoice_count:05d}"
        )

        # Handle sales_area - get the code string (not the ForeignKey object)
        # Invoice.sales_area is a CharField(max_length=2), not a ForeignKey
        sales_area_code = None
        if laybye.sales_area:
            sales_area_code = str(laybye.sales_area.number).zfill(2)
        else:
            default_sales_area = SalesArea.objects.filter(is_active=True).first()
            if default_sales_area:
                sales_area_code = str(default_sales_area.number).zfill(2)

        # Create invoice
        invoice = Invoice.objects.create(
            debtor=debtor,
            invoice_number=invoice_number,
            invoice_date=today,
            delivery_name=laybye.customer_name,
            delivery_address_line1=laybye.address_line1,
            delivery_address_line2=laybye.address_line2,
            delivery_address_line3=laybye.address_line3,
            delivery_telephone=laybye.telephone,
            sales_area=sales_area_code,
            subtotal=(
                round(laybye.total_amount - laybye.vat_amount, 2)
                if laybye.total_amount
                else Decimal("0.00")
            ),
            vat_amount=(
                round(laybye.vat_amount, 2)
                if hasattr(laybye, "vat_amount") and laybye.vat_amount
                else Decimal("0.00")
            ),
            total_amount=(
                round(laybye.total_amount, 2)
                if laybye.total_amount
                else Decimal("0.00")
            ),
            total_cost=Decimal("0.00"),
            gross_profit=Decimal("0.00"),
            status="DRAFT",
            is_posted=False,
        )

        # Copy laybye sale lines to invoice lines (only 'SP' = Sale type)
        laybye_lines = LaybyeLine.objects.filter(
            laybye=laybye, transaction_type="SP"
        ).order_by("transaction_date", "transaction_time")

        line_number = 1
        for laybye_line in laybye_lines:
            # Calculate line_cost from quantity * cost_price
            line_cost = (
                (laybye_line.quantity * laybye_line.cost_price)
                if laybye_line.cost_price
                else Decimal("0.00")
            )

            InvoiceLine.objects.create(
                invoice=invoice,
                line_number=line_number,
                stock_code=laybye_line.stock_code,
                description=laybye_line.description,
                quantity=laybye_line.quantity,
                unit_price=laybye_line.unit_price,
                discount_percentage=laybye_line.discount_percentage,
                tax_code=laybye_line.tax_code,
                line_total=laybye_line.line_total,
                vat_amount=laybye_line.vat_amount,
                cost_price=laybye_line.cost_price,
                line_cost=line_cost,
                line_profit=(
                    laybye_line.selling_price - laybye_line.cost_price
                    if laybye_line.selling_price and laybye_line.cost_price
                    else Decimal("0.00")
                ),
            )
            line_number += 1

        # Update laybye status
        laybye.status = "CONVERTED_TO_INVOICE"
        laybye.save()

        logger.info(
            f"Converted laybye {laybye.laybye_number} to invoice {invoice.invoice_number} "
            f"for debtor {debtor.dno}"
        )

        return invoice

    @transaction.atomic
    def convert_quotation_to_invoice(quotation, debtor):
        """
        Convert quotation to customer invoice.

        Args:
            quotation: Quotation instance to convert
            debtor: Debtor instance (customer)

        Returns:
            Invoice: Created invoice

        Raises:
            ValueError: If quotation cannot be converted
        """
        if quotation.status == "CONVERTED_TO_INVOICE":
            raise ValueError("Quotation already converted to invoice")

        if quotation.status == "CANCELLED":
            raise ValueError("Cannot convert cancelled quotation to invoice")

        if quotation.status == "EXPIRED":
            raise ValueError("Cannot convert expired quotation to invoice")

        if not debtor:
            raise ValueError(
                "Debtor is required to create invoice. Please select a debtor."
            )

        # Generate invoice number (format: INV-YYYYMMDD-XXXXX)
        from apps.settings.models import SalesArea
        from django.utils import timezone

        today = timezone.now().date()
        invoice_count = Invoice.objects.filter(invoice_date=today).count() + 1
        invoice_number = (
            f"INV-{today.year}{today.month:02d}{today.day:02d}-{invoice_count:05d}"
        )

        # Handle sales_area - get the code string (not the ForeignKey object)
        # Invoice.sales_area is a CharField(max_length=2), not a ForeignKey
        sales_area_code = None
        if quotation.sales_area:
            sales_area_code = str(quotation.sales_area.number).zfill(2)
        else:
            default_sales_area = SalesArea.objects.filter(is_active=True).first()
            if default_sales_area:
                sales_area_code = str(default_sales_area.number).zfill(2)

        # Create invoice
        invoice = Invoice.objects.create(
            debtor=debtor,
            invoice_number=invoice_number,
            invoice_date=today,
            delivery_name=quotation.customer_name,
            delivery_address_line1=quotation.address_line1,
            delivery_address_line2=quotation.address_line2,
            delivery_address_line3=quotation.address_line3,
            delivery_telephone=quotation.telephone,
            sales_area=sales_area_code,
            subtotal=(
                round(quotation.subtotal, 2) if quotation.subtotal else Decimal("0.00")
            ),
            vat_amount=(
                round(quotation.vat_amount, 2)
                if quotation.vat_amount
                else Decimal("0.00")
            ),
            total_amount=(
                round(quotation.total_amount, 2)
                if quotation.total_amount
                else Decimal("0.00")
            ),
            total_cost=Decimal("0.00"),
            gross_profit=(
                round(quotation.gross_profit, 2)
                if quotation.gross_profit
                else Decimal("0.00")
            ),
            status="DRAFT",
            is_posted=False,
        )

        # Copy quotation lines to invoice lines
        for quote_line in quotation.lines.all():
            # Calculate line_cost from quantity * cost_price
            line_cost = (
                (quote_line.quantity * quote_line.cost_price)
                if quote_line.cost_price
                else Decimal("0.00")
            )

            InvoiceLine.objects.create(
                invoice=invoice,
                line_number=quote_line.line_number,
                stock_code=quote_line.stock_code,
                description=quote_line.description,
                quantity=quote_line.quantity,
                unit_price=quote_line.unit_price,
                discount_percentage=quote_line.discount_percentage,
                tax_code=quote_line.tax_code,
                line_total=quote_line.line_total,
                vat_amount=quote_line.vat_amount,
                cost_price=quote_line.cost_price,
                line_cost=line_cost,
                line_profit=(
                    (quote_line.unit_price - quote_line.cost_price)
                    * quote_line.quantity
                    if quote_line.unit_price and quote_line.cost_price
                    else Decimal("0.00")
                ),
            )

        # Update quotation status
        quotation.status = "CONVERTED_TO_INVOICE"
        quotation.save()

        logger.info(
            f"Converted quotation {quotation.quotation_number} to invoice {invoice.invoice_number} "
            f"for debtor {debtor.dno}"
        )

        return invoice


class RepairService:
    """Service class for repair voucher operations."""

    @staticmethod
    @transaction.atomic
    def issue_to_supplier(repair, supplier_account, transport_mode=""):
        """Issue repair to supplier."""
        if repair.status != "C":
            raise ValueError("Repair must be in CREATED status to issue")

        repair.supplier_number = (
            int(supplier_account) if str(supplier_account).isdigit() else None
        )
        repair.date_sent = date.today()
        repair.status = "I"
        repair.save()

        return repair

    @staticmethod
    @transaction.atomic
    def receive_from_supplier(repair, repair_cost, supplier_invoice=""):
        """Receive repaired item from supplier."""
        if repair.status != "I":
            raise ValueError("Repair must be in ISSUED status to receive")

        repair.date_returned = date.today()
        repair.repair_cost = repair_cost
        repair.status = "R"
        repair.save()

        return repair

    @staticmethod
    @transaction.atomic
    def invoice_customer(
        repair,
        charge_type,
        lines_data,
        debtor_id=None,
        new_debtor_data=None,
        tenders_data=None,
        cashier=None,
        station_number=1,
    ):
        """
        Manual §R "5. Charge for the Repair": a genuine two-way branch, not
        a status flip. Cash option creates a real Cash Sale ending in a
        Tender Routine. Account option resolves an existing Debtor or
        captures a new one on the fly, then creates a real Invoice. In BOTH
        branches, line items are manually re-captured at charge time (with
        a cost-price toggle in the DOS UI) — they are NOT auto-copied from
        RepairLine, which is a separate supplier-side issue/receipt trail.

        Args:
            repair: Repair instance (must be status 'R' — Received)
            charge_type: 'cash' or 'account'
            lines_data: list of dicts — stock_code, description, quantity,
                unit_price, discount_percentage, tax_code, cost_price
            debtor_id: existing Debtor pk (account branch)
            new_debtor_data: dict for DebtorCreateUpdateSerializer to create
                a debtor on the fly (account branch, "New Debtor")
            tenders_data: list of tender dicts (cash branch)
            cashier, station_number: for the created CashSale (cash branch)

        Returns:
            dict: {'charge_type': ..., 'document': CashSale or Invoice}
        """
        if repair.status != "R":
            raise ValueError("Repair must be RECEIVED before invoicing")

        if charge_type not in ("cash", "account"):
            raise ValueError("charge_type must be 'cash' or 'account'")

        if not lines_data:
            raise POSValidationException(
                "At least one line item is required to charge the repair"
            )

        # Normalize line dicts once — request.data delivers strings/floats,
        # every DecimalField write below (CashSaleLine/InvoiceLine, plus
        # CalculationService) expects real Decimals.
        lines_data = [
            {
                **line_data,
                "quantity": Decimal(str(line_data["quantity"])),
                "unit_price": Decimal(str(line_data["unit_price"])),
                "discount_percentage": Decimal(
                    str(line_data.get("discount_percentage") or 0)
                ),
                "cost_price": Decimal(str(line_data.get("cost_price") or 0)),
            }
            for line_data in lines_data
        ]

        if charge_type == "cash":
            import uuid

            sale_number = f"CS-{uuid.uuid4().hex[:8].upper()}"
            cash_sale = CashSale.objects.create(
                sale_number=sale_number,
                sale_date=date.today(),
                customer_name=repair.customer_name,
                telephone=repair.telephone,
                cashier=cashier,
                station_number=station_number,
            )

            subtotal = Decimal("0.00")
            vat_total = Decimal("0.00")
            cost_total = Decimal("0.00")
            for idx, line_data in enumerate(lines_data, start=1):
                calc = CalculationService.calculate_line_totals(
                    quantity=line_data["quantity"],
                    unit_price=line_data["unit_price"],
                    discount_percentage=line_data.get(
                        "discount_percentage", Decimal("0.00")
                    ),
                    tax_code=line_data.get("tax_code", 1),
                    cost_price=line_data.get("cost_price", Decimal("0.00")),
                )
                CashSaleLine.objects.create(
                    cash_sale=cash_sale,
                    line_number=idx,
                    stock_code=line_data.get("stock_code", ""),
                    description=line_data.get("description", ""),
                    quantity=line_data["quantity"],
                    unit_price=line_data["unit_price"],
                    discount_percentage=line_data.get(
                        "discount_percentage", Decimal("0.00")
                    ),
                    tax_code=line_data.get("tax_code", 1),
                    line_total=calc["line_total"],
                    vat_amount=calc["vat_amount"],
                    cost_price=line_data.get("cost_price", Decimal("0.00")),
                    line_profit=calc["line_profit"],
                )
                subtotal += calc["line_total_before_vat"]
                vat_total += calc["vat_amount"]
                cost_total += calc["line_cost"]

            cash_sale.subtotal = subtotal
            cash_sale.vat_amount = vat_total
            cash_sale.total_amount = subtotal + vat_total
            cash_sale.total_cost = cost_total
            cash_sale.gross_profit = subtotal - cost_total
            cash_sale.save()

            for tender_data in tenders_data or []:
                tender_data = dict(tender_data)
                tender_data["amount"] = Decimal(str(tender_data.get("amount", 0)))
                Tender.objects.create(cash_sale=cash_sale, **tender_data)

            CashSaleService.post_cash_sale(cash_sale)

            repair.status = "V"
            repair.save()

            logger.info(
                f"Repair {repair.repair_number} charged as Cash Sale {cash_sale.sale_number}"
            )
            return {"charge_type": "cash", "document": cash_sale}

        # Account branch
        if debtor_id:
            debtor = Debtor.objects.get(pk=debtor_id)
        elif new_debtor_data:
            from apps.debtors.serializers import DebtorCreateUpdateSerializer

            debtor_serializer = DebtorCreateUpdateSerializer(data=new_debtor_data)
            debtor_serializer.is_valid(raise_exception=True)
            debtor = debtor_serializer.save()
        else:
            raise ValueError(
                "debtor_id or new_debtor_data is required for the Account charge option"
            )

        invoice = Invoice.objects.create(
            debtor=debtor,
            invoice_number=f"INV-REP-{repair.repair_number}",
            invoice_date=date.today(),
            delivery_name=repair.customer_name,
            delivery_address_line1=repair.address_line1,
            delivery_telephone=repair.telephone,
            order_number=repair.order_number,
        )

        for idx, line_data in enumerate(lines_data, start=1):
            InvoiceLine.objects.create(
                invoice=invoice,
                line_number=idx,
                stock_code=line_data.get("stock_code", ""),
                description=line_data.get("description", ""),
                quantity=line_data["quantity"],
                unit_price=line_data["unit_price"],
                discount_percentage=line_data.get(
                    "discount_percentage", Decimal("0.00")
                ),
                tax_code=line_data.get("tax_code", 1),
                cost_price=line_data.get("cost_price", Decimal("0.00")),
            )

        invoice.post()

        repair.status = "V"
        repair.debtor = debtor
        repair.save()

        logger.info(
            f"Repair {repair.repair_number} charged as Invoice {invoice.invoice_number}"
        )
        return {"charge_type": "account", "document": invoice}
