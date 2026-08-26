"""
Cash Book Module Validators
Comprehensive validation functions for transactions, categories, and reconciliation
Per specification CBTRAN, CBEXP, CBINC, CBCHEQ field validation rules
"""

import re
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError


def validate_positive_amount(value):
    """Validate that amount is positive"""
    if isinstance(value, Decimal):
        if value <= 0:
            raise ValidationError("Amount must be greater than 0")
    elif isinstance(value, (int, float)):
        if Decimal(str(value)) <= 0:
            raise ValidationError("Amount must be greater than 0")


def validate_non_negative_amount(value):
    """Validate that amount is non-negative"""
    if isinstance(value, Decimal):
        if value < 0:
            raise ValidationError("Amount cannot be negative")
    elif isinstance(value, (int, float)):
        if Decimal(str(value)) < 0:
            raise ValidationError("Amount cannot be negative")


def validate_transaction_date(value):
    """Validate that transaction date is not in future"""
    if isinstance(value, str):
        value = datetime.strptime(value, "%Y-%m-%d").date()

    if value > date.today():
        raise ValidationError("Transaction date cannot be in the future")


def validate_reference_field(value):
    """Validate reference field - max 20 characters per spec CBREF"""
    if not value:
        return  # Optional field

    if len(value) > 20:
        raise ValidationError(
            f"Reference field must not exceed 20 characters (got {len(value)})"
        )


def validate_bank_account_number(value):
    """Validate bank account number format"""
    if not value:
        return

    # Remove spaces and hyphens
    value = value.replace(" ", "").replace("-", "")

    # Check if it's between 10-20 digits
    if not (10 <= len(value) <= 20):
        raise ValidationError(
            "Bank account number must be between 10 and 20 characters"
        )

    # Check if it contains only alphanumeric characters
    if not value.replace(".", "").isalnum():
        raise ValidationError(
            "Bank account number must contain only alphanumeric characters"
        )


def validate_transaction_number_format(value):
    """Validate transaction number format"""
    # Expected format: PREFIX-YYYYMMDD-00001
    pattern = r"^[A-Z]{3}-\d{8}-\d{5}$"

    if not re.match(pattern, value):
        raise ValidationError(
            "Invalid transaction number format. Expected: PREFIX-YYYYMMDD-00001"
        )


def validate_vat_total_calculation(
    value_excl_vat: Decimal, tax_amount: Decimal, total_incl_vat: Decimal
):
    """
    Validate VAT calculation per spec: TOTAL = VALUE + TAX

    Raises: ValidationError if amounts don't match
    """
    calculated_total = (value_excl_vat or Decimal("0")) + (tax_amount or Decimal("0"))

    # Allow for rounding differences (max 0.01)
    if abs(calculated_total - total_incl_vat) > Decimal("0.01"):
        raise ValidationError(
            f"VAT calculation error: {value_excl_vat} + {tax_amount} != {total_incl_vat}"
        )


def validate_audit_type(value):
    """
    Validate audit type per spec CBAUDIT (1-4)

    1: Accounts Receivable Receipts
    2: Sundry Income
    3: Accounts Payable Payments
    4: Expenses
    """
    if value not in [1, 2, 3, 4]:
        raise ValidationError(
            "Audit type must be 1-4 (1=Receivables, 2=Income, 3=Payables, 4=Expenses)"
        )


def validate_tax_code(value):
    """
    Validate tax code per spec TAX (1-4)

    1: 14% VAT Applicable
    2: 0% VAT (Zero-rated)
    3: Exempt supplies
    4: Foreign transactions
    """
    if value not in [1, 2, 3, 4]:
        raise ValidationError(
            "Tax code must be 1-4 (1=14% VAT, 2=Zero%, 3=Exempt, 4=Foreign)"
        )


def validate_bank_recon_tag(value):
    """
    Validate bank reconciliation tag per spec CBTAG

    R: Reconciled
    P: Pending
    D: Disputed
    U: Unreconciled
    """
    if value not in ["R", "P", "D", "U"]:
        raise ValidationError(
            "Bank reconciliation tag must be R/P/D/U (Reconciled/Pending/Disputed/Unreconciled)"
        )


def validate_reconciliation_date(statement_date, reconciliation_date):
    """Validate that reconciliation date is after or equal to statement date"""
    if isinstance(statement_date, str):
        statement_date = datetime.strptime(statement_date, "%Y-%m-%d").date()
    if isinstance(reconciliation_date, str):
        reconciliation_date = datetime.strptime(reconciliation_date, "%Y-%m-%d").date()

    if reconciliation_date < statement_date:
        raise ValidationError(
            "Reconciliation date must be on or after the statement date"
        )


def validate_cheque_number_format(value):
    """
    Validate cheque number format - 6 numeric per spec CBTRANO
    """
    if not value:
        return

    # Remove any whitespace
    value = str(value).strip()

    # Must be exactly 6 digits (per spec: numeric 6)
    pattern = r"^\d{6}$"

    if not re.match(pattern, value):
        raise ValidationError(
            "Cheque number must be exactly 6 digits (per spec CBTRANO)"
        )


def validate_amount_decimal_places(value):
    """
    Validate that decimal amounts have max 2 decimal places
    (financial standard: dollars and cents)
    """
    if isinstance(value, Decimal):
        if value.as_tuple().exponent < -2:
            raise ValidationError("Amount must have maximum 2 decimal places")


def validate_reconciliation_balances(
    closing_balance_per_statement,
    closing_balance_per_books,
    outstanding_deposits=Decimal("0"),
    outstanding_cheques=Decimal("0"),
    bank_errors=Decimal("0"),
    book_errors=Decimal("0"),
):
    """
    Validate that reconciliation balances.

    Raises: ValidationError if reconciliation does not balance
    """
    calculated_balance = (
        closing_balance_per_statement
        + outstanding_deposits
        - outstanding_cheques
        + bank_errors
        - book_errors
    )

    difference = abs(calculated_balance - closing_balance_per_books)

    if difference >= Decimal("0.01"):
        raise ValidationError(
            f"Reconciliation does not balance. Difference: {difference}"
        )


def validate_no_duplicate_transactions(
    transaction_type: str,
    transaction_date: date,
    amount: Decimal,
    reference: str = "",
    exclude_id: int = None,
):
    """
    Check for duplicate transactions within 24 hours of same amount
    Helps prevent accidental duplicate entry
    """
    from .models import CashBookTransaction

    start_date = transaction_date - timedelta(days=1)
    end_date = transaction_date + timedelta(days=1)

    duplicates = CashBookTransaction.objects.filter(
        transaction_type=transaction_type,
        amount=amount,
        transaction_date__range=[start_date, end_date],
    )

    if exclude_id:
        duplicates = duplicates.exclude(id=exclude_id)

    if duplicates.exists():
        raise ValidationError(
            f"Possible duplicate transaction detected. Another {transaction_type} "
            f"for {amount} was entered within 24 hours."
        )


def validate_category_exists(category_id: int):
    """
    Validate that category exists and is active
    """
    if not category_id:
        return  # Optional field

    from apps.settings.models import ExpenseCategory, IncomeCategory

    # Check both expense and income categories
    expense_exists = ExpenseCategory.objects.filter(
        id=category_id, is_active=True
    ).exists()
    income_exists = IncomeCategory.objects.filter(
        id=category_id, is_active=True
    ).exists()

    if not (expense_exists or income_exists):
        raise ValidationError(f"Category {category_id} does not exist or is not active")


def validate_cash_breakdown(
    cash_amount,
    notes_200=0,
    notes_100=0,
    notes_50=0,
    notes_20=0,
    notes_10=0,
    coins_5=0,
    coins_2=0,
    coins_1=0,
    coins_050=0,
    coins_020=0,
    coins_010=0,
    coins_005=0,
):
    """
    Validate that cash breakdown adds up to cash amount.

    Raises: ValidationError if breakdown doesn't match cash amount
    """
    calculated_total = Decimal("0")
    calculated_total += notes_200 * Decimal("200")
    calculated_total += notes_100 * Decimal("100")
    calculated_total += notes_50 * Decimal("50")
    calculated_total += notes_20 * Decimal("20")
    calculated_total += notes_10 * Decimal("10")
    calculated_total += coins_5 * Decimal("5")
    calculated_total += coins_2 * Decimal("2")
    calculated_total += coins_1 * Decimal("1")
    calculated_total += coins_050 * Decimal("0.50")
    calculated_total += coins_020 * Decimal("0.20")
    calculated_total += coins_010 * Decimal("0.10")
    calculated_total += coins_005 * Decimal("0.05")

    if abs(calculated_total - Decimal(str(cash_amount))) > Decimal("0.01"):
        raise ValidationError(
            f"Cash breakdown does not match total. Expected: {cash_amount}, Got: {calculated_total}"
        )


def validate_monthly_balance_consistency(
    balance_month_to_date: Decimal,
    balance_month_01: Decimal = None,
    balance_month_02: Decimal = None,
    balance_month_03: Decimal = None,
    balance_month_04: Decimal = None,
    balance_month_05: Decimal = None,
    balance_month_06: Decimal = None,
    balance_month_07: Decimal = None,
    balance_month_08: Decimal = None,
    balance_month_09: Decimal = None,
    balance_month_10: Decimal = None,
    balance_month_11: Decimal = None,
    balance_month_12: Decimal = None,
):
    """
    Validate that all monthly balance values are non-negative
    Per spec: Monthly values are locked after month-end closing
    """
    months = [
        balance_month_01,
        balance_month_02,
        balance_month_03,
        balance_month_04,
        balance_month_05,
        balance_month_06,
        balance_month_07,
        balance_month_08,
        balance_month_09,
        balance_month_10,
        balance_month_11,
        balance_month_12,
        balance_month_to_date,
    ]

    for month_num, balance in enumerate(months, start=1):
        if balance is not None and balance < Decimal("0"):
            month_name = f"Month {month_num}" if month_num <= 12 else "MTD"
            raise ValidationError(f"{month_name} balance cannot be negative: {balance}")
