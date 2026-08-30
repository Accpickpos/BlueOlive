"""
Debtors services.
Business logic for debtor transactions and operations.
"""

from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import F, Q, Sum

from .models import Darea, Debtopen, Debtor, DebtorAudit, DebtorTransaction, Dpdc


class DebtorService:
    """Service class for debtor operations."""

    @staticmethod
    def calculate_age_analysis(debtor):
        """Calculate age analysis for a debtor."""
        return {
            "dno": debtor.dno,
            "dname": debtor.dname,
            "dcontact": debtor.dcontact,
            "dtel": debtor.dtel,
            "dclimit": debtor.dclimit,
            "current": debtor.dcrnt,
            "days_30": debtor.d30,
            "days_60": debtor.d60,
            "days_90": debtor.d90,
            "days_120": debtor.d120,
            "days_150": debtor.d150,
            "days_180": debtor.d180,
            "total_balance": debtor.total_balance,
            "overdue_balance": debtor.overdue_balance,
            "ddatlpd": debtor.ddatlpd,
            "damtlpd": debtor.damtlpd,
        }

    @staticmethod
    def get_debtors_summary():
        """Get summary statistics for all debtors."""
        debtors = Debtor.objects.all()

        total_debtors = debtors.count()
        blocked_debtors = debtors.filter(blockflag="Y").count()
        active_debtors = total_debtors - blocked_debtors

        aggregates = debtors.aggregate(
            total_balance=Sum(
                F("dcrnt")
                + F("d30")
                + F("d60")
                + F("d90")
                + F("d120")
                + F("d150")
                + F("d180")
            ),
            current_balance=Sum("dcrnt"),
            overdue_30=Sum("d30"),
            overdue_60=Sum("d60"),
            overdue_90=Sum("d90"),
            overdue_120=Sum(F("d120") + F("d150") + F("d180")),
            total_credit_limit=Sum("dclimit"),
        )

        total_balance = aggregates["total_balance"] or Decimal("0.00")
        total_credit_limit = aggregates["total_credit_limit"] or Decimal("0.00")

        # Calculate utilization percentage
        utilization_percentage = (
            float(total_credit_limit) / 100 if total_credit_limit > 0 else 0
        )

        return {
            "total_debtors": total_debtors,
            "active_debtors": active_debtors,
            "blocked_debtors": blocked_debtors,
            "total_balance": total_balance,
            "current_balance": aggregates["current_balance"] or Decimal("0.00"),
            "overdue_30": aggregates["overdue_30"] or Decimal("0.00"),
            "overdue_60": aggregates["overdue_60"] or Decimal("0.00"),
            "overdue_90": aggregates["overdue_90"] or Decimal("0.00"),
            "overdue_120_plus": aggregates["overdue_120"] or Decimal("0.00"),
            "total_credit_limit": total_credit_limit,
            "utilization_percentage": utilization_percentage,
            "total_receivable": total_balance,
            "aging_summary": {
                "current": aggregates["current_balance"] or Decimal("0.00"),
                "days_30": aggregates["overdue_30"] or Decimal("0.00"),
                "days_60": aggregates["overdue_60"] or Decimal("0.00"),
                "days_90": aggregates["overdue_90"] or Decimal("0.00"),
                "days_120_plus": aggregates["overdue_120"] or Decimal("0.00"),
            },
            "critical_aging": aggregates["overdue_120"] or Decimal("0.00"),
        }

    @staticmethod
    def post_debtran(
        debtor,
        dtype,
        dttot,
        dtsub=None,
        dtgst=None,
        ordno="",
        custref="",
        del1="",
        del2="",
        del3="",
        del4="",
        transaction_date=None,
        source_type="MANUAL",
        source_reference="",
        age_period="0",
    ):
        """
        Post a transaction to the debtor's account (DEBTRAN).
        Updates debtor balance and creates transaction record.

        Args:
            debtor: Debtor instance
            dtype: Transaction type (IN=Invoice, CN=Credit Note, RCP=Receipt, etc.)
            dttot: Total amount
            dtsub: Amount excl VAT
            dtgst: VAT amount
            ordno: Order number
            custref: Customer reference
            del1-4: Delivery details
            transaction_date: Date of the transaction (defaults to today)
            source_type: One of DebtorTransaction.SOURCE_CHOICES
            source_reference: Link to the originating record (e.g. invoice_number)
            age_period: Debtopen.ageflag bucket ("0".."4") the Open Item row
                (if any is created for this transaction) is posted into.
                Manual §2.2 "Debit/Credit Journal for Open Item Debtors":
                "The total value of the journal may only be allocated to
                ONE ageing period" — callers that let the user choose a
                period (post_journal) pass it through here; everything
                else defaults to "0" (Current), same as before this param
                existed.
        """
        if debtor.is_blocked:
            raise ValueError(f"Account {debtor.dno} is blocked")

        # Calculate defaults if not provided
        if dtsub is None:
            dtsub = dttot
        if dtgst is None:
            dtgst = Decimal("0.00")

        # select_for_update() requires an active transaction on whatever
        # connection `debtor` is routed to. debtor is a shop-app model, so
        # that's the tenant's own DB alias — never "default" — and tenant
        # connections run in true driver-level autocommit
        # (tenancy/utils.py sets ISOLATION_LEVEL_AUTOCOMMIT), so a bare
        # transaction.atomic() (which only opens a transaction on
        # "default") leaves the tenant connection un-transacted and
        # select_for_update() raises TransactionManagementError. Using the
        # alias debtor was actually loaded on opens the transaction on the
        # right connection.
        alias = debtor._state.db or "default"
        with transaction.atomic(using=alias):
            # Lock the debtor row to prevent concurrent transaction number
            # generation
            debtor = Debtor.objects.select_for_update().get(pk=debtor.pk)

            # Create sequential transaction number (within lock to prevent duplicates)
            last_tran = (
                DebtorTransaction.objects.filter(debtor=debtor)
                .order_by("-transaction_number")
                .first()
            )
            new_dtrano = (
                str(int(last_tran.transaction_number) + 1).zfill(6)
                if last_tran
                else "000001"
            )

            # Create debtor transaction (DEBTRAN). dttot/dtsub/dtgst are
            # always passed in as positive magnitudes (matching every
            # existing caller, e.g. Invoice.post()'s dtype="IN"), but
            # DebtorTransaction.clean() requires CN/CR/RF transactions to
            # be *stored* with a negative total_amount ("Credit
            # transactions should have negative amounts") — flip the sign
            # only for storage here; the balance_change calc below still
            # uses the original positive dttot.
            stored_sign = Decimal("-1") if dtype in ["CN", "CR", "RF"] else Decimal("1")
            trans = DebtorTransaction.objects.create(
                debtor=debtor,
                transaction_number=new_dtrano,
                transaction_type=dtype,
                transaction_date=transaction_date or date.today(),
                subtotal=dtsub * stored_sign,
                vat_amount=dtgst * stored_sign,
                total_amount=dttot * stored_sign,
                vat_status="S",  # Default to Taxable
                source_type=source_type,
                source_reference=source_reference,
                order_number=ordno,
                customer_reference=custref,
                description_line1=del1,
                description_line2=del2,
                description_line3=del3,
                description_line4=del4,
            )

            # Determine if transaction increases or decreases balance
            if dtype in ["IN", "DM"]:  # Invoice, Debit Memo
                balance_change = dttot
            elif dtype in ["CN", "CM"]:  # Credit Note, Credit Memo
                balance_change = -dttot
            elif dtype in ["RCP", "JC"]:  # Receipt, Journal Credit
                balance_change = -dttot
            else:
                balance_change = dttot

            # Update debtor balance (goes to current)
            debtor.dcrnt += balance_change
            debtor.dsalesm += dttot if dtype == "IN" else Decimal("0.00")
            debtor.dsalesy += dttot if dtype == "IN" else Decimal("0.00")
            debtor.save()

            # Create open item record (DEBTOPEN) for Open Item accounts only.
            # BBF accounts track balance purely via the aging buckets updated
            # above (dcrnt/d30/.../d180) — they don't need per-transaction
            # tracking. Open Item accounts need EVERY transaction individually
            # trackable until matched/settled (manual: "all outstanding and
            # unmatched transaction types are listed"; receipts "must be
            # allocated to specific transactions"). This condition was
            # previously inverted (`!= 'O'`), which meant Open Item debtors —
            # the ones this mechanism exists for — never got any open-item
            # records at all, breaking enquiry screens and receipt allocation
            # for that account type entirely.
            if debtor.acctype == "O":
                Debtopen.objects.create(
                    dno=debtor,
                    dtrano=new_dtrano,
                    type=dtype,
                    date=date.today(),
                    total=abs(dttot),
                    balancedue=abs(dttot) if balance_change > 0 else Decimal("0.00"),
                    ageflag=age_period,
                    posted="Y",
                )

            # Create audit record (DEBTORAUD)
            DebtorAudit.objects.create(
                dno=debtor,
                dtrano=new_dtrano,
                type=dtype,
                thistype=dtype,
                thistran=new_dtrano,
                date=date.today(),
                amount=dttot,
            )

        return trans

    @staticmethod
    @transaction.atomic
    def post_receipt(
        debtor, amount, amount_due=None, allocations=None, ordno="", custref=""
    ):
        """
        Post a receipt (payment) to the debtor's account.

        Args:
            debtor: Debtor instance
            amount: Actual amount tendered/received
            amount_due: Balance Brought Forward debtors only — manual §1
                "2. Receipts on Account": "Accpick will automatically
                calculate the settlement discount amount. This is the
                difference between the amount due and the amount
                tendered." When given, the FULL amount_due clears the
                balance (posted as dttot) and the difference is recorded
                as settlement_discount on the transaction — the
                amount-difference-to-percent direction, opposite of
                CalculationService.apply_settlement_discount (which goes
                percent-to-amount and isn't the right tool for this flow).
                When omitted, behaves exactly as before: `amount` alone is
                posted, no discount — fully backward compatible.
            allocations: Open Item debtors only — list of
                {'open_item_id', 'amount', 'settlement_discount'}
                dicts. Manual: payment is "allocated to the correct ageing
                periods" line-by-line against specific open transactions,
                with "No Settlement Discount on part payments". Applied via
                apply_receipt_allocation against caller-specified Debtopen
                rows belonging to this debtor.
            ordno: Order reference
            custref: Customer reference
        """
        if debtor.is_blocked:
            raise ValueError(f"Account {debtor.dno} is blocked")

        amount = Decimal(str(amount))
        if amount <= 0:
            raise ValueError("Receipt amount must be positive")

        settlement_discount = Decimal("0.00")
        post_total = amount

        if amount_due is not None:
            amount_due = Decimal(str(amount_due))
            if amount_due < amount:
                raise ValueError("Amount due cannot be less than amount tendered")
            settlement_discount = amount_due - amount
            post_total = amount_due

        # Create receipt transaction. dttot is the full amount cleared
        # against the balance (amount_due when given, else the amount
        # tendered) — this is what makes the settlement discount "free"
        # money from the debtor's perspective rather than a partial payment.
        trans = DebtorService.post_debtran(
            debtor=debtor,
            dtype="RCP",
            dttot=post_total,
            dtsub=post_total,
            dtgst=Decimal("0.00"),
            ordno=ordno,
            custref=custref,
        )
        if settlement_discount:
            trans.settlement_discount = settlement_discount
            trans.save(update_fields=["settlement_discount"])

        # Update payment tracking
        debtor.ddatlpd = date.today()
        debtor.damtlpd = amount
        debtor.save()

        if debtor.acctype == "O" and allocations:
            for alloc in allocations:
                open_item = Debtopen.objects.select_for_update().get(
                    pk=alloc["open_item_id"], dno=debtor
                )
                # 'amount' matches DebteopenViewSet.allocate_receipt's
                # pre-existing allocations-list contract — kept the same key
                # name here since both routes feed apply_receipt_allocation.
                DebtorService.apply_receipt_allocation(
                    open_item=open_item,
                    amount_paid=alloc["amount"],
                    settlement_discount=alloc.get("settlement_discount", 0),
                    receipt_transaction=trans,
                )

        return trans

    @staticmethod
    @transaction.atomic
    def apply_receipt_allocation(
        open_item, amount_paid, settlement_discount, receipt_transaction
    ):
        """
        Allocate part of a receipt against one open item (DEBTOPEN row).

        Manual §1 "2. Receipts on Account" (Open Item debtors — see also the
        "Full Payment [*] vs Part Payment" note): a settlement discount is
        only permitted when the allocation fully settles the open item's
        balance due — "No Settlement Discount on part payments". Mirrors
        apps.creditors.OpenItemAllocationSerializer's validation rule, but
        (unlike apps.creditors' open_item_allocation_post_save signal, which
        only subtracts amount_paid) correctly subtracts
        amount_paid + settlement_discount together when reducing the open
        item's balance, so a discounted full settlement actually zeroes out.

        Used both by DebtorService.post_receipt (Open Item branch) and
        DebteopenViewSet.allocate_receipt, so there's one place this rule
        lives rather than two independently-maintained copies.
        """
        from .models import ReceiptAllocation

        amount_paid = Decimal(str(amount_paid))
        settlement_discount = Decimal(str(settlement_discount or 0))

        if amount_paid <= 0:
            raise ValueError("Allocation amount must be greater than zero")
        if settlement_discount < 0:
            raise ValueError("Settlement discount cannot be negative")

        total_applied = amount_paid + settlement_discount
        if total_applied > open_item.balancedue:
            raise ValueError(
                f"Allocation of {total_applied} exceeds open item balance of {open_item.balancedue}"
            )
        if settlement_discount > 0 and total_applied < open_item.balancedue:
            raise ValueError(
                "Settlement discount is not permitted on a partial payment — it may only "
                "be applied when the allocation fully settles the open item."
            )

        allocation = ReceiptAllocation.objects.create(
            receipt=receipt_transaction,
            open_item=open_item,
            amount_paid=amount_paid,
            settlement_discount=settlement_discount,
        )

        open_item.balancedue -= total_applied
        open_item.save(update_fields=["balancedue"])

        DebtorAudit.objects.create(
            dno=open_item.dno,
            dtrano=open_item.dtrano,
            type=open_item.type,
            thistype="AL",
            thistran=receipt_transaction.transaction_number,
            date=date.today(),
            amount=amount_paid,
        )

        return allocation

    @staticmethod
    @transaction.atomic
    def post_journal(debtor, journal_type, amount, custref="", age_period="0"):
        """
        Post a debit or credit journal adjustment to the debtor's account.

        Args:
            debtor: Debtor instance
            journal_type: 'JD' (Journal Debit, increases balance owing) or
                          'JC' (Journal Credit, reduces balance owing)
            amount: Journal amount (positive)
            custref: Customer reference / reason for the journal
            age_period: Open Item accounts only — manual §2.2 "Debit/Credit
                Journal for Open Item Debtors": "The total value of the
                journal may only be allocated to ONE ageing period."
                One of Debtopen.AGEING_CHOICES ("0"=Current .. "4"=120+
                Days). Ignored for Balance Brought Forward accounts (no
                Debtopen row is created for them).
        """
        if journal_type not in ("JD", "JC"):
            raise ValueError("journal_type must be 'JD' or 'JC'")

        if debtor.is_blocked:
            raise ValueError(f"Account {debtor.dno} is blocked")

        if amount <= 0:
            raise ValueError("Journal amount must be positive")

        # Manual §2.2: "enter a short explanation motivating the journal.
        # This information appears on the Debtor's Statement, the Journal
        # Transactions Report and on the General Ledger Integration" —
        # implies it's expected, not optional, for an audit trail entry.
        if not custref or not custref.strip():
            raise ValueError("A reference/motivation is required for journal entries")

        valid_age_periods = {choice[0] for choice in Debtopen.AGEING_CHOICES}
        if age_period not in valid_age_periods:
            raise ValueError(f"age_period must be one of {sorted(valid_age_periods)}")

        return DebtorService.post_debtran(
            debtor=debtor,
            dtype=journal_type,
            dttot=amount,
            dtsub=amount,
            dtgst=Decimal("0.00"),
            custref=custref,
            age_period=age_period,
        )

    @staticmethod
    @transaction.atomic
    def convert_account_category(debtor, new_category):
        """
        Manual §Maintenance "Account Category Conversions" (Open Item <->
        Balance Brought Forward):

        - Open Item -> BBF: "confirm conversion from Open Item to Balance
          Brought Forward and [Yes] to clear all open item transactions" —
          the aggregate ageing buckets (dcrnt/d30/.../d180) already carry
          the correct balance (they're maintained for every account
          regardless of acctype — see post_debtran), so the per-transaction
          Debtopen rows are no longer needed once acctype stops being 'O'
          and are cleared.
        - BBF -> Open Item: "The Open Item Entry Screen will appear ... to
          enter all outstanding transactions" — auto-take-on one Debtopen
          row per non-zero aged bucket so the account has itemized open
          items to allocate receipts against going forward.

        Returns the updated debtor.
        """
        old_category = debtor.acctype
        debtor.acctype = new_category
        debtor.save(update_fields=["acctype"])

        if old_category == new_category:
            return debtor

        if old_category == "O" and new_category != "O":
            Debtopen.objects.filter(dno=debtor).delete()

        elif old_category != "O" and new_category == "O":
            # Debtopen.AGEING_CHOICES only has 5 buckets ("0".."4"), so
            # d120/d150/d180 all collapse into "4" (120+ Days) — same
            # grouping DebtorViewSet.age_analysis already uses.
            aged_buckets = [
                (debtor.dcrnt, "0"),
                (debtor.d30, "1"),
                (debtor.d60, "2"),
                (debtor.d90, "3"),
                (debtor.d120, "4"),
                (debtor.d150, "4"),
                (debtor.d180, "4"),
            ]
            last_tran = (
                DebtorTransaction.objects.filter(debtor=debtor)
                .order_by("-transaction_number")
                .first()
            )
            next_number = int(last_tran.transaction_number) + 1 if last_tran else 1
            for amount, ageflag in aged_buckets:
                if amount and amount > 0:
                    Debtopen.objects.create(
                        dno=debtor,
                        dtrano=str(next_number).zfill(6),
                        type="JD",
                        date=date.today(),
                        total=amount,
                        balancedue=amount,
                        ageflag=ageflag,
                        posted="Y",
                    )
                    next_number += 1

        return debtor

    @staticmethod
    def calculate_interest(
        debtor, rate=0.01, start_period=2, charge_credit_balances=False
    ):
        """
        Calculate interest on overdue balances.

        Args:
            debtor: Debtor instance
            rate: Monthly interest rate (default 1%)
            start_period: Period from which to charge interest
                         (2=30days, 3=60days, etc.)
            charge_credit_balances: manual §2.2 "Pay Interest on Credit
                Balances" Y/N option. When False (default, matching common
                practice), a bucket in credit (negative) contributes 0
                rather than reducing interest owed on other buckets. When
                True, buckets are summed as-is including negative ones.

        Returns:
            Decimal: Interest amount
        """
        if debtor.dintflag != "Y":
            return Decimal("0.00")

        buckets = []
        if start_period <= 2:
            buckets.append(debtor.d30)
        if start_period <= 3:
            buckets.append(debtor.d60)
        if start_period <= 4:
            buckets.append(debtor.d90)
        if start_period <= 5:
            buckets.append(debtor.d120)
        if start_period <= 6:
            buckets.append(debtor.d150)
        if start_period <= 7:
            buckets.append(debtor.d180)

        if charge_credit_balances:
            interest_base = sum(buckets, Decimal("0.00"))
        else:
            interest_base = sum((b for b in buckets if b > 0), Decimal("0.00"))

        interest = interest_base * Decimal(str(rate))
        return interest.quantize(Decimal("0.01"))

    @staticmethod
    @transaction.atomic
    def charge_interest_batch(rate=0.01, start_period=2, charge_credit_balances=False):
        """
        Charge interest on all debtors who have dintflag=Y.

        Returns:
            dict: Summary of interest charged
        """
        debtors = Debtor.objects.filter(dintflag="Y")

        total_interest = Decimal("0.00")
        debtors_charged = 0

        for debtor in debtors:
            interest = DebtorService.calculate_interest(
                debtor, rate, start_period, charge_credit_balances
            )

            if interest > 0:
                # Create interest transaction (INT type)
                DebtorService.post_debtran(
                    debtor=debtor,
                    dtype="INT",
                    dttot=interest,
                    dtsub=interest,
                    dtgst=Decimal("0.00"),
                    custref="Monthly Interest Charge",
                )

                total_interest += interest
                debtors_charged += 1

        return {
            "debtors_charged": debtors_charged,
            "total_interest": total_interest,
        }

    @staticmethod
    def get_debtor_statement(debtor, start_date=None, end_date=None):
        """
        Generate debtor statement for a period.

        Args:
            debtor: Debtor instance
            start_date: Start date (default: first day of current month)
            end_date: End date (default: today)

        Returns:
            dict: Statement data
        """
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()

        # Get transactions for period
        transactions = DebtorTransaction.objects.filter(
            debtor=debtor,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date,
        ).order_by("transaction_date")

        # Calculate opening balance (transactions before start_date)
        opening_transactions = DebtorTransaction.objects.filter(
            debtor=debtor, transaction_date__lt=start_date
        ).aggregate(total=Sum("total_amount"))
        opening_balance = opening_transactions["total"] or Decimal("0.00")

        # Calculate closing balance
        period_total = transactions.aggregate(total=Sum("total_amount"))[
            "total"
        ] or Decimal("0.00")
        closing_balance = opening_balance + period_total

        return {
            "debtor": debtor,
            "opening_balance": opening_balance,
            "transactions": transactions,
            "closing_balance": closing_balance,
            "current_balance": debtor.dcrnt,
            "balance_30_days": debtor.d30,
            "balance_60_days": debtor.d60,
            "balance_90_days": debtor.d90,
            "balance_120_days": debtor.d120,
            "balance_150_days": debtor.d150,
            "balance_180_days": debtor.d180,
        }

    @staticmethod
    @transaction.atomic
    def age_balances():
        """
        Age all debtor balances by one period.
        This should be run at month-end.
        Shifts all aging buckets forward and resets current to zero.
        """
        debtors = Debtor.objects.all()

        for debtor in debtors:
            # Shift balances forward (age by one period)
            debtor.d180 = debtor.d150
            debtor.d150 = debtor.d120
            debtor.d120 = debtor.d90
            debtor.d90 = debtor.d60
            debtor.d60 = debtor.d30
            debtor.d30 = debtor.dcrnt
            debtor.dcrnt = Decimal("0.00")

            # Reset MTD stats but keep YTD
            debtor.dsalesm = Decimal("0.00")
            debtor.dprofitm = Decimal("0.00")

            debtor.save()

        return debtors.count()

    @staticmethod
    def check_credit_limit(debtor):
        """
        Check if debtor is over credit limit.

        Returns:
            dict: Credit limit status
        """
        total_balance = debtor.total_balance
        credit_limit = debtor.dclimit

        over_limit = total_balance > credit_limit
        available_credit = credit_limit - total_balance

        return {
            "dno": debtor.dno,
            "dname": debtor.dname,
            "dclimit": credit_limit,
            "total_balance": total_balance,
            "available_credit": available_credit,
            "over_limit": over_limit,
            "percentage_used": (
                (total_balance / credit_limit * 100) if credit_limit > 0 else 0
            ),
        }

    @staticmethod
    def get_top_customers(limit=10, period="month"):
        """
        Get top customers by sales value.

        Args:
            limit: Number of customers to return
            period: 'month', 'year', or 'all'

        Returns:
            QuerySet: Top debtors
        """
        if period == "month":
            field = "dsalesm"
        elif period == "year":
            field = "dsalesy"
        else:
            # All time - use YTD as proxy
            field = "dsalesy"

        return Debtor.objects.filter(is_active=True).order_by(f"-{field}")[:limit]
