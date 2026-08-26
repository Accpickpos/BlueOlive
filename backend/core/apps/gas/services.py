"""
Gas app business logic: LedgerPostingService (GL integration) and RentalService
(checkout/return lifecycle).

Architecture decisions this implements (see /plan-eng-review and
/plan-ceo-review, 2026-07-28):
  - Synchronous, same-DB-transaction posting (no Celery/async) — tenant schema
    scoping is request-scoped (tenancy/schema_middleware.py) and does not
    propagate to background workers without extra plumbing this milestone
    intentionally avoids.
  - LedgerPostingService is an in-process Python interface, not an HTTP API —
    matches the existing pos -> stock_control / debtors direct-import pattern.
  - Full atomic() rollback on any failure, including a GL posting failure —
    stock, POS, and GL either all succeed or all roll back together.
  - Cylinders are tracked as per-customer aggregate counts against StockItem;
    checkout decrements stock ONCE. billed_for_replacement must NOT decrement
    stock again — the cylinder already left inventory at checkout.
"""
import logging
from datetime import date as date_cls, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.general_ledger.models import GLMast, GLTran, GLParam
from apps.pos.calculation_service import CalculationService
from apps.stock_control.models import StockItem

from .exceptions import RentalLedgerException, RentalStateException, RentalStockException
from .models import RentalSettings, RentalTransaction

logger = logging.getLogger(__name__)

# Guard window for accidental double-submit (double-click) on checkout.
DOUBLE_SUBMIT_WINDOW_SECONDS = 30


class LedgerPostingService:
    """
    Posts double-entry GL transactions directly to GLTran + updates GLMast's
    current-period balance. Writes with source='S' (System) — bypasses the
    manual GLBatch staging table, which exists for human-entered batches
    awaiting review, not automated system postings.

    No prior example of this pattern existed in the codebase before this
    milestone (verified during /plan-eng-review) — this is the first
    implementation other apps can follow.
    """

    @staticmethod
    def _apply_period_balance(account: GLMast, curperiod: int, leg_type: str, amount: Decimal):
        """Update GLMast's current-period balance for one leg of a transaction.

        Standard double-entry: a debit increases a debit-normal account and
        decreases a credit-normal account; a credit does the opposite.
        """
        field_name = f'period{curperiod}'
        current = getattr(account, field_name)

        same_side = (leg_type == account.drorcr)
        delta = amount if same_side else -amount

        setattr(account, field_name, current + delta)
        account.save(update_fields=[field_name, 'updated_at'])

    @staticmethod
    def post_entry(*, debit_accno: int, credit_accno: int, amount: Decimal,
                    entry_date, reference: str, details: str) -> int:
        """
        Post one balanced double-entry transaction (one debit leg, one credit
        leg, same amount, same batch). Returns the batch number used.

        Raises RentalLedgerException if either account doesn't exist or amount
        is not positive — caller is expected to be inside an atomic() block so
        this propagates as a full rollback.
        """
        if amount <= 0:
            raise RentalLedgerException(f"Cannot post a non-positive amount: {amount}")

        try:
            debit_account = GLMast.objects.select_for_update().get(accno=debit_accno)
            credit_account = GLMast.objects.select_for_update().get(accno=credit_accno)
        except GLMast.DoesNotExist as exc:
            raise RentalLedgerException(
                f"GL account not found (debit={debit_accno}, credit={credit_accno}). "
                "Run the setup_rental_gl_accounts management command / configure "
                "RentalSettings before accepting live transactions."
            ) from exc

        param, _ = GLParam.objects.select_for_update().get_or_create(pk=1)
        param.batchno += 1
        param.save(update_fields=['batchno', 'updated_at'])
        batchno = param.batchno
        curperiod = param.curperiod

        common = dict(
            batchno=batchno, date=entry_date, time=timezone.now().time(),
            source='S', reference=reference[:10], details=details[:30], amount=amount,
        )
        GLTran.objects.create(accno=debit_accno, type='D', **common)
        GLTran.objects.create(accno=credit_accno, type='C', **common)

        LedgerPostingService._apply_period_balance(debit_account, curperiod, 'D', amount)
        LedgerPostingService._apply_period_balance(credit_account, curperiod, 'C', amount)

        logger.info(
            "gas.gl_posted batch=%s debit=%s credit=%s amount=%s reference=%s",
            batchno, debit_accno, credit_accno, amount, reference,
        )
        return batchno


class RentalService:
    """Checkout/return lifecycle for LPG cylinder rentals."""

    @staticmethod
    def _require_gl_accounts(settings_row: RentalSettings, *fields):
        missing = [f for f in fields if getattr(settings_row, f) is None]
        if missing:
            raise RentalLedgerException(
                f"RentalSettings is missing GL account mapping for: {', '.join(missing)}. "
                "Configure these before accepting live transactions."
            )

    @staticmethod
    @transaction.atomic
    def checkout_cylinder(*, debtor, stock_item: StockItem, quantity: Decimal,
                           deposit_amount: Decimal, user, reference: str = '') -> RentalTransaction:
        logger.info(
            "gas.checkout_attempt debtor=%s stock_item=%s qty=%s deposit=%s user=%s",
            debtor.pk, stock_item.pk, quantity, deposit_amount, getattr(user, 'pk', None),
        )

        if stock_item.available_quantity < quantity:
            logger.warning(
                "gas.checkout_failed reason=insufficient_stock stock_item=%s available=%s requested=%s",
                stock_item.pk, stock_item.available_quantity, quantity,
            )
            raise RentalStockException(
                f"Not enough {stock_item.description} in stock "
                f"(available: {stock_item.available_quantity}, requested: {quantity})"
            )

        cutoff = timezone.now() - timedelta(seconds=DOUBLE_SUBMIT_WINDOW_SECONDS)
        duplicate = RentalTransaction.objects.filter(
            debtor=debtor, stock_item=stock_item, quantity=quantity,
            deposit_amount=deposit_amount, created_at__gte=cutoff,
        ).exists()
        if duplicate:
            logger.warning(
                "gas.checkout_failed reason=double_submit debtor=%s stock_item=%s",
                debtor.pk, stock_item.pk,
            )
            raise RentalStateException(
                "An identical rental checkout was just submitted — this looks like a "
                "double-click, not a new request. Wait a moment and check the rental list "
                "before retrying."
            )

        settings_row = RentalSettings.get_solo()
        RentalService._require_gl_accounts(settings_row, 'deposits_held_accno', 'cash_accno')

        stock_item.quantity_on_hand -= quantity
        stock_item.save(update_fields=['quantity_on_hand'])

        rental = RentalTransaction.objects.create(
            debtor=debtor, stock_item=stock_item, quantity=quantity,
            deposit_amount=deposit_amount, checkout_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=settings_row.overdue_threshold_days),
        )

        try:
            batchno = LedgerPostingService.post_entry(
                debit_accno=settings_row.cash_accno,
                credit_accno=settings_row.deposits_held_accno,
                amount=deposit_amount,
                entry_date=rental.checkout_date,
                reference=reference or f"RENT{rental.pk}",
                details=f"Deposit held - {debtor.dname}"[:30],
            )
        except RentalLedgerException:
            logger.error(
                "gas.checkout_gl_post_failed rental=%s — rolling back full transaction",
                rental.pk,
            )
            raise

        rental.gl_batchno_checkout = batchno
        rental.save(update_fields=['gl_batchno_checkout'])

        logger.info("gas.checkout_succeeded rental=%s gl_batch=%s", rental.pk, batchno)
        return rental

    @staticmethod
    @transaction.atomic
    def return_cylinder(*, rental_id: int, reconciliation_state: str, user,
                         replacement_unit_price: Decimal = None,
                         reference: str = '') -> RentalTransaction:
        logger.info(
            "gas.return_attempt rental=%s state=%s user=%s",
            rental_id, reconciliation_state, getattr(user, 'pk', None),
        )

        try:
            rental = RentalTransaction.objects.select_for_update().get(pk=rental_id)
        except RentalTransaction.DoesNotExist:
            logger.warning("gas.return_failed reason=no_matching_rental rental=%s", rental_id)
            raise RentalStateException("No matching open rental found")

        if rental.status != RentalTransaction.STATUS_OPEN:
            logger.warning(
                "gas.return_failed reason=already_returned rental=%s current_state=%s",
                rental_id, rental.reconciliation_state,
            )
            raise RentalStateException("This rental was already returned")

        settings_row = RentalSettings.get_solo()
        today = timezone.now().date()
        reference = reference or f"RENT{rental.pk}"
        batchno = None

        if reconciliation_state == RentalTransaction.RECON_REFUNDED:
            RentalService._require_gl_accounts(settings_row, 'deposits_held_accno', 'cash_accno')
            batchno = LedgerPostingService.post_entry(
                debit_accno=settings_row.deposits_held_accno,
                credit_accno=settings_row.cash_accno,
                amount=rental.deposit_amount,
                entry_date=today, reference=reference,
                details=f"Deposit refund - {rental.debtor.dname}"[:30],
            )
            rental.stock_item.quantity_on_hand += rental.quantity
            rental.stock_item.save(update_fields=['quantity_on_hand'])

        elif reconciliation_state == RentalTransaction.RECON_WRITTEN_OFF:
            RentalService._require_gl_accounts(settings_row, 'deposits_held_accno', 'writeoff_income_accno')
            batchno = LedgerPostingService.post_entry(
                debit_accno=settings_row.deposits_held_accno,
                credit_accno=settings_row.writeoff_income_accno,
                amount=rental.deposit_amount,
                entry_date=today, reference=reference,
                details=f"Deposit written off - {rental.debtor.dname}"[:30],
            )
            # Cylinder was not returned — stock stays as-is, it was never given back.

        elif reconciliation_state == RentalTransaction.RECON_DISPUTED:
            # No financial movement while a dispute is unresolved — flag only.
            # is_reconciled (ReconciliationMixin) stays False until resolved.
            pass

        elif reconciliation_state == RentalTransaction.RECON_BILLED_FOR_REPLACEMENT:
            if replacement_unit_price is None:
                raise RentalStateException(
                    "billed_for_replacement requires replacement_unit_price"
                )
            RentalService._require_gl_accounts(
                settings_row, 'deposits_held_accno', 'sales_revenue_accno', 'vat_output_accno',
            )
            totals = CalculationService.calculate_line_totals(
                quantity=rental.quantity, unit_price=replacement_unit_price,
            )
            # Held deposit is applied against the replacement charge. If the
            # amounts differ, staff must reconcile the difference manually —
            # not silently absorbed here.
            if totals['line_total'] != rental.deposit_amount:
                logger.warning(
                    "gas.replacement_amount_mismatch rental=%s deposit=%s charge=%s "
                    "— reconcile the difference manually",
                    rental.pk, rental.deposit_amount, totals['line_total'],
                )
            batchno = LedgerPostingService.post_entry(
                debit_accno=settings_row.deposits_held_accno,
                credit_accno=settings_row.sales_revenue_accno,
                amount=totals['line_total_before_vat'],
                entry_date=today, reference=reference,
                details=f"Replacement sale - {rental.debtor.dname}"[:30],
            )
            if totals['vat_amount'] > 0:
                LedgerPostingService.post_entry(
                    debit_accno=settings_row.deposits_held_accno,
                    credit_accno=settings_row.vat_output_accno,
                    amount=totals['vat_amount'],
                    entry_date=today, reference=reference,
                    details=f"Replacement VAT - {rental.debtor.dname}"[:30],
                )
            # No stock_item quantity_on_hand change — the cylinder already left
            # inventory at original checkout. Decrementing again here would
            # double-count against a unit that was never restocked.

        else:
            raise RentalStateException(f"Unknown reconciliation_state: {reconciliation_state}")

        rental.status = RentalTransaction.STATUS_RETURNED
        rental.returned_date = today
        rental.reconciliation_state = reconciliation_state
        rental.gl_batchno_return = batchno
        if reconciliation_state != RentalTransaction.RECON_DISPUTED:
            rental.is_reconciled = True
            rental.reconciled_at = timezone.now()
            rental.reconciled_by = user
        rental.save(update_fields=[
            'status', 'returned_date', 'reconciliation_state', 'gl_batchno_return',
            'is_reconciled', 'reconciled_at', 'reconciled_by',
        ])

        logger.info(
            "gas.return_succeeded rental=%s state=%s gl_batch=%s",
            rental.pk, reconciliation_state, batchno,
        )
        return rental
