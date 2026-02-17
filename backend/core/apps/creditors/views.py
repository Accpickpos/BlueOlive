"""
Enterprise-grade views for Creditors module
Features: Comprehensive permissions, pagination, filtering, transaction management
"""

import logging
from rest_framework import viewsets, status, filters, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from django.db.models import Q, Sum, F, DecimalField, Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime
from decimal import Decimal

from .models import (
    Creditor, GoodsReceivedNote, GRNLineItem,
    CreditorInvoice, CreditorInvoiceLineItem, CreditorCreditNote,
    CreditorCreditNoteLineItem, CreditorPayment, CreditorJournal,
    CreditorOpenItem, OpenItemAllocation, RFC, RFCLineItem,
    ExpenseCategoryMonthlyBalance, OpenItemAudit
)
from .serializers import (
    CreditorListSerializer, CreditorDetailSerializer, CreditorCreateUpdateSerializer,
    GoodsReceivedNoteSerializer, GoodsReceivedNoteCreateSerializer,
    CreditorInvoiceSerializer, CreditorPaymentSerializer, CreditorJournalSerializer,
    OpenItemAllocationSerializer, OpenItemSerializer,
    RFCSerializer, RFCLineItemSerializer,
    AgingAnalysisSerializer, BulkPaymentSerializer
)
from .permissions import (
    HasCreditorPermission, CanModifyCreditor, CanReceiveGoods,
    CanPostCreditorInvoice, CanPostCreditorPayment, CanReconcileCreditor
)



# ============================================================================
# PAGINATION
# ============================================================================

class StandardResultsSetPagination(pagination.PageNumberPagination):
    """Standard pagination for list views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LargeResultsSetPagination(pagination.PageNumberPagination):
    """Pagination for large datasets"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


# ============================================================================
# CREDITOR VIEWSET
# ============================================================================

class CreditorViewSet(viewsets.ModelViewSet):
    """
    Enterprise ViewSet for managing creditors/suppliers.
    
    Features:
    - Comprehensive filtering, searching, and ordering
    - Bulk operations (activate, deactivate, recalculate_aged_balances)
    - Balance aging analysis
    - Outstanding items summaries
    - Pagination and optimization
    
    Endpoints:
    - GET /creditors/ - List creditors
    - POST /creditors/ - Create creditor (ADMIN/MANAGER only)
    - GET /creditors/{id}/ - Get creditor details
    - PUT /creditors/{id}/ - Update creditor (ADMIN/MANAGER only)
    - PATCH /creditors/{id}/ - Partial update (ADMIN/MANAGER only)
    - DELETE /creditors/{id}/ - Deactivate creditor (ADMIN/MANAGER only)
    - GET /creditors/{id}/aging-analysis/ - Get balance aging
    - GET /creditors/{id}/outstanding-items/ - Get overdue items
    - GET /creditors/outstanding-balance/ - List all outstanding items
    - POST /creditors/bulk-activate/ - Bulk activate (ADMIN/MANAGER only)
    - POST /creditors/bulk-deactivate/ - Bulk deactivate (ADMIN/MANAGER only)
    
    Permissions:
    - List/Retrieve: All authenticated users
    - Create/Update/Delete: ADMIN and MANAGER roles only
    """
    
    queryset = Creditor.objects.all()
    permission_classes = [IsAuthenticated, HasCreditorPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter
    ]
    filterset_fields = ['is_active', 'account_category', 'credit_terms']
    search_fields = ['supplier_number', 'name', 'email', 'telephone', 'contact_person']
    ordering_fields = ['supplier_number', 'name', 'current_balance', 'created_at']
    ordering = ['supplier_number']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return CreditorListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CreditorCreateUpdateSerializer
        return CreditorDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related"""
        queryset = Creditor.objects.all()
        
        # Optimize with select_related
        queryset = queryset.select_related(
            'credit_terms', 'sales_area'
        )
        
        # Filter by balance range if provided
        balance_min = self.request.query_params.get('balance_min')
        balance_max = self.request.query_params.get('balance_max')
        
        if balance_min:
            try:
                queryset = queryset.filter(current_balance__gte=Decimal(balance_min))
            except (ValueError, TypeError):
                pass
        
        if balance_max:
            try:
                queryset = queryset.filter(current_balance__lte=Decimal(balance_max))
            except (ValueError, TypeError):
                pass
        
        # Filter overdue items if requested
        show_overdue = self.request.query_params.get('overdue_only')
        if show_overdue and show_overdue.lower() == 'true':
            queryset = queryset.filter(
                Q(balance_30_days__gt=0) | Q(balance_60_days__gt=0) | 
                Q(balance_90_days__gt=0) | Q(balance_120_days__gt=0) |
                Q(balance_150_days__gt=0) | Q(balance_180_days__gt=0)
            )
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def aging_analysis(self, request, pk=None):
        """Get detailed aging analysis for creditor"""
        creditor = self.get_object()
        
        serializer = AgingAnalysisSerializer({
            'supplier_number': creditor.supplier_number,
            'name': creditor.name,
            'current_balance': creditor.balance_current,
            'balance_30_days': creditor.balance_30_days,
            'balance_60_days': creditor.balance_60_days,
            'balance_90_days': creditor.balance_90_days,
            'balance_120_days': creditor.balance_120_days,
            'balance_150_days': creditor.balance_150_days,
            'balance_180_days': creditor.balance_180_days,
            'total_balance': creditor.get_current_balance(),
            'last_paid_date': creditor.last_paid_date,
            'credit_terms': creditor.credit_terms.credit_name if creditor.credit_terms else 'N/A'
        })
        
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def outstanding_items(self, request, pk=None):
        """Get outstanding/overdue items for creditor"""
        creditor = self.get_object()
        
        outstanding = CreditorOpenItem.objects.filter(
            creditor=creditor,
            balance_due__gt=0,
            is_fully_allocated=False
        ).order_by('transaction_date')
        
        serializer = OpenItemSerializer(outstanding, many=True)
        
        total_balance = outstanding.aggregate(
            total=Sum('balance_due')
        )['total'] or Decimal('0')
        
        return Response({
            'creditor': creditor.name,
            'count': outstanding.count(),
            'total_outstanding': float(total_balance),
            'items': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def outstanding_balance(self, request):
        """Get outstanding balance items with aging for all suppliers"""
        try:
            # Get creditors with outstanding balances
            creditors = Creditor.objects.filter(
                current_balance__gt=0
            ).select_related('credit_terms', 'sales_area').order_by('-current_balance')
            
            # Filter by creditor if provided
            creditor_id = request.query_params.get('creditor_id')
            supplier_id = request.query_params.get('supplier_id')
            supplier_account_number = request.query_params.get('supplier_account_number')
            
            if creditor_id:
                creditors = creditors.filter(id=creditor_id)
            elif supplier_id:
                creditors = creditors.filter(id=supplier_id)
            elif supplier_account_number:
                creditors = creditors.filter(id=supplier_account_number)
            
            # Paginate
            page = self.paginate_queryset(creditors)
            if page is not None:
                # Format response to match frontend expectations
                data = []
                for creditor in page:
                    data.append({
                        'id': creditor.id,
                        'supplier_id': creditor.id,
                        'creditor_id': creditor.id,
                        'supplier_number': creditor.supplier_number,
                        'name': creditor.name,
                        'capture_date': datetime.now().date().isoformat(),
                        'balance_current': float(creditor.current_balance or 0),
                        'balance_30_days': float(creditor.balance_30_days or 0),
                        'balance_60_days': float(creditor.balance_60_days or 0),
                        'balance_90_days': float(creditor.balance_90_days or 0),
                        'balance_120_days': float(creditor.balance_120_days or 0),
                        'balance_150_days': float(creditor.balance_150_days or 0),
                        'balance_180_days': float(creditor.balance_180_days or 0),
                        'created_at': creditor.created_at.isoformat() if creditor.created_at else None,
                        'updated_at': creditor.updated_at.isoformat() if creditor.updated_at else None,
                    })
                return self.get_paginated_response(data)
            
            # Non-paginated response
            data = []
            for creditor in creditors:
                data.append({
                    'id': creditor.id,
                    'supplier_id': creditor.id,
                    'creditor_id': creditor.id,
                    'supplier_number': creditor.supplier_number,
                    'name': creditor.name,
                    'capture_date': datetime.now().date().isoformat(),
                    'balance_current': float(creditor.current_balance or 0),
                    'balance_30_days': float(creditor.balance_30_days or 0),
                    'balance_60_days': float(creditor.balance_60_days or 0),
                    'balance_90_days': float(creditor.balance_90_days or 0),
                    'balance_120_days': float(creditor.balance_120_days or 0),
                    'balance_150_days': float(creditor.balance_150_days or 0),
                    'balance_180_days': float(creditor.balance_180_days or 0),
                    'created_at': creditor.created_at.isoformat() if creditor.created_at else None,
                    'updated_at': creditor.updated_at.isoformat() if creditor.updated_at else None,
                })
            return Response(data)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f'Error in outstanding_balance: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Failed to fetch outstanding balances: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def bulk_activate(self, request):
        """Bulk activate creditors"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'ids list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = Creditor.objects.filter(id__in=ids).update(is_active=True)
        return Response({
            'message': f'Activated {updated} creditors',
            'count': updated
        })
    
    @action(detail=False, methods=['post'])
    def bulk_deactivate(self, request):
        """Bulk deactivate creditors"""
        ids = request.data.get('ids', [])
        if not ids:
            return Response(
                {'error': 'ids list is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated = Creditor.objects.filter(id__in=ids).update(is_active=False)
        return Response({
            'message': f'Deactivated {updated} creditors',
            'count': updated
        })
    
    @action(detail=False, methods=['post'])
    def recalculate_aged_balances(self, request):
        """Recalculate aged balances for creditors"""
        ids = request.data.get('ids', [])
        
        if ids:
            creditors = Creditor.objects.filter(id__in=ids)
        else:
            creditors = Creditor.objects.all()
        
        count = 0
        for creditor in creditors:
            creditor.recalculate_aged_balances()
            count += 1
        
        return Response({
            'message': f'Recalculated aged balances for {count} creditors',
            'count': count
        })


# ============================================================================
# GOODS RECEIVED NOTE VIEWSET
# ============================================================================

class GoodsReceivedNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Goods Received Notes.
    ADMIN and MANAGER roles can create/update GRNs.
    """
    
    permission_classes = [IsAuthenticated, CanReceiveGoods]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted', 'transaction_date']
    search_fields = ['transaction_number', 'supplier_invoice_number', 'creditor__name']
    ordering_fields = ['transaction_date', 'transaction_number']
    ordering = ['-transaction_date']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GoodsReceivedNoteCreateSerializer
        return GoodsReceivedNoteSerializer
    
    def get_queryset(self):
        return GoodsReceivedNote.objects.select_related(
            'creditor', 'posted_by'
        ).prefetch_related('line_items')
    
    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create GRN with transaction handling"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============================================================================
# CREDITOR INVOICE VIEWSET
# ============================================================================

class CreditorInvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Creditor Invoices.
    ADMIN and MANAGER roles can create/update invoices.
    """
    
    permission_classes = [IsAuthenticated, CanPostCreditorInvoice]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted', 'transaction_date']
    search_fields = ['transaction_number', 'supplier_invoice_number', 'creditor__name']
    ordering_fields = ['transaction_date', 'due_date']
    ordering = ['-transaction_date']
    serializer_class = CreditorInvoiceSerializer
    
    def get_queryset(self):
        return CreditorInvoice.objects.select_related(
            'creditor', 'posted_by'
        ).prefetch_related('line_items')
    
    @action(detail=False, methods=['get'])
    def overdue_invoices(self, request):
        """Get all overdue invoices"""
        today = datetime.now().date()
        invoices = CreditorInvoice.objects.filter(
            due_date__lt=today,
            is_posted=True
        ).select_related('creditor').order_by('due_date')
        
        page = self.paginate_queryset(invoices)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(invoices, many=True)
        return Response(serializer.data)


# ============================================================================
# CREDITOR PAYMENT VIEWSET
# ============================================================================

class CreditorPaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Creditor Payments.
    ADMIN and MANAGER roles can create/update payments.
    """
    
    permission_classes = [IsAuthenticated, CanPostCreditorPayment]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted', 'payment_method']
    search_fields = ['transaction_number', 'creditor__name', 'cheque_number']
    ordering_fields = ['transaction_date']
    ordering = ['-transaction_date']
    serializer_class = CreditorPaymentSerializer
    
    def get_queryset(self):
        return CreditorPayment.objects.select_related(
            'creditor', 'posted_by', 'payment_method'
        )
    
    @db_transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create payment with open item allocation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment = serializer.save()
        
        # Handle allocations if provided
        allocations = request.data.get('allocations', [])
        for allocation in allocations:
            try:
                open_item = CreditorOpenItem.objects.get(id=allocation['open_item_id'])
                OpenItemAllocation.objects.create(
                    payment=payment,
                    open_item=open_item,
                    amount_paid=Decimal(allocation['amount_paid']),
                    settlement_discount=Decimal(allocation.get('settlement_discount', 0))
                )
                
                # Update open item balance
                open_item.balance_due -= Decimal(allocation['amount_paid'])
                if open_item.balance_due <= 0:
                    open_item.is_fully_allocated = True
                open_item.save()
            except (CreditorOpenItem.DoesNotExist, KeyError):
                pass
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ============================================================================
# CREDITOR JOURNAL VIEWSET
# ============================================================================

class CreditorJournalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Creditor Journals.
    ADMIN and MANAGER roles can create/update journals (reconciliation adjustments).
    """
    
    permission_classes = [IsAuthenticated, CanReconcileCreditor]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'journal_type', 'is_posted']
    search_fields = ['transaction_number', 'creditor__name']
    ordering_fields = ['transaction_date']
    ordering = ['-transaction_date']
    serializer_class = CreditorJournalSerializer
    
    def get_queryset(self):
        return CreditorJournal.objects.select_related(
            'creditor', 'posted_by'
        )


# ============================================================================
# OPEN ITEM VIEWSET
# ============================================================================

class OpenItemViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing open items"""
    
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'transaction_type', 'is_fully_allocated']
    search_fields = ['transaction_number', 'creditor__name']
    ordering_fields = ['transaction_date', 'due_date', 'balance_due']
    ordering = ['transaction_date']
    serializer_class = OpenItemSerializer
    
    def get_queryset(self):
        return CreditorOpenItem.objects.select_related(
            'creditor'
        ).order_by('transaction_date')
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue open items"""
        today = datetime.now().date()
        overdue = CreditorOpenItem.objects.filter(
            due_date__lt=today,
            balance_due__gt=0,
            is_fully_allocated=False
        ).order_by('due_date')
        
        page = self.paginate_queryset(overdue)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(overdue, many=True)
        return Response(serializer.data)


# ============================================================================
# RFC VIEWSET
# ============================================================================

class RFCViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Returns for Credit.
    ADMIN and MANAGER roles can create/update RFCs.
    """
    
    permission_classes = [IsAuthenticated, HasCreditorPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'status']
    search_fields = ['rfc_number', 'creditor__name']
    ordering_fields = ['return_date', 'status']
    ordering = ['-return_date']
    serializer_class = RFCSerializer
    
    def get_queryset(self):
        return RFC.objects.select_related(
            'creditor'
        ).prefetch_related('line_items')
    
    @action(detail=True, methods=['post'])
    def mark_credited(self, request, pk=None):
        """Mark RFC as credited"""
        rfc = self.get_object()
        
        if rfc.status != 'pending':
            return Response(
                {'error': 'Only pending RFCs can be marked as credited'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rfc.status = 'credited'
        rfc.credited_date = request.data.get('credited_date', datetime.now().date())
        rfc.save()
        
        return Response(self.get_serializer(rfc).data)
    
    @action(detail=True, methods=['post'])
    def mark_replaced(self, request, pk=None):
        """Mark RFC as replaced"""
        rfc = self.get_object()
        
        if rfc.status != 'pending':
            return Response(
                {'error': 'Only pending RFCs can be marked as replaced'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rfc.status = 'replaced'
        rfc.replaced_date = request.data.get('replaced_date', datetime.now().date())
        rfc.save()
        
        return Response(self.get_serializer(rfc).data)




# ============================================================================
# SUMMARY ENDPOINT
# ============================================================================

class CreditorsSummaryView(APIView):
    """Summary statistics for creditors module"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get creditors summary"""
        today = datetime.now().date()
        
        summary = {
            'total_creditors': Creditor.objects.count(),
            'active_creditors': Creditor.objects.filter(is_active=True).count(),
            'total_outstanding': CreditorOpenItem.objects.filter(
                balance_due__gt=0
            ).aggregate(Sum('balance_due'))['balance_due__sum'] or Decimal('0'),
            'overdue_items': CreditorOpenItem.objects.filter(
                due_date__lt=today,
                balance_due__gt=0
            ).count(),
            'pending_rfcs': RFC.objects.filter(status='pending').count(),
            'unposted_invoices': CreditorInvoice.objects.filter(is_posted=False).count(),
        }
        
        return Response(summary)
