"""
Cash Book Module Services
Contains business logic for transactions, VAT calculations, reconciliation, and reporting
"""
from django.db import transaction as db_transaction
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from .models import (
    CashBookTransaction, OtherIncome, OtherExpense,
    BankDeposit, CashWithdrawal, BankTransfer, BankCharge, InterestReceived,
    BankReconciliation, BankReconciliationItem
)


class VATService:
    """Service for VAT calculations"""
    
    @staticmethod
    def get_vat_rate():
        """Get current VAT rate from settings"""
        return Decimal(str(getattr(settings, 'ACCPICK_VAT_RATE', '0.14')))
    
    @staticmethod
    def calculate_vat(amount: Decimal, tax_code: int, is_inclusive: bool) -> Decimal:
        """
        Calculate VAT amount for a transaction.
        
        Args:
            amount: Transaction amount
            tax_code: 1 for VAT applicable (14%), 2 for no VAT (0%)
            is_inclusive: True if amount includes VAT, False if exclusive
            
        Returns:
            VAT amount
        """
        vat_rate = VATService.get_vat_rate()
        
        if tax_code != 1:  # No VAT
            return Decimal('0')
        
        if is_inclusive:
            # VAT is already included in amount
            return amount - (amount / (1 + vat_rate))
        else:
            # VAT needs to be added to amount
            return amount * vat_rate
    
    @staticmethod
    def get_net_amount(amount: Decimal, tax_code: int, is_inclusive: bool) -> Decimal:
        """Get net amount before VAT"""
        if tax_code != 1 or not is_inclusive:
            return amount
        
        vat_rate = VATService.get_vat_rate()
        return amount / (1 + vat_rate)


class TransactionNumberGenerator:
    """Service for generating unique transaction numbers"""
    
    PREFIXES = {
        'RECEIPT': 'RCP',
        'PAYMENT': 'PAY',
        'DEPOSIT': 'DEP',
        'WITHDRAWAL': 'WDL',
        'TRANSFER': 'TRN',
        'BANK_CHARGE': 'BCH',
        'INTEREST': 'INT',
        'OTHER_INCOME': 'INC',
        'OTHER_EXPENSE': 'EXP',
    }
    
    @staticmethod
    def generate(transaction_type: str, transaction_date: Optional[datetime] = None) -> str:
        """
        Generate unique transaction number.
        
        Format: PREFIX-YYYYMMDD-00001
        
        Args:
            transaction_type: Type of transaction
            transaction_date: Date for transaction (defaults to today)
            
        Returns:
            Unique transaction number
        """
        if transaction_date is None:
            transaction_date = timezone.now().date()
        elif hasattr(transaction_date, 'date'):
            transaction_date = transaction_date.date()
        
        prefix = TransactionNumberGenerator.PREFIXES.get(transaction_type, 'TXN')
        
        # Count existing transactions of this type on this date
        count = CashBookTransaction.objects.filter(
            transaction_type=transaction_type,
            transaction_date=transaction_date
        ).count()
        
        return f"{prefix}-{transaction_date.strftime('%Y%m%d')}-{count + 1:05d}"


class BalanceCalculationService:
    """Service for calculating running balances"""
    
    @staticmethod
    def update_running_balances(from_transaction: Optional[CashBookTransaction] = None):
        """
        Recalculate running balances for all transactions.
        
        If from_transaction is provided, only updates transactions from that point onward.
        Otherwise, recalculates all balances from scratch.
        
        Args:
            from_transaction: Starting transaction or None to recalculate all
        """
        if from_transaction:
            # Get the previous transaction to initialize balances
            prev_txn = CashBookTransaction.objects.filter(
                transaction_date__lt=from_transaction.transaction_date
            ).order_by('-transaction_date', '-transaction_number').first()
            
            if prev_txn:
                cash_balance = prev_txn.running_balance_cash
                bank_balance = prev_txn.running_balance_bank
            else:
                cash_balance = Decimal('0')
                bank_balance = Decimal('0')
            
            # Get transactions from this point onward
            txns = CashBookTransaction.objects.filter(
                transaction_date__gte=from_transaction.transaction_date
            ).order_by('transaction_date', 'transaction_number')
        else:
            cash_balance = Decimal('0')
            bank_balance = Decimal('0')
            txns = CashBookTransaction.objects.all().order_by('transaction_date', 'transaction_number')
        
        # Update balances
        for txn in txns:
            if txn.is_debit:
                if txn.account_type == 'CASH':
                    cash_balance += txn.amount
                else:
                    bank_balance += txn.amount
            elif txn.is_credit:
                if txn.account_type == 'CASH':
                    cash_balance -= txn.amount
                else:
                    bank_balance -= txn.amount
            
            txn.running_balance_cash = cash_balance
            txn.running_balance_bank = bank_balance
            txn.save(update_fields=['running_balance_cash', 'running_balance_bank'])
    
    @staticmethod
    def get_current_balances() -> Dict[str, Decimal]:
        """Get current cash and bank balances"""
        last_txn = CashBookTransaction.objects.all().order_by(
            '-transaction_date', '-transaction_number'
        ).first()
        
        if last_txn:
            return {
                'cash': last_txn.running_balance_cash,
                'bank': last_txn.running_balance_bank,
                'total': last_txn.running_balance_cash + last_txn.running_balance_bank,
            }
        
        return {'cash': Decimal('0'), 'bank': Decimal('0'), 'total': Decimal('0')}
    
    @staticmethod
    def get_account_balances() -> Dict[str, Dict[str, Decimal]]:
        """Get balances for each bank account"""
        accounts = CashBookTransaction.objects.filter(
            account_type='BANK'
        ).values('bank_account_number').distinct()
        
        balances = {}
        for account in accounts:
            account_num = account['bank_account_number']
            last_txn = CashBookTransaction.objects.filter(
                bank_account_number=account_num
            ).order_by('-transaction_date', '-transaction_number').first()
            
            balances[account_num] = {
                'balance': last_txn.running_balance_bank if last_txn else Decimal('0'),
                'unreconciled_count': CashBookTransaction.objects.filter(
                    bank_account_number=account_num,
                    is_reconciled=False
                ).count(),
            }
        
        return balances


class TransactionService:
    """Service for creating and managing transactions"""
    
    @staticmethod
    @db_transaction.atomic
    def create_other_income(
        transaction_date,
        income_category_id,
        amount: Decimal,
        description: str,
        is_vat_inclusive: bool = True,
        tax_code: int = 1,
        reference: str = '',
        paid_into: str = 'CASH',
        bank_account_number: str = '',
        created_by: str = 'system'
    ) -> OtherIncome:
        """
        Create an other income transaction.
        
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
        vat_amount = VATService.calculate_vat(amount, tax_code, is_vat_inclusive)
        
        # Generate transaction number
        transaction_number = TransactionNumberGenerator.generate('OTHER_INCOME', transaction_date)
        
        # Determine account type
        account_type = 'BANK' if paid_into == 'BANK' else 'CASH'
        
        # Create base transaction
        base_transaction = CashBookTransaction.objects.create(
            transaction_type='OTHER_INCOME',
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            account_type=account_type,
            bank_account_number=bank_account_number,
            amount=amount,
            reference=reference,
            description=description,
            created_by=created_by
        )
        
        # Create other income record
        other_income = OtherIncome.objects.create(
            transaction=base_transaction,
            income_category_id=income_category_id,
            is_vat_inclusive=is_vat_inclusive,
            vat_amount=vat_amount,
            tax_code=tax_code,
            paid_into=paid_into
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
        reference: str = '',
        paid_from: str = 'CASH',
        bank_account_number: str = '',
        petty_cash_slip_number: str = '',
        created_by: str = 'system'
    ) -> OtherExpense:
        """Create an other expense transaction"""
        vat_amount = VATService.calculate_vat(amount, tax_code, is_vat_inclusive)
        
        transaction_number = TransactionNumberGenerator.generate('OTHER_EXPENSE', transaction_date)
        
        account_type = 'BANK' if paid_from == 'BANK' else 'CASH'
        
        base_transaction = CashBookTransaction.objects.create(
            transaction_type='OTHER_EXPENSE',
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            account_type=account_type,
            bank_account_number=bank_account_number,
            amount=amount,
            reference=reference,
            description=description,
            created_by=created_by
        )
        
        other_expense = OtherExpense.objects.create(
            transaction=base_transaction,
            expense_category_id=expense_category_id,
            is_vat_inclusive=is_vat_inclusive,
            vat_amount=vat_amount,
            tax_code=tax_code,
            paid_from=paid_from,
            petty_cash_slip_number=petty_cash_slip_number
        )
        
        return other_expense
    
    @staticmethod
    @db_transaction.atomic
    def create_bank_deposit(
        transaction_date,
        bank_account_number: str,
        bank_name: str,
        cash_amount: Decimal = Decimal('0'),
        cheque_amount: Decimal = Decimal('0'),
        deposit_slip_number: str = '',
        branch: str = '',
        cash_breakdown: Optional[Dict] = None,
        reference: str = '',
        created_by: str = 'system'
    ) -> BankDeposit:
        """Create a bank deposit transaction"""
        total_amount = cash_amount + cheque_amount
        
        transaction_number = TransactionNumberGenerator.generate('DEPOSIT', transaction_date)
        
        base_transaction = CashBookTransaction.objects.create(
            transaction_type='DEPOSIT',
            transaction_number=transaction_number,
            transaction_date=transaction_date,
            account_type='BANK',
            bank_account_number=bank_account_number,
            amount=total_amount,
            reference=reference,
            description='Bank deposit',
            created_by=created_by
        )
        
        # Prepare deposit data
        deposit_data = {
            'transaction': base_transaction,
            'deposit_slip_number': deposit_slip_number,
            'bank_name': bank_name,
            'branch': branch,
            'cash_amount': cash_amount,
            'cheque_amount': cheque_amount,
        }
        
        # Add cash breakdown if provided
        if cash_breakdown:
            deposit_data.update(cash_breakdown)
        
        deposit = BankDeposit.objects.create(**deposit_data)
        
        return deposit


class SummaryService:
    """Service for generating financial summaries and reports"""
    
    @staticmethod
    def get_period_summary(start_date, end_date) -> Dict:
        """
        Get summary of transactions for a period.
        
        Args:
            start_date: Start date for period
            end_date: End date for period
            
        Returns:
            Dictionary with summary data
        """
        queryset = CashBookTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        # Get opening balances
        opening_txn = CashBookTransaction.objects.filter(
            transaction_date__lt=start_date
        ).order_by('-transaction_date', '-transaction_number').first()
        
        opening_cash = opening_txn.running_balance_cash if opening_txn else Decimal('0')
        opening_bank = opening_txn.running_balance_bank if opening_txn else Decimal('0')
        
        # Calculate totals by type
        from django.db.models import Sum
        
        receipts = queryset.filter(
            transaction_type__in=['RECEIPT', 'DEPOSIT', 'INTEREST', 'OTHER_INCOME']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        payments = queryset.filter(
            transaction_type__in=['PAYMENT', 'WITHDRAWAL', 'TRANSFER', 'BANK_CHARGE', 'OTHER_EXPENSE']
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Get closing balances
        closing_txn = queryset.order_by('-transaction_date', '-transaction_number').first()
        closing_cash = closing_txn.running_balance_cash if closing_txn else opening_cash
        closing_bank = closing_txn.running_balance_bank if closing_txn else opening_bank
        
        return {
            'start_date': start_date,
            'end_date': end_date,
            'opening_balance_cash': opening_cash,
            'opening_balance_bank': opening_bank,
            'opening_balance_total': opening_cash + opening_bank,
            'total_receipts': receipts,
            'total_payments': payments,
            'closing_balance_cash': closing_cash,
            'closing_balance_bank': closing_bank,
            'closing_balance_total': closing_cash + closing_bank,
            'transaction_count': queryset.count(),
            'net_change': (closing_cash + closing_bank) - (opening_cash + opening_bank),
        }
    
    @staticmethod
    def get_transaction_breakdown(start_date, end_date) -> Dict[str, Decimal]:
        """Get breakdown of transactions by type"""
        queryset = CashBookTransaction.objects.filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        from django.db.models import Sum
        
        breakdown = {}
        for txn_type, display in CashBookTransaction.TRANSACTION_TYPE_CHOICES:
            total = queryset.filter(
                transaction_type=txn_type
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            breakdown[txn_type] = total
        
        return breakdown


class ReconciliationService:
    """Service for bank reconciliation"""
    
    @staticmethod
    def validate_reconciliation(reconciliation: BankReconciliation) -> Tuple[bool, str]:
        """
        Validate if reconciliation balances.
        
        Returns:
            Tuple of (is_valid, message)
        """
        calculated_balance = (
            reconciliation.closing_balance_per_statement +
            reconciliation.outstanding_deposits -
            reconciliation.outstanding_cheques +
            reconciliation.bank_errors -
            reconciliation.book_errors
        )
        
        difference = abs(calculated_balance - reconciliation.closing_balance_per_books)
        
        if difference < Decimal('0.01'):
            return True, "Reconciliation balances"
        
        return False, f"Reconciliation does not balance. Difference: {difference}"
    
    @staticmethod
    @db_transaction.atomic
    def complete_reconciliation(
        reconciliation: BankReconciliation,
        completed_by: str
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
        is_valid, message = ReconciliationService.validate_reconciliation(reconciliation)
        if not is_valid:
            return False, message
        
        # Update reconciliation
        reconciliation.status = 'COMPLETED'
        reconciliation.completed_at = timezone.now()
        reconciliation.completed_by = completed_by
        reconciliation.save()
        
        # Mark transactions as reconciled
        for item in reconciliation.items.all():
            if item.transaction:
                item.transaction.is_reconciled = True
                item.transaction.reconciliation = reconciliation
                item.transaction.save(update_fields=['is_reconciled', 'reconciliation'])
        
        return True, "Reconciliation completed successfully"
    
    @staticmethod
    def prevent_transaction_modification(transaction: CashBookTransaction) -> bool:
        """
        Check if transaction can be modified.
        
        Returns:
            True if transaction cannot be modified (is reconciled), False otherwise
        """
        return transaction.is_reconciled
