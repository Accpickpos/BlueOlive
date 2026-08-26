"""
Cash Book Business Services - Enhanced
Comprehensive business logic for all cash book operations with enterprise best practices

**AUTHORITATIVE SOURCE**: This module is the primary source for all business logic.
All new code should import directly from this module.
**Note**: services.py is a compatibility/delegation layer that redirects to this module.

Key Services:
- CashBookVATService: VAT calculations per spec (tax codes 1-4)
- CashBookTransactionService: Transaction CRUD with spec compliance (CBTRAN)
- CategoryBalanceService: MTD/monthly balance tracking (CBEXP, CBINC)
- UnpresentedChequeService: Cheque management (CBCHEQ)
- CashBookReportService: Monthly summaries and reports

**Transaction Number Format**: YYYYMMDDNN (8 digits date + 2 digit sequence)
Per spec CBTRANO (6 numeric digits for unique identification)
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db import transaction as db_transaction
from django.utils import timezone

from .models import (
    BankCharge,
    BankDeposit,
    BankReconciliation,
    BankReconciliationItem,
    BankTransfer,
    CashBookTransaction,
    CashFloat,
    CashWithdrawal,
    ExpenseCategoryBalance,
    IncomeCategoryBalance,
    InterestReceived,
    OtherExpense,
    OtherIncome,
    UnpresentedCheque,
)


class CashBookVATService:
    """
    Service for VAT calculations per specification
    Handles VAT rates, tax codes, and amount calculations
    """

    VAT_RATE = Decimal("0.14")  # 14% VAT

    TAX_CODE_MAP = {
        1: {"rate": Decimal("0.14"), "description": "VAT Applicable (14%)"},
        2: {"rate": Decimal("0.00"), "description": "Zero-rated (0%)"},
        3: {"rate": Decimal("0.00"), "description": "Exempt (0%)"},
        4: {"rate": Decimal("0.00"), "description": "Foreign Transaction"},
    }

    @classmethod
    def get_vat_rate_for_code(cls, tax_code: int) -> Decimal:
        """Get VAT rate for tax code"""
        return cls.TAX_CODE_MAP.get(tax_code, {}).get("rate", Decimal("0.00"))

    @classmethod
    def calculate_tax_amount(
        cls, value: Decimal, tax_code: int, is_inclusive: bool
    ) -> Decimal:
        """
        Calculate tax amount for a transaction

        Args:
            value: Amount (excl or incl VAT depending on is_inclusive)
            tax_code: Tax code (1-4)
            is_inclusive: True if value includes VAT, False if exclusive

        Returns:
            Tax amount
        """
        rate = cls.get_vat_rate_for_code(tax_code)
        if rate == 0:
            return Decimal("0")

        if is_inclusive:
            # Value includes VAT: tax = value - (value / (1 + rate))
            return value - (value / (1 + rate))
        else:
            # Value excludes VAT: tax = value * rate
            return value * rate

    @classmethod
    def calculate_total_incl_vat(
        cls, value_excl_vat: Decimal, tax_amount: Decimal
    ) -> Decimal:
        """
        Calculate total including VAT
        Per spec: TOTAL = VALUE + TAX

        Args:
            value_excl_vat: Amount excluding VAT
            tax_amount: Tax amount

        Returns:
            Total including VAT
        """
        return (value_excl_vat or Decimal("0")) + (tax_amount or Decimal("0"))

    @classmethod
    def get_net_amount(cls, total: Decimal, tax_code: int) -> Decimal:
        """Get net amount before VAT"""
        rate = cls.get_vat_rate_for_code(tax_code)
        if rate == 0:
            return total
        return total / (1 + rate)


class CashBookTransactionService:
    """
    Service for cash book transaction operations
    Handles creation, validation, and modification of transactions
    """

    AUDIT_TYPE_GL_MAPPING = {
        1: "1100",  # Accounts Receivable Receipts
        2: "2000",  # Sundry Income
        3: "2100",  # Accounts Payable Payments
        4: "4000",  # Expenses
    }

    @staticmethod
    def create_transaction(
        transaction_type: str,
        transaction_date: date,
        value_excl_vat: Decimal,
        tax_code: int,
        audit_type: int,
        category_id: int = None,
        reference: str = "",
        description: str = "",
        account_type: str = "CASH",
        bank_account_number: str = "",
        created_by: str = "",
        **kwargs,
    ) -> CashBookTransaction:
        """
        Create a new cash book transaction with automatic VAT calculation

        Args:
            transaction_type: Type of transaction
            transaction_date: Date of transaction
            value_excl_vat: Amount excluding VAT (per spec VALUE)
            tax_code: Tax code (per spec TAX)
            audit_type: Audit type 1-4 (per spec CBAUDIT)
            category_id: Category number (per spec CATNO)
            reference: Additional reference (per spec CBREF, max 20 chars)
            description: Transaction description
            account_type: CASH or BANK
            bank_account_number: Bank account (if applicable)
            created_by: User creating transaction

        Returns:
            Created CashBookTransaction

        Raises:
            ValidationError: If transaction fails validation
        """
        # Validate date not in future
        if transaction_date > timezone.now().date():
            raise ValidationError("Transaction date cannot be in the future")

        # Validate audit type
        if audit_type not in CashBookTransactionService.AUDIT_TYPE_GL_MAPPING:
            raise ValidationError(f"Invalid audit type: {audit_type}")

        # Generate transaction number and create transaction in a single atomic block
        # This prevents race conditions in transaction number generation
        with db_transaction.atomic():
            # Lock rows for this transaction type/date combination to prevent duplicates
            locked_transactions = (
                CashBookTransaction.objects.select_for_update().filter(
                    transaction_date=transaction_date, transaction_type=transaction_type
                )
            )
            # Get count within the lock scope
            count = locked_transactions.count()

            # Format: YYYYMMDD + 2-digit sequence (supports up to 99 per day)
            seq_num = str(count + 1).zfill(2)
            transaction_number = f"{transaction_date.strftime('%Y%m%d')}{seq_num}"

            # Calculate VAT and total
            vat_service = CashBookVATService()
            tax_amount = vat_service.calculate_tax_amount(
                value_excl_vat, tax_code, is_inclusive=False
            )
            total_incl_vat = vat_service.calculate_total_incl_vat(
                value_excl_vat, tax_amount
            )

            # Create transaction
            txn = CashBookTransaction.objects.create(
                transaction_type=transaction_type,
                transaction_number=transaction_number,
                transaction_date=transaction_date,
                account_type=account_type,
                bank_account_number=bank_account_number,
                amount=total_incl_vat,  # Keep amount field for backward compatibility
                value_excl_vat=value_excl_vat,
                tax_amount=tax_amount,
                total_incl_vat=total_incl_vat,
                category_id=category_id,
                audit_type=audit_type,
                reference=reference[:20],  # Enforce max 20 chars per spec
                description=description,
                bank_recon_tag="U",  # Default to Unreconciled per spec CBTAG
                created_by=created_by,
                **kwargs,
            )

            # Validate before returning
            txn.full_clean()

        return txn

    @staticmethod
    def _generate_transaction_number(transaction_type: str, txn_date: date) -> str:
        """
        Generate unique transaction number (per spec CBTRANO - 6 numeric)
        Format: YYYYMMDDNNNN (8-digit date + 4-digit sequence)
        """
        date_part = txn_date.strftime("%Y%m%d")

        # Count transactions on this date
        count = CashBookTransaction.objects.filter(
            transaction_date=txn_date, transaction_type=transaction_type
        ).count()

        # Format: YYYYMMDD + 4-digit sequence (supports up to 9,999 per day)
        seq_num = str(count + 1).zfill(4)
        return f"{date_part}{seq_num}"

    @staticmethod
    def update_transaction(
        transaction: CashBookTransaction, **kwargs
    ) -> CashBookTransaction:
        """
        Update transaction with validation

        Raises:
            ValidationError: If transaction is reconciled or modification invalid
        """
        if not transaction.can_be_modified():
            raise ValidationError("Cannot modify reconciled transactions")

        # Handle VAT fields if provided
        if "value_excl_vat" in kwargs:
            value_excl_vat = kwargs["value_excl_vat"]
            tax_code = kwargs.get("tax_code", transaction.audit_type)

            vat_service = CashBookVATService()
            tax_amount = vat_service.calculate_tax_amount(
                value_excl_vat, tax_code, is_inclusive=False
            )
            total_incl_vat = vat_service.calculate_total_incl_vat(
                value_excl_vat, tax_amount
            )

            kwargs["tax_amount"] = tax_amount
            kwargs["total_incl_vat"] = total_incl_vat
            kwargs["amount"] = total_incl_vat

        # Enforce reference max length (per spec CBREF - 20 chars)
        if "reference" in kwargs:
            kwargs["reference"] = kwargs["reference"][:20]

        for key, value in kwargs.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        transaction.full_clean()
        transaction.save()

        return transaction

    @staticmethod
    def delete_transaction(transaction: CashBookTransaction) -> bool:
        """
        Delete transaction (only if not reconciled)

        Returns:
            True if deleted, False otherwise
        """
        if not transaction.can_be_deleted():
            raise ValidationError("Cannot delete reconciled transactions")

        transaction_id = transaction.id
        transaction.delete()
        return not CashBookTransaction.objects.filter(id=transaction_id).exists()


class CategoryBalanceService:
    """
    Service for managing expense and income category balances
    Per spec CBEXP and CBINC with monthly balance tracking
    """

    @staticmethod
    def update_expense_category_balance(
        expense_category_id: int,
        value_excl_vat: Decimal,
        tax_amount: Decimal = None,
        transaction_date: date = None,
    ):
        """Update expense category balance with transaction"""
        if transaction_date is None:
            transaction_date = timezone.now().date()

        try:
            balance = ExpenseCategoryBalance.objects.get(
                expense_category_id=expense_category_id
            )
        except ExpenseCategoryBalance.DoesNotExist:
            # Create if doesn't exist (auto-create on first transaction)
            from apps.settings.models import ExpenseCategory

            category = ExpenseCategory.objects.get(id=expense_category_id)
            balance = ExpenseCategoryBalance.objects.create(expense_category=category)

        # Update MTD balance
        balance.balance_month_to_date += value_excl_vat or Decimal("0")
        balance.input_vat_month_to_date += tax_amount or Decimal("0")

        balance.save()
        return balance

    @staticmethod
    def update_income_category_balance(
        income_category_id: int,
        value_excl_vat: Decimal,
        tax_amount: Decimal = None,
        transaction_date: date = None,
    ):
        """Update income category balance with transaction"""
        if transaction_date is None:
            transaction_date = timezone.now().date()

        try:
            balance = IncomeCategoryBalance.objects.get(
                income_category_id=income_category_id
            )
        except IncomeCategoryBalance.DoesNotExist:
            # Create if doesn't exist (auto-create on first transaction)
            from apps.settings.models import IncomeCategory

            category = IncomeCategory.objects.get(id=income_category_id)
            balance = IncomeCategoryBalance.objects.create(income_category=category)

        # Update MTD balance
        balance.balance_month_to_date += value_excl_vat or Decimal("0")
        balance.output_vat_month_to_date += tax_amount or Decimal("0")

        balance.save()
        return balance

    @staticmethod
    def close_month(month_num: int, year: int) -> Dict:
        """
        Close month balances - lock MTD and move to monthly field

        Args:
            month_num: Month (1-12)
            year: Year

        Returns:
            Summary of closed balances
        """
        summary = {
            "expenses_closed": 0,
            "income_closed": 0,
            "total_expenses": Decimal("0"),
            "total_income": Decimal("0"),
        }

        # Close expense balances
        exp_balances = ExpenseCategoryBalance.objects.all()
        for balance in exp_balances:
            field_name = f"balance_month_{month_num:02d}"
            setattr(balance, field_name, balance.balance_month_to_date)
            balance.balance_month_to_date = Decimal("0")  # Reset MTD
            balance.input_vat_month_to_date = Decimal("0")
            balance.save()
            summary["total_expenses"] += getattr(balance, field_name)
            summary["expenses_closed"] += 1

        # Close income balances
        inc_balances = IncomeCategoryBalance.objects.all()
        for balance in inc_balances:
            field_name = f"balance_month_{month_num:02d}"
            setattr(balance, field_name, balance.balance_month_to_date)
            balance.balance_month_to_date = Decimal("0")  # Reset MTD
            balance.output_vat_month_to_date = Decimal("0")
            balance.save()
            summary["total_income"] += getattr(balance, field_name)
            summary["income_closed"] += 1

        return summary


class UnpresentedChequeService:
    """
    Service for managing unpresented cheques per spec CBCHEQ
    Tracks cheques issued but not yet presented at bank
    """

    @staticmethod
    def create_unpresented_cheque(
        cheque_number: str,
        cheque_date: date,
        value: Decimal,
        tax_code: int,
        total: Decimal,
        month_end_date: date,
        reference: str = "",
        tag: str = "U",
    ) -> UnpresentedCheque:
        """
        Create unpresented cheque record (per spec CBCHEQ)

        Args:
            cheque_number: Cheque # (per spec CBTRANO - 6 numeric)
            cheque_date: Date (per spec DATE)
            value: Value (per spec VALUE, 10,2)
            tax_code: Tax code (per spec TAX)
            total: Total (per spec TOTAL, 10,2)
            month_end_date: Month-end date for reconciliation
            reference: Additional reference (per spec CBREF - 20 char)
            tag: Reconciliation tag (per spec CBTAG)

        Returns:
            Created UnpresentedCheque
        """
        cheque = UnpresentedCheque(
            cheque_number=cheque_number[:6],  # Enforce 6 digit per spec
            cheque_date=cheque_date,
            value=value,
            tax_code=tax_code,
            total=total,
            tag=tag,
            month_end_date=month_end_date,
            reference=reference[:20],  # Enforce 20 char max per spec
        )
        cheque.full_clean()
        cheque.save()
        return cheque

    @staticmethod
    def get_reconciliation_summary(month_end_date: date) -> Dict:
        """
        Get summary of unpresented cheques for bank reconciliation
        Per spec: used in bank reconciliation process

        Args:
            month_end_date: End of period date

        Returns:
            Summary dict with total and age analysis
        """
        cheques = UnpresentedCheque.objects.filter(
            is_presented=False, month_end_date=month_end_date
        )

        return {
            "count": cheques.count(),
            "total_value": cheques.aggregate(total=models.Sum("total"))["total"]
            or Decimal("0"),
            "stale_count": cheques.filter(is_stale=True).count(),
            "requires_follow_up": cheques.filter(requires_follow_up=True).count(),
            "cheques": list(
                cheques.values(
                    "cheque_number",
                    "cheque_date",
                    "value",
                    "total",
                    "tag",
                    "days_outstanding",
                )
            ),
        }

    @staticmethod
    def mark_cheques_as_presented(
        cheque_numbers: List[str], presented_date: date = None
    ):
        """
        Mark multiple cheques as presented during bank reconciliation

        Args:
            cheque_numbers: List of cheque numbers
            presented_date: Date cheque appeared on statement
        """
        if presented_date is None:
            presented_date = timezone.now().date()

        cheques = UnpresentedCheque.objects.filter(
            cheque_number__in=cheque_numbers, is_presented=False
        )

        count = 0
        for cheque in cheques:
            cheque.mark_as_presented(presented_date)
            count += 1

        return count


class CashBookReportService:
    """
    Service for generating cash book reports
    Monthly summaries, VAT analysis, reconciliation reports
    """

    @staticmethod
    def get_monthly_summary(year: int, month: int) -> Dict:
        """
        Generate monthly cash book summary

        Args:
            year: Year
            month: Month (1-12)

        Returns:
            Monthly summary with opening balance, receipts, payments, etc.
        """
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        # Get transactions for month
        transactions = CashBookTransaction.objects.filter(
            transaction_date__range=[month_start, month_end]
        )

        receipts = transactions.filter(
            audit_type__in=[1, 2]  # Receivables & Sundry Income
        ).aggregate(total=models.Sum("value_excl_vat"))["total"] or Decimal("0")

        payments = transactions.filter(
            audit_type__in=[3, 4]  # Payables & Expenses
        ).aggregate(total=models.Sum("value_excl_vat"))["total"] or Decimal("0")

        # Get VAT summary
        vat_summary = transactions.aggregate(
            total_input_vat=models.Sum(
                models.Case(
                    models.When(audit_type__in=[1, 3], then="tax_amount"),
                    default=Decimal("0"),
                )
            ),
            total_output_vat=models.Sum(
                models.Case(
                    models.When(audit_type__in=[2], then="tax_amount"),
                    default=Decimal("0"),
                )
            ),
        )

        return {
            "period": f"{year}-{month:02d}",
            "total_receipts": receipts,
            "total_payments": payments,
            "net_movement": receipts - payments,
            "vat_input": vat_summary.get("total_input_vat") or Decimal("0"),
            "vat_output": vat_summary.get("total_output_vat") or Decimal("0"),
            "transaction_count": transactions.count(),
        }

    @staticmethod
    def get_category_breakdown(month: int = None) -> Dict:
        """
        Get expense and income by category
        """
        # NOTE: `month` is currently accepted but not applied as a filter -
        # ExpenseCategoryBalance/IncomeCategoryBalance store running
        # month-to-date/year-to-date totals rather than per-transaction
        # records, so there's nothing here to filter by an arbitrary month.
        expenses = ExpenseCategoryBalance.objects.all()
        income = IncomeCategoryBalance.objects.all()

        return {
            "expenses": {
                "mtd": {
                    exp.expense_category.name: exp.balance_month_to_date
                    for exp in expenses
                },
                "ytd": {
                    exp.expense_category.name: exp.year_to_date_balance
                    for exp in expenses
                },
            },
            "income": {
                "mtd": {
                    inc.income_category.name: inc.balance_month_to_date
                    for inc in income
                },
                "ytd": {
                    inc.income_category.name: inc.year_to_date_balance for inc in income
                },
            },
        }
