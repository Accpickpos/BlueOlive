"""
Services for Stockfinder API integration.
Handles communication with Stockfinder system for stock loading,
order processing, and document retrieval.
"""
import requests
import logging
import hashlib
import hmac
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from .models import (
    StockFinderConfig,
    StockFinderSyncLog,
    StockFinderStockItem,
    StockFinderSalesOrder,
    StockFinderSalesOrderLine,
    StockFinderPurchaseOrder,
    StockFinderPurchaseOrderLine,
    StockFinderWebhookEvent,
)
from apps.stock_control.models import StockItem
from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderLine
from apps.pos.models import JobCard, JobCardLine, Invoice, InvoiceLine

logger = logging.getLogger(__name__)


class StockFinderAPIError(Exception):
    """Exception raised for Stockfinder API errors."""
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class StockFinderService:
    """
    Service class for communicating with Stockfinder API.
    Handles authentication, requests, and response parsing.
    """
    
    def __init__(self, config: StockFinderConfig):
        self.config = config
        self.base_url = config.base_url.rstrip('/')
        self.api_key = config.api_key
        self.api_secret = config.api_secret
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate request headers with authentication."""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        if self.api_key:
            headers['X-API-Key'] = self.api_key
        return headers
    
    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for request authentication."""
        if not self.api_secret:
            return ''
        signature = hmac.new(
            self.api_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make authenticated request to Stockfinder API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Prepare payload for signature
        payload = json.dumps(data) if data else ''
        signature = self._generate_signature(payload)
        
        headers = self._get_headers()
        if signature:
            headers['X-Signature'] = signature
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=30
            )
            
            # Log the request
            logger.info(f"Stockfinder API: {method} {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                raise StockFinderAPIError(
                    f"API request failed: {response.text}",
                    status_code=response.status_code,
                    response_data=response.json() if response.content else {}
                )
            
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Stockfinder API request failed: {str(e)}")
            raise StockFinderAPIError(f"Request failed: {str(e)}")
    
    # Stock Loading Methods
    def get_stock_by_sku(self, stock_code: str) -> Optional[Dict]:
        """Get stock information for a single SKU."""
        return self._make_request('GET', f'/stock/{stock_code}')
    
    def get_stock_by_skus(self, stock_codes: List[str]) -> List[Dict]:
        """Get stock information for multiple SKUs."""
        result = self._make_request(
            'POST',
            '/stock/bulk',
            data={'stock_codes': stock_codes}
        )
        return result.get('items', [])
    
    def search_stock(self, query: str, category: Optional[str] = None) -> List[Dict]:
        """Search stock items by description or code."""
        params = {'q': query}
        if category:
            params['category'] = category
        result = self._make_request('GET', '/stock/search', params=params)
        return result.get('items', [])
    
    # Sales Order Methods
    def create_sales_order(self, order_data: Dict) -> Dict:
        """Create a sales order in Stockfinder."""
        return self._make_request('POST', '/orders', data=order_data)
    
    def get_sales_order(self, order_id: str) -> Dict:
        """Get sales order details from Stockfinder."""
        return self._make_request('GET', f'/orders/{order_id}')
    
    def update_sales_order(self, order_id: str, update_data: Dict) -> Dict:
        """Update a sales order in Stockfinder."""
        return self._make_request('PATCH', f'/orders/{order_id}', data=update_data)
    
    # Purchase Order Methods
    def create_purchase_order(self, po_data: Dict) -> Dict:
        """Create a purchase order in Stockfinder."""
        return self._make_request('POST', '/purchase-orders', data=po_data)
    
    def get_purchase_order(self, po_id: str) -> Dict:
        """Get purchase order details from Stockfinder."""
        return self._make_request('GET', f'/purchase-orders/{po_id}')
    
    # Document Retrieval Methods
    def get_documents(
        self,
        document_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        document_number: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve documents from Stockfinder."""
        params = {'type': document_type}
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
        if document_number:
            params['number'] = document_number
        
        result = self._make_request('GET', '/documents', params=params)
        return result.get('documents', [])


class StockFinderSyncService:
    """
    Service for synchronizing data with Stockfinder.
    Handles stock loading, order processing, and more.
    """
    
    def __init__(self, config: StockFinderConfig):
        self.config = config
        self.api_service = StockFinderService(config)
    
    @transaction.atomic
    def sync_stock_items(self, stock_codes: List[str]) -> StockFinderSyncLog:
        """
        Sync stock items from Stockfinder for given stock codes.
        Updates local cache with latest stock information.
        """
        log = StockFinderSyncLog.objects.create(
            sync_type='stock',
            config=self.config,
            status='in_progress',
            started_at=timezone.now(),
            request_data={'stock_codes': stock_codes}
        )
        
        try:
            # Fetch stock data from Stockfinder
            items = self.api_service.get_stock_by_skus(stock_codes)
            
            items_processed = 0
            items_failed = 0
            
            for item_data in items:
                try:
                    self._upsert_stock_item(item_data)
                    items_processed += 1
                except Exception as e:
                    logger.error(f"Failed to sync stock item {item_data.get('stock_code')}: {str(e)}")
                    items_failed += 1
            
            # Update log
            log.status = 'completed'
            log.items_processed = items_processed
            log.items_failed = items_failed
            log.completed_at = timezone.now()
            log.response_data = {'items_synced': items_processed}
            log.save()
            
            # Update config last_sync
            self.config.last_sync = timezone.now()
            self.config.save()
            
            return log
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = timezone.now()
            log.save()
            raise
    
    def _upsert_stock_item(self, item_data: Dict) -> StockFinderStockItem:
        """Create or update a stock item from Stockfinder data."""
        stock_code = item_data.get('stock_code')
        
        # Try to find local stock item
        local_stock = None
        if stock_code:
            try:
                local_stock = StockItem.objects.get(stock_code=stock_code)
            except StockItem.DoesNotExist:
                pass
        
        # Parse custom pricing
        custom_pricing = {}
        if self.config.enable_custom_pricing:
            for field in ['custom_price_field_1', 'custom_price_field_2', 'custom_price_field_3']:
                field_name = getattr(self.config, field)
                if field_name and field_name in item_data:
                    custom_pricing[field_name] = item_data[field_name]
        
        defaults = {
            'description': item_data.get('description', ''),
            'category': item_data.get('category', ''),
            'quantity_on_hand': Decimal(str(item_data.get('quantity_on_hand', 0))),
            'quantity_available': Decimal(str(item_data.get('quantity_available', 0))),
            'quantity_allocated': Decimal(str(item_data.get('quantity_allocated', 0))),
            'quantity_on_order': Decimal(str(item_data.get('quantity_on_order', 0))),
            'cost_price': Decimal(str(item_data.get('cost_price', 0))),
            'retail_price': Decimal(str(item_data.get('retail_price', 0))),
            'custom_pricing': custom_pricing,
            'barcode': item_data.get('barcode', ''),
            'manufacturer_code': item_data.get('manufacturer_code', ''),
            'supplier_code': item_data.get('supplier_code', ''),
            'local_stock_item': local_stock,
        }
        
        stock_item, created = StockFinderStockItem.objects.update_or_create(
            stockfinder_id=item_data.get('id', stock_code),
            defaults=defaults
        )
        
        return stock_item
    
    @transaction.atomic
    def process_sales_order_webhook(self, order_data: Dict) -> StockFinderSalesOrder:
        """
        Process a sales order received from Stockfinder webhook.
        Creates local sales order and optionally a JobCard.
        """
        log = StockFinderSyncLog.objects.create(
            sync_type='sales_order',
            config=self.config,
            status='in_progress',
            started_at=timezone.now(),
            request_data=order_data
        )
        
        try:
            # Check if order already exists
            stockfinder_order_id = order_data.get('stockfinder_order_id')
            
            if StockFinderSalesOrder.objects.filter(
                stockfinder_order_id=stockfinder_order_id
            ).exists():
                raise StockFinderAPIError(f"Order {stockfinder_order_id} already exists")
            
            # Create sales order
            order = StockFinderSalesOrder.objects.create(
                stockfinder_order_id=stockfinder_order_id,
                customer_name=order_data.get('customer_name', ''),
                customer_email=order_data.get('customer_email', ''),
                customer_phone=order_data.get('customer_phone', ''),
                vehicle_registration=order_data.get('vehicle_registration', ''),
                vehicle_make=order_data.get('vehicle_make', ''),
                vehicle_model=order_data.get('vehicle_model', ''),
                order_date=order_data.get('order_date'),
                required_date=order_data.get('required_date'),
                notes=order_data.get('notes', ''),
                fitment_center=order_data.get('fitment_center', ''),
                status='pending'
            )
            
            # Create order lines
            for idx, line_data in enumerate(order_data.get('lines', []), 1):
                self._create_order_line(order, line_data, idx)
            
            # Calculate totals
            order.calculate_totals()
            
            # Optionally create a local JobCard
            if self.config.fitment_center_code:
                job_card = self._create_local_job_card(order)
                order.local_job_card = job_card
                order.save()
            
            log.status = 'completed'
            log.items_processed = order.lines.count()
            log.completed_at = timezone.now()
            log.save()
            
            return order
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = timezone.now()
            log.save()
            raise
    
    def _create_order_line(
        self,
        order: StockFinderSalesOrder,
        line_data: Dict,
        line_number: int
    ) -> StockFinderSalesOrderLine:
        """Create an order line item."""
        stock_code = line_data.get('stock_code', '')
        
        # Find local stock item
        local_stock = None
        if stock_code:
            try:
                local_stock = StockItem.objects.get(stock_code=stock_code)
            except StockItem.DoesNotExist:
                pass
        
        return StockFinderSalesOrderLine.objects.create(
            order=order,
            line_number=line_number,
            stock_code=stock_code,
            description=line_data.get('description', ''),
            quantity=Decimal(str(line_data.get('quantity', 1))),
            unit_price=Decimal(str(line_data.get('unit_price', 0))),
            tax_amount=Decimal(str(line_data.get('tax_amount', 0))),
            line_total=Decimal(str(line_data.get('line_total', 0))),
            local_stock_item=local_stock
        )
    
    def _create_local_job_card(self, order: StockFinderSalesOrder) -> Optional[JobCard]:
        """Create a local JobCard from the Stockfinder order."""
        try:
            job_card = JobCard.objects.create(
                reference=f"SF-{order.stockfinder_order_id}",
                description=f"Job for {order.customer_name}",
                vehicle_registration=order.vehicle_registration,
                vehicle_make=order.vehicle_make,
                vehicle_model=order.vehicle_model,
                status='pending',
                notes=order.notes,
            )
            
            # Create job card lines from order lines
            for order_line in order.lines.all():
                JobCardLine.objects.create(
                    job_card=job_card,
                    stock_item=order_line.local_stock_item,
                    description=order_line.description,
                    quantity=order_line.quantity,
                    unit_price=order_line.unit_price,
                )
            
            return job_card
            
        except Exception as e:
            logger.error(f"Failed to create local job card: {str(e)}")
            return None
    
    @transaction.atomic
    def process_purchase_order_creation(
        self,
        po_data: Dict,
        create_local_po: bool = True
    ) -> StockFinderPurchaseOrder:
        """
        Process a purchase order created from Stockfinder purchase.
        Optionally creates a local PurchaseOrder.
        """
        log = StockFinderSyncLog.objects.create(
            sync_type='purchase_order',
            config=self.config,
            status='in_progress',
            started_at=timezone.now(),
            request_data=po_data
        )
        
        try:
            stockfinder_po_id = po_data.get('stockfinder_po_id')
            
            # Create Stockfinder purchase order record
            order = StockFinderPurchaseOrder.objects.create(
                stockfinder_po_id=stockfinder_po_id,
                supplier_name=po_data.get('supplier_name', ''),
                supplier_code=po_data.get('supplier_code', ''),
                order_date=po_data.get('order_date'),
                expected_date=po_data.get('expected_date'),
                notes=po_data.get('notes', ''),
                status='pending'
            )
            
            # Create PO lines
            for idx, line_data in enumerate(po_data.get('lines', []), 1):
                self._create_po_line(order, line_data, idx)
            
            # Calculate totals
            order.calculate_totals()
            
            # Create local PO if requested
            local_po = None
            if create_local_po:
                local_po = self._create_local_purchase_order(order)
                order.local_purchase_order = local_po
                order.save()
            
            log.status = 'completed'
            log.items_processed = order.lines.count()
            log.completed_at = timezone.now()
            log.save()
            
            return order
            
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            log.completed_at = timezone.now()
            log.save()
            raise
    
    def _create_po_line(
        self,
        order: StockFinderPurchaseOrder,
        line_data: Dict,
        line_number: int
    ) -> StockFinderPurchaseOrderLine:
        """Create a purchase order line item."""
        return StockFinderPurchaseOrderLine.objects.create(
            order=order,
            line_number=line_number,
            stock_code=line_data.get('stock_code', ''),
            description=line_data.get('description', ''),
            quantity=Decimal(str(line_data.get('quantity', 1))),
            unit_cost=Decimal(str(line_data.get('unit_cost', 0))),
            line_total=Decimal(str(line_data.get('line_total', 0))),
        )
    
    def _create_local_purchase_order(
        self,
        sf_po: StockFinderPurchaseOrder
    ) -> Optional[PurchaseOrder]:
        """Create a local PurchaseOrder from Stockfinder PO."""
        try:
            from apps.creditors.models import Creditor
            
            # Try to find supplier
            supplier = None
            if sf_po.supplier_code:
                try:
                    supplier = Creditor.objects.get(code=sf_po.supplier_code)
                except Creditor.DoesNotExist:
                    pass
            
            po = PurchaseOrder.objects.create(
                reference=f"SF-{sf_po.stockfinder_po_id}",
                supplier=supplier,
                order_date=sf_po.order_date,
                expected_date=sf_po.expected_date,
                notes=sf_po.lines,
                status='pending'
            )
            
            # Create PO lines
            for sf_line in sf_po.lines.all():
                stock_item = None
                if sf_line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=sf_line.stock_code)
                    except StockItem.DoesNotExist:
                        pass
                
                PurchaseOrderLine.objects.create(
                    purchase_order=po,
                    stock_item=stock_item,
                    description=sf_line.description,
                    quantity=sf_line.quantity,
                    unit_cost=sf_line.unit_cost,
                )
            
            po.calculate_totals()
            return po
            
        except Exception as e:
            logger.error(f"Failed to create local purchase order: {str(e)}")
            return None


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Verify the webhook signature from Stockfinder."""
    if not secret or not signature:
        return False
    
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)
