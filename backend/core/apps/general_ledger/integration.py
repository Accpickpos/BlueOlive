"""
Integration Transfer — posts final-state Debtors/Creditors/Stock Control/
Cash Book transactions into GL.

Idempotency is handled entirely by GLIntegrationLog (source_app,
source_model, source_pk unique together) rather than by adding a
"posted to GL" field to each of the 4 source apps' models — this keeps the
entire pipeline's blast radius inside general_ledger. A record already
logged is never re-transferred.

Where a source transaction type has no confident natural GL pairing, the
record is skipped (with a logged reason) rather than guessed — a wrong
account mapping produces a real wrong financial posting, which is worse
than an outstanding one. See the plan's account-mapping table for the full
rationale per source/type.
"""

import logging
from decimal import Decimal

from django.db import transaction
from django.utils.dateparse import parse_date

from .exceptions import GLIntegrationException, GLPostingException
from .models import GLIntegrationLog, GLIntegrationSettings
from .services import GLPostingService

logger = logging.getLogger(__name__)


class IntegrationTransferService:
    @staticmethod
    def _settings():
        settings_row, _ = GLIntegrationSettings.objects.get_or_create(pk=1)
        return settings_row

    @staticmethod
    def _require(settings_row, *fields):
        missing = [f for f in fields if getattr(settings_row, f) is None]
        if missing:
            raise GLIntegrationException(
                f"GLIntegrationSettings is missing account mapping for: "
                f"{', '.join(missing)}. Configure these before running Integration "
                "Transfer."
            )

    @staticmethod
    def _already_transferred(source_app, source_model, source_pk):
        return GLIntegrationLog.objects.filter(
            source_app=source_app, source_model=source_model, source_pk=source_pk
        ).exists()

    @staticmethod
    def _log(source_app, source_model, source_pk, gl_batchno):
        GLIntegrationLog.objects.create(
            source_app=source_app,
            source_model=source_model,
            source_pk=source_pk,
            gl_batchno=gl_batchno,
        )

    @staticmethod
    def _apply_date_range(queryset, date_field, date_from, date_to):
        if date_from:
            d = parse_date(date_from) if isinstance(date_from, str) else date_from
            if d:
                queryset = queryset.filter(**{f"{date_field}__gte": d})
        if date_to:
            d = parse_date(date_to) if isinstance(date_to, str) else date_to
            if d:
                queryset = queryset.filter(**{f"{date_field}__lte": d})
        return queryset

    # ------------------------------------------------------------------
    # Debtors
    # ------------------------------------------------------------------
    @staticmethod
    def transfer_debtors(date_from=None, date_to=None):
        from apps.debtors.models import DebtorTransaction

        settings_row = IntegrationTransferService._settings()
        SOURCE_APP = "debtors"
        SOURCE_MODEL = "DebtorTransaction"

        qs = DebtorTransaction.objects.filter(status="posted").order_by(
            "transaction_date"
        )
        qs = IntegrationTransferService._apply_date_range(
            qs, "transaction_date", date_from, date_to
        )

        transferred, skipped, errors = 0, [], []

        with transaction.atomic():
            for txn in qs.select_related("debtor"):
                if IntegrationTransferService._already_transferred(
                    SOURCE_APP, SOURCE_MODEL, txn.pk
                ):
                    continue

                try:
                    lines = IntegrationTransferService._debtor_lines(
                        txn, settings_row
                    )
                except GLIntegrationException as e:
                    skipped.append(
                        {"pk": txn.pk, "type": txn.transaction_type, "reason": str(e)}
                    )
                    continue

                if lines is None:
                    # No natural pairing at all for this type — always skip.
                    skipped.append(
                        {
                            "pk": txn.pk,
                            "type": txn.transaction_type,
                            "reason": f"No GL pairing defined for debtors "
                            f"transaction_type={txn.transaction_type!r}.",
                        }
                    )
                    continue

                try:
                    gl_batchno = GLPostingService.post_batch(lines)
                except GLPostingException as e:
                    errors.append({"pk": txn.pk, "error": str(e)})
                    continue

                IntegrationTransferService._log(
                    SOURCE_APP, SOURCE_MODEL, txn.pk, gl_batchno
                )
                transferred += 1

        return {"transferred": transferred, "skipped": skipped, "errors": errors}

    @staticmethod
    def _debtor_lines(txn, settings_row):
        """Build the (debit, credit) leg pair for one DebtorTransaction.
        Returns None if the type has no defined pairing at all (always
        skip); raises GLIntegrationException if the pairing exists but its
        required account mapping isn't configured yet."""
        ref = f"D{txn.pk}"
        details = f"{txn.get_transaction_type_display()} - {txn.debtor.dname}"[:30]
        common = dict(date=txn.transaction_date, reference=ref, details=details)

        if txn.transaction_type in ("IN", "CS"):
            IntegrationTransferService._require(
                settings_row, "debtors_control_accno", "sales_accno"
            )
            lines = [
                {
                    "accno": settings_row.debtors_control_accno,
                    "type": "D",
                    "amount": txn.total_amount,
                    **common,
                },
                {
                    "accno": settings_row.sales_accno,
                    "type": "C",
                    "amount": txn.subtotal,
                    **common,
                },
            ]
            if txn.vat_amount:
                IntegrationTransferService._require(settings_row, "vat_output_accno")
                lines.append(
                    {
                        "accno": settings_row.vat_output_accno,
                        "type": "C",
                        "amount": txn.vat_amount,
                        **common,
                    }
                )
            return lines

        if txn.transaction_type in ("CN", "CR"):
            IntegrationTransferService._require(
                settings_row, "debtors_control_accno", "sales_accno"
            )
            lines = [
                {
                    "accno": settings_row.sales_accno,
                    "type": "D",
                    "amount": txn.subtotal,
                    **common,
                },
                {
                    "accno": settings_row.debtors_control_accno,
                    "type": "C",
                    "amount": txn.total_amount,
                    **common,
                },
            ]
            if txn.vat_amount:
                IntegrationTransferService._require(settings_row, "vat_output_accno")
                lines.insert(
                    1,
                    {
                        "accno": settings_row.vat_output_accno,
                        "type": "D",
                        "amount": txn.vat_amount,
                        **common,
                    },
                )
            return lines

        if txn.transaction_type in ("PM", "RCP"):
            IntegrationTransferService._require(
                settings_row, "debtors_control_accno", "bank_control_accno"
            )
            return [
                {
                    "accno": settings_row.bank_control_accno,
                    "type": "D",
                    "amount": txn.total_amount,
                    **common,
                },
                {
                    "accno": settings_row.debtors_control_accno,
                    "type": "C",
                    "amount": txn.total_amount,
                    **common,
                },
            ]

        if txn.transaction_type == "INT":
            IntegrationTransferService._require(
                settings_row, "debtors_control_accno", "debtors_interest_income_accno"
            )
            return [
                {
                    "accno": settings_row.debtors_control_accno,
                    "type": "D",
                    "amount": txn.total_amount,
                    **common,
                },
                {
                    "accno": settings_row.debtors_interest_income_accno,
                    "type": "C",
                    "amount": txn.total_amount,
                    **common,
                },
            ]

        if txn.transaction_type in ("JD", "JC"):
            IntegrationTransferService._require(
                settings_row, "debtors_control_accno", "debtors_suspense_accno"
            )
            debtors_leg_type = "D" if txn.transaction_type == "JD" else "C"
            suspense_leg_type = "C" if txn.transaction_type == "JD" else "D"
            return [
                {
                    "accno": settings_row.debtors_control_accno,
                    "type": debtors_leg_type,
                    "amount": txn.total_amount,
                    **common,
                },
                {
                    "accno": settings_row.debtors_suspense_accno,
                    "type": suspense_leg_type,
                    "amount": txn.total_amount,
                    **common,
                },
            ]

        if txn.transaction_type == "RF":
            IntegrationTransferService._require(
                settings_row, "debtors_control_accno", "bank_control_accno"
            )
            return [
                {
                    "accno": settings_row.debtors_control_accno,
                    "type": "D",
                    "amount": txn.total_amount,
                    **common,
                },
                {
                    "accno": settings_row.bank_control_accno,
                    "type": "C",
                    "amount": txn.total_amount,
                    **common,
                },
            ]

        return None

    # ------------------------------------------------------------------
    # Creditors
    # ------------------------------------------------------------------
    @staticmethod
    def transfer_creditors(date_from=None, date_to=None):
        from apps.creditors.models import (
            CreditorCreditNote,
            CreditorInvoice,
            CreditorJournal,
            CreditorPayment,
            GoodsReceivedNote,
        )

        settings_row = IntegrationTransferService._settings()
        SOURCE_APP = "creditors"
        transferred, skipped, errors = 0, [], []

        model_builders = [
            (GoodsReceivedNote, IntegrationTransferService._grn_lines),
            (CreditorInvoice, IntegrationTransferService._creditor_invoice_lines),
            (CreditorCreditNote, IntegrationTransferService._creditor_cn_lines),
            (CreditorPayment, IntegrationTransferService._creditor_payment_lines),
            (CreditorJournal, IntegrationTransferService._creditor_journal_lines),
        ]

        with transaction.atomic():
            for model, builder in model_builders:
                qs = model.objects.filter(is_posted=True).order_by("transaction_date")
                qs = IntegrationTransferService._apply_date_range(
                    qs, "transaction_date", date_from, date_to
                )
                for doc in qs.select_related("creditor"):
                    if IntegrationTransferService._already_transferred(
                        SOURCE_APP, model.__name__, doc.pk
                    ):
                        continue
                    try:
                        lines = builder(doc, settings_row)
                    except GLIntegrationException as e:
                        skipped.append(
                            {"model": model.__name__, "pk": doc.pk, "reason": str(e)}
                        )
                        continue

                    try:
                        gl_batchno = GLPostingService.post_batch(lines)
                    except GLPostingException as e:
                        errors.append(
                            {"model": model.__name__, "pk": doc.pk, "error": str(e)}
                        )
                        continue

                    IntegrationTransferService._log(
                        SOURCE_APP, model.__name__, doc.pk, gl_batchno
                    )
                    transferred += 1

        return {"transferred": transferred, "skipped": skipped, "errors": errors}

    @staticmethod
    def _grn_lines(grn, settings_row):
        IntegrationTransferService._require(
            settings_row, "stock_control_accno", "creditors_control_accno"
        )
        ref = f"GRN{grn.pk}"
        details = f"GRN - {grn.creditor.name}"[:30]
        common = dict(date=grn.transaction_date, reference=ref, details=details)
        lines = [
            {
                "accno": settings_row.stock_control_accno,
                "type": "D",
                "amount": grn.subtotal + (grn.surcharge_amount or Decimal("0.00")),
                **common,
            },
            {
                "accno": settings_row.creditors_control_accno,
                "type": "C",
                "amount": grn.total_amount,
                **common,
            },
        ]
        if grn.total_vat:
            IntegrationTransferService._require(settings_row, "vat_input_accno")
            lines.insert(
                1,
                {
                    "accno": settings_row.vat_input_accno,
                    "type": "D",
                    "amount": grn.total_vat,
                    **common,
                },
            )
        return lines

    @staticmethod
    def _creditor_invoice_lines(invoice, settings_row):
        IntegrationTransferService._require(settings_row, "creditors_control_accno")
        ref = f"INV{invoice.pk}"
        details = f"Invoice - {invoice.creditor.name}"[:30]
        common = dict(date=invoice.transaction_date, reference=ref, details=details)

        lines = []
        for line_item in invoice.line_items.select_related("expense_category").all():
            expense_accno = (
                line_item.expense_category.gl_accno
                or settings_row.cashbook_default_expense_accno
            )
            if not expense_accno:
                raise GLIntegrationException(
                    f"Invoice {invoice.pk} line {line_item.pk}: expense category "
                    f"{line_item.expense_category.name!r} has no gl_accno and "
                    "GLIntegrationSettings.cashbook_default_expense_accno is not set."
                )
            lines.append(
                {
                    "accno": expense_accno,
                    "type": "D",
                    "amount": line_item.amount,
                    **common,
                }
            )
            if line_item.tax_amount:
                IntegrationTransferService._require(settings_row, "vat_input_accno")
                lines.append(
                    {
                        "accno": settings_row.vat_input_accno,
                        "type": "D",
                        "amount": line_item.tax_amount,
                        **common,
                    }
                )

        lines.append(
            {
                "accno": settings_row.creditors_control_accno,
                "type": "C",
                "amount": invoice.total_amount,
                **common,
            }
        )
        return lines

    @staticmethod
    def _creditor_cn_lines(cn, settings_row):
        IntegrationTransferService._require(
            settings_row, "stock_control_accno", "creditors_control_accno"
        )
        ref = f"CRN{cn.pk}"
        details = f"Credit Note - {cn.creditor.name}"[:30]
        common = dict(date=cn.transaction_date, reference=ref, details=details)
        lines = [
            {
                "accno": settings_row.creditors_control_accno,
                "type": "D",
                "amount": cn.total_amount,
                **common,
            },
            {
                "accno": settings_row.stock_control_accno,
                "type": "C",
                "amount": cn.subtotal,
                **common,
            },
        ]
        if cn.total_vat:
            IntegrationTransferService._require(settings_row, "vat_input_accno")
            lines.append(
                {
                    "accno": settings_row.vat_input_accno,
                    "type": "C",
                    "amount": cn.total_vat,
                    **common,
                }
            )
        return lines

    @staticmethod
    def _creditor_payment_lines(payment, settings_row):
        IntegrationTransferService._require(
            settings_row, "creditors_control_accno", "bank_control_accno"
        )
        ref = f"PAY{payment.pk}"
        details = f"Payment - {payment.creditor.name}"[:30]
        common = dict(date=payment.transaction_date, reference=ref, details=details)

        lines = [
            {
                "accno": settings_row.creditors_control_accno,
                "type": "D",
                "amount": payment.amount_due,
                **common,
            },
            {
                "accno": settings_row.bank_control_accno,
                "type": "C",
                "amount": payment.amount_paid,
                **common,
            },
        ]
        if payment.settlement_discount_amount:
            if settings_row.creditors_discount_received_accno:
                lines.append(
                    {
                        "accno": settings_row.creditors_discount_received_accno,
                        "type": "C",
                        "amount": payment.settlement_discount_amount,
                        **common,
                    }
                )
            else:
                # No discount account configured — post only what was
                # actually paid (Dr Creditors Control by amount_paid, not
                # amount_due) rather than raising or guessing an account.
                # This keeps the entry balanced, but leaves the discount
                # portion (amount_due - amount_paid) sitting on Creditors
                # Control unrecognized until creditors_discount_received_accno
                # is configured and the residual is cleared with a manual
                # journal — a v1 limitation, not silently-wrong accounting.
                lines[0] = {
                    "accno": settings_row.creditors_control_accno,
                    "type": "D",
                    "amount": payment.amount_paid,
                    **common,
                }
        return lines

    @staticmethod
    def _creditor_journal_lines(journal, settings_row):
        IntegrationTransferService._require(
            settings_row, "creditors_control_accno", "creditors_suspense_accno"
        )
        ref = f"CRJ{journal.pk}"
        details = f"Journal - {journal.creditor.name}"[:30]
        common = dict(date=journal.transaction_date, reference=ref, details=details)

        creditors_leg_type = "C" if journal.journal_type == "CJ" else "D"
        suspense_leg_type = "D" if journal.journal_type == "CJ" else "C"
        return [
            {
                "accno": settings_row.creditors_control_accno,
                "type": creditors_leg_type,
                "amount": journal.total_amount,
                **common,
            },
            {
                "accno": settings_row.creditors_suspense_accno,
                "type": suspense_leg_type,
                "amount": journal.total_amount,
                **common,
            },
        ]

    # ------------------------------------------------------------------
    # Stock Control
    # ------------------------------------------------------------------
    @staticmethod
    def transfer_stock_control(date_from=None, date_to=None):
        """
        Only completed StockTake sessions are transferred, one posting per
        stock take, net of all its items' variance_value. StockMovementLedger
        rows are always skipped — that model has no status field at all and
        its movement_type codes are free-text/legacy-imported with no
        reliable "final" signal, so there is no safe way to know which rows
        are ready for GL.
        """
        from apps.stock_control.models import StockTake

        settings_row = IntegrationTransferService._settings()
        SOURCE_APP = "stock_control"
        SOURCE_MODEL = "StockTake"

        qs = StockTake.objects.filter(status="UPDATED").order_by("stock_take_date")
        qs = IntegrationTransferService._apply_date_range(
            qs, "stock_take_date", date_from, date_to
        )

        transferred, skipped, errors = 0, [], []

        with transaction.atomic():
            for stock_take in qs:
                if IntegrationTransferService._already_transferred(
                    SOURCE_APP, SOURCE_MODEL, stock_take.pk
                ):
                    continue

                net_variance = sum(
                    (item.variance_value for item in stock_take.items.all()),
                    Decimal("0.00"),
                )
                if net_variance == 0:
                    # Nothing to post, but still log it so it doesn't show up
                    # as outstanding forever.
                    IntegrationTransferService._log(
                        SOURCE_APP, SOURCE_MODEL, stock_take.pk, gl_batchno=0
                    )
                    continue

                try:
                    IntegrationTransferService._require(
                        settings_row,
                        "stock_control_accno",
                        "stock_shrinkage_expense_accno"
                        if net_variance < 0
                        else "stock_gain_income_accno",
                    )
                except GLIntegrationException as e:
                    skipped.append({"pk": stock_take.pk, "reason": str(e)})
                    continue

                ref = f"ST{stock_take.pk}"
                details = f"Stock take {stock_take.stock_take_date}"[:30]
                common = dict(
                    date=stock_take.stock_take_date, reference=ref, details=details
                )
                if net_variance < 0:
                    lines = [
                        {
                            "accno": settings_row.stock_shrinkage_expense_accno,
                            "type": "D",
                            "amount": abs(net_variance),
                            **common,
                        },
                        {
                            "accno": settings_row.stock_control_accno,
                            "type": "C",
                            "amount": abs(net_variance),
                            **common,
                        },
                    ]
                else:
                    lines = [
                        {
                            "accno": settings_row.stock_control_accno,
                            "type": "D",
                            "amount": net_variance,
                            **common,
                        },
                        {
                            "accno": settings_row.stock_gain_income_accno,
                            "type": "C",
                            "amount": net_variance,
                            **common,
                        },
                    ]

                try:
                    gl_batchno = GLPostingService.post_batch(lines)
                except GLPostingException as e:
                    errors.append({"pk": stock_take.pk, "error": str(e)})
                    continue

                IntegrationTransferService._log(
                    SOURCE_APP, SOURCE_MODEL, stock_take.pk, gl_batchno
                )
                transferred += 1

        return {"transferred": transferred, "skipped": skipped, "errors": errors}

    # ------------------------------------------------------------------
    # Cash Book
    # ------------------------------------------------------------------
    @staticmethod
    def transfer_cash_book(date_from=None, date_to=None):
        """
        Only OTHER_INCOME/OTHER_EXPENSE transactions are transferred.
        Everything tagged audit_type in (1, 3) — Accounts Receivable
        Receipts / Accounts Payable Payments — is always skipped: those
        overlap with debtors/creditors transactions already covered by
        transfer_debtors()/transfer_creditors(), and posting both would
        double-post against Debtors/Creditors Control.
        """
        from apps.cash_book.models import CashBookTransaction

        settings_row = IntegrationTransferService._settings()
        SOURCE_APP = "cash_book"
        SOURCE_MODEL = "CashBookTransaction"

        qs = CashBookTransaction.objects.filter(
            is_reconciled=True,
            transaction_type__in=("OTHER_INCOME", "OTHER_EXPENSE"),
        ).exclude(audit_type__in=(1, 3)).order_by("transaction_date")
        qs = IntegrationTransferService._apply_date_range(
            qs, "transaction_date", date_from, date_to
        )

        transferred, skipped, errors = 0, [], []

        with transaction.atomic():
            for txn in qs:
                if IntegrationTransferService._already_transferred(
                    SOURCE_APP, SOURCE_MODEL, txn.pk
                ):
                    continue

                try:
                    lines = IntegrationTransferService._cash_book_lines(
                        txn, settings_row
                    )
                except GLIntegrationException as e:
                    skipped.append({"pk": txn.pk, "reason": str(e)})
                    continue

                try:
                    gl_batchno = GLPostingService.post_batch(lines)
                except GLPostingException as e:
                    errors.append({"pk": txn.pk, "error": str(e)})
                    continue

                IntegrationTransferService._log(
                    SOURCE_APP, SOURCE_MODEL, txn.pk, gl_batchno
                )
                transferred += 1

        return {"transferred": transferred, "skipped": skipped, "errors": errors}

    @staticmethod
    def _cash_book_lines(txn, settings_row):
        bank_or_cash_accno = (
            settings_row.bank_control_accno
            if txn.account_type == "BANK"
            else settings_row.cash_control_accno
        )
        field_name = "bank_control_accno" if txn.account_type == "BANK" else "cash_control_accno"
        IntegrationTransferService._require(settings_row, field_name)

        ref = f"CB{txn.pk}"
        details = txn.description[:30]
        common = dict(date=txn.transaction_date, reference=ref, details=details)

        if txn.transaction_type == "OTHER_INCOME":
            other_income = getattr(txn, "other_income", None)
            income_accno = (
                other_income.income_category.gl_accno
                if other_income and other_income.income_category.gl_accno
                else settings_row.cashbook_default_income_accno
            )
            if not income_accno:
                raise GLIntegrationException(
                    f"CashBookTransaction {txn.pk}: no gl_accno on its income "
                    "category and GLIntegrationSettings.cashbook_default_income_accno "
                    "is not set."
                )
            lines = [
                {
                    "accno": bank_or_cash_accno,
                    "type": "D",
                    "amount": txn.value_excl_vat or txn.amount,
                    **common,
                },
                {
                    "accno": income_accno,
                    "type": "C",
                    "amount": txn.value_excl_vat or txn.amount,
                    **common,
                },
            ]
            if txn.tax_amount:
                IntegrationTransferService._require(settings_row, "vat_output_accno")
                lines.append(
                    {
                        "accno": settings_row.vat_output_accno,
                        "type": "C",
                        "amount": txn.tax_amount,
                        **common,
                    }
                )
            return lines

        # OTHER_EXPENSE
        other_expense = getattr(txn, "other_expense", None)
        expense_accno = (
            other_expense.expense_category.gl_accno
            if other_expense and other_expense.expense_category.gl_accno
            else settings_row.cashbook_default_expense_accno
        )
        if not expense_accno:
            raise GLIntegrationException(
                f"CashBookTransaction {txn.pk}: no gl_accno on its expense "
                "category and GLIntegrationSettings.cashbook_default_expense_accno "
                "is not set."
            )
        lines = [
            {
                "accno": expense_accno,
                "type": "D",
                "amount": txn.value_excl_vat or txn.amount,
                **common,
            },
            {
                "accno": bank_or_cash_accno,
                "type": "C",
                "amount": txn.value_excl_vat or txn.amount,
                **common,
            },
        ]
        if txn.tax_amount:
            IntegrationTransferService._require(settings_row, "vat_input_accno")
            lines.append(
                {
                    "accno": settings_row.vat_input_accno,
                    "type": "D",
                    "amount": txn.tax_amount,
                    **common,
                }
            )
        return lines

    # ------------------------------------------------------------------
    # Orchestration & enquiry
    # ------------------------------------------------------------------
    @staticmethod
    def transfer_all(date_from=None, date_to=None):
        return {
            "debtors": IntegrationTransferService.transfer_debtors(
                date_from=date_from, date_to=date_to
            ),
            "creditors": IntegrationTransferService.transfer_creditors(
                date_from=date_from, date_to=date_to
            ),
            "stock_control": IntegrationTransferService.transfer_stock_control(
                date_from=date_from, date_to=date_to
            ),
            "cash_book": IntegrationTransferService.transfer_cash_book(
                date_from=date_from, date_to=date_to
            ),
        }

    @staticmethod
    def outstanding():
        """Posted/final-state source records not yet in GLIntegrationLog —
        answers the spec's "Outstanding Batches" enquiry with zero schema
        changes to the source apps."""
        from apps.cash_book.models import CashBookTransaction
        from apps.creditors.models import (
            CreditorCreditNote,
            CreditorInvoice,
            CreditorJournal,
            CreditorPayment,
            GoodsReceivedNote,
        )
        from apps.debtors.models import DebtorTransaction
        from apps.stock_control.models import StockTake

        def _count_outstanding(model, source_app, qs):
            logged_pks = set(
                GLIntegrationLog.objects.filter(
                    source_app=source_app, source_model=model.__name__
                ).values_list("source_pk", flat=True)
            )
            return qs.exclude(pk__in=logged_pks).count()

        return {
            "debtors": _count_outstanding(
                DebtorTransaction,
                "debtors",
                DebtorTransaction.objects.filter(status="posted"),
            ),
            "creditors": {
                model.__name__: _count_outstanding(
                    model, "creditors", model.objects.filter(is_posted=True)
                )
                for model in (
                    GoodsReceivedNote,
                    CreditorInvoice,
                    CreditorCreditNote,
                    CreditorPayment,
                    CreditorJournal,
                )
            },
            "stock_control": _count_outstanding(
                StockTake, "stock_control", StockTake.objects.filter(status="UPDATED")
            ),
            "cash_book": _count_outstanding(
                CashBookTransaction,
                "cash_book",
                CashBookTransaction.objects.filter(
                    is_reconciled=True,
                    transaction_type__in=("OTHER_INCOME", "OTHER_EXPENSE"),
                ).exclude(audit_type__in=(1, 3)),
            ),
        }
