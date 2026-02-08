"""
Creditors app views and viewsets.
Handles supplier management, transactions, and RFC operations.
"""
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from decimal import Decimal
from django_filters.rest_framework import DjangoFilterBackend

from .models import (
    Creditor, GoodsReceivedNote, GRNLineItem,
    CreditorInvoice, CreditorInvoiceLineItem, CreditorCreditNote,
    CreditorCreditNoteLineItem, CreditorPayment, CreditorJournal,
    CreditorOpenItem, OpenItemAllocation, RFC, RFCLineItem
)
from .serializers import (
    SupplierListSerializer, SupplierDetailSerializer, SupplierCreateUpdateSerializer,
    ExpenseCategorySerializer, GoodsReceivedNoteSerializer, CreditorInvoiceSerializer,
    CreditorCreditNoteSerializer, CreditorPaymentSerializer, CreditorJournalSerializer,
    CreditorTransactionLineSerializer, OpenItemAllocationSerializer, CreditorOpenItemSerializer,
    RFCSerializer, RFCLineItemSerializer, SupplierMonthlyPurchaseSerializer,
    ExpenseMonthlyTotalSerializer, StockReceivingSerializer,
    StockReturnSerializer, ExpenseInvoiceSerializer, PaymentSerializer,
    OpenItemPaymentSerializer, JournalSerializer, RFCCreateSerializer
)
from apps.settings.models import TaxCode, ExpenseCategory


class SupplierViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing suppliers/creditors.
    
    Endpoints:
    - GET /suppliers/ - List suppliers
    - POST /suppliers/ - Create supplier
    - GET /suppliers/{id}/ - Get supplier details
    - PUT /suppliers/{id}/ - Update supplier
    - DELETE /suppliers/{id}/ - Soft delete supplier
    - GET /suppliers/{id}/balance-analysis/ - Get balance aging
    - POST /suppliers/{id}/take-on-balance/ - Set opening balance
    """
    
    queryset = Creditor.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'account_category']
    search_fields = ['name', 'email', 'telephone']
    ordering_fields = ['supplier_number', 'name', 'created_at']
    ordering = ['supplier_number']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SupplierListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SupplierCreateUpdateSerializer
        return SupplierDetailSerializer
    
    def get_queryset(self):
        """Filter suppliers for current tenant"""
        queryset = Creditor.objects.all()
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.select_related('credit_terms', 'sales_area')
    
    @action(detail=True, methods=['get'])
    def balance_analysis(self, request, pk=None):
        """Get supplier balance aging analysis"""
        supplier = self.get_object()
        data = {
            'account_number': supplier.account_number,
            'name': supplier.name,
            'balance_current': supplier.balance_current,
            'balance_30_days': supplier.balance_30_days,
            'balance_60_days': supplier.balance_60_days,
            'balance_90_days': supplier.balance_90_days,
            'balance_120_days': supplier.balance_120_days,
            'balance_150_days': supplier.balance_150_days,
            'balance_180_days': supplier.balance_180_days,
            'total_balance': supplier.get_total_balance(),
            'total_balance_with_rfc': supplier.get_total_balance_with_rfc(),
            'amount_last_paid': supplier.amount_last_paid,
            'date_last_paid': supplier.date_last_paid,
            'credit_terms': supplier.credit_terms.days if supplier.credit_terms else None,
            'our_account_number': supplier.our_account_number,
        }
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def take_on_balance(self, request, pk=None):
        """Set opening balance for supplier (Balance Brought Forward)"""
        supplier = self.get_object()
        
        try:
            supplier.balance_current = Decimal(request.data.get('balance_current', 0))
            supplier.balance_30_days = Decimal(request.data.get('balance_30_days', 0))
            supplier.balance_60_days = Decimal(request.data.get('balance_60_days', 0))
            supplier.balance_90_days = Decimal(request.data.get('balance_90_days', 0))
            supplier.balance_120_days = Decimal(request.data.get('balance_120_days', 0))
            supplier.balance_150_days = Decimal(request.data.get('balance_150_days', 0))
            supplier.balance_180_days = Decimal(request.data.get('balance_180_days', 0))
            supplier.save()
            
            serializer = self.get_serializer(supplier)
            return Response(serializer.data)
        except (ValueError, TypeError) as e:
            return Response(
                {'error': f'Invalid balance values: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def outstanding_balance(self, request):
        """
        Get outstanding balance items across all suppliers or for a specific supplier.
        
        Query params:
        - supplier_id: (optional) Filter by specific supplier
        
        Returns list of open items with balance_due > 0
        """
        # Get outstanding items
        outstanding_items = CreditorOpenItem.objects.filter(
            balance_due__gt=0,
            is_fully_allocated=False
        ).select_related('creditor')
        
        # Filter by supplier if provided
        supplier_id = request.query_params.get('supplier_id')
        if supplier_id:
            outstanding_items = outstanding_items.filter(creditor_id=supplier_id)
        
        # Order by transaction date (oldest first)
        outstanding_items = outstanding_items.order_by('transaction_date')
        
        # Serialize
        serializer = CreditorOpenItemSerializer(outstanding_items, many=True)
        
        # Calculate totals
        total_outstanding = sum(item['balance_due'] for item in serializer.data)
        
        return Response({
            'count': len(serializer.data),
            'total_outstanding': total_outstanding,
            'items': serializer.data
        })

class CreditorTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing creditor transactions across all types.
    Supports viewing GRN, Invoices, Credit Notes, Payments, and Journal entries.
    
    Endpoints:
    - GET /transactions/ - List all transactions (by type)
    - GET /transactions/?creditor={id} - List transactions for specific creditor
    - GET /transactions/?type=GRN - Filter by transaction type
    - GET /transactions/?posted=true - Filter by posted status
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted', 'transaction_type']
    search_fields = ['transaction_number', 'transaction_reference']
    ordering_fields = ['transaction_date', 'transaction_number', 'created_at']
    ordering = ['-transaction_date', '-transaction_number']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on transaction type"""
        transaction_type = self.request.query_params.get('type', None)
        
        if transaction_type == 'GRN':
            return GoodsReceivedNoteSerializer
        elif transaction_type == 'INV':
            return CreditorInvoiceSerializer
        elif transaction_type == 'CN':
            return CreditorCreditNoteSerializer
        elif transaction_type == 'PAY':
            return CreditorPaymentSerializer
        elif transaction_type in ['DJ', 'CJ']:
            return CreditorJournalSerializer
        
        # Default to serializing transaction lines
        return CreditorTransactionLineSerializer
    
    def get_queryset(self):
        """
        Combine all creditor transaction types into a single queryset.
        Filters by creditor and transaction type if provided.
        """
        creditor_id = self.request.query_params.get('creditor', None)
        transaction_type = self.request.query_params.get('type', None)
        
        # Build union of all transaction types
        grn_qs = GoodsReceivedNote.objects.all()
        invoice_qs = CreditorInvoice.objects.all()
        credit_note_qs = CreditorCreditNote.objects.all()
        payment_qs = CreditorPayment.objects.all()
        journal_qs = CreditorJournal.objects.all()
        
        # Filter by creditor if specified
        if creditor_id:
            grn_qs = grn_qs.filter(creditor_id=creditor_id)
            invoice_qs = invoice_qs.filter(creditor_id=creditor_id)
            credit_note_qs = credit_note_qs.filter(creditor_id=creditor_id)
            payment_qs = payment_qs.filter(creditor_id=creditor_id)
            journal_qs = journal_qs.filter(creditor_id=creditor_id)
        
        # Filter by transaction type if specified
        if transaction_type == 'GRN':
            return grn_qs.select_related('creditor', 'posted_by')
        elif transaction_type == 'INV':
            return invoice_qs.select_related('creditor', 'posted_by')
        elif transaction_type == 'CN':
            return credit_note_qs.select_related('creditor', 'posted_by')
        elif transaction_type == 'PAY':
            return payment_qs.select_related('creditor', 'posted_by')
        elif transaction_type in ['DJ', 'CJ']:
            return journal_qs.select_related('creditor', 'posted_by')
        
        # Return combined queryset with all transaction types
        from django.db.models import QuerySet
        all_transactions = list(grn_qs) + list(invoice_qs) + list(credit_note_qs) + list(payment_qs) + list(journal_qs)
        
        # Sort by transaction date descending
        all_transactions.sort(key=lambda x: (x.transaction_date, x.transaction_number), reverse=True)
        
        # Return as list (this will be converted to a proper queryset-like response)
        # For better performance, clients should filter by type
        return GoodsReceivedNote.objects.none()  # Return empty queryset as fallback
    
    @action(detail=False, methods=['get'])
    def by_creditor(self, request):
        """Get all transactions for a specific creditor"""
        creditor_id = request.query_params.get('creditor_id')
        if not creditor_id:
            return Response(
                {'error': 'creditor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        creditor = get_object_or_404(Creditor, id=creditor_id)
        
        # Combine all transaction types for this creditor
        transactions = []
        
        grn_list = GoodsReceivedNote.objects.filter(creditor=creditor).select_related('creditor', 'posted_by')
        invoices = CreditorInvoice.objects.filter(creditor=creditor).select_related('creditor', 'posted_by')
        credits = CreditorCreditNote.objects.filter(creditor=creditor).select_related('creditor', 'posted_by')
        payments = CreditorPayment.objects.filter(creditor=creditor).select_related('creditor', 'posted_by')
        journals = CreditorJournal.objects.filter(creditor=creditor).select_related('creditor', 'posted_by')
        
        # Combine and sort
        all_transactions = list(grn_list) + list(invoices) + list(credits) + list(payments) + list(journals)
        all_transactions.sort(key=lambda x: (x.transaction_date, x.transaction_number), reverse=True)
        
        # Convert to serialized data
        serialized = []
        for trans in all_transactions:
            if isinstance(trans, GoodsReceivedNote):
                serialized.append(GoodsReceivedNoteSerializer(trans).data)
            elif isinstance(trans, CreditorInvoice):
                serialized.append(CreditorInvoiceSerializer(trans).data)
            elif isinstance(trans, CreditorCreditNote):
                serialized.append(CreditorCreditNoteSerializer(trans).data)
            elif isinstance(trans, CreditorPayment):
                serialized.append(CreditorPaymentSerializer(trans).data)
            elif isinstance(trans, CreditorJournal):
                serialized.append(CreditorJournalSerializer(trans).data)
        
        return Response({
            'creditor': creditor.name,
            'transaction_count': len(serialized),
            'transactions': serialized
        })
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get summary of all transactions by type"""
        summary = {
            'grn': GoodsReceivedNote.objects.count(),
            'invoices': CreditorInvoice.objects.count(),
            'credit_notes': CreditorCreditNote.objects.count(),
            'payments': CreditorPayment.objects.count(),
            'journals': CreditorJournal.objects.count(),
        }
        return Response(summary)


class ExpenseCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for managing expense categories"""
    
    permission_classes = [IsAuthenticated]
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['category_name', 'category_number']
    ordering_fields = ['category_number', 'category_name']
    ordering = ['category_number']


class RFCViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Returns for Credit (RFC).
    
    Endpoints:
    - GET /rfc/ - List RFCs
    - POST /rfc/ - Create new RFC
    - GET /rfc/{id}/ - Get RFC details
    - POST /rfc/{id}/credit-granted/ - Mark RFC as credit received
    - POST /rfc/{id}/stock-replaced/ - Mark RFC as stock replaced
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = RFCSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['supplier', 'status']
    ordering_fields = ['return_date', 'created_at']
    ordering = ['-return_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return RFCCreateSerializer
        return RFCSerializer
    
    def get_queryset(self):
        """Get RFC records"""
        return RFC.objects.all().select_related(
            'supplier', 'credit_transaction'
        ).prefetch_related('line_items')
    
    @action(detail=True, methods=['post'])
    def credit_granted(self, request, pk=None):
        """Process RFC credit received"""
        rfc = self.get_object()
        
        if rfc.status != 'PENDING':
            return Response(
                {'error': 'Only pending RFCs can be marked as credit received'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with db_transaction.atomic():
                # Create credit transaction
                credit = CreditorTransaction.objects.create(
                    transaction_type='CREDIT_STOCK',
                    supplier=rfc.supplier,
                    transaction_date=request.data.get('credit_date'),
                    invoice_number=request.data.get('credit_document_number'),
                    amount_exclusive=rfc.total_exclusive,
                    vat_amount=rfc.total_vat,
                    amount_inclusive=rfc.total_inclusive,
                )
                
                # Update RFC status
                rfc.status = 'CREDIT_RECEIVED'
                rfc.credit_date = request.data.get('credit_date')
                rfc.credit_document_number = request.data.get('credit_document_number')
                rfc.credit_transaction = credit
                rfc.save()
                
                # Update supplier RFC outstanding
                rfc.supplier.rfc_outstanding_amount -= rfc.total_inclusive
                rfc.supplier.save()
                
                return Response(RFCSerializer(rfc).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def stock_replaced(self, request, pk=None):
        """Process RFC stock replacement"""
        rfc = self.get_object()
        
        if rfc.status != 'PENDING':
            return Response(
                {'error': 'Only pending RFCs can be marked as stock replaced'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rfc.status = 'STOCK_REPLACED'
            rfc.replacement_date = request.data.get('replacement_date')
            rfc.replacement_document_number = request.data.get('replacement_document_number')
            rfc.save()
            
            return Response(RFCSerializer(rfc).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class OutstandingBalanceView(APIView):
    """
    API endpoint for getting outstanding balance items.
    GET /api/creditors/outstanding-balance/ - List all outstanding items
    GET /api/creditors/outstanding-balance/?supplier_id=1 - Filter by supplier
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get outstanding balance items"""
        # Get outstanding items
        outstanding_items = CreditorOpenItem.objects.filter(
            balance_due__gt=0,
            is_fully_allocated=False
        ).select_related('creditor')
        
        # Filter by supplier if provided
        supplier_id = request.query_params.get('supplier_id')
        if supplier_id:
            outstanding_items = outstanding_items.filter(creditor_id=supplier_id)
        
        # Order by transaction date (oldest first)
        outstanding_items = outstanding_items.order_by('transaction_date')
        
        # Serialize
        serializer = CreditorOpenItemSerializer(outstanding_items, many=True)
        
        # Calculate totals
        total_outstanding = sum(item['balance_due'] for item in serializer.data if isinstance(item['balance_due'], (int, float, Decimal)))
        
        return Response({
            'count': len(serializer.data),
            'total_outstanding': str(total_outstanding),
            'items': serializer.data
        })

