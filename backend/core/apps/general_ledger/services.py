"""
General Ledger posting primitives.

GLPostingService is the shared double-entry posting engine for GLBatch
posting, Standing Journal posting, and Integration Transfer. It is a fresh
implementation, not a refactor of apps.gas.services.LedgerPostingService —
gas is a recently shipped, reviewed, tested module and rewiring it to share
this service would earn no functional benefit while risking a regression in
tested behavior for the sake of avoiding ~40 lines of duplication. The core
math (_apply_period_balance) is intentionally identical between the two; if
gas's posting needs ever diverge from this service's, that is fine — they
are independent by design.

No signals.py / apps.py ready() hook exists for this app and none should be
added speculatively. Every posting path here (GLBatch.post, standing journal
post_due, Integration transfer) is an explicit service call triggered by an
API action — mirroring apps.gas's "service call from the originating flow,
not signal-driven" precedent.
"""

import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from .exceptions import GLPostingException
from .models import GLMast, GLParam, GLTran

logger = logging.getLogger(__name__)


class GLPostingService:
    """Posts double-entry GL transactions directly to GLTran and updates
    GLMast's period balances. Writes with source='S' (System) by default —
    the manual GLBatch staging table is a separate capture/review step that
    calls into post_batch() once its own balance check has passed; it does
    not go through GLBatch again itself."""

    @staticmethod
    def _apply_period_balance(
        account: GLMast, period: int, leg_type: str, amount: Decimal
    ):
        """Update GLMast's balance for one leg of a transaction, for the
        given period.

        Standard double-entry: a debit increases a debit-normal account and
        decreases a credit-normal account; a credit does the opposite. Each
        period{N} field is stored "same-side-positive" — positive means the
        account's own drorcr side, regardless of whether drorcr is D or C.
        """
        field_name = f"period{period}"
        current = getattr(account, field_name)

        same_side = leg_type == account.drorcr
        delta = amount if same_side else -amount

        setattr(account, field_name, current + delta)
        account.save(update_fields=[field_name, "updated_at"])

    @staticmethod
    @transaction.atomic
    def post_entry(
        *,
        debit_accno: int,
        credit_accno: int,
        amount: Decimal,
        entry_date,
        reference: str,
        details: str,
        source: str = "S",
        period: int = None,
    ) -> int:
        """
        Post one balanced double-entry transaction (one debit leg, one
        credit leg, same amount, same batch). Returns the batch number used.

        Raises GLPostingException if either account doesn't exist or amount
        is not positive — caller is expected to be inside an atomic() block
        so this propagates as a full rollback.

        `period` defaults to GLParam.curperiod when not given (matches
        apps.gas's always-current-period behaviour); pass it explicitly to
        post into a specific period (e.g. a GLBatch row's own `period`
        field, or a standing journal's `stperiod`).
        """
        if amount <= 0:
            raise GLPostingException(f"Cannot post a non-positive amount: {amount}")

        try:
            debit_account = GLMast.objects.select_for_update().get(accno=debit_accno)
            credit_account = GLMast.objects.select_for_update().get(accno=credit_accno)
        except GLMast.DoesNotExist as exc:
            raise GLPostingException(
                f"GL account not found (debit={debit_accno}, credit={credit_accno}). "
                "Configure the correct account mapping before posting."
            ) from exc

        param, _ = GLParam.objects.select_for_update().get_or_create(pk=1)
        param.batchno += 1
        param.save(update_fields=["batchno", "updated_at"])
        batchno = param.batchno
        post_period = period if period is not None else param.curperiod

        common = dict(
            batchno=batchno,
            date=entry_date,
            time=timezone.now().time(),
            source=source,
            reference=reference[:10],
            details=details[:30],
            amount=amount,
        )
        GLTran.objects.create(accno=debit_accno, type="D", **common)
        GLTran.objects.create(accno=credit_accno, type="C", **common)

        GLPostingService._apply_period_balance(debit_account, post_period, "D", amount)
        GLPostingService._apply_period_balance(credit_account, post_period, "C", amount)

        logger.info(
            "general_ledger.gl_posted batch=%s debit=%s credit=%s amount=%s reference=%s",
            batchno,
            debit_accno,
            credit_accno,
            amount,
            reference,
        )
        return batchno

    @staticmethod
    @transaction.atomic
    def post_batch(lines: list) -> int:
        """
        Post an arbitrary set of balanced lines as one journal batch.

        Each line is a dict: {accno, type: "D"|"C", amount, date, reference,
        details, period (optional, defaults to GLParam.curperiod), source
        (optional, defaults to "S")}.

        Validates sum(debits) == sum(credits) BEFORE writing anything — this
        is the actual enforcement point for the spec's "only journals in
        balance will be saved" rule. Raises GLPostingException and performs
        zero database writes if the lines don't balance, or if any line has
        a non-positive amount, or if fewer than 2 lines are given.

        Returns the single batch number allocated for the whole set.
        """
        if len(lines) < 2:
            raise GLPostingException(
                "A journal batch needs at least two lines (one debit, one credit)."
            )

        total_debits = Decimal("0.00")
        total_credits = Decimal("0.00")
        for line in lines:
            amount = Decimal(str(line["amount"]))
            if amount <= 0:
                raise GLPostingException(
                    f"Cannot post a non-positive amount: {amount} "
                    f"(account {line['accno']})"
                )
            if line["type"] == "D":
                total_debits += amount
            elif line["type"] == "C":
                total_credits += amount
            else:
                raise GLPostingException(
                    f"Invalid line type {line['type']!r} — must be 'D' or 'C'."
                )

        if total_debits != total_credits:
            raise GLPostingException(
                f"Journal batch is not balanced: debits={total_debits}, "
                f"credits={total_credits}, difference={total_debits - total_credits}."
            )

        accnos = {line["accno"] for line in lines}
        accounts = {
            acc.accno: acc
            for acc in GLMast.objects.select_for_update().filter(accno__in=accnos)
        }
        missing = accnos - set(accounts.keys())
        if missing:
            raise GLPostingException(
                f"GL account(s) not found: {sorted(missing)}. "
                "Configure the correct account mapping before posting."
            )

        param, _ = GLParam.objects.select_for_update().get_or_create(pk=1)
        param.batchno += 1
        param.save(update_fields=["batchno", "updated_at"])
        batchno = param.batchno

        for line in lines:
            amount = Decimal(str(line["amount"]))
            post_period = line.get("period") or param.curperiod
            GLTran.objects.create(
                accno=line["accno"],
                type=line["type"],
                batchno=batchno,
                date=line.get("date") or timezone.now().date(),
                time=timezone.now().time(),
                source=line.get("source", "S"),
                reference=line.get("reference", "")[:10],
                details=line.get("details", "")[:30],
                amount=amount,
            )
            GLPostingService._apply_period_balance(
                accounts[line["accno"]], post_period, line["type"], amount
            )

        logger.info(
            "general_ledger.gl_batch_posted batch=%s lines=%s total=%s",
            batchno,
            len(lines),
            total_debits,
        )
        return batchno
