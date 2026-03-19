"""
API Views for Stockfinder integration.
Provides endpoints for stock loading, order processing, and document retrieval.
"""
from rest_framework import viewsets, status, views
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    StockFinderConfig,
    StockFinderSyncLog,
    StockFinderWebhookEvent,
    StockFinderStockItem,
    StockFinderSalesOrder,
    StockFinderPurchaseOrder,
)
from .serializers import (
    StockFinderConfigSerializer,
    StockFinderSyncLogSerializer,
    StockFinderWebhookEventSerializer,
    StockFinderStockItemSerializer,
    StockFinderStockItemBulkSerializer,
    StockFinderSalesOrderSerializer,
    StockFinderSalesOrderCreateSerializer,
    StockFinderPurchaseOrderSerializer,
    StockFinderPurchaseOrderCreateSerializer,
    DocumentSearchSerializer,
)
from .services import (
    StockFinderService,
    StockFinderSyncService,
    verify_webhook_signature,
    StockFinderAPIError,
)
from apps.pos.models import Invoice, InvoiceLine, JobCard
from apps.purchase_orders.models import PurchaseOrder
from apps.debtors.models import SalesOrder as DebtorSalesOrder, Debtor


class StockFinderConfigViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Stockfinder API configurations.
    """
    serializer_class = StockFinderConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return configurations for current tenant."""
        return StockFinderConfig.objects.filter(
            tenant=self.request.user.tenant
        )
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test connection to Stockfinder API."""
        config = self.get_object()
        
        try:
            service = StockFinderService(config)
            # Try to make a simple API call to test connection
            result = service._make_request('GET', '/health')
            return Response({
                'status': 'success',
                'message': 'Connection successful',
                'data': result
            })
        except StockFinderAPIError as e:
            return Response({
                'status': 'error',
                'message': e.message,
                'details': e.response_data
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Connection failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def sync_stock(self, request, pk=None):
        """Manually trigger stock sync."""
        config = self.get_object()
        
        # Get stock codes to sync (from request or all active)
        stock_codes = request.data.get('stock_codes', [])
        
        if not stock_codes:
            # Sync all stock items that have been linked
            stock_codes = list(
                StockFinderStockItem.objects.filter(
                    is_active=True
                ).values_list('stock_code', flat=True)[:100]
            )
        
        if not stock_codes:
            return Response({
                'status': 'error',
                'message': 'No stock codes to sync'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sync_service = StockFinderSyncService(config)
            log = sync_service.sync_stock_items(stock_codes)
            
            return Response({
                'status': 'success',
                'message': f'Stock sync completed. Processed: {log.items_processed}, Failed: {log.items_failed}',
                'log_id': log.id
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': f'Sync failed: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


class StockFinderSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing sync logs.
    """
    serializer_class = StockFinderSyncLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return logs for current configuration."""
        config_id = self.request.query_params.get('config')
        queryset = StockFinderSyncLog.objects.all()
        
        if config_id:
            queryset = queryset.filter(config_id=config_id)
        
        return queryset.order_by('-created_at')


class StockFinderWebhookView(APIView):
    """
    Webhook endpoint for receiving events from Stockfinder.
    """
    permission_classes = [AllowAny]  # Authentication handled via signature
    
    def post(self, request):
        """Handle incoming webhook events from Stockfinder."""
        # Get signature from headers
        signature = request.headers.get('X-Signature', '')
        
        # Get configuration for webhook
        config = StockFinderConfig.objects.filter(
            webhook_enabled=True,
            is_active=True
        ).first()
        
        if not config:
            return Response({
                'error': 'Webhook not configured'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify signature if secret is set
        if config.webhook_secret:
            payload = request.body
            if not verify_webhook_signature(
                payload,
                signature,
                config.webhook_secret
            ):
                return Response({
                    'error': 'Invalid signature'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Parse event data
        try:
            event_data = request.data
        except Exception:
            return Response({
                'error': 'Invalid JSON'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        event_type = event_data.get('event_type')
        
        # Create webhook event record
        webhook_event = StockFinderWebhookEvent.objects.create(
            event_type=event_type,
            payload=event_data
        )
        
        # Process the event
        try:
            sync_service = StockFinderSyncService(config)
            
            if event_type == 'order_created':
                order = sync_service.process_sales_order_webhook(
                    event_data.get('data', {})
                )
                webhook_event.processed = True
                webhook_event.save()
                
                return Response({
                    'status': 'success',
                    'event_id': webhook_event.event_id,
                    'order_id': order.id
                })
            
            elif event_type == 'stock_updated':
                # Handle stock update event
                stock_codes = event_data.get('data', {}).get('stock_codes', [])
                if stock_codes:
                    sync_service.sync_stock_items(stock_codes)
                webhook_event.processed = True
                webhook_event.save()
                
                return Response({
                    'status': 'success',
                    'event_id': webhook_event.event_id
                })
            
            else:
                webhook_event.processing_error = f'Unknown event type: {event_type}'
                webhook_event.save()
                return Response({
                    'status': 'ignored',
                    'message': f'Event type {event_type} not supported'
                })
                
        except Exception as e:
            webhook_event.processing_error = str(e)
            webhook_event.save()
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class StockFinderStockViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for querying stock items from Stockfinder.
    """
    serializer_class = StockFinderStockItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return cached stock items."""
        queryset = StockFinderStockItem.objects.filter(is_active=True)
        
        # Filter by stock code
        stock_code = self.request.query_params.get('stock_code')
        if stock_code:
            queryset = queryset.filter(stock_code__icontains=stock_code)
        
        # Filter by description
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(description__icontains=search) |
                Q(stock_code__icontains=search)
            )
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset
    
    @action(detail=False, methods=['post'])
    def bulk_lookup(self, request):
        """
        Bulk lookup stock items by stock codes.
        This is the main endpoint for querying multiple SKUs.
        """
        serializer = StockFinderStockItemBulkSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stock_codes = serializer.validated_data['stock_codes']
        include_custom = serializer.validated_data.get('include_custom_pricing', False)
        
        # First check local cache
        cached_items = StockFinderStockItem.objects.filter(
            stock_code__in=stock_codes,
            is_active=True
        )
        
        # Find missing codes
        cached_codes = set(cached_items.values_list('stock_code', flat=True))
        missing_codes = [code for code in stock_codes if code not in cached_codes]
        
        # If we have a config, try to fetch missing from API
        config = StockFinderConfig.objects.filter(
            is_active=True
        ).first()
        
        if config and missing_codes:
            try:
                sync_service = StockFinderSyncService(config)
                sync_service.sync_stock_items(missing_codes)
                
                # Refresh cached items
                cached_items = StockFinderStockItem.objects.filter(
                    stock_code__in=stock_codes,
                    is_active=True
                )
            except Exception as e:
                # Return what we have even if sync failed
                pass
        
        # Serialize results
        result_serializer = StockFinderStockItemSerializer(
            cached_items,
            many=True,
            fields=(
                ['stock_code', 'description', 'quantity_on_hand', 
                 'quantity_available', 'cost_price', 'retail_price']
                if not include_custom else None
            )
        )
        
        return Response({
            'items': result_serializer.data,
            'requested': len(stock_codes),
            'found': cached_items.count(),
            'missing': missing_codes
        })


class StockFinderOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sales orders from Stockfinder.
    """
    serializer_class = StockFinderSalesOrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return sales orders."""
        queryset = StockFinderSalesOrder.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by customer
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(
                Q(customer_name__icontains=customer) |
                Q(vehicle_registration__icontains=customer)
            )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        return queryset.order_by('-order_date')
    
    def create(self, request, *args, **kwargs):
        """Manually create a sales order (for testing)."""
        serializer = StockFinderSalesOrderCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config = StockFinderConfig.objects.filter(is_active=True).first()
        if not config:
            return Response({
                'error': 'No active Stockfinder configuration'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sync_service = StockFinderSyncService(config)
            order = sync_service.process_sales_order_webhook(
                serializer.validated_data
            )
            
            return Response(
                StockFinderSalesOrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def create_job_card(self, request, pk=None):
        """Create a local JobCard from this order."""
        order = self.get_object()
        
        if order.local_job_card:
            return Response({
                'error': 'Job card already exists',
                'job_card_id': order.local_job_card.id
            })
        
        config = StockFinderConfig.objects.filter(is_active=True).first()
        if not config:
            return Response({
                'error': 'No active Stockfinder configuration'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sync_service = StockFinderSyncService(config)
            job_card = sync_service._create_local_job_card(order)
            
            if job_card:
                order.local_job_card = job_card
                order.status = 'in_progress'
                order.save()
                
                return Response({
                    'status': 'success',
                    'job_card_id': job_card.id,
                    'job_card_reference': job_card.reference
                })
            else:
                return Response({
                    'error': 'Failed to create job card'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def create_invoice(self, request, pk=None):
        """Create a local Invoice from this order."""
        order = self.get_object()
        
        if order.local_invoice:
            return Response({
                'error': 'Invoice already exists',
                'invoice_id': order.local_invoice.id
            })
        
        # Create invoice from order
        try:
            # Generate invoice number
            today = timezone.now().date()
            invoice_count = Invoice.objects.filter(
                invoice_date=today
            ).count() + 1
            invoice_number = f"SF-INV-{today.year}{today.month:02d}{today.day:02d}-{invoice_count:05d}"
            
            # Try to find a debtor or create a generic one for stockfinder orders
            # For now, we'll use a placeholder debtor - in production you'd want to
            # either find an existing debtor or create one from the order details
            debtor, created = Debtor.objects.get_or_create(
                dno='STOCKFINDER',
                defaults={
                    'name': 'Stockfinder Orders',
                    'email': 'stockfinder@example.com',
                    'status': 'ACTIVE'
                }
            )
            
            # Calculate totals from order lines
            subtotal = sum(line.line_total for line in order.lines.all())
            # Assuming standard 15% VAT
            vat_rate = Decimal('15.00')
            vat_amount = (subtotal * vat_rate / 100).quantize(Decimal('0.01'))
            total_amount = subtotal + vat_amount
            
            invoice = Invoice.objects.create(
                debtor=debtor,
                invoice_number=invoice_number,
                invoice_date=timezone.now().date(),
                delivery_name=order.customer_name,
                delivery_address_line1=order.notes or '',
                delivery_telephone=order.customer_phone or '',
                order_number=order.stockfinder_order_id,
                subtotal=subtotal,
                vat_amount=vat_amount,
                total_amount=total_amount,
                status='DRAFT',
                is_posted=False
            )
            
            # Create invoice lines
            line_number = 1
            for order_line in order.lines.all():
                # Calculate line VAT (assuming 15% standard rate)
                line_vat = (order_line.line_total * vat_rate / 100).quantize(Decimal('0.01'))
                
                InvoiceLine.objects.create(
                    invoice=invoice,
                    line_number=line_number,
                    stock_code=order_line.stock_code,
                    description=order_line.description,
                    quantity=order_line.quantity,
                    unit_price=order_line.unit_price,
                    tax_code=1,  # Standard rate
                    vat_rate=vat_rate,
                    line_total=order_line.line_total,
                    vat_amount=line_vat
                )
                line_number += 1
            
            order.local_invoice = invoice
            order.save()
            
            return Response({
                'status': 'success',
                'invoice_id': invoice.id,
                'invoice_number': invoice.invoice_number
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class StockFinderPurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders from Stockfinder.
    """
    serializer_class = StockFinderPurchaseOrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return purchase orders."""
        queryset = StockFinderPurchaseOrder.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by supplier
        supplier = self.request.query_params.get('supplier')
        if supplier:
            queryset = queryset.filter(
                Q(supplier_name__icontains=supplier) |
                Q(supplier_code__icontains=supplier)
            )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        return queryset.order_by('-order_date')
    
    def create(self, request, *args, **kwargs):
        """Manually create a purchase order."""
        serializer = StockFinderPurchaseOrderCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        config = StockFinderConfig.objects.filter(is_active=True).first()
        if not config:
            return Response({
                'error': 'No active Stockfinder configuration'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sync_service = StockFinderSyncService(config)
            po = sync_service.process_purchase_order_creation(
                serializer.validated_data,
                create_local_po=True
            )
            
            return Response(
                StockFinderPurchaseOrderSerializer(po).data,
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def create_local_po(self, request, pk=None):
        """Create a local PurchaseOrder from this Stockfinder PO."""
        sf_po = self.get_object()
        
        if sf_po.local_purchase_order:
            return Response({
                'error': 'Local PO already exists',
                'po_id': sf_po.local_purchase_order.id
            })
        
        config = StockFinderConfig.objects.filter(is_active=True).first()
        if not config:
            return Response({
                'error': 'No active Stockfinder configuration'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sync_service = StockFinderSyncService(config)
            local_po = sync_service._create_local_purchase_order(sf_po)
            
            if local_po:
                sf_po.local_purchase_order = local_po
                sf_po.status = 'sent'
                sf_po.save()
                
                return Response({
                    'status': 'success',
                    'po_id': local_po.id,
                    'po_reference': local_po.reference
                })
            else:
                return Response({
                    'error': 'Failed to create local purchase order'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class DocumentRetrievalView(APIView):
    """
    Unified document retrieval endpoint.
    Supports querying sales orders, invoices, purchase orders, and credit notes
    by date range or document number.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Search for documents.
        
        Query parameters:
        - document_type: sales_order, invoice, purchase_order, credit_note
        - start_date: Start of date range (YYYY-MM-DD)
        - end_date: End of date range (YYYY-MM-DD)
        - document_number: Specific document number
        - customer_name: Filter by customer (for sales orders/invoices)
        - supplier_name: Filter by supplier (for purchase orders)
        - page: Page number
        - page_size: Results per page
        """
        serializer = DocumentSearchSerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        doc_type = serializer.validated_data['document_type']
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        document_number = serializer.validated_data.get('document_number')
        page = serializer.validated_data.get('page', 1)
        page_size = serializer.validated_data.get('page_size', 20)
        
        results = []
        
        # Query based on document type
        if doc_type == 'sales_order':
            results = self._get_sales_orders(
                start_date, end_date, document_number,
                serializer.validated_data.get('customer_name')
            )
        elif doc_type == 'invoice':
            results = self._get_invoices(
                start_date, end_date, document_number,
                serializer.validated_data.get('customer_name')
            )
        elif doc_type == 'purchase_order':
            results = self._get_purchase_orders(
                start_date, end_date, document_number,
                serializer.validated_data.get('supplier_name')
            )
        elif doc_type == 'credit_note':
            results = self._get_credit_notes(
                start_date, end_date, document_number
            )
        
        # Paginate results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_results = results[start_idx:end_idx]
        
        return Response({
            'count': len(results),
            'page': page,
            'page_size': page_size,
            'total_pages': (len(results) + page_size - 1) // page_size,
            'documents': paginated_results
        })
    
    def _get_sales_orders(self, start_date, end_date, document_number, customer_name):
        """Get sales orders matching criteria."""
        queryset = DebtorSalesOrder.objects.all()
        
        if document_number:
            queryset = queryset.filter(order_number__icontains=document_number)
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        if customer_name:
            queryset = queryset.filter(
                Q(debtor__name__icontains=customer_name) |
                Q(customer_name__icontains=customer_name)
            )
        
        return [{
            'id': order.id,
            'document_type': 'sales_order',
            'document_number': order.order_number,
            'date': order.order_date,
            'customer_name': order.debtor.name if order.debtor else order.customer_name,
            'status': order.status,
            'subtotal': order.subtotal or 0,
            'tax_amount': order.tax_amount or 0,
            'total_amount': order.total or 0,
        } for order in queryset[:100]]
    
    def _get_invoices(self, start_date, end_date, document_number, customer_name):
        """Get invoices matching criteria."""
        queryset = Invoice.objects.all()
        
        if document_number:
            queryset = queryset.filter(reference__icontains=document_number)
        if start_date:
            queryset = queryset.filter(invoice_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(invoice_date__lte=end_date)
        if customer_name:
            queryset = queryset.filter(
                Q(customer_name__icontains=customer_name) |
                Q(debtor__name__icontains=customer_name)
            )
        
        return [{
            'id': inv.id,
            'document_type': 'invoice',
            'document_number': inv.reference,
            'date': inv.invoice_date,
            'customer_name': inv.customer_name,
            'status': inv.status,
            'subtotal': inv.subtotal or 0,
            'tax_amount': inv.tax_amount or 0,
            'total_amount': inv.total or 0,
        } for inv in queryset[:100]]
    
    def _get_purchase_orders(self, start_date, end_date, document_number, supplier_name):
        """Get purchase orders matching criteria."""
        queryset = PurchaseOrder.objects.all()
        
        if document_number:
            queryset = queryset.filter(reference__icontains=document_number)
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        if supplier_name:
            queryset = queryset.filter(
                Q(supplier__name__icontains=supplier_name) |
                Q(supplier_name__icontains=supplier_name)
            )
        
        return [{
            'id': po.id,
            'document_type': 'purchase_order',
            'document_number': po.reference,
            'date': po.order_date,
            'supplier_name': po.supplier.name if po.supplier else po.supplier_name,
            'status': po.status,
            'subtotal': po.subtotal or 0,
            'tax_amount': po.tax_amount or 0,
            'total_amount': po.total or 0,
        } for po in queryset[:100]]
    
    def _get_credit_notes(self, start_date, end_date, document_number):
        """Get credit notes matching criteria."""
        from apps.pos.models import CreditNote
        
        queryset = CreditNote.objects.all()
        
        if document_number:
            queryset = queryset.filter(reference__icontains=document_number)
        if start_date:
            queryset = queryset.filter(credit_note_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(credit_note_date__lte=end_date)
        
        return [{
            'id': cn.id,
            'document_type': 'credit_note',
            'document_number': cn.reference,
            'date': cn.credit_note_date,
            'customer_name': cn.customer_name,
            'status': cn.status,
            'subtotal': cn.subtotal or 0,
            'tax_amount': cn.tax_amount or 0,
            'total_amount': cn.total or 0,
        } for cn in queryset[:100]]
