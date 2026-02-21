"""
Cash Book Module Views (Refactored)
Handles all cash/bank transaction API endpoints with proper error handling and permissions
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Q, Count, Prefetch
from django.utils import timezone
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    IncomeCategory, CashBookTransaction, OtherIncome, OtherExpense,
    BankDeposit, CashWithdrawal, BankTransfer, BankCharge, InterestReceived,
    BankReconciliation, BankReconciliationItem, CashFloat,
    ExpenseCategoryBalance, IncomeCategoryBalance, UnpresentedCheque
)
from .serializers import *
from .services import (
    TransactionService, VATService, BalanceCalculationService,
    SummaryService, ReconciliationService
)
from .permissions import (
    CanCreateTransactions, CanViewTransactions, CanReconcile,
    CanModifyReconciledTransactions
)
from apps.common.permissions import BaseModelPermission, CanReconcile as CommonCanReconcile


class IncomeCategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for Income Categories"""
    queryset = IncomeCategory.objects.all()
    serializer_class = IncomeCategorySerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'number']
    ordering_fields = ['number', 'name']
    ordering = ['number']


class CashBookTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing cash book transactions
    Read-only - transactions created through specific endpoints
    """
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['transaction_type', 'account_type', 'is_reconciled', 'transaction_date']
    search_fields = ['transaction_number', 'description', 'reference']
    ordering_fields = ['transaction_date', 'transaction_number']
    ordering = ['-transaction_date', '-transaction_number']
    
    def get_queryset(self):
        """Optimize query with select_related"""
        return CashBookTransaction.objects.select_related(
            'reconciliation'
        ).prefetch_related(
            'other_income__income_category',
            'other_expense__expense_category',
            'bank_deposit',
            'cash_withdrawal',
            'bank_transfer',
            'bank_charge',
            'interest_received'
        ).all()
    
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
                {'error': 'start_date and end_date parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            summary_data = SummaryService.get_period_summary(start_date, end_date)
            return Response(summary_data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def breakdown(self, request):
        """Get transaction breakdown by type"""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'error': 'start_date and end_date parameters are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            breakdown = SummaryService.get_transaction_breakdown(start_date, end_date)
            return Response(breakdown)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def bank_balances(self, request):
        """Get current balances for all bank accounts (optimized)"""
        from .services import BalanceCalculationService
        
        balances_data = BalanceCalculationService.get_account_balances()
        
        return Response({
            'accounts': balances_data,
            'timestamp': timezone.now()
        })
    
    @action(detail=False, methods=['get'])
    def current_balance(self, request):
        """Get current overall balances"""
        balances = BalanceCalculationService.get_current_balances()
        return Response(balances)


class OtherIncomeViewSet(viewsets.ModelViewSet):
    """API endpoint for Other Income transactions"""
    serializer_class = OtherIncomeSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions, CanModifyReconciledTransactions]
    ordering = ['-transaction__transaction_date']
    
    def get_queryset(self):
        return OtherIncome.objects.select_related(
            'transaction', 'income_category'
        ).all()
    
    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create other income transaction"""
        serializer = CreateOtherIncomeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            data = serializer.validated_data
            other_income = TransactionService.create_other_income(
                transaction_date=data['transaction_date'],
                income_category_id=data['income_category_id'],
                amount=data['amount'],
                description=data['description'],
                is_vat_inclusive=data.get('is_vat_inclusive', True),
                tax_code=data.get('tax_code', 1),
                reference=data.get('reference', ''),
                paid_into=data.get('paid_into', 'CASH'),
                bank_account_number=data.get('bank_account_number', ''),
                created_by=request.user.username
            )
            
            response_serializer = OtherIncomeSerializer(other_income)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create transaction: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class OtherExpenseViewSet(viewsets.ModelViewSet):
    """API endpoint for Other Expense transactions"""
    serializer_class = OtherExpenseSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions, CanModifyReconciledTransactions]
    ordering = ['-transaction__transaction_date']
    
    def get_queryset(self):
        return OtherExpense.objects.select_related(
            'transaction', 'expense_category'
        ).all()
    
    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create other expense transaction"""
        serializer = CreateOtherExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            data = serializer.validated_data
            other_expense = TransactionService.create_other_expense(
                transaction_date=data['transaction_date'],
                expense_category_id=data['expense_category_id'],
                amount=data['amount'],
                description=data['description'],
                is_vat_inclusive=data.get('is_vat_inclusive', True),
                tax_code=data.get('tax_code', 1),
                reference=data.get('reference', ''),
                paid_from=data.get('paid_from', 'CASH'),
                bank_account_number=data.get('bank_account_number', ''),
                petty_cash_slip_number=data.get('petty_cash_slip_number', ''),
                created_by=request.user.username
            )
            
            response_serializer = OtherExpenseSerializer(other_expense)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create transaction: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class BankDepositViewSet(viewsets.ModelViewSet):
    """API endpoint for Bank Deposits"""
    serializer_class = BankDepositSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions, CanModifyReconciledTransactions]
    ordering = ['-transaction__transaction_date']
    
    def get_queryset(self):
        return BankDeposit.objects.select_related('transaction').all()
    
    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create bank deposit"""
        serializer = CreateBankDepositSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            data = serializer.validated_data
            
            # Prepare cash breakdown
            cash_breakdown = {
                'notes_200': data.get('notes_200', 0),
                'notes_100': data.get('notes_100', 0),
                'notes_50': data.get('notes_50', 0),
                'notes_20': data.get('notes_20', 0),
                'notes_10': data.get('notes_10', 0),
                'coins_5': data.get('coins_5', 0),
                'coins_2': data.get('coins_2', 0),
                'coins_1': data.get('coins_1', 0),
                'coins_050': data.get('coins_050', 0),
                'coins_020': data.get('coins_020', 0),
                'coins_010': data.get('coins_010', 0),
                'coins_005': data.get('coins_005', 0),
            }
            
            deposit = TransactionService.create_bank_deposit(
                transaction_date=data['transaction_date'],
                bank_account_number=data['bank_account_number'],
                bank_name=data['bank_name'],
                cash_amount=data['cash_amount'],
                cheque_amount=data['cheque_amount'],
                deposit_slip_number=data.get('deposit_slip_number', ''),
                branch=data.get('branch', ''),
                cash_breakdown=cash_breakdown,
                reference=data.get('reference', ''),
                created_by=request.user.username
            )
            
            response_serializer = BankDepositSerializer(deposit)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create deposit: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class CashWithdrawalViewSet(viewsets.ModelViewSet):
    """API endpoint for Cash Withdrawals"""
    serializer_class = CashWithdrawalSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions, CanModifyReconciledTransactions]
    ordering = ['-transaction__transaction_date']
    
    def get_queryset(self):
        return CashWithdrawal.objects.select_related('transaction').all()


class BankTransferViewSet(viewsets.ModelViewSet):
    """API endpoint for Bank Transfers"""
    serializer_class = BankTransferSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions, CanModifyReconciledTransactions]
    ordering = ['-transaction__transaction_date']
    
    def get_queryset(self):
        return BankTransfer.objects.select_related('transaction').all()


class BankChargeViewSet(viewsets.ModelViewSet):
    """API endpoint for Bank Charges"""
    serializer_class = BankChargeSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions, CanModifyReconciledTransactions]
    ordering = ['-transaction__transaction_date']
    
    def get_queryset(self):
        return BankCharge.objects.select_related('transaction').all()


class InterestReceivedViewSet(viewsets.ModelViewSet):
    """API endpoint for Interest Received"""
    serializer_class = InterestReceivedSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions, CanModifyReconciledTransactions]
    ordering = ['-transaction__transaction_date']
    
    def get_queryset(self):
        return InterestReceived.objects.select_related('transaction').all()


class BankReconciliationViewSet(viewsets.ModelViewSet):
    """API endpoint for Bank Reconciliations"""
    permission_classes = [IsAuthenticated, CanReconcile]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['bank_account_number', 'status']
    ordering = ['-reconciliation_date']
    
    def get_queryset(self):
        return BankReconciliation.objects.prefetch_related(
            Prefetch(
                'items',
                queryset=BankReconciliationItem.objects.select_related('transaction')
            )
        ).all()
    
    def get_serializer_class(self):
        if self.action == 'list':
            return BankReconciliationListSerializer
        return BankReconciliationSerializer
    
    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create new bank reconciliation"""
        serializer = CreateBankReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        from .services import TransactionNumberGenerator
        
        today = timezone.now().date()
        recon_count = BankReconciliation.objects.filter(
            reconciliation_date=today
        ).count()
        reconciliation_number = f"REC-{today.strftime('%Y%m%d')}-{recon_count + 1:05d}"
        
        try:
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
        
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
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
        
        try:
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
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete reconciliation"""
        reconciliation = self.get_object()
        
        serializer = CompleteReconciliationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        
        try:
            # Update reconciliation data
            reconciliation.outstanding_deposits = data['outstanding_deposits']
            reconciliation.outstanding_cheques = data['outstanding_cheques']
            reconciliation.bank_errors = data.get('bank_errors', Decimal('0'))
            reconciliation.book_errors = data.get('book_errors', Decimal('0'))
            reconciliation.notes = data.get('notes', reconciliation.notes)
            
            # Use service to complete with validation
            success, message = ReconciliationService.complete_reconciliation(
                reconciliation,
                completed_by=request.user.username
            )
            
            if not success:
                return Response(
                    {'error': message},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            response_serializer = BankReconciliationSerializer(reconciliation)
            return Response(response_serializer.data)
        
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CashFloatViewSet(viewsets.ModelViewSet):
    """API endpoint for Cash Float management"""
    queryset = CashFloat.objects.all()
    serializer_class = CashFloatSerializer
    permission_classes = [IsAuthenticated, CanCreateTransactions]
    ordering = ['-float_date']


class ExpenseCategoryBalanceViewSet(viewsets.ModelViewSet):
    """API endpoint for expense category balances (per spec CBEXP)"""
    queryset = ExpenseCategoryBalance.objects.select_related('expense_category')
    serializer_class = ExpenseCategoryBalanceSerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['expense_category']
    search_fields = ['expense_category__name']
    ordering_fields = ['balance_month_to_date', 'updated_at']
    ordering = ['-balance_month_to_date']
    
    @action(detail=True, methods=['patch'])
    def close_month(self, request, pk=None):
        """Close month for category balance"""
        balance = self.get_object()
        
        month = request.data.get('month')
        year = request.data.get('year')
        
        if not month or not year:
            return Response(
                {'error': 'month and year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            balance.set_month_balance(month, balance.balance_month_to_date)
            balance.balance_month_to_date = Decimal('0')
            balance.input_vat_month_to_date = Decimal('0')
            balance.save()
            
            serializer = self.get_serializer(balance)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def recalculate_mtd(self, request, pk=None):
        """Recalculate MTD balance from transactions"""
        balance = self.get_object()
        
        try:
            mtd_value, mtd_vat = balance.calculate_mtd_from_transactions()
            balance.save()
            
            serializer = self.get_serializer(balance)
            return Response({
                'balance': serializer.data,
                'mtd_value': str(mtd_value),
                'mtd_vat': str(mtd_vat)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class IncomeCategoryBalanceViewSet(viewsets.ModelViewSet):
    """API endpoint for income category balances (per spec CBINC)"""
    queryset = IncomeCategoryBalance.objects.select_related('income_category')
    serializer_class = IncomeCategoryBalanceSerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['income_category']
    search_fields = ['income_category__name']
    ordering_fields = ['balance_month_to_date', 'updated_at']
    ordering = ['-balance_month_to_date']
    
    @action(detail=True, methods=['patch'])
    def close_month(self, request, pk=None):
        """Close month for category balance"""
        balance = self.get_object()
        
        month = request.data.get('month')
        year = request.data.get('year')
        
        if not month or not year:
            return Response(
                {'error': 'month and year are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            balance.set_month_balance(month, balance.balance_month_to_date)
            balance.balance_month_to_date = Decimal('0')
            balance.output_vat_month_to_date = Decimal('0')
            balance.save()
            
            serializer = self.get_serializer(balance)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def recalculate_mtd(self, request, pk=None):
        """Recalculate MTD balance from transactions"""
        balance = self.get_object()
        
        try:
            mtd_value, mtd_vat = balance.calculate_mtd_from_transactions()
            balance.save()
            
            serializer = self.get_serializer(balance)
            return Response({
                'balance': serializer.data,
                'mtd_value': str(mtd_value),
                'mtd_vat': str(mtd_vat)
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class UnpresentedChequeViewSet(viewsets.ModelViewSet):
    """API endpoint for unpresented cheques (per spec CBCHEQ)"""
    queryset = UnpresentedCheque.objects.all()
    serializer_class = UnpresentedChequeSerializer
    permission_classes = [IsAuthenticated, CanViewTransactions]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_presented', 'tag', 'is_stale', 'requires_follow_up']
    search_fields = ['cheque_number', 'reference']
    ordering_fields = ['cheque_date', 'days_outstanding']
    ordering = ['-cheque_date']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UnpresentedChequeListSerializer
        elif self.action == 'create':
            return CreateUnpresentedChequeSerializer
        return UnpresentedChequeSerializer
    
    @action(detail=True, methods=['patch'])
    def mark_presented(self, request, pk=None):
        """Mark cheque as presented"""
        cheque = self.get_object()
        
        presented_date = request.data.get('presented_date')
        
        try:
            cheque.mark_as_presented(presented_date)
            serializer = UnpresentedChequeSerializer(cheque)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def reconciliation_summary(self, request):
        """Get unpresented cheques summary for bank reconciliation"""
        month_end_date = request.query_params.get('month_end_date')
        
        if not month_end_date:
            return Response(
                {'error': 'month_end_date parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from datetime import datetime
            month_end = datetime.strptime(month_end_date, '%Y-%m-%d').date()
            summary = UnpresentedCheque.get_unpresented_summary(month_end)
            return Response(summary)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_mark_presented(self, request):
        """Mark multiple cheques as presented"""
        cheque_numbers = request.data.get('cheque_numbers', [])
        presented_date = request.data.get('presented_date')
        
        if not cheque_numbers:
            return Response(
                {'error': 'cheque_numbers list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from cash_book.business_services import UnpresentedChequeService
            count = UnpresentedChequeService.mark_cheques_as_presented(
                cheque_numbers, presented_date
            )
            return Response({
                'count': count,
                'message': f'{count} cheques marked as presented'
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
