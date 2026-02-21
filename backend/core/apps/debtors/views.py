"""
Debtors views.
API viewsets for all debtor-related operations.
Based on DMAST, DEBTRAN, DEBTOPEN, DPDC, DEBTORAUD tables.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncMonth
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction as db_transaction

from .models import (
    Debtor, DebtorTransaction, Debtopen, Dpdc, DebtorAudit, Darea
)
from apps.pos.models import CreditNote, CashSale, JobCard, Invoice
from apps.purchase_orders.models import PurchaseOrder
from .serializers import (
    DebtorListSerializer, DebtorDetailSerializer,
    DebtorCreateUpdateSerializer, DebtorTransactionSerializer,
    DebteopenSerializer, DpdcSerializer, DebtorAuditSerializer,
    DareaSerializer, AgeAnalysisSerializer, DebtorSummarySerializer,
    DebtranListSerializer, DebtOpenListSerializer
)
from .filters import DebtorFilter, DebtorTransactionFilter
from .permissions import (
    HasDebtorPermission, CanModifyDebtor, CanPostInvoice, 
    CanChargeInterest
)
from apps.common.permissions import BaseModelPermission, CanPostTransaction


class DebtorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing debtors (customers) - DMAST table.
    
    Provides CRUD operations plus actions:
    - age_analysis: Age analysis for debtor
    - transactions: Get debtor transactions
    - summary: Get all debtors summary
    - block: Block debtor account
    - unblock: Unblock debtor account
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: ADMIN and MANAGER roles only
    """
    queryset = Debtor.objects.all()
    permission_classes = [IsAuthenticated, HasDebtorPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_number', 'name', 'short_name', 'contact_person']
    ordering_fields = ['customer_number', 'name', 'balance_current', 'created_at']
    ordering = ['customer_number']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DebtorListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DebtorCreateUpdateSerializer
        return DebtorDetailSerializer
    
    @action(detail=True, methods=['get'])
    def age_analysis(self, request, pk=None):
        """Get age analysis for a debtor."""
        try:
            debtor = self.get_object()
            data = {
                'dno': debtor.customer_number,
                'dname': debtor.name,
                'dcontact': debtor.contact_person,
                'dtel': debtor.phone,
                'dclimit': debtor.credit_limit,
                'current': debtor.balance_current,
                'days_30': debtor.balance_30_days,
                'days_60': debtor.balance_60_days,
                'days_90': debtor.balance_90_days,
                'days_120': debtor.balance_120_days,
                'days_150': debtor.balance_150_days,
                'days_180': debtor.balance_180_days,
                'total_balance': debtor.get_total_balance(),
                'overdue_balance': debtor.get_overdue_balance(),
                'ddatlpd': debtor.last_payment_date,
                'damtlpd': debtor.last_payment_amount,
            }
            serializer = AgeAnalysisSerializer(data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for a debtor (DEBTRAN)."""
        try:
            debtor = self.get_object()
            
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            dtype = request.query_params.get('dtype')
            
            transactions = DebtorTransaction.objects.filter(customer_number=debtor)
            
            if start_date:
                transactions = transactions.filter(dtdate__gte=start_date)
            if end_date:
                transactions = transactions.filter(dtdate__lte=end_date)
            if dtype:
                transactions = transactions.filter(dtype=dtype)
            
            transactions = transactions.order_by('-dtdate')
            
            page = self.paginate_queryset(transactions)
            if page is not None:
                serializer = DebtorTransactionSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = DebtorTransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary statistics for all debtors."""
        try:
            debtors = self.get_queryset()
            
            total_debtors = debtors.count()
            active_debtors = debtors.filter(is_active=True).count()
            blocked_debtors = debtors.filter(block_flag='Y').count()
            
            aggregates = debtors.aggregate(
                total_balance=Sum('balance_current'),
                current_balance=Sum('balance_current'),
                d30_total=Sum('balance_30_days'),
                d60_total=Sum('balance_60_days'),
                d90_total=Sum('balance_90_days'),
            )
            
            data = {
                'total_debtors': total_debtors,
                'active_debtors': active_debtors,
                'blocked_debtors': blocked_debtors,
                'total_balance': aggregates['total_balance'] or Decimal('0.00'),
                'current_balance': aggregates['current_balance'] or Decimal('0.00'),
                'overdue_30': aggregates['d30_total'] or Decimal('0.00'),
                'overdue_60': aggregates['d60_total'] or Decimal('0.00'),
                'overdue_90': aggregates['d90_total'] or Decimal('0.00'),
                'overdue_120_plus': sum([
                    debtors.aggregate(Sum('balance_120_days'))['balance_120_days__sum'] or Decimal('0.00'),
                    debtors.aggregate(Sum('balance_150_days'))['balance_150_days__sum'] or Decimal('0.00'),
                    debtors.aggregate(Sum('balance_180_days'))['balance_180_days__sum'] or Decimal('0.00'),
                ]),
            }
            
            serializer = DebtorSummarySerializer(data)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """Block a debtor account."""
        try:
            debtor = self.get_object()
            debtor.set_blocked(True)
            
            return Response({
                'status': 'success',
                'message': f'Debtor {debtor.customer_number} blocked successfully'
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def unblock(self, request, pk=None):
        """Unblock a debtor account."""
        try:
            debtor = self.get_object()
            debtor.set_blocked(False)
            
            return Response({
                'status': 'success',
                'message': f'Debtor {debtor.customer_number} unblocked successfully'
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def balance_details(self, request, pk=None):
        """Get detailed balance breakdown for debtor."""
        try:
            debtor = self.get_object()
            
            balance_data = {
                'customer_number': debtor.customer_number,
                'name': debtor.name,
                'credit_limit': float(debtor.credit_limit),
                'balance_breakdown': {
                    'current': float(debtor.balance_current),
                    '30_days': float(debtor.balance_30_days),
                    '60_days': float(debtor.balance_60_days),
                    '90_days': float(debtor.balance_90_days),
                    '120_days': float(debtor.balance_120_days),
                    '150_days': float(debtor.balance_150_days),
                    '180_days': float(debtor.balance_180_days),
                },
                'total_balance': float(debtor.get_total_balance()),
                'available_credit': float(debtor.credit_limit - debtor.get_total_balance()),
                'credit_utilization_pct': float(
                    (debtor.get_total_balance() / debtor.credit_limit * 100) 
                    if debtor.credit_limit > 0 else 0
                ),
                'is_blocked': debtor.is_blocked(),
                'is_active': debtor.is_active,
                'last_payment': {
                    'date': debtor.last_payment_date,
                    'amount': float(debtor.last_payment_amount),
                },
                'sales': {
                    'mtd': float(debtor.sales_month),
                    'ytd': float(debtor.sales_year),
                },
            }
            return Response(balance_data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DebtorTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for debtor transactions (DEBTRAN).
    Read-only as transactions are created through posting processes.
    
    Provides actions:
    - summary: Get transaction summary by type
    - monthly_trends: Get monthly transaction trends
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
        return super().get_queryset().select_related('customer_number')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get transaction summary by type.
        Returns count and total amount for each transaction type.
        """
        try:
            summary = self.get_queryset().values('transaction_type').annotate(
                count=Count('id'),
                total=Sum('total_amount')
            ).order_by('transaction_type')
            return Response(list(summary))
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def monthly_trends(self, request):
        """
        Get monthly transaction trends for the past year.
        Returns count and total for each transaction type by month.
        """
        try:
            trends = self.get_queryset().filter(
                transaction_date__gte=date.today() - timedelta(days=365)
            ).annotate(
                month=TruncMonth('transaction_date')
            ).values('month', 'transaction_type').annotate(
                count=Count('id'),
                total=Sum('total_amount')
            ).order_by('month', 'transaction_type')
            return Response(list(trends))
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def aging_summary(self, request):
        """
        Get aging summary for all outstanding transactions.
        Groups outstanding amounts by age bucket.
        """
        try:
            aging = DebtorTransaction.objects.aging_analysis()
            return Response(aging)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def debtor_summary(self, request):
        """
        Get summary of outstanding balance by debtor.
        Useful for AR dashboard and collection follow-up.
        """
        try:
            summary = self.get_queryset().filter(
                transaction_type__in=['IN', 'CS'],
                is_allocated=False
            ).values('customer_number', 'customer_number__name').annotate(
                outstanding=Sum('total_amount'),
                transaction_count=Count('id')
            ).order_by('-outstanding')
            return Response(list(summary))
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DebteopenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for open item transactions (DEBTOPEN).
    Tracks individual open item postings for debtor accounts.
    """
    queryset = Debtopen.objects.all()
    serializer_class = DebteopenSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer_number', 'type', 'posted', 'ageflag']
    ordering_fields = ['date', 'total']
    ordering = ['-date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('customer_number')
    
    @action(detail=False, methods=['get'])
    def outstanding(self, request):
        """Get all outstanding open items."""
        try:
            outstanding = self.get_queryset().filter(
                balancedue__gt=0,
                posted='Y'
            )
            
            page = self.paginate_queryset(outstanding)
            if page is not None:
                serializer = DebteopenSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = DebteopenSerializer(outstanding, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def allocate(self, request, pk=None):
        """Allocate payment against open item."""
        try:
            debtor = self.get_object()
            allocation_amount = Decimal(str(request.data.get('amount', 0)))
            
            if allocation_amount <= 0:
                return Response(
                    {'status': 'error', 'message': 'Allocation amount must be greater than zero'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if allocation_amount > debtor.balancedue:
                return Response(
                    {'status': 'error', 'message': 'Allocation cannot exceed balance due'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            debtor.balancedue -= allocation_amount
            debtor.save(update_fields=['balancedue'])
            
            return Response({
                'status': 'success',
                'message': 'Payment allocated successfully',
                'new_balance': float(debtor.balancedue)
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DpdcViewSet(viewsets.ModelViewSet):
    """
    ViewSet for post-dated cheques (DPDC).
    """
    queryset = Dpdc.objects.all()
    serializer_class = DpdcSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer_number', 'status', 'date']
    ordering_fields = ['date', 'amount']
    ordering = ['date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('customer_number')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active post-dated cheques."""
        try:
            active = self.get_queryset().filter(status='A')
            
            page = self.paginate_queryset(active)
            if page is not None:
                serializer = DpdcSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = DpdcSerializer(active, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def due_today(self, request):
        """Get PDCs due today."""
        try:
            today = date.today()
            pdcs = self.get_queryset().filter(
                date=today,
                status='A'
            )
            
            if not pdcs.exists():
                return Response({
                    'status': 'no_data',
                    'message': f'No post-dated cheques due today',
                    'data': []
                })
            
            serializer = DpdcSerializer(pdcs, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Mark cheque as processed."""
        try:
            pdc = self.get_object()
            
            if pdc.status == 'P':
                return Response(
                    {'status': 'error', 'message': 'PDC already processed'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            pdc.status = 'P'
            pdc.save(update_fields=['status'])
            
            return Response({
                'status': 'success',
                'message': 'PDC marked as processed'
            })
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class DebtorAuditViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for debtor audit records (DEBTORAUD).
    Read-only for audit trail purposes.
    """
    queryset = DebtorAudit.objects.all()
    serializer_class = DebtorAuditSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['customer_number', 'type', 'date']
    ordering_fields = ['date']
    ordering = ['-date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('customer_number')


class DareaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for sales area/salesman data (DAREA).
    """
    queryset = Darea.objects.all()
    serializer_class = DareaSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['darea', 'dareaname']
    ordering = ['darea']


class DocumentSearchViewSet(viewsets.ViewSet):
    """
    Unified document search endpoint for Stockfinder API integration.
    
    Searches across:
    - Invoices
    - Credit Notes
    - Cash Sales
    - Purchase Orders
    - Job Cards
    
    Supports filtering by:
    - Document type (invoice, credit_note, cash_sale, purchase_order, job_card)
    - Document number
    - Date range
    - Debtor/Customer
    - Status
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Unified document search.
        
        Query Parameters:
        - type: Document type (invoice, credit_note, cash_sale, purchase_order, job_card, all)
        - number: Document number or partial match
        - date_from: Start date (YYYY-MM-DD)
        - date_to: End date (YYYY-MM-DD)
        - debtor_id: Debtor number
        - status: Document status
        """
        try:
            doc_type = request.query_params.get('type', 'all').lower()
            doc_number = request.query_params.get('number', '').strip()
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            debtor_id = request.query_params.get('debtor_id')
            doc_status = request.query_params.get('status')
            
            results = {
                'invoices': [],
                'credit_notes': [],
                'cash_sales': [],
                'purchase_orders': [],
                'job_cards': [],
                'total_documents': 0
            }
            
            # Build date filters
            date_filters = {}
            if date_from:
                date_filters['date_gte'] = date_from
            if date_to:
                date_filters['date_lte'] = date_to
            
            # Search Invoices
            if doc_type in ['invoice', 'all']:
                invoices = Invoice.objects.all()
                
                if doc_number:
                    invoices = invoices.filter(invoice_number__icontains=doc_number)
                
                if debtor_id:
                    invoices = invoices.filter(debtor__customer_number=debtor_id)
                
                if doc_status:
                    invoices = invoices.filter(status=doc_status)
                
                if date_from and date_to:
                    invoices = invoices.filter(
                        invoice_date__gte=date_from,
                        invoice_date__lte=date_to
                    )
                elif date_from:
                    invoices = invoices.filter(invoice_date__gte=date_from)
                elif date_to:
                    invoices = invoices.filter(invoice_date__lte=date_to)
                
                invoices = invoices.select_related('debtor').values(
                    'id', 'invoice_number', 'invoice_date', 'debtor__name',
                    'total_amount', 'status'
                )[:50]
                
                results['invoices'] = [
                    {
                        'document_id': inv['id'],
                        'document_number': inv['invoice_number'],
                        'document_type': 'invoice',
                        'document_date': inv['invoice_date'],
                        'customer': inv['debtor__name'],
                        'amount': float(inv['total_amount']),
                        'status': inv['status']
                    }
                    for inv in invoices
                ]
            
            # Search Credit Notes
            if doc_type in ['credit_note', 'all']:
                credit_notes = CreditNote.objects.all()
                
                if doc_number:
                    credit_notes = credit_notes.filter(credit_number__icontains=doc_number)
                
                if debtor_id:
                    credit_notes = credit_notes.filter(debtor_account=debtor_id)
                
                if date_from and date_to:
                    credit_notes = credit_notes.filter(
                        credit_date__gte=date_from,
                        credit_date__lte=date_to
                    )
                elif date_from:
                    credit_notes = credit_notes.filter(credit_date__gte=date_from)
                elif date_to:
                    credit_notes = credit_notes.filter(credit_date__lte=date_to)
                
                credit_notes = credit_notes.values(
                    'id', 'credit_number', 'credit_date', 'customer_name',
                    'total_amount', 'is_posted'
                )[:50]
                
                results['credit_notes'] = [
                    {
                        'document_id': cn['id'],
                        'document_number': cn['credit_number'],
                        'document_type': 'credit_note',
                        'document_date': cn['credit_date'],
                        'customer': cn['customer_name'],
                        'amount': float(cn['total_amount']),
                        'status': 'POSTED' if cn['is_posted'] else 'DRAFT'
                    }
                    for cn in credit_notes
                ]
            
            # Search Cash Sales
            if doc_type in ['cash_sale', 'all']:
                cash_sales = CashSale.objects.all()
                
                if doc_number:
                    cash_sales = cash_sales.filter(sale_number__icontains=doc_number)
                
                if date_from and date_to:
                    cash_sales = cash_sales.filter(
                        sale_date__gte=date_from,
                        sale_date__lte=date_to
                    )
                elif date_from:
                    cash_sales = cash_sales.filter(sale_date__gte=date_from)
                elif date_to:
                    cash_sales = cash_sales.filter(sale_date__lte=date_to)
                
                cash_sales = cash_sales.values(
                    'id', 'sale_number', 'sale_date', 'customer_name',
                    'total_amount', 'is_posted'
                )[:50]
                
                results['cash_sales'] = [
                    {
                        'document_id': cs['id'],
                        'document_number': cs['sale_number'],
                        'document_type': 'cash_sale',
                        'document_date': cs['sale_date'],
                        'customer': cs['customer_name'],
                        'amount': float(cs['total_amount']),
                        'status': 'POSTED' if cs['is_posted'] else 'DRAFT'
                    }
                    for cs in cash_sales
                ]
            
            # Search Purchase Orders
            if doc_type in ['purchase_order', 'all']:
                purchase_orders = PurchaseOrder.objects.all()
                
                if doc_number:
                    purchase_orders = purchase_orders.filter(po_number__icontains=doc_number)
                
                if doc_status:
                    purchase_orders = purchase_orders.filter(status=doc_status)
                
                if date_from and date_to:
                    purchase_orders = purchase_orders.filter(
                        po_date__gte=date_from,
                        po_date__lte=date_to
                    )
                elif date_from:
                    purchase_orders = purchase_orders.filter(po_date__gte=date_from)
                elif date_to:
                    purchase_orders = purchase_orders.filter(po_date__lte=date_to)
                
                purchase_orders = purchase_orders.select_related('supplier').values(
                    'id', 'po_number', 'po_date', 'supplier__cname',
                    'total_amount', 'status'
                )[:50]
                
                results['purchase_orders'] = [
                    {
                        'document_id': po['id'],
                        'document_number': po['po_number'],
                        'document_type': 'purchase_order',
                        'document_date': po['po_date'],
                        'supplier': po['supplier__cname'],
                        'amount': float(po['total_amount']),
                        'status': po['status']
                    }
                    for po in purchase_orders
                ]
            
            # Search Job Cards
            if doc_type in ['job_card', 'all']:
                job_cards = JobCard.objects.all()
                
                if doc_number:
                    job_cards = job_cards.filter(job_number__icontains=doc_number)
                
                if doc_status:
                    job_cards = job_cards.filter(status=doc_status)
                
                if date_from and date_to:
                    job_cards = job_cards.filter(
                        job_date__gte=date_from,
                        job_date__lte=date_to
                    )
                elif date_from:
                    job_cards = job_cards.filter(job_date__gte=date_from)
                elif date_to:
                    job_cards = job_cards.filter(job_date__lte=date_to)
                
                job_cards = job_cards.values(
                    'id', 'job_number', 'job_date', 'customer_name',
                    'total_amount', 'status'
                )[:50]
                
                results['job_cards'] = [
                    {
                        'document_id': jc['id'],
                        'document_number': jc['job_number'],
                        'document_type': 'job_card',
                        'document_date': jc['job_date'],
                        'customer': jc['customer_name'],
                        'amount': float(jc['total_amount']),
                        'status': jc['status']
                    }
                    for jc in job_cards
                ]
            
            # Calculate total documents
            results['total_documents'] = (
                len(results['invoices']) +
                len(results['credit_notes']) +
                len(results['cash_sales']) +
                len(results['purchase_orders']) +
                len(results['job_cards'])
            )
            
            return Response(results)
        
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )