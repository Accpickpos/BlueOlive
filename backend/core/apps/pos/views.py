"""
Point of Sale views.
API viewsets for all POS operations based on PointOfSale.pdf
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum
from datetime import date
from .models import (
    ReceiptOnAccount, CreditNote, CashReturn,
    CashACheque, TransactionQuery,
    CashSale, Laybye, Quotation, JobCard, Payout, Repair, CashControl
)

from .serializers import (
    CashSaleListSerializer, CashSaleDetailSerializer, CashSaleCreateSerializer,
    LaybyeListSerializer, LaybyeDetailSerializer,
    QuotationListSerializer, QuotationDetailSerializer,
    PayoutSerializer, RepairSerializer,
    JobCardListSerializer, JobCardDetailSerializer,
    CashControlSerializer, CashControlSummarySerializer, ReceiptOnAccountSerializer,
    CreditNoteListSerializer, CreditNoteDetailSerializer, CreditNoteCreateSerializer,
    CashReturnSerializer, CashReturnCreateSerializer,
    CashAChequeSerializer, TransactionQuerySerializer
)
from .services import (
    CashSaleService, LaybyeService, QuotationService, RepairService
)
from .filters import (
    CashSaleFilter, LaybyeFilter, QuotationFilter, JobCardFilter
)


class CashSaleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for cash sales.
    
    Actions:
    - list, create, retrieve, update, destroy
    - post_sale: Post cash sale to update stock
    - cancel_sale: Cancel a cash sale
    """
    queryset = CashSale.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = CashSaleFilter
    ordering_fields = ['sale_date', 'sale_time', 'total_amount']
    ordering = ['-sale_date', '-sale_time']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return CashSaleListSerializer
        elif self.action == 'create':
            return CashSaleCreateSerializer
        return CashSaleDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'list':
            queryset = queryset.select_related('cashier', 'sales_area')
        elif self.action == 'retrieve':
            queryset = queryset.select_related('cashier', 'sales_area').prefetch_related('lines', 'tenders')
        return queryset
    
    @action(detail=True, methods=['post'])
    def post_sale(self, request, pk=None):
        """Post cash sale to update stock."""
        cash_sale = self.get_object()
        
        try:
            CashSaleService.post_cash_sale(cash_sale)
            return Response({
                'status': 'success',
                'message': f'Cash sale {cash_sale.sale_number} posted successfully'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel_sale(self, request, pk=None):
        """Cancel a cash sale."""
        cash_sale = self.get_object()
        reason = request.data.get('reason', '')
        
        try:
            CashSaleService.cancel_cash_sale(cash_sale, reason)
            return Response({
                'status': 'success',
                'message': f'Cash sale {cash_sale.sale_number} cancelled'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def daily_total(self, request):
        """Get total sales for a specific date."""
        sale_date = request.query_params.get('date', date.today())
        
        total = CashSale.objects.filter(
            sale_date=sale_date,
            is_posted=True,
            is_cancelled=False
        ).aggregate(total=Sum('total_amount'))
        
        return Response({
            'date': sale_date,
            'total_sales': total['total'] or 0
        })
    
    @action(detail=False, methods=['post'])
    def check_prices(self, request):
        """
        Check available prices and validate line item pricing.
        
        POST data:
        {
            "stock_code": "ITEM001",
            "quantity": 5,
            "unit_price": "150.00",
            "discount_percent": 10
        }
        
        Returns available price levels and validation results.
        """
        from .price_validation_service import PriceValidationService
        
        stock_code = request.data.get('stock_code')
        quantity = request.data.get('quantity', 1)
        unit_price = request.data.get('unit_price')
        discount_percent = request.data.get('discount_percent', 0)
        
        if not stock_code:
            return Response(
                {'error': 'stock_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get available prices
            prices = PriceValidationService.get_valid_prices_for_item(stock_code)
            
            # Validate if price provided
            validation_result = None
            if unit_price:
                validation_result = PriceValidationService.validate_line_item_price(
                    stock_code=stock_code,
                    quantity=quantity,
                    unit_price=unit_price,
                    discount_percent=discount_percent,
                    price_level=1,
                    transaction_date=date.today()
                )
            
            return Response({
                'stock_code': stock_code,
                'available_prices': {
                    'price_level_1': float(prices['selling_price_1']),
                    'price_level_2': float(prices['selling_price_2']),
                    'price_level_3': float(prices['selling_price_3']),
                    'markup_percent_1': float(prices['markup_percent_1']),
                    'markup_percent_2': float(prices['markup_percent_2']),
                    'markup_percent_3': float(prices['markup_percent_3']),
                    'cost_price': float(prices['cost_price']),
                    'maximum_discount': float(prices['maximum_discount']),
                },
                'validation': validation_result,
                'has_special_deal': prices.get('special_deal') is not None,
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def price_analysis(self, request):
        """
        Get detailed price analysis for a stock item.
        Shows all price levels, markups, and profit analysis.
        
        POST data:
        {
            "stock_code": "ITEM001"
        }
        """
        from .price_validation_service import PriceValidationService
        
        stock_code = request.data.get('stock_code')
        
        if not stock_code:
            return Response(
                {'error': 'stock_code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            analysis = PriceValidationService.get_price_analysis(stock_code, date.today())
            return Response(analysis)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class LaybyeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for laybyes.
    
    Actions:
    - list, create, retrieve, update, destroy
    - make_payment: Record a payment
    - cancel_laybye: Cancel with retention
    - check_expired: Find expired laybyes
    """
    queryset = Laybye.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = LaybyeFilter
    ordering_fields = ['laybye_date', 'expiry_date', 'total_amount']
    ordering = ['-laybye_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'list':
            return LaybyeListSerializer
        return LaybyeDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('lines', 'payments')
        return queryset
    
    @action(detail=True, methods=['post'])
    def make_payment(self, request, pk=None):
        """Make a payment on a laybye."""
        laybye = self.get_object()
        amount = request.data.get('amount')
        sales_area_id = request.data.get('sales_area')
        
        if not amount:
            return Response(
                {'error': 'Amount is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from decimal import Decimal
            amount = Decimal(str(amount))
            
            from apps.settings.models import SalesArea
            sales_area = SalesArea.objects.get(id=sales_area_id) if sales_area_id else None
            
            payment = LaybyeService.make_payment(laybye, amount, sales_area)
            
            return Response({
                'status': 'success',
                'message': 'Payment recorded successfully',
                'new_balance': float(laybye.balance_due)
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def cancel_laybye(self, request, pk=None):
        """Cancel a laybye."""
        laybye = self.get_object()
        retention_percentage = float(request.data.get('retention_percentage', 0))
        
        try:
            LaybyeService.cancel_laybye(laybye, retention_percentage)
            return Response({
                'status': 'success',
                'message': 'Laybye cancelled',
                'refund_amount': float(laybye.refund_amount)
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def check_expired(self, request):
        """Check for and mark expired laybyes."""
        count = LaybyeService.check_expired_laybyes()
        return Response({
            'status': 'success',
            'expired_count': count
        })
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active laybyes."""
        active_laybyes = self.get_queryset().filter(status='ACTIVE')
        
        page = self.paginate_queryset(active_laybyes)
        if page is not None:
            serializer = LaybyeListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = LaybyeListSerializer(active_laybyes, many=True)
        return Response(serializer.data)


class QuotationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for quotations.
    
    Actions:
    - list, create, retrieve, update, destroy
    - convert_to_invoice: Convert to customer invoice
    - convert_to_job: Convert to job card
    """
    queryset = Quotation.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = QuotationFilter
    ordering_fields = ['quotation_date', 'expiry_date', 'total_amount']
    ordering = ['-quotation_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'list':
            return QuotationListSerializer
        return QuotationDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('lines')
        return queryset
    
    @action(detail=True, methods=['post'])
    def convert_to_invoice(self, request, pk=None):
        """Convert quotation to invoice."""
        quotation = self.get_object()
        debtor_id = request.data.get('debtor_id')
        
        if not debtor_id:
            return Response(
                {'error': 'debtor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.debtors.models import Debtor
            debtor = Debtor.objects.get(id=debtor_id)
            
            QuotationService.convert_to_invoice(quotation, debtor)
            
            return Response({
                'status': 'success',
                'message': 'Quotation converted to invoice'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def convert_to_job(self, request, pk=None):
        """Convert quotation to job card."""
        quotation = self.get_object()
        
        try:
            job_card = QuotationService.convert_to_job_card(quotation)
            
            return Response({
                'status': 'success',
                'message': 'Quotation converted to job card',
                'job_number': job_card.job_number
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PayoutViewSet(viewsets.ModelViewSet):
    """ViewSet for cash payouts."""
    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['payout_date', 'cashier', 'station_number']
    ordering_fields = ['payout_date', 'amount']
    ordering = ['-payout_date']


class RepairViewSet(viewsets.ModelViewSet):
    """
    ViewSet for repair vouchers.
    
    Actions:
    - list, create, retrieve, update, destroy
    - issue_to_supplier: Issue repair to supplier
    - receive_from_supplier: Receive repaired item
    - invoice_customer: Invoice customer for repair
    """
    queryset = Repair.objects.all()
    serializer_class = RepairSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'date_required']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def issue_to_supplier(self, request, pk=None):
        """Issue repair to supplier."""
        repair = self.get_object()
        supplier_account = request.data.get('supplier_account')
        transport_mode = request.data.get('transport_mode', '')
        
        if not supplier_account:
            return Response(
                {'error': 'supplier_account is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            RepairService.issue_to_supplier(repair, supplier_account, transport_mode)
            return Response({
                'status': 'success',
                'message': 'Repair issued to supplier'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def receive_from_supplier(self, request, pk=None):
        """Receive repaired item from supplier."""
        repair = self.get_object()
        repair_cost = request.data.get('repair_cost')
        supplier_invoice = request.data.get('supplier_invoice', '')
        
        if not repair_cost:
            return Response(
                {'error': 'repair_cost is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from decimal import Decimal
            repair_cost = Decimal(str(repair_cost))
            
            RepairService.receive_from_supplier(repair, repair_cost, supplier_invoice)
            return Response({
                'status': 'success',
                'message': 'Repair received from supplier'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def invoice_customer(self, request, pk=None):
        """Invoice customer for repair."""
        repair = self.get_object()
        
        try:
            RepairService.invoice_customer(repair)
            return Response({
                'status': 'success',
                'message': 'Repair invoiced to customer'
            })
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class JobCardViewSet(viewsets.ModelViewSet):
    """ViewSet for job cards."""
    queryset = JobCard.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobCardFilter
    ordering_fields = ['job_date', 'total_amount']
    ordering = ['-job_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'list':
            return JobCardListSerializer
        return JobCardDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('lines')
        return queryset
    
    @action(detail=True, methods=['post'])
    def convert_to_invoice(self, request, pk=None):
        """Convert job card to customer invoice."""
        job_card = self.get_object()
        debtor_id = request.data.get('debtor_id')
        
        if not debtor_id:
            return Response(
                {'error': 'debtor_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from apps.debtors.models import Debtor
            debtor = Debtor.objects.get(id=debtor_id)
            
            from .services import QuotationService
            invoice = QuotationService.convert_job_card_to_invoice(job_card, debtor)
            
            # Import the invoice serializer
            from .serializers import InvoiceDetailSerializer
            serializer = InvoiceDetailSerializer(invoice)
            
            return Response({
                'status': 'success',
                'message': 'Job card converted to invoice',
                'invoice': serializer.data
            }, status=status.HTTP_201_CREATED)
        except Debtor.DoesNotExist:
            return Response(
                {'error': f'Debtor with id {debtor_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CashControlViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for cash control records.
    Read-only as these are generated by the system.
    """
    queryset = CashControl.objects.all()
    serializer_class = CashControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['control_date', 'cashier', 'station_number', 'is_cleared']
    ordering_fields = ['control_date']
    ordering = ['-control_date']
    
    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily cash control summary."""
        control_date = request.query_params.get('date', date.today())
        cashier_id = request.query_params.get('cashier')
        station_number = request.query_params.get('station_number')
        
        summary = CashSaleService.get_daily_summary(
            control_date,
            cashier_id,
            station_number
        )
        
        serializer = CashControlSummarySerializer(summary)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        """Mark cash control as cleared."""
        cash_control = self.get_object()
        cash_control.is_cleared = True
        cash_control.save()
        
        return Response({
            'status': 'success',
            'message': 'Cash control cleared'
        })
    



"""
Additional Point of Sale views for missing features.
Receipt on Account, Credit Note, Cash Return, Cash a Cheque, Transaction Query
"""


class ReceiptOnAccountViewSet(viewsets.ModelViewSet):
    """
    ViewSet for receipts on account.
    
    Actions:
    - list, create, retrieve, update, destroy
    - post_receipt: Post receipt to debtor account
    """
    queryset = ReceiptOnAccount.objects.all()
    serializer_class = ReceiptOnAccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['receipt_date', 'debtor_account', 'tender_type', 'is_posted', 'cashier', 'station_number']
    ordering_fields = ['receipt_date', 'amount']
    ordering = ['-receipt_date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('debtor', 'cashier')
    
    @action(detail=True, methods=['post'])
    def post_receipt(self, request, pk=None):
        """Post receipt to debtor account."""
        receipt = self.get_object()
        
        if receipt.is_posted:
            return Response(
                {'error': 'Receipt already posted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update debtor balance (would integrate with debtors app)
            receipt.is_posted = True
            receipt.save()
            
            return Response({
                'status': 'success',
                'message': f'Receipt {receipt.receipt_number} posted successfully'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def daily_total(self, request):
        """Get total receipts for a specific date."""
        receipt_date = request.query_params.get('date', date.today())
        
        from django.db.models import Sum
        total = ReceiptOnAccount.objects.filter(
            receipt_date=receipt_date,
            is_posted=True
        ).aggregate(total=Sum('total_amount'))
        
        return Response({
            'date': receipt_date,
            'total_receipts': total['total'] or 0
        })


class CreditNoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for credit notes.
    
    Actions:
    - list, create, retrieve, update, destroy
    - post_credit: Post credit note
    """
    queryset = CreditNote.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['credit_date', 'debtor_account', 'is_posted', 'cashier', 'station_number']
    ordering_fields = ['credit_date', 'total_amount']
    ordering = ['-credit_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'list':
            return CreditNoteListSerializer
        elif self.action == 'create':
            return CreditNoteCreateSerializer
        return CreditNoteDetailSerializer
    
    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('lines')
        return queryset.select_related('cashier', 'sales_area')
    
    @action(detail=True, methods=['post'])
    def post_credit(self, request, pk=None):
        """Post credit note to update stock and debtor account."""
        credit_note = self.get_object()
        
        if credit_note.is_posted:
            return Response(
                {'error': 'Credit note already posted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update stock for each line
            from apps.stock_control.models import StockItem, StockMovement
            for line in credit_note.lines.all():
                if line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=line.stock_code)
                        stock_item.quantity_on_hand += line.quantity
                        stock_item.save()
                        
                        # Create stock movement
                        StockMovement.objects.create(
                            stock_item=stock_item,
                            movement_type='CRN',
                            movement_date=credit_note.credit_date,
                            transaction_number=credit_note.credit_number,
                            quantity_in=line.quantity,
                            quantity_balance=stock_item.quantity_on_hand,
                            unit_price=line.unit_price,
                            station_number=credit_note.station_number
                        )
                    except StockItem.DoesNotExist:
                        pass
            
            credit_note.is_posted = True
            credit_note.save()
            
            return Response({
                'status': 'success',
                'message': f'Credit note {credit_note.credit_number} posted successfully'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CashReturnViewSet(viewsets.ModelViewSet):
    """
    ViewSet for cash returns.
    
    Actions:
    - list, create, retrieve, update, destroy
    - post_return: Post cash return
    """
    queryset = CashReturn.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['return_date', 'is_posted', 'cashier', 'station_number']
    ordering_fields = ['return_date', 'total_amount']
    ordering = ['-return_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return CashReturnCreateSerializer
        return CashReturnSerializer
    
    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('lines')
        return queryset.select_related('cashier')
    
    @action(detail=True, methods=['post'])
    def post_return(self, request, pk=None):
        """Post cash return to update stock."""
        cash_return = self.get_object()
        
        if cash_return.is_posted:
            return Response(
                {'error': 'Cash return already posted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Update stock for each line
            from apps.stock_control.models import StockItem, StockMovement
            for line in cash_return.lines.all():
                if line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=line.stock_code)
                        stock_item.quantity_on_hand += line.quantity
                        stock_item.save()
                        
                        # Create stock movement
                        StockMovement.objects.create(
                            stock_item=stock_item,
                            movement_type='CSR',
                            movement_date=cash_return.return_date,
                            transaction_number=cash_return.return_number,
                            reference=cash_return.reason,
                            quantity_in=line.quantity,
                            quantity_balance=stock_item.quantity_on_hand,
                            unit_price=line.unit_price,
                            station_number=cash_return.station_number
                        )
                    except StockItem.DoesNotExist:
                        pass
            
            cash_return.is_posted = True
            cash_return.save()
            
            return Response({
                'status': 'success',
                'message': f'Cash return {cash_return.return_number} posted successfully'
            })
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CashAChequeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for cash a cheque transactions.
    
    Actions:
    - list, create, retrieve, update, destroy
    - process: Mark cheque as processed
    """
    queryset = CashACheque.objects.all()
    serializer_class = CashAChequeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transaction_date', 'is_processed', 'cashier', 'station_number']
    ordering_fields = ['transaction_date', 'cheque_amount']
    ordering = ['-transaction_date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('cashier')
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Mark cheque as processed."""
        cheque = self.get_object()
        
        cheque.is_processed = True
        cheque.save()
        
        return Response({
            'status': 'success',
            'message': f'Cheque {cheque.cheque_number} marked as processed'
        })
    
    @action(detail=False, methods=['get'])
    def unprocessed(self, request):
        """Get all unprocessed cheques."""
        unprocessed = self.get_queryset().filter(is_processed=False)
        
        page = self.paginate_queryset(unprocessed)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(unprocessed, many=True)
        return Response(serializer.data)


class TransactionQueryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for transaction queries.
    
    Actions:
    - list, create, retrieve, update, destroy
    - search: Search for transactions
    - resolve: Resolve a query
    """
    queryset = TransactionQuery.objects.all()
    serializer_class = TransactionQuerySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['query_date', 'query_type', 'query_status', 'assigned_to']
    ordering_fields = ['query_date']
    ordering = ['-query_date']
    
    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related('assigned_to', 'resolved_by')
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """Search for transactions."""
        query_type = request.data.get('query_type')
        transaction_number = request.data.get('transaction_number', '')
        customer_name = request.data.get('customer_name', '')
        date_from = request.data.get('date_from')
        date_to = request.data.get('date_to')
        
        results = []
        
        # Search based on query type
        if query_type == 'CASH_SALE':
            qs = CashSale.objects.all()
            if transaction_number:
                qs = qs.filter(sale_number__icontains=transaction_number)
            if customer_name:
                qs = qs.filter(customer_name__icontains=customer_name)
            if date_from:
                qs = qs.filter(sale_date__gte=date_from)
            if date_to:
                qs = qs.filter(sale_date__lte=date_to)
            
            results = list(qs.values('sale_number', 'sale_date', 'customer_name', 'total_amount'))
        
        elif query_type == 'LAYBYE':
            qs = Laybye.objects.all()
            if transaction_number:
                qs = qs.filter(laybye_number__icontains=transaction_number)
            if customer_name:
                qs = qs.filter(customer_name__icontains=customer_name)
            if date_from:
                qs = qs.filter(laybye_date__gte=date_from)
            if date_to:
                qs = qs.filter(laybye_date__lte=date_to)
            
            results = list(qs.values('laybye_number', 'laybye_date', 'customer_name', 'total_amount', 'status'))
        
        elif query_type == 'QUOTATION':
            qs = Quotation.objects.all()
            if transaction_number:
                qs = qs.filter(quotation_number__icontains=transaction_number)
            if customer_name:
                qs = qs.filter(customer_name__icontains=customer_name)
            if date_from:
                qs = qs.filter(quotation_date__gte=date_from)
            if date_to:
                qs = qs.filter(quotation_date__lte=date_to)
            
            results = list(qs.values('quotation_number', 'quotation_date', 'customer_name', 'total_amount', 'status'))
        
        # More query types can be added...
        
        return Response({
            'query_type': query_type,
            'results_count': len(results),
            'results': results
        })
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a query."""
        query = self.get_object()
        resolution_notes = request.data.get('resolution_notes', '')
        
        query.query_status = 'RESOLVED'
        query.resolution_notes = resolution_notes
        query.resolved_by = request.user
        query.resolved_date = date.today()
        query.save()
        
        return Response({
            'status': 'success',
            'message': f'Query {query.query_number} resolved'
        })
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign query to a user."""
        query = self.get_object()
        assigned_to_id = request.data.get('assigned_to')
        
        if not assigned_to_id:
            return Response(
                {'error': 'assigned_to is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from django.contrib.auth.models import User
        try:
            user = User.objects.get(id=assigned_to_id)
            query.assigned_to = user
            query.query_status = 'IN_PROGRESS'
            query.save()
            
            return Response({
                'status': 'success',
                'message': f'Query assigned to {user.username}'
            })
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )