"""
Debtors views.
API viewsets for all debtor-related operations.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from datetime import date, timedelta
from django.db import transaction as db_transaction
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Debtor, DebtorTransaction, Invoice, PostDatedCheque, AuditLog
from .serializers import (
    DebtorListSerializer, DebtorDetailSerializer,
    DebtorCreateUpdateSerializer, DebtorTransactionSerializer,
    InvoiceListSerializer, InvoiceDetailSerializer,
    InvoiceCreateSerializer, InvoiceUpdateSerializer,
    PostDatedChequeSerializer, AgeAnalysisSerializer,
    DebtorStatementSerializer, DebtorSummarySerializer
)
from .services import DebtorService, InvoiceService
from .filters import DebtorFilter, InvoiceFilter, DebtorTransactionFilter
from .permissions import HasDebtorPermission, CanModifyDebtor, CanPostInvoice


class DebtorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing debtors (customers).
    
    Provides CRUD operations plus additional actions:
    - age_analysis: Get age analysis for a debtor
    - transactions: Get all transactions for a debtor
    - statement: Generate debtor statement
    - check_credit: Check credit limit status
    - summary: Get summary statistics for all debtors
    - top_customers: Get top customers by sales
    """
    queryset = Debtor.objects.all()
    permission_classes = [IsAuthenticated, HasDebtorPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = DebtorFilter
    search_fields = ['account_number', 'name', 'search_name', 'contact_person']
    ordering_fields = ['account_number', 'name', 'current_balance', 'created_at']
    ordering = ['account_number']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DebtorListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DebtorCreateUpdateSerializer
        return DebtorDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset with select_related."""
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.select_related('sales_area')
        return queryset
    
    @action(detail=True, methods=['get'])
    def age_analysis(self, request, pk=None):
        """Get age analysis for a specific debtor."""
        debtor = self.get_object()
        data = DebtorService.calculate_age_analysis(debtor)
        serializer = AgeAnalysisSerializer(data)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for a debtor."""
        debtor = self.get_object()
        
        # Get filter parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        transaction_type = request.query_params.get('transaction_type')
        
        # Base query
        transactions = DebtorTransaction.objects.filter(debtor=debtor)
        
        # Apply filters
        if start_date:
            transactions = transactions.filter(transaction_date__gte=start_date)
        if end_date:
            transactions = transactions.filter(transaction_date__lte=end_date)
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        
        transactions = transactions.order_by('-transaction_date')
        
        # Check if no transactions exist
        if not transactions.exists():
            return Response({
                'status': 'no_data',
                'message': f'No transactions found for debtor {debtor.account_number}',
                'data': []
            })
        
        # Paginate
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = DebtorTransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = DebtorTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statement(self, request, pk=None):
        """Generate debtor statement for a period."""
        debtor = self.get_object()
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Parse dates if provided
        if start_date:
            from datetime import datetime
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            from datetime import datetime
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        try:
            statement_data = DebtorService.get_debtor_statement(
                debtor, start_date, end_date
            )
            
            # Check if statement has any transactions
            if not statement_data['transactions']:
                return Response({
                    'status': 'no_data',
                    'message': f'No statement data found for debtor {debtor.account_number} for the specified period',
                    'data': statement_data
                })
            
            serializer = DebtorStatementSerializer(statement_data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def check_credit(self, request, pk=None):
        """Check credit limit status for a debtor."""
        debtor = self.get_object()
        credit_status = DebtorService.check_credit_limit(debtor)
        return Response(credit_status)
    
    @action(detail=True, methods=['get'], url_path='balance-details', name='Balance Details')
    def balance_details(self, request, pk=None):
        """Get detailed balance breakdown for a debtor."""
        debtor = self.get_object()
        
        if not debtor:
            return Response(
                {'status': 'error', 'message': 'Debtor not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            balance_data = {
                'account_number': debtor.account_number,
                'name': debtor.name,
                'contact_person': debtor.contact_person,
                'telephone1': debtor.telephone1,
                'email': debtor.email if hasattr(debtor, 'email') else '',
                'credit_limit': float(debtor.credit_limit),
                'balance_breakdown': {
                    'current': float(debtor.current_balance),
                    'days_30': float(debtor.balance_30_days),
                    'days_60': float(debtor.balance_60_days),
                    'days_90': float(debtor.balance_90_days),
                    'days_120': float(debtor.balance_120_days),
                    'days_150': float(debtor.balance_150_days),
                    'days_180': float(debtor.balance_180_days),
                },
                'total_balance': float(debtor.total_balance),
                'available_credit': float(debtor.credit_limit - debtor.total_balance),
                'credit_used_percentage': float((debtor.total_balance / debtor.credit_limit * 100) if debtor.credit_limit > 0 else 0),
                'is_over_credit_limit': debtor.total_balance > debtor.credit_limit,
                'is_blocked': debtor.is_blocked,
                'block_reason': debtor.block_reason if debtor.is_blocked else '',
                'is_active': debtor.is_active,
                'last_payment_date': debtor.last_payment_date,
                'last_payment_amount': float(debtor.last_payment_amount) if debtor.last_payment_amount else 0,
                'sales_mtd': float(debtor.sales_mtd),
                'sales_ytd': float(debtor.sales_ytd),
                'charge_interest': debtor.charge_interest,
            }
            return Response(balance_data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': f'Failed to retrieve balance details: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for all debtors."""
        summary_data = DebtorService.get_debtors_summary()
        serializer = DebtorSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def top_customers(self, request):
        """Get top customers by sales value."""
        limit = int(request.query_params.get('limit', 10))
        period = request.query_params.get('period', 'month')  # month, year, all
        
        try:
            top_debtors = InvoiceService.get_top_customers(limit, period)
            
            if not top_debtors:
                return Response({
                    'status': 'no_data',
                    'message': f'No top customers found for period: {period}',
                    'data': []
                })
            
            serializer = DebtorListSerializer(top_debtors, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    @db_transaction.atomic
    def charge_interest(self, request):
        """Charge interest on all eligible debtors."""
        try:
            rate = float(request.data.get('rate', 0.01))
            start_period = int(request.data.get('start_period', 2))
            
            result = DebtorService.charge_interest_batch(rate, start_period)
            
            if result['debtors_charged'] == 0:
                return Response({
                    'status': 'no_data',
                    'message': 'No eligible debtors found to charge interest',
                    'data': result
                })
            
            return Response(result)
        except (ValueError, TypeError) as e:
            return Response(
                {'status': 'error', 'message': f'Invalid parameters: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    @db_transaction.atomic
    def age_balances(self, request):
        """Age all debtor balances (month-end process)."""
        try:
            count = DebtorService.age_balances()
            
            if count == 0:
                return Response({
                    'status': 'no_data',
                    'message': 'No active debtors found to age',
                    'debtors_aged': count
                })
            
            return Response({
                'status': 'success',
                'debtors_aged': count,
                'message': f'Aged balances for {count} debtors'
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a debtor account."""
        debtor = self.get_object()
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response(
                {'error': 'Block reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Store old value for audit
        old_value = f"is_blocked={debtor.is_blocked}"
        
        debtor.is_blocked = True
        debtor.block_reason = reason
        debtor.blocked_by = str(request.user)
        debtor.blocked_date = date.today()
        debtor.save()
        
        # Create audit log
        AuditLog.objects.create(
            debtor=debtor,
            change_type='BLOCK',
            old_value=old_value,
            new_value=f"is_blocked=True, reason={reason}",
            changed_by=str(request.user),
            description=f"Account blocked: {reason}"
        )
        
        return Response({
            'status': 'success',
            'message': f'Debtor {debtor.account_number} blocked'
        })
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """Unblock a debtor account."""
        debtor = self.get_object()
        
        # Store old value for audit
        old_value = f"is_blocked={debtor.is_blocked}"
        
        debtor.is_blocked = False
        debtor.block_reason = ''
        debtor.unblocked_date = date.today()
        debtor.save()
        
        # Create audit log
        AuditLog.objects.create(
            debtor=debtor,
            change_type='UNBLOCK',
            old_value=old_value,
            new_value="is_blocked=False",
            changed_by=str(request.user),
            description="Account unblocked"
        )
        
        return Response({
            'status': 'success',
            'message': f'Debtor {debtor.account_number} unblocked'
        })


class DebtorTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing debtor transactions.
    Read-only as transactions are created through other processes.
    """
    queryset = DebtorTransaction.objects.all()
    serializer_class = DebtorTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = DebtorTransactionFilter
    ordering_fields = ['transaction_date', 'total_amount']
    ordering = ['-transaction_date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('debtor')


class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing invoices.
    
    Provides CRUD operations plus:
    - post_invoice: Post invoice to debtor account
    - cancel_invoice: Cancel an invoice
    - reprint: Mark invoice for reprinting
    """
    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InvoiceFilter
    search_fields = ['invoice_number', 'debtor__name', 'debtor__account_number', 'order_number']
    ordering_fields = ['invoice_date', 'invoice_number', 'total_amount']
    ordering = ['-invoice_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return InvoiceListSerializer
        elif self.action == 'create':
            return InvoiceCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InvoiceUpdateSerializer
        return InvoiceDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.select_related('debtor', 'sales_area')
        elif self.action == 'retrieve':
            queryset = queryset.select_related('debtor', 'sales_area').prefetch_related('lines')
        return queryset
    
    def perform_create(self, serializer):
        """Create invoice."""
        invoice = serializer.save()
        return Response(
            InvoiceDetailSerializer(invoice).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    @db_transaction.atomic
    def post_invoice(self, request, pk=None):
        """Post invoice to debtor account."""
        invoice = self.get_object()
        
        try:
            # Validate invoice can be posted
            if not invoice.can_be_posted():
                return Response(
                    {'status': 'error', 'message': f'Invoice cannot be posted (status: {invoice.status})'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Use service to post invoice
            DebtorService.post_invoice(invoice)
            invoice.mark_as_posted()
            
            return Response({
                'status': 'success',
                'message': f'Invoice {invoice.invoice_number} posted successfully',
                'invoice': InvoiceDetailSerializer(invoice).data
            })
        except (ValueError, DjangoValidationError) as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': f'Failed to post invoice: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    @db_transaction.atomic
    def cancel_invoice(self, request, pk=None):
        """Cancel an invoice."""
        invoice = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            # Validate cancellation
            if invoice.status == 'PAID':
                return Response(
                    {'status': 'error', 'message': 'Cannot cancel a paid invoice'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            DebtorService.cancel_invoice(invoice, reason)
            invoice.mark_as_cancelled(reason)
            
            return Response({
                'status': 'success',
                'message': f'Invoice {invoice.invoice_number} cancelled',
                'invoice': InvoiceDetailSerializer(invoice).data
            })
        except (ValueError, DjangoValidationError) as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': f'Failed to cancel invoice: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def recalculate(self, request, pk=None):
        """Recalculate invoice totals from lines."""
        invoice = self.get_object()
        
        if invoice.is_posted:
            return Response(
                {'status': 'error', 'message': 'Cannot recalculate posted invoice'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            invoice = InvoiceService.calculate_totals(invoice)
            serializer = InvoiceDetailSerializer(invoice)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': f'Failed to recalculate invoice: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def unposted(self, request):
        """Get all unposted invoices."""
        invoices = self.get_queryset().filter(
            is_posted=False,
            is_cancelled=False
        )
        
        if not invoices.exists():
            return Response({
                'status': 'no_data',
                'message': 'No unposted invoices found',
                'data': []
            })
        
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = InvoiceListSerializer(invoices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_date_range(self, request):
        """Get invoices within a date range."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {'status': 'error', 'message': 'start_date and end_date required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        invoices = self.get_queryset().filter(
            invoice_date__gte=start_date,
            invoice_date__lte=end_date
        )
        
        if not invoices.exists():
            return Response({
                'status': 'no_data',
                'message': f'No invoices found between {start_date} and {end_date}',
                'invoices': [],
                'totals': {
                    'total_amount': 0,
                    'total_vat': 0,
                    'total_profit': 0,
                    'count': 0
                }
            })
        
        # Calculate totals
        totals = invoices.aggregate(
            total_amount=Sum('total_amount'),
            total_vat=Sum('vat_amount'),
            total_profit=Sum('gross_profit'),
            count=Count('id')
        )
        
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = InvoiceListSerializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data).data
            response_data['totals'] = totals
            return Response(response_data)
        
        serializer = InvoiceListSerializer(invoices, many=True)
        return Response({
            'invoices': serializer.data,
            'totals': totals
        })


class PostDatedChequeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing post-dated cheques.
    """
    queryset = PostDatedCheque.objects.all()
    serializer_class = PostDatedChequeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['debtor', 'is_processed', 'cheque_date']
    ordering_fields = ['cheque_date', 'amount']
    ordering = ['cheque_date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('debtor')
    
    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """Get PDCs due today."""
        today = date.today()
        pdcs = self.get_queryset().filter(
            cheque_date=today,
            is_processed=False
        )
        
        if not pdcs.exists():
            return Response({
                'status': 'no_data',
                'message': f'No post-dated cheques due today ({today})',
                'data': []
            })
        
        serializer = self.get_serializer(pdcs, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue PDCs."""
        today = date.today()
        pdcs = self.get_queryset().filter(
            cheque_date__lt=today,
            is_processed=False
        )
        
        if not pdcs.exists():
            return Response({
                'status': 'no_data',
                'message': 'No overdue post-dated cheques',
                'data': []
            })
        
        serializer = self.get_serializer(pdcs, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Mark PDC as processed."""
        pdc = self.get_object()
        
        if pdc.is_processed:
            return Response(
                {'status': 'error', 'message': 'PDC already processed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            pdc.is_processed = True
            pdc.processed_date = date.today()
            pdc.save()
            
            return Response({
                'status': 'success',
                'message': 'PDC marked as processed'
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': f'Failed to process PDC: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get PDC summary."""
        queryset = self.get_queryset()
        
        total_pdcs = queryset.count()
        processed = queryset.filter(is_processed=True).count()
        outstanding = queryset.filter(is_processed=False).count()
        
        total_amount = queryset.filter(is_processed=False).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        return Response({
            'total_pdcs': total_pdcs,
            'processed': processed,
            'outstanding': outstanding,
            'total_amount_outstanding': total_amount,
        })