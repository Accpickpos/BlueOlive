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
from datetime import date, timedelta
from decimal import Decimal
from django.db import transaction as db_transaction

from .models import (
    Debtor, DebtorTransaction, Debtopen, Dpdc, DebtorAudit, Darea
)
from .serializers import (
    DebtorListSerializer, DebtorDetailSerializer,
    DebtorCreateUpdateSerializer, DebtorTransactionSerializer,
    DebteopenSerializer, DpdcSerializer, DebtorAuditSerializer,
    DareaSerializer, AgeAnalysisSerializer, DebtorSummarySerializer,
    DebtranListSerializer, DebtOpenListSerializer
)


class DebtorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing debtors (customers) - DMAST table.
    
    Provides CRUD operations plus actions:
    - age_analysis: Age analysis for debtor
    - transactions: Get debtor transactions
    - summary: Get all debtors summary
    - block: Block debtor account
    - unblock: Unblock debtor account
    """
    queryset = Debtor.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['dno', 'dname', 'dsname', 'dcontact']
    ordering_fields = ['dno', 'dname', 'dcrnt', 'created_at']
    ordering = ['dno']
    
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
                'dno': debtor.dno,
                'dname': debtor.dname,
                'dcontact': debtor.dcontact,
                'dtel': debtor.dtel,
                'dclimit': debtor.dclimit,
                'current': debtor.dcrnt,
                'days_30': debtor.d30,
                'days_60': debtor.d60,
                'days_90': debtor.d90,
                'days_120': debtor.d120,
                'days_150': debtor.d150,
                'days_180': debtor.d180,
                'total_balance': debtor.get_total_balance(),
                'overdue_balance': debtor.get_overdue_balance(),
                'ddatlpd': debtor.ddatlpd,
                'damtlpd': debtor.damtlpd,
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
            
            transactions = DebtorTransaction.objects.filter(dno=debtor)
            
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
            blocked_debtors = debtors.filter(blockflag='Y').count()
            
            aggregates = debtors.aggregate(
                total_balance=Sum('dcrnt'),
                current_balance=Sum('dcrnt'),
                d30_total=Sum('d30'),
                d60_total=Sum('d60'),
                d90_total=Sum('d90'),
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
                    debtors.aggregate(Sum('d120'))['d120__sum'] or Decimal('0.00'),
                    debtors.aggregate(Sum('d150'))['d150__sum'] or Decimal('0.00'),
                    debtors.aggregate(Sum('d180'))['d180__sum'] or Decimal('0.00'),
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
                'message': f'Debtor {debtor.dno} blocked successfully'
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
                'message': f'Debtor {debtor.dno} unblocked successfully'
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
                'dno': debtor.dno,
                'dname': debtor.dname,
                'dclimit': float(debtor.dclimit),
                'balance_breakdown': {
                    'current': float(debtor.dcrnt),
                    '30_days': float(debtor.d30),
                    '60_days': float(debtor.d60),
                    '90_days': float(debtor.d90),
                    '120_days': float(debtor.d120),
                    '150_days': float(debtor.d150),
                    '180_days': float(debtor.d180),
                },
                'total_balance': float(debtor.get_total_balance()),
                'available_credit': float(debtor.dclimit - debtor.get_total_balance()),
                'credit_utilization_pct': float(
                    (debtor.get_total_balance() / debtor.dclimit * 100) 
                    if debtor.dclimit > 0 else 0
                ),
                'is_blocked': debtor.is_blocked(),
                'is_active': debtor.is_active,
                'last_payment': {
                    'date': debtor.ddatlpd,
                    'amount': float(debtor.damtlpd),
                },
                'sales': {
                    'mtd': float(debtor.dsalesm),
                    'ytd': float(debtor.dsalesy),
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
    """
    queryset = DebtorTransaction.objects.all()
    serializer_class = DebtorTransactionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['dno', 'dtype', 'dtdate']
    ordering_fields = ['dtdate', 'dttot']
    ordering = ['-dtdate']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('dno')


class DebteopenViewSet(viewsets.ModelViewSet):
    """
    ViewSet for open item transactions (DEBTOPEN).
    Tracks individual open item postings for debtor accounts.
    """
    queryset = Debtopen.objects.all()
    serializer_class = DebteopenSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['dno', 'type', 'posted', 'ageflag']
    ordering_fields = ['date', 'total']
    ordering = ['-date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('dno')
    
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
    filterset_fields = ['dno', 'status', 'date']
    ordering_fields = ['date', 'amount']
    ordering = ['date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('dno')
    
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
    filterset_fields = ['dno', 'type', 'date']
    ordering_fields = ['date']
    ordering = ['-date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('dno')


class DareaViewSet(viewsets.ModelViewSet):
    """
    ViewSet for sales area/salesman data (DAREA).
    """
    queryset = Darea.objects.all()
    serializer_class = DareaSerializer
    permission_classes = [IsAuthenticated]
    ordering_fields = ['darea', 'dareaname']
    ordering = ['darea']