# backend/core/apps/creditors/views.py
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from apps.shop_filter_mixin import ShopFilterMixin

from .models import (
    Creditor, CreditorTransaction,
    GoodsReceivedNote, GRNLineItem,
    CreditorInvoice, CreditorInvoiceLineItem,
    CreditorCreditNote, CreditorCreditNoteLineItem,
    CreditorPayment,
    CreditorJournal,
    SupplierLedgerEntry,
    CreditorOpenItem, OpenItemAllocation,
    OpenItemAudit,
    RFC, RFCLineItem,
    ExpenseCategoryMonthlyBalance,
    ExpenseCategoryTransaction,
    SupplierPaymentOrder,
    CreditorTransactionLine,
    OutstandingBalance,
)
from .serializers import (
    CreditorListSerializer, CreditorSerializer, CreditorAgedBalanceSummarySerializer,
    GoodsReceivedNoteSerializer, GoodsReceivedNoteWriteSerializer, GRNLineItemSerializer,
    CreditorInvoiceSerializer, CreditorInvoiceWriteSerializer, CreditorInvoiceLineItemSerializer,
    CreditorCreditNoteSerializer, CreditorCreditNoteWriteSerializer, CreditorCreditNoteLineItemSerializer,
    CreditorPaymentSerializer,
    CreditorJournalSerializer,
    SupplierLedgerEntrySerializer,
    CreditorOpenItemSerializer, OpenItemAllocationSerializer,
    OpenItemAuditSerializer,
    RFCSerializer, RFCWriteSerializer, RFCLineItemSerializer,
    ExpenseCategoryMonthlyBalanceSerializer,
    ExpenseCategoryTransactionSerializer,
    SupplierPaymentOrderSerializer,
    CreditorTransactionLineSerializer,
    OutstandingBalanceSerializer,
    OutstandingBalanceCreateSerializer,
)


# ============================================================================
# CREDITOR (SUPPLIER) MASTER
# ============================================================================

class CreditorViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    CRUD for Creditor master accounts.

    list:   GET  /creditors/                  — paginated list (lightweight)
    create: POST /creditors/
    retrieve: GET /creditors/{id}/            — full detail
    update: PUT  /creditors/{id}/
    partial_update: PATCH /creditors/{id}/
    destroy: DELETE /creditors/{id}/

    Extra actions:
      GET  /creditors/{id}/aged_balances/      — aging snapshot
      POST /creditors/{id}/recalculate_aged/   — trigger recalculation from open items
      GET  /creditors/{id}/open_items/         — open items for this creditor
      GET  /creditors/{id}/ledger/             — full suptran ledger for this creditor
      GET  /creditors/{id}/transactions/       — summary of all transaction types
      GET  /creditors/age_analysis/            — age analysis across ALL creditors
    """

    queryset         = Creditor.objects.select_related('credit_terms', 'sales_area')
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['account_category', 'is_active']
    search_fields    = ['supplier_number', 'name', 'telephone', 'email']
    ordering_fields  = ['supplier_number', 'name', 'total_outstanding_balance']
    ordering         = ['supplier_number']

    def get_serializer_class(self):
        if self.action == 'list':
            return CreditorListSerializer
        if self.action == 'age_analysis':
            return CreditorAgedBalanceSummarySerializer
        return CreditorSerializer

    def perform_destroy(self, instance):
        """
        Manual (§4.1 [411.htm]): "Deletion is not permitted when: an
        account has a balance, or where transactions were posted to this
        account for the current month." Previously unenforced — unlike the
        typed transaction viewsets (GRN/Invoice/CreditNote/Journal/Payment)
        which already guard against deleting *posted* transactions, the
        Creditor master itself had no destroy override at all.
        """
        from rest_framework.exceptions import ValidationError

        if instance.total_outstanding_balance != 0:
            raise ValidationError(
                f"Cannot delete creditor {instance.supplier_number}: account has an "
                f"outstanding balance of {instance.total_outstanding_balance}."
            )

        today = timezone.now().date()
        has_transactions_this_month = CreditorTransaction.objects.filter(
            creditor=instance,
            transaction_date__year=today.year,
            transaction_date__month=today.month,
        ).exists()
        if has_transactions_this_month:
            raise ValidationError(
                f"Cannot delete creditor {instance.supplier_number}: transactions were "
                f"posted to this account in the current month."
            )

        super().perform_destroy(instance)

    # --- Session capture on create/update ---
    def _capture_session(self, serializer):
        """Attach station and user from the request session before saving."""
        extra = {}
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            extra['created_by_user'] = self.request.user.username[:20]
        serializer.save(**extra)

    # --- Extra actions ---

    @action(detail=True, methods=['get'], url_path='aged_balances')
    def aged_balances(self, request, pk=None):
        creditor = self.get_object()
        serializer = CreditorAgedBalanceSummarySerializer(creditor)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='recalculate_aged')
    def recalculate_aged(self, request, pk=None):
        """Recalculate aging buckets from open items for this creditor."""
        creditor = self.get_object()
        creditor.recalculate_aged_balances()
        serializer = CreditorAgedBalanceSummarySerializer(creditor)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='open_items')
    def open_items(self, request, pk=None):
        creditor = self.get_object()
        qs = creditor.open_items.filter(is_fully_allocated=False).order_by('due_date')
        serializer = CreditorOpenItemSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='ledger')
    def ledger(self, request, pk=None):
        """Full suptran ledger for this creditor, newest first."""
        creditor = self.get_object()
        qs = creditor.ledger_entries.order_by('-transaction_date', 'transaction_number')
        serializer = SupplierLedgerEntrySerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='transactions')
    def transactions(self, request, pk=None):
        """Summary counts and totals by transaction type for this creditor."""
        creditor = self.get_object()
        data = {
            'grns':     GoodsReceivedNote.objects.filter(creditor=creditor).count(),
            'invoices': CreditorInvoice.objects.filter(creditor=creditor).count(),
            'payments': CreditorPayment.objects.filter(creditor=creditor).count(),
            'journals': CreditorJournal.objects.filter(creditor=creditor).count(),
            'rfcs':     RFC.objects.filter(creditor=creditor).count(),
        }
        return Response(data)

    @action(detail=False, methods=['get'], url_path='age_analysis')
    def age_analysis(self, request):
        """Age analysis across all active creditors with an outstanding balance."""
        qs = Creditor.objects.filter(
            is_active=True, total_outstanding_balance__gt=0
        ).order_by('supplier_number')
        serializer = CreditorAgedBalanceSummarySerializer(qs, many=True)
        return Response(serializer.data)


# ============================================================================
# GOODS RECEIVED NOTE
# ============================================================================

class GoodsReceivedNoteViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    GRN list / detail / create.

    list:     GET  /grns/
    create:   POST /grns/                  — nested line_items accepted
    retrieve: GET  /grns/{id}/
    update:   PUT  /grns/{id}/             — header only (lines managed separately)
    destroy:  DELETE /grns/{id}/           — only if not posted

    Extra:
      GET  /grns/by_creditor/?creditor={id}  — filter by creditor
      POST /grns/{id}/post/                  — mark as posted
    """

    queryset = GoodsReceivedNote.objects.select_related('creditor').prefetch_related('line_items')
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted', 'transaction_type']
    search_fields    = ['transaction_number', 'supplier_invoice_number', 'transaction_reference']
    ordering_fields  = ['transaction_date', 'transaction_number', 'total_amount']
    ordering         = ['-transaction_date']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return GoodsReceivedNoteWriteSerializer
        return GoodsReceivedNoteSerializer

    def perform_create(self, serializer):
        user = self.request.user.username[:20] if self.request.user.is_authenticated else ''
        serializer.save(created_by_user=user)

    def destroy(self, request, *args, **kwargs):
        grn = self.get_object()
        if grn.is_posted:
            return Response(
                {'detail': 'Cannot delete a posted GRN.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='by_creditor')
    def by_creditor(self, request):
        creditor_id = request.query_params.get('creditor')
        if not creditor_id:
            return Response({'detail': 'creditor query param required.'}, status=400)
        qs = self.get_queryset().filter(creditor_id=creditor_id)
        serializer = GoodsReceivedNoteSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='post')
    def post_grn(self, request, pk=None):
        grn = self.get_object()
        if grn.is_posted:
            return Response({'detail': 'GRN is already posted.'}, status=400)
        grn.is_posted = True
        grn.posted_at = timezone.now()
        grn.save()
        return Response(GoodsReceivedNoteSerializer(grn).data)


class GRNLineItemViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """Line items nested under a GRN — /grns/{grn_pk}/lines/"""

    serializer_class   = GRNLineItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GRNLineItem.objects.filter(grn_id=self.kwargs['grn_pk'])

    def perform_create(self, serializer):
        grn = GoodsReceivedNote.objects.get(pk=self.kwargs['grn_pk'])
        next_line = (self.get_queryset().order_by('-line_number').values_list('line_number', flat=True).first() or 0) + 1
        serializer.save(grn=grn, line_number=next_line)


# ============================================================================
# CREDITOR INVOICE
# ============================================================================

class CreditorInvoiceViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Expense invoices (electricity, rent, etc.).

    Extra:
      POST /invoices/{id}/post/
    """

    queryset = CreditorInvoice.objects.select_related('creditor').prefetch_related('line_items')
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted']
    search_fields    = ['transaction_number', 'supplier_invoice_number', 'transaction_reference']
    ordering_fields  = ['transaction_date', 'total_amount']
    ordering         = ['-transaction_date']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CreditorInvoiceWriteSerializer
        return CreditorInvoiceSerializer

    def perform_create(self, serializer):
        user = self.request.user.username[:20] if self.request.user.is_authenticated else ''
        serializer.save(created_by_user=user)

    def destroy(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.is_posted:
            return Response({'detail': 'Cannot delete a posted invoice.'}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='post')
    def post_invoice(self, request, pk=None):
        invoice = self.get_object()
        if invoice.is_posted:
            return Response({'detail': 'Invoice is already posted.'}, status=400)
        invoice.is_posted = True
        invoice.posted_at = timezone.now()
        invoice.save()
        return Response(CreditorInvoiceSerializer(invoice).data)


class CreditorInvoiceLineItemViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """Nested line items — /invoices/{invoice_pk}/lines/"""

    serializer_class   = CreditorInvoiceLineItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CreditorInvoiceLineItem.objects.filter(invoice_id=self.kwargs['invoice_pk'])

    def perform_create(self, serializer):
        invoice   = CreditorInvoice.objects.get(pk=self.kwargs['invoice_pk'])
        next_line = (self.get_queryset().order_by('-line_number').values_list('line_number', flat=True).first() or 0) + 1
        serializer.save(invoice=invoice, line_number=next_line)


# ============================================================================
# CREDITOR CREDIT NOTE
# ============================================================================

class CreditorCreditNoteViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Credit notes from suppliers.

    Extra:
      POST /credit_notes/{id}/post/
    """

    queryset = CreditorCreditNote.objects.select_related('creditor').prefetch_related('line_items')
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted']
    search_fields    = ['transaction_number', 'supplier_credit_note_number']
    ordering_fields  = ['transaction_date', 'total_amount']
    ordering         = ['-transaction_date']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CreditorCreditNoteWriteSerializer
        return CreditorCreditNoteSerializer

    def perform_create(self, serializer):
        user = self.request.user.username[:20] if self.request.user.is_authenticated else ''
        serializer.save(created_by_user=user)

    def destroy(self, request, *args, **kwargs):
        cn = self.get_object()
        if cn.is_posted:
            return Response({'detail': 'Cannot delete a posted credit note.'}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='post')
    def post_cn(self, request, pk=None):
        cn = self.get_object()
        if cn.is_posted:
            return Response({'detail': 'Credit note is already posted.'}, status=400)
        cn.is_posted = True
        cn.posted_at = timezone.now()
        cn.save()
        return Response(CreditorCreditNoteSerializer(cn).data)


class CreditorCreditNoteLineItemViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """Nested line items — /credit_notes/{cn_pk}/lines/"""

    serializer_class   = CreditorCreditNoteLineItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CreditorCreditNoteLineItem.objects.filter(credit_note_id=self.kwargs['cn_pk'])

    def perform_create(self, serializer):
        cn        = CreditorCreditNote.objects.get(pk=self.kwargs['cn_pk'])
        next_line = (self.get_queryset().order_by('-line_number').values_list('line_number', flat=True).first() or 0) + 1
        serializer.save(credit_note=cn, line_number=next_line)


# ============================================================================
# CREDITOR PAYMENT
# ============================================================================

class CreditorPaymentViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Payments made to suppliers.

    Extra:
      POST /payments/{id}/post/
      POST /payments/{id}/allocate/   — allocate to open items
    """

    queryset = CreditorPayment.objects.select_related('creditor', 'payment_method')
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted', 'is_unallocated']
    search_fields    = ['transaction_number', 'transaction_reference']
    ordering_fields  = ['transaction_date', 'amount_paid']
    ordering         = ['-transaction_date']
    serializer_class = CreditorPaymentSerializer

    def perform_create(self, serializer):
        user = self.request.user.username[:20] if self.request.user.is_authenticated else ''
        serializer.save(created_by_user=user)

    def destroy(self, request, *args, **kwargs):
        payment = self.get_object()
        if payment.is_posted:
            return Response({'detail': 'Cannot delete a posted payment.'}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='post')
    def post_payment(self, request, pk=None):
        payment = self.get_object()
        if payment.is_posted:
            return Response({'detail': 'Payment is already posted.'}, status=400)
        payment.is_posted = True
        payment.posted_at = timezone.now()
        payment.save()
        return Response(CreditorPaymentSerializer(payment).data)

    @action(detail=True, methods=['post'], url_path='allocate')
    def allocate(self, request, pk=None):
        """
        Allocate this payment to one or more open items.
        Expects: [{"open_item": <id>, "amount_paid": <decimal>, "settlement_discount": <decimal>}, ...]
        """
        payment = self.get_object()
        allocations = request.data if isinstance(request.data, list) else [request.data]
        created = []
        errors  = []

        for item_data in allocations:
            serializer = OpenItemAllocationSerializer(data={**item_data, 'payment': payment.pk})
            if serializer.is_valid():
                serializer.save()
                created.append(serializer.data)
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({'created': created, 'errors': errors}, status=207)
        return Response(created, status=status.HTTP_201_CREATED)


# ============================================================================
# CREDITOR JOURNAL
# ============================================================================

class CreditorJournalViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Debit/credit journal adjustments.

    Extra:
      POST /journals/{id}/post/
    """

    queryset = CreditorJournal.objects.select_related('creditor')
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'is_posted', 'journal_type']
    search_fields    = ['transaction_number', 'transaction_reference']
    ordering_fields  = ['transaction_date', 'journal_amount']
    ordering         = ['-transaction_date']
    serializer_class = CreditorJournalSerializer

    def perform_create(self, serializer):
        user = self.request.user.username[:20] if self.request.user.is_authenticated else ''
        serializer.save(created_by_user=user)

    def destroy(self, request, *args, **kwargs):
        journal = self.get_object()
        if journal.is_posted:
            return Response({'detail': 'Cannot delete a posted journal.'}, status=400)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='post')
    def post_journal(self, request, pk=None):
        journal = self.get_object()
        if journal.is_posted:
            return Response({'detail': 'Journal is already posted.'}, status=400)
        journal.is_posted = True
        journal.posted_at = timezone.now()
        journal.save()
        return Response(CreditorJournalSerializer(journal).data)


# ============================================================================
# SUPPLIER LEDGER ENTRY (read-only — imported from suptran.dbf)
# ============================================================================

class SupplierLedgerEntryViewSet(ShopFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    Read-only view of raw suptran ledger entries.
    These are imported from the DBF — not created through the API.
    """

    queryset = SupplierLedgerEntry.objects.select_related('creditor')
    serializer_class   = SupplierLedgerEntrySerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['creditor', 'transaction_type']
    search_fields      = ['transaction_number', 'reference']
    ordering_fields    = ['transaction_date', 'total_amount']
    ordering           = ['-transaction_date']


# ============================================================================
# OPEN ITEMS
# ============================================================================

class CreditorOpenItemViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Open items (supopen).

    list:     GET  /open_items/
    retrieve: GET  /open_items/{id}/

    Extra:
      GET  /open_items/outstanding/         — unallocated items only
      GET  /open_items/by_creditor/?creditor={id}
    """

    queryset = CreditorOpenItem.objects.select_related('creditor')
    serializer_class   = CreditorOpenItemSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['creditor', 'transaction_type', 'is_fully_allocated', 'is_legacy']
    search_fields      = ['transaction_number']
    ordering_fields    = ['transaction_date', 'due_date', 'balance_due']
    ordering           = ['due_date']

    # Open items are system-created — only allow PATCH for is_legacy flag
    http_method_names = ['get', 'patch', 'head', 'options']

    @action(detail=False, methods=['get'], url_path='outstanding')
    def outstanding(self, request):
        qs = self.get_queryset().filter(is_fully_allocated=False)
        serializer = CreditorOpenItemSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by_creditor')
    def by_creditor(self, request):
        creditor_id = request.query_params.get('creditor')
        if not creditor_id:
            return Response({'detail': 'creditor query param required.'}, status=400)
        qs = self.get_queryset().filter(creditor_id=creditor_id)
        serializer = CreditorOpenItemSerializer(qs, many=True)
        return Response(serializer.data)


class OpenItemAllocationViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Payment allocations against open items.
    Typically created via /payments/{id}/allocate/ but also accessible directly.
    """

    queryset = OpenItemAllocation.objects.select_related('payment', 'open_item')
    serializer_class   = OpenItemAllocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['payment', 'open_item']


# ============================================================================
# OPEN ITEM AUDIT (read-only)
# ============================================================================

class OpenItemAuditViewSet(ShopFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    Audit trail of open item changes — system-written, read-only via API.
    """

    queryset = OpenItemAudit.objects.select_related('creditor')
    serializer_class   = OpenItemAuditSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['creditor', 'transaction_type']
    ordering_fields    = ['audit_timestamp', 'transaction_date']
    ordering           = ['-audit_timestamp']


# ============================================================================
# RFC (RETURN FOR CREDIT)
# ============================================================================

class RFCViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Returns for credit (supcrmas + supcrtrn).

    Extra:
      GET  /rfcs/by_status/?status={PE|CR|RE|CA}
      PATCH /rfcs/{id}/update_status/
    """

    queryset = RFC.objects.select_related('creditor').prefetch_related('line_items')
    permission_classes = [IsAuthenticated]
    filter_backends  = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['creditor', 'status']
    search_fields    = ['rfc_number']
    ordering_fields  = ['date_sent', 'date_returned']
    ordering         = ['-date_sent']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RFCWriteSerializer
        return RFCSerializer

    @action(detail=False, methods=['get'], url_path='by_status')
    def by_status(self, request):
        status_val = request.query_params.get('status')
        qs = self.get_queryset()
        if status_val:
            qs = qs.filter(status=status_val)
        serializer = RFCSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'], url_path='update_status')
    def update_status(self, request, pk=None):
        rfc = self.get_object()
        new_status = request.data.get('status')
        valid = [s[0] for s in RFC.STATUS_CHOICES]
        if new_status not in valid:
            return Response({'detail': f"Invalid status. Choose from: {valid}"}, status=400)
        rfc.status = new_status
        rfc.save()
        return Response(RFCSerializer(rfc).data)


class RFCLineItemViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """Nested line items — /rfcs/{rfc_pk}/lines/"""

    serializer_class   = RFCLineItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return RFCLineItem.objects.filter(rfc_id=self.kwargs['rfc_pk'])

    def perform_create(self, serializer):
        rfc       = RFC.objects.get(pk=self.kwargs['rfc_pk'])
        next_line = (self.get_queryset().order_by('-line_number').values_list('line_number', flat=True).first() or 0) + 1
        serializer.save(rfc=rfc, line_number=next_line)


# ============================================================================
# EXPENSE CATEGORY MONTHLY BALANCE (read-only — system-accumulated)
# ============================================================================

class ExpenseCategoryMonthlyBalanceViewSet(ShopFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    Expense category monthly totals (supexp). System-accumulated — read-only.

    Extra:
      GET /expense_monthly/?year={year}
      GET /expense_monthly/?category={id}&year={year}
    """

    queryset = ExpenseCategoryMonthlyBalance.objects.select_related('expense_category')
    serializer_class   = ExpenseCategoryMonthlyBalanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['expense_category', 'year']
    ordering_fields    = ['year', 'expense_category']
    ordering           = ['-year', 'expense_category']


# ============================================================================
# EXPENSE CATEGORY TRANSACTION
# ============================================================================

class ExpenseCategoryTransactionViewSet(ShopFilterMixin, viewsets.ReadOnlyModelViewSet):
    """
    Individual expense postings (supexpt). Read-only — written by posting engine.

    Extra:
      GET /expense_transactions/by_creditor/?creditor={id}
      GET /expense_transactions/by_category/?category={id}
    """

    queryset = ExpenseCategoryTransaction.objects.select_related('expense_category', 'creditor')
    serializer_class   = ExpenseCategoryTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['expense_category', 'creditor', 'source_type', 'tax_indicator']
    search_fields      = ['transaction_number']
    ordering_fields    = ['transaction_date', 'amount_exclusive']
    ordering           = ['-transaction_date']

    @action(detail=False, methods=['get'], url_path='by_creditor')
    def by_creditor(self, request):
        creditor_id = request.query_params.get('creditor')
        if not creditor_id:
            return Response({'detail': 'creditor query param required.'}, status=400)
        qs = self.get_queryset().filter(creditor_id=creditor_id)
        serializer = ExpenseCategoryTransactionSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='by_category')
    def by_category(self, request):
        category_id = request.query_params.get('category')
        if not category_id:
            return Response({'detail': 'category query param required.'}, status=400)
        qs = self.get_queryset().filter(expense_category_id=category_id)
        serializer = ExpenseCategoryTransactionSerializer(qs, many=True)
        return Response(serializer.data)


# ============================================================================
# SUPPLIER PAYMENT ORDER
# ============================================================================

class SupplierPaymentOrderViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    Scheduled outgoing payment orders (suppo).

    Extra:
      GET  /payment_orders/pending/         — unprocessed orders
      POST /payment_orders/{id}/process/    — mark as processed (payment run)
    """

    queryset = SupplierPaymentOrder.objects.select_related('creditor')
    serializer_class   = SupplierPaymentOrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields   = ['creditor', 'is_processed']
    ordering_fields    = ['payment_date', 'amount']
    ordering           = ['payment_date']

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        qs = self.get_queryset().filter(is_processed=False)
        serializer = SupplierPaymentOrderSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='process')
    def process(self, request, pk=None):
        """Mark a payment order as processed by the payment run."""
        order = self.get_object()
        if order.is_processed:
            return Response({'detail': 'Payment order already processed.'}, status=400)
        # Use update() to bypass editable=False restriction on model fields
        SupplierPaymentOrder.objects.filter(pk=order.pk).update(
            is_processed=True,
            processed_date=timezone.now().date()
        )
        order.refresh_from_db()
        return Response(SupplierPaymentOrderSerializer(order).data)


# ============================================================================
# CREDITOR TRANSACTION LINE (generic)
# ============================================================================

class CreditorTransactionLineViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """Generic transaction lines (ContentType polymorphic)."""

    queryset = CreditorTransactionLine.objects.all()
    serializer_class   = CreditorTransactionLineSerializer
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend]
    filterset_fields   = ['content_type', 'object_id', 'stock_item', 'expense_category']


# ============================================================================
# OUTSTANDING BALANCE CAPTURE
# ============================================================================

class OutstandingBalanceViewSet(ShopFilterMixin, viewsets.ModelViewSet):
    """
    API endpoint for managing supplier outstanding balances.
    
    Endpoints:
      GET    /outstanding-balances/           - List all outstanding balances
      POST   /outstanding-balances/           - Create new outstanding balance
      GET    /outstanding-balances/{id}/      - Get single outstanding balance
      PUT    /outstanding-balances/{id}/      - Update outstanding balance
      PATCH  /outstanding-balances/{id}/      - Partial update
      DELETE /outstanding-balances/{id}/      - Delete outstanding balance
      
    Filtering:
      ?creditor={id}    - Filter by creditor
      ?as_at_date={date} - Filter by as_at_date
    """

    queryset = OutstandingBalance.objects.select_related('creditor').all()
    permission_classes = [IsAuthenticated]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields   = ['creditor', 'as_at_date', 'capture_date']
    search_fields      = ['creditor__name', 'creditor__supplier_number', 'supplier_account_number', 'transaction_number']
    ordering_fields    = ['capture_date', 'as_at_date', 'balance', 'created_at']
    ordering           = ['-capture_date', '-as_at_date']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return OutstandingBalanceCreateSerializer
        return OutstandingBalanceSerializer

    def perform_create(self, serializer):
        """Set capture_date to today if not provided."""
        if not serializer.validated_data.get('capture_date'):
            from django.utils import timezone
            serializer.save(capture_date=timezone.now().date())
        else:
            serializer.save()

    @action(detail=False, methods=['post'], url_path='capture')
    def capture_balance(self, request):
        """
        Capture a new outstanding balance.
        This is an alias for create that matches the frontend's capture endpoint.
        """
        serializer = OutstandingBalanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)