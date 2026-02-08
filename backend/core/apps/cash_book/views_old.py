"""
Cash Book Module Views
Handles all cash/bank transaction API endpoints
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, Count
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    IncomeCategory, CashBookTransaction, OtherIncome, OtherExpense,
    BankDeposit, CashWithdrawal, BankTransfer, BankCharge, InterestReceived,
    BankReconciliation, BankReconciliationItem, CashFloat
)
from .serializers import *


class IncomeCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for Income Categories"""
    queryset = IncomeCategory.objects.all()
    serializer_class = IncomeCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'number']
    ordering_fields = ['number', 'name']
    ordering = ['number']


class CashBookTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing cash book transactions
    Read-only - transactions created through specific endpoints
    """
    queryset = CashBookTransaction.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'account_type', 'is_reconciled', 'transaction_date']
    search_fields = ['transaction_number', 'description', 'reference']
    ordering_fields = ['transaction_date', 'transaction_number']
    ordering = ['-transaction_date', '-transaction_number']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return CashBookTransactionListSerializer
        return CashBookTransactionSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get cash book summary for a period"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        )
        
        # Calculate opening balances (transactions before start_date)
        opening_txns = CashBookTransaction.objects.filter(
            transaction_date__lt=start_date
        ).order_by('-transaction_date', '-transaction_number').first()
        
        opening_cash = opening_txns.running_balance_cash if opening_txns else Decimal('0')
        opening_bank = opening_txns.running_balance_bank if opening_txns else Decimal('0')
        
        # Calculate totals
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
        
        return Response({
            'start_date': start_date,
            'end_date': end_date,
            'opening_balance_cash': opening_cash,
            'opening_balance_bank': opening_bank,
            'total_receipts': receipts,
            'total_payments': payments,
            'closing_balance_cash': closing_cash,
            'closing_balance_bank': closing_bank,
            'transaction_count': queryset.count()
        })
    
    @action(detail=False, methods=['get'])
    def bank_balances(self, request):
        """Get current balances for all bank accounts"""
        # Get unique bank accounts
        accounts = CashBookTransaction.objects.filter(
            account_type='BANK'
        ).values('bank_account_number').distinct()
        
        balances = []
        for account in accounts:
            account_num = account['bank_account_number']
            
            # Get latest transaction for this account
            latest = CashBookTransaction.objects.filter(
                bank_account_number=account_num
            ).order_by('-transaction_date', '-transaction_number').first()
            
            # Count unreconciled items
            unreconciled = CashBookTransaction.objects.filter(
                bank_account_number=account_num,
                is_reconciled=False
            ).count()
            
            # Get last reconciliation date
            last_recon = BankReconciliation.objects.filter(
                bank_account_number=account_num,
                status='COMPLETED'
            ).order_by('-reconciliation_date').first()
            
            balances.append({
                'bank_account_number': account_num,
                'current_balance': latest.running_balance_bank if latest else Decimal('0'),
                'unreconciled_items': unreconciled,
                'last_reconciliation_date': last_recon.reconciliation_date if last_recon else None
            })
        
        return Response(balances)


class OtherIncomeViewSet(viewsets.ModelViewSet):
    """API endpoint for Other Income transactions"""
    queryset = OtherIncome.objects.select_related('transaction', 'income_category').all()
    serializer_class = OtherIncomeSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-transaction__transaction_date']
    
    def create(self, request, *args, **kwargs):
        """Create other income transaction"""
        serializer = CreateOtherIncomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Calculate VAT
        from django.conf import settings
        vat_rate = Decimal(str(settings.ACCPICK_VAT_RATE))
        
        amount = data['amount']
        tax_code = data.get('tax_code', 1)
        is_inclusive = data.get('is_vat_inclusive', True)
        
        if is_inclusive and tax_code == 1:
            vat_amount = amount - (amount / (1 + vat_rate))
        elif not is_inclusive and tax_code == 1:
            vat_amount = amount * vat_rate
        else:
            vat_amount = Decimal('0')
        
        # Generate transaction number
        today = timezone.now().date()
        txn_count = CashBookTransaction.objects.filter(
            transaction_type='OTHER_INCOME',
            transaction_date=today
        ).count()
        transaction_number = f"INC-{today.strftime('%Y%m%d')}-{txn_count + 1:05d}"
        
        # Determine account type
        paid_into = data.get('paid_into', 'CASH')
        account_type = 'CASH' if paid_into == 'CASH' else 'BANK'
        
        # Create transaction
        transaction = CashBookTransaction.objects.create(
            transaction_type='OTHER_INCOME',
            transaction_number=transaction_number,
            transaction_date=data['transaction_date'],
            account_type=account_type,
            bank_account_number=data.get('bank_account_number', ''),
            amount=amount,
            reference=data.get('reference', ''),
            description=data['description'],
            created_by=request.user.username
        )
        
        # Create other income
        other_income = OtherIncome.objects.create(
            transaction=transaction,
            income_category_id=data['income_category_id'],
            is_vat_inclusive=is_inclusive,
            vat_amount=vat_amount,
            tax_code=tax_code,
            paid_into=paid_into
        )
        
        response_serializer = OtherIncomeSerializer(other_income)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class OtherExpenseViewSet(viewsets.ModelViewSet):
    """API endpoint for Other Expense transactions"""
    queryset = OtherExpense.objects.select_related('transaction', 'expense_category').all()
    serializer_class = OtherExpenseSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-transaction__transaction_date']
    
    def create(self, request, *args, **kwargs):
        """Create other expense transaction"""
        serializer = CreateOtherExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Calculate VAT
        from django.conf import settings
        vat_rate = Decimal(str(settings.ACCPICK_VAT_RATE))
        
        amount = data['amount']
        tax_code = data.get('tax_code', 1)
        is_inclusive = data.get('is_vat_inclusive', True)
        
        if is_inclusive and tax_code == 1:
            vat_amount = amount - (amount / (1 + vat_rate))
        elif not is_inclusive and tax_code == 1:
            vat_amount = amount * vat_rate
        else:
            vat_amount = Decimal('0')
        
        # Generate transaction number
        today = timezone.now().date()
        txn_count = CashBookTransaction.objects.filter(
            transaction_type='OTHER_EXPENSE',
            transaction_date=today
        ).count()
        transaction_number = f"EXP-{today.strftime('%Y%m%d')}-{txn_count + 1:05d}"
        
        # Determine account type
        paid_from = data.get('paid_from', 'CASH')
        account_type = 'CASH' if paid_from == 'CASH' else 'BANK'
        
        # Create transaction
        transaction = CashBookTransaction.objects.create(
            transaction_type='OTHER_EXPENSE',
            transaction_number=transaction_number,
            transaction_date=data['transaction_date'],
            account_type=account_type,
            bank_account_number=data.get('bank_account_number', ''),
            amount=amount,
            reference=data.get('reference', ''),
            description=data['description'],
            created_by=request.user.username
        )
        
        # Create other expense
        other_expense = OtherExpense.objects.create(
            transaction=transaction,
            expense_category_id=data['expense_category_id'],
            is_vat_inclusive=is_inclusive,
            vat_amount=vat_amount,
            tax_code=tax_code,
            paid_from=paid_from,
            petty_cash_slip_number=data.get('petty_cash_slip_number', '')
        )
        
        response_serializer = OtherExpenseSerializer(other_expense)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class BankDepositViewSet(viewsets.ModelViewSet):
    """API endpoint for Bank Deposits"""
    queryset = BankDeposit.objects.select_related('transaction').all()
    serializer_class = BankDepositSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-transaction__transaction_date']
    
    def create(self, request, *args, **kwargs):
        """Create bank deposit"""
        serializer = CreateBankDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        total_amount = data['cash_amount'] + data['cheque_amount']
        
        # Generate transaction number
        today = timezone.now().date()
        txn_count = CashBookTransaction.objects.filter(
            transaction_type='DEPOSIT',
            transaction_date=today
        ).count()
        transaction_number = f"DEP-{today.strftime('%Y%m%d')}-{txn_count + 1:05d}"
        
        # Create transaction
        transaction = CashBookTransaction.objects.create(
            transaction_type='DEPOSIT',
            transaction_number=transaction_number,
            transaction_date=data['transaction_date'],
            account_type='BANK',
            bank_account_number=data['bank_account_number'],
            amount=total_amount,
            reference=data.get('reference', ''),
            description=data.get('description', 'Bank deposit'),
            created_by=request.user.username
        )
        
        # Create deposit
        deposit = BankDeposit.objects.create(
            transaction=transaction,
            deposit_slip_number=data.get('deposit_slip_number', ''),
            bank_name=data['bank_name'],
            branch=data.get('branch', ''),
            cash_amount=data['cash_amount'],
            cheque_amount=data['cheque_amount'],
            notes_200=data.get('notes_200', 0),
            notes_100=data.get('notes_100', 0),
            notes_50=data.get('notes_50', 0),
            notes_20=data.get('notes_20', 0),
            notes_10=data.get('notes_10', 0),
            coins_5=data.get('coins_5', 0),
            coins_2=data.get('coins_2', 0),
            coins_1=data.get('coins_1', 0),
            coins_050=data.get('coins_050', 0),
            coins_020=data.get('coins_020', 0),
            coins_010=data.get('coins_010', 0),
            coins_005=data.get('coins_005', 0)
        )
        
        response_serializer = BankDepositSerializer(deposit)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class CashWithdrawalViewSet(viewsets.ModelViewSet):
    """API endpoint for Cash Withdrawals"""
    queryset = CashWithdrawal.objects.select_related('transaction').all()
    serializer_class = CashWithdrawalSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-transaction__transaction_date']
    
    def create(self, request, *args, **kwargs):
        """Create cash withdrawal"""
        serializer = CreateCashWithdrawalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Generate transaction number
        today = timezone.now().date()
        txn_count = CashBookTransaction.objects.filter(
            transaction_type='WITHDRAWAL',
            transaction_date=today
        ).count()
        transaction_number = f"WDL-{today.strftime('%Y%m%d')}-{txn_count + 1:05d}"
        
        # Create transaction
        transaction = CashBookTransaction.objects.create(
            transaction_type='WITHDRAWAL',
            transaction_number=transaction_number,
            transaction_date=data['transaction_date'],
            account_type='BANK',
            bank_account_number=data['bank_account_number'],
            amount=data['amount'],
            reference=data.get('reference', ''),
            description=data['purpose'],
            created_by=request.user.username
        )
        
        # Create withdrawal
        withdrawal = CashWithdrawal.objects.create(
            transaction=transaction,
            withdrawal_slip_number=data.get('withdrawal_slip_number', ''),
            withdrawn_by=data['withdrawn_by'],
            purpose=data['purpose']
        )
        
        response_serializer = CashWithdrawalSerializer(withdrawal)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class BankTransferViewSet(viewsets.ModelViewSet):
    """API endpoint for Bank Transfers"""
    queryset = BankTransfer.objects.select_related('transaction').all()
    serializer_class = BankTransferSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-transaction__transaction_date']
    
    def create(self, request, *args, **kwargs):
        """Create bank transfer"""
        serializer = CreateBankTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Generate transaction number
        today = timezone.now().date()
        txn_count = CashBookTransaction.objects.filter(
            transaction_type='TRANSFER',
            transaction_date=today
        ).count()
        transaction_number = f"TRN-{today.strftime('%Y%m%d')}-{txn_count + 1:05d}"
        
        # Create transaction
        transaction = CashBookTransaction.objects.create(
            transaction_type='TRANSFER',
            transaction_number=transaction_number,
            transaction_date=data['transaction_date'],
            account_type='BANK',
            bank_account_number=data['from_account'],
            amount=data['amount'],
            reference=data.get('transfer_reference', ''),
            description=data.get('description', 'Bank transfer'),
            created_by=request.user.username
        )
        
        # Create transfer
        transfer = BankTransfer.objects.create(
            transaction=transaction,
            from_account=data['from_account'],
            to_account=data['to_account'],
            transfer_reference=data.get('transfer_reference', ''),
            transfer_fee=data.get('transfer_fee', Decimal('0'))
        )
        
        response_serializer = BankTransferSerializer(transfer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class BankChargeViewSet(viewsets.ModelViewSet):
    """API endpoint for Bank Charges"""
    queryset = BankCharge.objects.select_related('transaction').all()
    serializer_class = BankChargeSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-transaction__transaction_date']
    
    def create(self, request, *args, **kwargs):
        """Create bank charge"""
        serializer = CreateBankChargeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Generate transaction number
        today = timezone.now().date()
        txn_count = CashBookTransaction.objects.filter(
            transaction_type='BANK_CHARGE',
            transaction_date=today
        ).count()
        transaction_number = f"BCH-{today.strftime('%Y%m%d')}-{txn_count + 1:05d}"
        
        # Create transaction
        transaction = CashBookTransaction.objects.create(
            transaction_type='BANK_CHARGE',
            transaction_number=transaction_number,
            transaction_date=data['transaction_date'],
            account_type='BANK',
            bank_account_number=data['bank_account_number'],
            amount=data['amount'],
            reference=data.get('statement_reference', ''),
            description=data.get('description', f"Bank charge - {data['charge_type']}"),
            created_by=request.user.username
        )
        
        # Create bank charge
        bank_charge = BankCharge.objects.create(
            transaction=transaction,
            charge_type=data['charge_type'],
            statement_reference=data.get('statement_reference', '')
        )
        
        response_serializer = BankChargeSerializer(bank_charge)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class InterestReceivedViewSet(viewsets.ModelViewSet):
    """API endpoint for Interest Received"""
    queryset = InterestReceived.objects.select_related('transaction').all()
    serializer_class = InterestReceivedSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-transaction__transaction_date']
    
    def create(self, request, *args, **kwargs):
        """Create interest received"""
        serializer = CreateInterestReceivedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Generate transaction number
        today = timezone.now().date()
        txn_count = CashBookTransaction.objects.filter(
            transaction_type='INTEREST',
            transaction_date=today
        ).count()
        transaction_number = f"INT-{today.strftime('%Y%m%d')}-{txn_count + 1:05d}"
        
        # Create transaction
        transaction = CashBookTransaction.objects.create(
            transaction_type='INTEREST',
            transaction_number=transaction_number,
            transaction_date=data['transaction_date'],
            account_type='BANK',
            bank_account_number=data['bank_account_number'],
            amount=data['amount'],
            reference=data.get('reference', ''),
            description=data.get('description', 'Interest received'),
            created_by=request.user.username
        )
        
        # Create interest
        interest = InterestReceived.objects.create(
            transaction=transaction,
            interest_period_start=data['interest_period_start'],
            interest_period_end=data['interest_period_end'],
            interest_rate=data.get('interest_rate', Decimal('0'))
        )
        
        response_serializer = InterestReceivedSerializer(interest)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


class BankReconciliationViewSet(viewsets.ModelViewSet):
    """API endpoint for Bank Reconciliations"""
    queryset = BankReconciliation.objects.prefetch_related('items').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['bank_account_number', 'status']
    ordering = ['-reconciliation_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BankReconciliationListSerializer
        return BankReconciliationSerializer
    
    def create(self, request, *args, **kwargs):
        """Create new bank reconciliation"""
        serializer = CreateBankReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Generate reconciliation number
        today = timezone.now().date()
        recon_count = BankReconciliation.objects.filter(
            reconciliation_date=today
        ).count()
        reconciliation_number = f"REC-{today.strftime('%Y%m%d')}-{recon_count + 1:05d}"
        
        # Create reconciliation
        reconciliation = BankReconciliation.objects.create(
            reconciliation_number=reconciliation_number,
            reconciliation_date=data['reconciliation_date'],
            bank_account_number=data['bank_account_number'],
            statement_date=data['statement_date'],
            statement_number=data.get('statement_number', ''),
            opening_balance=data['opening_balance'],
            closing_balance_per_statement=data['closing_balance_per_statement'],
            closing_balance_per_books=data['closing_balance_per_books'],
            notes=data.get('notes', ''),
            status='IN_PROGRESS'
        )
        
        response_serializer = BankReconciliationSerializer(reconciliation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add reconciliation item"""
        reconciliation = self.get_object()
        
        if reconciliation.status == 'COMPLETED':
            return Response(
                {'error': 'Cannot modify completed reconciliation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = AddReconciliationItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        item = BankReconciliationItem.objects.create(
            reconciliation=reconciliation,
            item_type=data['item_type'],
            transaction_id=data.get('transaction_id'),
            manual_date=data.get('manual_date'),
            manual_reference=data.get('manual_reference', ''),
            manual_description=data.get('manual_description', ''),
            manual_amount=data.get('manual_amount', Decimal('0'))
        )
        
        response_serializer = BankReconciliationItemSerializer(item)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete reconciliation"""
        reconciliation = self.get_object()
        
        serializer = CompleteReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Update reconciliation
        reconciliation.outstanding_deposits = data['outstanding_deposits']
        reconciliation.outstanding_cheques = data['outstanding_cheques']
        reconciliation.bank_errors = data.get('bank_errors', Decimal('0'))
        reconciliation.book_errors = data.get('book_errors', Decimal('0'))
        reconciliation.notes = data.get('notes', reconciliation.notes)
        reconciliation.status = 'COMPLETED'
        reconciliation.completed_at = timezone.now()
        reconciliation.completed_by = request.user.username
        reconciliation.save()
        
        # Mark transactions as reconciled
        for item in reconciliation.items.all():
            if item.transaction:
                item.transaction.is_reconciled = True
                item.transaction.reconciliation = reconciliation
                item.transaction.save()
        
        response_serializer = BankReconciliationSerializer(reconciliation)
        return Response(response_serializer.data)


class CashFloatViewSet(viewsets.ModelViewSet):
    """API endpoint for Cash Float management"""
    queryset = CashFloat.objects.all()
    serializer_class = CashFloatSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-float_date']
    
    def create(self, request, *args, **kwargs):
        """Create cash float"""
        serializer = CreateCashFloatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        # Calculate counted cash from breakdown
        counted_cash = Decimal('0')
        counted_cash += data.get('notes_200', 0) * Decimal('200')
        counted_cash += data.get('notes_100', 0) * Decimal('100')
        counted_cash += data.get('notes_50', 0) * Decimal('50')
        counted_cash += data.get('notes_20', 0) * Decimal('20')
        counted_cash += data.get('notes_10', 0) * Decimal('10')
        counted_cash += data.get('coins_5', 0) * Decimal('5')
        counted_cash += data.get('coins_2', 0) * Decimal('2')
        counted_cash += data.get('coins_1', 0) * Decimal('1')
        counted_cash += data.get('coins_050', 0) * Decimal('0.50')
        counted_cash += data.get('coins_020', 0) * Decimal('0.20')
        counted_cash += data.get('coins_010', 0) * Decimal('0.10')
        counted_cash += data.get('coins_005', 0) * Decimal('0.05')
        
        # Calculate expected cash
        expected_cash = (
            data['opening_float'] +
            data.get('cash_sales', Decimal('0')) +
            data.get('cash_receipts', Decimal('0')) -
            data.get('cash_payments', Decimal('0')) -
            data.get('banked_amount', Decimal('0'))
        )
        
        # Calculate variance
        variance = counted_cash - expected_cash
        is_balanced = abs(variance) < Decimal('0.01')
        
        # Create float
        cash_float = CashFloat.objects.create(
            float_date=data['float_date'],
            opening_float=data['opening_float'],
            cash_sales=data.get('cash_sales', Decimal('0')),
            cash_receipts=data.get('cash_receipts', Decimal('0')),
            cash_payments=data.get('cash_payments', Decimal('0')),
            banked_amount=data.get('banked_amount', Decimal('0')),
            counted_cash=counted_cash,
            notes_200=data.get('notes_200', 0),
            notes_100=data.get('notes_100', 0),
            notes_50=data.get('notes_50', 0),
            notes_20=data.get('notes_20', 0),
            notes_10=data.get('notes_10', 0),
            coins_5=data.get('coins_5', 0),
            coins_2=data.get('coins_2', 0),
            coins_1=data.get('coins_1', 0),
            coins_050=data.get('coins_050', 0),
            coins_020=data.get('coins_020', 0),
            coins_010=data.get('coins_010', 0),
            coins_005=data.get('coins_005', 0),
            variance=variance,
            variance_notes=data.get('variance_notes', ''),
            is_balanced=is_balanced,
            counted_by=data.get('counted_by', request.user.username)
        )
        
        response_serializer = CashFloatSerializer(cash_float)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)