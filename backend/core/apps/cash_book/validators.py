"""
Cash Book Module Validators
Validation functions for transactions and reconciliation
"""
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, datetime
import re


def validate_positive_amount(value):
    """Validate that amount is positive"""
    if isinstance(value, Decimal):
        if value <= 0:
            raise ValidationError('Amount must be greater than 0')
    elif isinstance(value, (int, float)):
        if Decimal(str(value)) <= 0:
            raise ValidationError('Amount must be greater than 0')


def validate_non_negative_amount(value):
    """Validate that amount is non-negative"""
    if isinstance(value, Decimal):
        if value < 0:
            raise ValidationError('Amount cannot be negative')
    elif isinstance(value, (int, float)):
        if Decimal(str(value)) < 0:
            raise ValidationError('Amount cannot be negative')


def validate_transaction_date(value):
    """Validate that transaction date is not in future"""
    if isinstance(value, str):
        value = datetime.strptime(value, '%Y-%m-%d').date()
    
    if value > date.today():
        raise ValidationError('Transaction date cannot be in the future')


def validate_bank_account_number(value):
    """Validate bank account number format"""
    if not value:
        return
    
    # Remove spaces and hyphens
    value = value.replace(' ', '').replace('-', '')
    
    # Check if it's between 10-20 digits
    if not (10 <= len(value) <= 20):
        raise ValidationError('Bank account number must be between 10 and 20 characters')
    
    # Check if it contains only alphanumeric characters
    if not value.replace('.', '').isalnum():
        raise ValidationError('Bank account number must contain only alphanumeric characters')


def validate_transaction_number_format(value):
    """Validate transaction number format"""
    # Expected format: PREFIX-YYYYMMDD-00001
    pattern = r'^[A-Z]{3}-\d{8}-\d{5}$'
    
    if not re.match(pattern, value):
        raise ValidationError(
            'Invalid transaction number format. Expected: PREFIX-YYYYMMDD-00001'
        )


def validate_reconciliation_date(statement_date, reconciliation_date):
    """Validate that reconciliation date is after or equal to statement date"""
    if isinstance(statement_date, str):
        statement_date = datetime.strptime(statement_date, '%Y-%m-%d').date()
    if isinstance(reconciliation_date, str):
        reconciliation_date = datetime.strptime(reconciliation_date, '%Y-%m-%d').date()
    
    if reconciliation_date < statement_date:
        raise ValidationError(
            'Reconciliation date must be on or after the statement date'
        )


def validate_reconciliation_balances(
    closing_balance_per_statement,
    closing_balance_per_books,
    outstanding_deposits=Decimal('0'),
    outstanding_cheques=Decimal('0'),
    bank_errors=Decimal('0'),
    book_errors=Decimal('0')
):
    """
    Validate that reconciliation balances.
    
    Raises: ValidationError if reconciliation does not balance
    """
    calculated_balance = (
        closing_balance_per_statement +
        outstanding_deposits -
        outstanding_cheques +
        bank_errors -
        book_errors
    )
    
    difference = abs(calculated_balance - closing_balance_per_books)
    
    if difference >= Decimal('0.01'):
        raise ValidationError(
            f'Reconciliation does not balance. Difference: {difference}'
        )


def validate_cash_breakdown(
    cash_amount,
    notes_200=0, notes_100=0, notes_50=0, notes_20=0, notes_10=0,
    coins_5=0, coins_2=0, coins_1=0,
    coins_050=0, coins_020=0, coins_010=0, coins_005=0
):
    """
    Validate that cash breakdown adds up to cash amount.
    
    Raises: ValidationError if breakdown doesn't match cash amount
    """
    calculated_total = Decimal('0')
    calculated_total += notes_200 * Decimal('200')
    calculated_total += notes_100 * Decimal('100')
    calculated_total += notes_50 * Decimal('50')
    calculated_total += notes_20 * Decimal('20')
    calculated_total += notes_10 * Decimal('10')
    calculated_total += coins_5 * Decimal('5')
    calculated_total += coins_2 * Decimal('2')
    calculated_total += coins_1 * Decimal('1')
    calculated_total += coins_050 * Decimal('0.50')
    calculated_total += coins_020 * Decimal('0.20')
    calculated_total += coins_010 * Decimal('0.10')
    calculated_total += coins_005 * Decimal('0.05')
    
    if abs(calculated_total - Decimal(str(cash_amount))) > Decimal('0.01'):
        raise ValidationError(
            f'Cash breakdown does not match total. Expected: {cash_amount}, Got: {calculated_total}'
        )
