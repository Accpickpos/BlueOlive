"""
Cash Book Module Services - Compatibility & Delegation Layer
Acts as a facade to business_services.py for backward compatibility
All business logic delegated to business_services.py for maintainability

IMPORTANT: This is a compatibility layer. All new code should import from business_services.py directly.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Optional, Tuple

from django.conf import settings
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.utils import timezone

from .business_services import (
    CashBookReportService,
    CashBookTransactionService,
    CashBookVATService,
    CategoryBalanceService,
    UnpresentedChequeService,
)
from .models import (
    BankCharge,
    BankDeposit,
    BankReconciliation,
    BankReconciliationItem,
    BankTransfer,
    CashBookTransaction,
    CashWithdrawal,
    ExpenseCategoryBalance,
    IncomeCategoryBalance,
    InterestReceived,
    OtherExpense,
    OtherIncome,
    UnpresentedCheque,
)

# ============================================================================
# COMPATIBILITY EXPORTS - These delegate to business_services.py
# ============================================================================


class VATService:
    """
    DEPRECATED: Use CashBookVATService from business_services.py

    This class provides backward compatibility only.
    All new code should use CashBookVATService directly.
    """

    @staticmethod
    def get_vat_rate():
        """Get current VAT rate from settings"""
        return Decimal(str(getattr(settings, "ACCPICK_VAT_RATE", "0.14")))

    @staticmethod
    def calculate_vat(amount: Decimal, tax_code: int, is_inclusive: bool) -> Decimal:
        """
        Calculate VAT amount for a transaction.

        DEPRECATED: Use CashBookVATService.calculate_tax_amount() instead

        Args:
            amount: Transaction amount
            tax_code: 1 for VAT applicable (14%), 2 for no VAT (0%)
            is_inclusive: True if amount includes VAT, False if exclusive

        Returns:
            VAT amount
        """
        return CashBookVATService.calculate_tax_amount(amount, tax_code, is_inclusive)

    @staticmethod
    def get_net_amount(
        amount: Decimal, tax_code: int, is_inclusive: bool = True
    ) -> Decimal:
        """
        DEPRECATED: Use CashBookVATService.get_net_amount() instead
        Get net amount before VAT
        """
        return CashBookVATService.get_net_amount(amount, tax_code)


class TransactionNumberGenerator:
    """
    DEPRECATED: Use CashBookTransactionService._generate_transaction_number() instead

    Note: This class uses a different format than business_services.
    New code should use the spec-compliant format from business_services.
    """

    PREFIXES = {
        "RECEIPT": "RCP",
        "PAYMENT": "PAY",
        "DEPOSIT": "DEP",
        "WITHDRAWAL": "WDL",
        "TRANSFER": "TRN",
        "BANK_CHARGE": "BCH",
        "INTEREST": "INT",
        "OTHER_INCOME": "INC",
        "OTHER_EXPENSE": "EXP",
    }

    @staticmethod
    def generate(
        transaction_type: str, transaction_date: Optional[datetime] = None
    ) -> str:
        """
        DEPRECATED: Use CashBookTransactionService methods instead

        Generate unique transaction number using legacy format: PREFIX-YYYYMMDD-00001

        Note: This format differs from spec. The spec requires YYYYMMDDNN format.
        For new code, use CashBookTransactionService._generate_transaction_number()

        Args:
            transaction_type: Type of transaction
            transaction_date: Date for transaction (defaults to today)

        Returns:
            Unique transaction number (legacy format)
        """
        if transaction_date is None:
            transaction_date = timezone.now().date()
        elif hasattr(transaction_date, "date"):
            transaction_date = transaction_date.date()

        prefix = TransactionNumberGenerator.PREFIXES.get(transaction_type, "TXN")

        # Count existing transactions of this type on this date
        count = CashBookTransaction.objects.filter(
            transaction_type=transaction_type, transaction_date=transaction_date
        ).count()

        return f"{prefix}-{transaction_date.strftime('%Y%m%d')}-{count + 1:05d}"


class BalanceCalculationService:
    """
    Service for calculating and managing category balances.

    This class provides backward compatibility and integration with signals.
    Business logic delegated to business_services.py
    """

    @staticmethod
    def update_running_balances(from_transaction: Optional[CashBookTransaction] = None):
        """
        Recalculate running balances for all transactions.

        This method handles cash/bank running balance calculations.
        Category balance updates are handled by update_category_balances().

        Args:
            from_transaction: Starting transaction or None to recalculate all
        """
        if from_transaction:
            # Get the previous transaction to initialize balances
            prev_txn = (
                CashBookTransaction.objects.filter(
                    transaction_date__lt=from_transaction.transaction_date
                )
                .order_by("-transaction_date", "-transaction_number")
                .first()
            )

            if prev_txn:
                cash_balance = prev_txn.running_balance_cash
                bank_balance = prev_txn.running_balance_bank
            else:
                cash_balance = Decimal("0")
                bank_balance = Decimal("0")

            # Get transactions from this point onward
            txns = CashBookTransaction.objects.filter(
                transaction_date__gte=from_transaction.transaction_date
            ).order_by("transaction_date", "transaction_number")
        else:
            cash_balance = Decimal("0")
            bank_balance = Decimal("0")
            txns = CashBookTransaction.objects.all().order_by(
                "transaction_date", "transaction_number"
            )

        # Update balances
        for txn in txns:
            if txn.is_debit:
                if txn.account_type == "CASH":
                    cash_balance += txn.amount
                else:
                    bank_balance += txn.amount
            elif txn.is_credit:
                if txn.account_type == "CASH":
                    cash_balance -= txn.amount
                else:
                    bank_balance -= txn.amount

            # .update() (not .save()) — this method IS the post_save handler's
            # own recalculation step; calling .save() here would re-fire
            # post_save on every transaction in the loop, which calls back
            # into this same method → infinite recursion.
            CashBookTransaction.objects.filter(pk=txn.pk).update(
                running_balance_cash=cash_balance, running_balance_bank=bank_balance
            )

    @staticmethod
    def get_current_balances() -> Dict[str, Decimal]:
        """Get current cash and bank balances"""
        last_txn = (
            CashBookTransaction.objects.all()
            .order_by("-transaction_date", "-transaction_number")
            .first()
        )

        if last_txn:
            return {
                "cash": last_txn.running_balance_cash,
                "bank": last_txn.running_balance_bank,
                "total": last_txn.running_balance_cash + last_txn.running_balance_bank,
            }

        return {"cash": Decimal("0"), "bank": Decimal("0"), "total": Decimal("0")}

    @staticmethod
    def update_category_balances(
        transaction: CashBookTransaction,
        value_excl_vat: Decimal = None,
        tax_amount: Decimal = None,
    ):
        """
        Update category MTD balances when transaction is created/modified.

        This delegates to CategoryBalanceService in business_services.py

        Args:
            transaction: The transaction being updated
            value_excl_vat: Amount excluding VAT
            tax_amount: VAT/Tax amount
        """
        if value_excl_vat is None:
            value_excl_vat = transaction.value_excl_vat
        if tax_amount is None:
            tax_amount = transaction.tax_amount

        # Delegate to business_services for category-specific updates
        if transaction.category_id:
            if transaction.audit_type in [1, 2]:  # Income
                CategoryBalanceService.update_income_category_balance(
                    transaction.category_id,
                    value_excl_vat,
                    tax_amount,
                    transaction.transaction_date,
                )
            elif transaction.audit_type in [3, 4]:  # Expenses
                CategoryBalanceService.update_expense_category_balance(
                    transaction.category_id,
                    value_excl_vat,
                    tax_amount,
                    transaction.transaction_date,
                )

    @staticmethod
    def get_account_balances() -> Dict[str, Dict[str, Decimal]]:
        """Get balances for each bank account"""
        accounts = (
            CashBookTransaction.objects.filter(account_type="BANK")
            .values("bank_account_number")
            .distinct()
        )

        balances = {}
        for account in accounts:
            account_num = account["bank_account_number"]
            last_txn = (
                CashBookTransaction.objects.filter(bank_account_number=account_num)
                .order_by("-transaction_date", "-transaction_number")
                .first()
            )

            balances[account_num] = {
                "balance": last_txn.running_balance_bank if last_txn else Decimal("0"),
                "unreconciled_count": CashBookTransaction.objects.filter(
                    bank_account_number=account_num, is_reconciled=False
                ).count(),
            }

        return balances


class TransactionService:
    """
    DEPRECATED: Use CashBookTransactionService from business_services.py

    Provides backward compatibility for legacy transaction creation methods.
    New code should use CashBookTransactionService.create_transaction() instead
    which is spec-compliant with proper VAT separation.
    """

    @staticmethod
    @db_transaction.atomic
    def create_other_income(
        transaction_date,
        income_category_id,
        amount: Decimal,
        description: str,
        is_vat_inclusive: bool = True,
        tax_code: int = 1,
        reference: str = "",
        paid_into: str = "CASH",
        bank_account_number: str = "",
        created_by: str = "system",
    ) -> OtherIncome:
        """
        Create an other income transaction (DEPRECATED).

        This method is maintained for backward compatibility.
        For new code, use CashBookTransactionService.create_transaction()
        with audit_type=1 or 2 (receivables/sundry income).

        Args:
            transaction_date: Date of transaction
            income_category_id: Income category ID
            amount: Transaction amount
            description: Transaction description
            is_vat_inclusive: Whether amount includes VAT
            tax_code: Tax code (1 for VAT, 2 for no VAT)
            reference: Optional reference
            paid_into: CASH or BANK
            bank_account_number: Bank account if paid into bank
            created_by: Username of creator

        Returns:
            Created OtherIncome instance
        """
        # Calculate VAT
        vat_amount = CashBookVATService.calculate_tax_amount(
            amount, tax_code, is_vat_inclusive
        )

        # Generate transaction number
        transaction_number = TransactionNumberGenerator.generate(
            "OTHER_INCOME", transaction_date
        )

        # Determine account type
        account_type = "BANK" if paid_into == "BANK" else "CASH"

        # Create base transaction
        base_transaction = CashBookTransaction.objects.create(
            transaction_type="OTHER_INCOME",
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            account_type=account_type,
            bank_account_number=bank_account_number,
            amount=amount,
            reference=reference,
            description=description,
            created_by=created_by,
        )

        # Create other income record
        other_income = OtherIncome.objects.create(
            transaction=base_transaction,
            income_category_id=income_category_id,
            is_vat_inclusive=is_vat_inclusive,
            vat_amount=vat_amount,
            tax_code=tax_code,
            paid_into=paid_into,
        )

        return other_income

    @staticmethod
    @db_transaction.atomic
    def create_other_expense(
        transaction_date,
        expense_category_id,
        amount: Decimal,
        description: str,
        is_vat_inclusive: bool = True,
        tax_code: int = 1,
        reference: str = "",
        paid_from: str = "CASH",
        bank_account_number: str = "",
        petty_cash_slip_number: str = "",
        created_by: str = "system",
    ) -> OtherExpense:
        """
        Create an other expense transaction (DEPRECATED).

        For new code, use CashBookTransactionService.create_transaction()
        with audit_type=3 or 4 (payables/expenses).
        """
        vat_amount = CashBookVATService.calculate_tax_amount(
            amount, tax_code, is_vat_inclusive
        )

        transaction_number = TransactionNumberGenerator.generate(
            "OTHER_EXPENSE", transaction_date
        )

        account_type = "BANK" if paid_from == "BANK" else "CASH"

        base_transaction = CashBookTransaction.objects.create(
            transaction_type="OTHER_EXPENSE",
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            account_type=account_type,
            bank_account_number=bank_account_number,
            amount=amount,
            reference=reference,
            description=description,
            created_by=created_by,
        )

        other_expense = OtherExpense.objects.create(
            transaction=base_transaction,
            expense_category_id=expense_category_id,
            is_vat_inclusive=is_vat_inclusive,
            vat_amount=vat_amount,
            tax_code=tax_code,
            paid_from=paid_from,
            petty_cash_slip_number=petty_cash_slip_number,
        )

        return other_expense

    @staticmethod
    @db_transaction.atomic
    def create_bank_deposit(
        transaction_date,
        bank_account_number: str,
        bank_name: str,
        cash_amount: Decimal = Decimal("0"),
        cheque_amount: Decimal = Decimal("0"),
        deposit_slip_number: str = "",
        branch: str = "",
        cash_breakdown: Optional[Dict] = None,
        reference: str = "",
        created_by: str = "system",
    ) -> BankDeposit:
        """Create a bank deposit transaction"""
        total_amount = cash_amount + cheque_amount

        transaction_number = TransactionNumberGenerator.generate(
            "DEPOSIT", transaction_date
        )

        base_transaction = CashBookTransaction.objects.create(
            transaction_type="DEPOSIT",
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            account_type="BANK",
            bank_account_number=bank_account_number,
            amount=total_amount,
            reference=reference,
            description="Bank deposit",
            created_by=created_by,
        )

        # Prepare deposit data
        deposit_data = {
            "transaction": base_transaction,
            "deposit_slip_number": deposit_slip_number,
            "bank_name": bank_name,
            "branch": branch,
            "cash_amount": cash_amount,
            "cheque_amount": cheque_amount,
        }

        # Add cash breakdown if provided
        if cash_breakdown:
            deposit_data.update(cash_breakdown)

        deposit = BankDeposit.objects.create(**deposit_data)

        return deposit

    @staticmethod
    def create_transaction_from_dict(data: dict) -> dict:
        """
        DEPRECATED: Use CashBookTransactionService.create_transaction() instead

        Create a transaction from a dictionary of data.

        Args:
            data: Dictionary containing transaction data

        Returns:
            Dictionary with success status and transaction data/error
        """
        try:
            transaction = CashBookTransactionService.create_transaction(
                transaction_date=data.get("transaction_date"),
                account_type=data.get("account_type"),
                is_debit=data.get("is_debit"),
                amount=Decimal(str(data.get("amount", 0))),
                transaction_type=data.get("transaction_type"),
                description=data.get("description"),
                reference=data.get("reference"),
                bank_details=data.get("bank_details"),
                category_id=data.get("category_id"),
                value_excl_vat=Decimal(str(data.get("value_excl_vat", 0))),
                tax_amount=Decimal(str(data.get("tax_amount", 0))),
                tax_code=data.get("tax_code", 2),
                created_by=data.get("created_by"),
            )
            return {"success": True, "transaction": transaction}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_transaction_with_details(transaction_id: int) -> dict:
        """
        DEPRECATED: Use ORM directly or CashBookTransactionService instead

        Get transaction with all related details.
        """
        try:
            transaction = CashBookTransaction.objects.get(id=transaction_id)
            return {
                "success": True,
                "transaction": transaction,
            }
        except CashBookTransaction.DoesNotExist:
            return {"success": False, "error": "Transaction not found"}


class SummaryService:
    """DEPRECATED: Use CashBookReportService from business_services.py"""

    @staticmethod
    def get_period_summary(start_date, end_date) -> Dict:
        """
        Get summary of transactions for a period.

        Uses CashBookReportService.get_monthly_summary() for business logic.

        Args:
            start_date: Start date for period
            end_date: End date for period

        Returns:
            Dictionary with summary data
        """
        queryset = CashBookTransaction.objects.filter(
            transaction_date__gte=start_date, transaction_date__lte=end_date
        )

        # Get opening balances
        opening_txn = (
            CashBookTransaction.objects.filter(transaction_date__lt=start_date)
            .order_by("-transaction_date", "-transaction_number")
            .first()
        )

        opening_cash = opening_txn.running_balance_cash if opening_txn else Decimal("0")
        opening_bank = opening_txn.running_balance_bank if opening_txn else Decimal("0")

        # Calculate totals by type
        from django.db.models import Sum

        receipts = queryset.filter(
            transaction_type__in=["RECEIPT", "DEPOSIT", "INTEREST", "OTHER_INCOME"]
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        payments = queryset.filter(
            transaction_type__in=[
                "PAYMENT",
                "WITHDRAWAL",
                "TRANSFER",
                "BANK_CHARGE",
                "OTHER_EXPENSE",
            ]
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # Get closing balances
        closing_txn = queryset.order_by(
            "-transaction_date", "-transaction_number"
        ).first()
        closing_cash = closing_txn.running_balance_cash if closing_txn else opening_cash
        closing_bank = closing_txn.running_balance_bank if closing_txn else opening_bank

        return {
            "start_date": start_date,
            "end_date": end_date,
            "opening_balance_cash": opening_cash,
            "opening_balance_bank": opening_bank,
            "opening_balance_total": opening_cash + opening_bank,
            "total_receipts": receipts,
            "total_payments": payments,
            "closing_balance_cash": closing_cash,
            "closing_balance_bank": closing_bank,
            "closing_balance_total": closing_cash + closing_bank,
            "transaction_count": queryset.count(),
            "net_change": (closing_cash + closing_bank) - (opening_cash + opening_bank),
        }

    @staticmethod
    def get_transaction_breakdown(start_date, end_date) -> Dict[str, Decimal]:
        """Get breakdown of transactions by type"""
        queryset = CashBookTransaction.objects.filter(
            transaction_date__gte=start_date, transaction_date__lte=end_date
        )

        from django.db.models import Sum

        breakdown = {}
        for txn_type, display in CashBookTransaction.TRANSACTION_TYPE_CHOICES:
            total = queryset.filter(transaction_type=txn_type).aggregate(
                total=Sum("amount")
            )["total"] or Decimal("0")
            breakdown[txn_type] = total

        return breakdown

    @staticmethod
    def get_summary_for_period(start_date: date, end_date: date) -> dict:
        """
        DEPRECATED: Use CashBookReportService.generate_period_summary() instead

        Get summary of transactions for a period.

        Args:
            start_date: Start date for period
            end_date: End date for period

        Returns:
            Dictionary with summary data
        """
        return CashBookReportService.generate_period_summary(start_date, end_date)

    @staticmethod
    def get_category_summary() -> list:
        """
        DEPRECATED: Use CashBookReportService.generate_category_summary() instead

        Get summary by category.

        Returns:
            List of category summaries
        """
        return CashBookReportService.generate_category_summary()

    @staticmethod
    def get_daily_summary(transaction_date: date) -> dict:
        """
        DEPRECATED: Use CashBookReportService methods instead

        Get summary for a specific day.

        Args:
            transaction_date: Date to summarize

        Returns:
            Dictionary with daily summary
        """
        transactions = CashBookTransaction.objects.filter(
            transaction_date=transaction_date
        ).order_by("transaction_number")

        total_debit = Decimal("0")
        total_credit = Decimal("0")
        total_vat = Decimal("0")

        for txn in transactions:
            if txn.is_debit:
                total_debit += txn.amount
            else:
                total_credit += txn.amount
            total_vat += txn.tax_amount or Decimal("0")

        return {
            "date": transaction_date,
            "transaction_count": transactions.count(),
            "total_debit": total_debit,
            "total_credit": total_credit,
            "net": total_debit - total_credit,
            "total_vat": total_vat,
        }


class ReconciliationService:
    """Service for bank reconciliation"""

    @staticmethod
    def get_outstanding_summary(bank_account_number: str) -> Dict[str, Decimal]:
        """
        Derive the reconciliation's outstanding-deposit/outstanding-cheque
        totals from transactions tagged 'P' (Pending) — the manual's
        "tagging" workflow: an operator tags each bank transaction that
        hasn't yet appeared on the bank statement, and reconciliation totals
        are summed from those tags rather than hand-typed. Outstanding
        cheques also folds in unpresented cheques from the dedicated
        UnpresentedCheque register (issued cheques tracked separately from
        the day-to-day CashBookTransaction feed).
        """
        pending = CashBookTransaction.objects.filter(
            account_type="BANK",
            bank_account_number=bank_account_number,
            bank_recon_tag="P",
            is_reconciled=False,
        )
        outstanding_deposits = sum(
            (t.amount for t in pending if t.is_debit), Decimal("0")
        )
        outstanding_cheques = sum(
            (t.amount for t in pending if t.is_credit), Decimal("0")
        )

        unpresented_total = UnpresentedCheque.objects.filter(
            is_presented=False
        ).aggregate(total=Sum("total"))["total"] or Decimal("0")
        outstanding_cheques += unpresented_total

        return {
            "outstanding_deposits": outstanding_deposits,
            "outstanding_cheques": outstanding_cheques,
            "pending_transaction_count": pending.count(),
        }

    @staticmethod
    def validate_reconciliation(reconciliation: BankReconciliation) -> Tuple[bool, str]:
        """
        Validate if reconciliation balances.

        Returns:
            Tuple of (is_valid, message)
        """
        calculated_balance = (
            reconciliation.closing_balance_per_statement
            + reconciliation.outstanding_deposits
            - reconciliation.outstanding_cheques
            + reconciliation.bank_errors
            - reconciliation.book_errors
        )

        difference = abs(calculated_balance - reconciliation.closing_balance_per_books)

        if difference < Decimal("0.01"):
            return True, "Reconciliation balances"

        return False, f"Reconciliation does not balance. Difference: {difference}"

    @staticmethod
    @db_transaction.atomic
    def complete_reconciliation(
        reconciliation: BankReconciliation, completed_by: str
    ) -> Tuple[bool, str]:
        """
        Complete a reconciliation and mark transactions as reconciled.

        Args:
            reconciliation: BankReconciliation instance
            completed_by: Username of person completing reconciliation

        Returns:
            Tuple of (success, message)
        """
        # Validate
        is_valid, message = ReconciliationService.validate_reconciliation(
            reconciliation
        )
        if not is_valid:
            return False, message

        # Update reconciliation
        reconciliation.status = "COMPLETED"
        reconciliation.completed_at = timezone.now()
        reconciliation.completed_by = completed_by
        reconciliation.save()

        # Mark transactions as reconciled: explicit reconciliation items
        # (added via add_item)...
        for item in reconciliation.items.all():
            if item.transaction:
                item.transaction.is_reconciled = True
                item.transaction.reconciliation = reconciliation
                item.transaction.save(update_fields=["is_reconciled", "reconciliation"])

        # ...and every transaction on this bank account tagged 'R'
        # (Reconciled) via the tagging workflow — transactions tagged 'P'
        # (Pending) are deliberately left untouched: they're still
        # outstanding against the bank statement and carry forward into the
        # next reconciliation (see BankReconciliationViewSet.month_end).
        tagged_reconciled = CashBookTransaction.objects.filter(
            account_type="BANK",
            bank_account_number=reconciliation.bank_account_number,
            bank_recon_tag="R",
            is_reconciled=False,
        )
        tagged_reconciled.update(is_reconciled=True, reconciliation=reconciliation)

        return True, "Reconciliation completed successfully"

    @staticmethod
    def prevent_transaction_modification(transaction: CashBookTransaction) -> bool:
        """
        Check if transaction can be modified.

        Returns:
            True if transaction cannot be modified (is reconciled), False otherwise
        """
        return transaction.is_reconciled


# ============================================================================
# EXPORT BUSINESS_SERVICES FOR DIRECT ACCESS
# ============================================================================
# New code should import directly from business_services.py:
# from .business_services import CashBookVATService, CashBookTransactionService, etc
#
# But these are exposed here for convenience:
__all__ = [
    # Main services (prefer importing from business_services.py)
    "CashBookVATService",
    "CashBookTransactionService",
    "CategoryBalanceService",
    "UnpresentedChequeService",
    "CashBookReportService",
    # Compatibility services (deprecated, use above instead)
    "VATService",
    "TransactionNumberGenerator",
    "BalanceCalculationService",
    "TransactionService",
    "SummaryService",
    "ReconciliationService",
]
