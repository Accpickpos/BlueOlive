"""
Services for Stockfinder API integration.
Handles receiving orders from Stockfinder and creating local records.
"""

import hashlib
import hmac
import logging
from decimal import Decimal
from typing import Dict, Optional

from apps.creditors.models import Creditor
from apps.pos.models import JobCard, JobCardLine
from apps.purchase_orders.models import PurchaseOrder, PurchaseOrderLine
from apps.stock_control.models import StockItem
from django.db import transaction
from django.utils import timezone

from .models import (
    StockFinderPurchaseOrder,
    StockFinderPurchaseOrderLine,
    StockFinderSalesOrder,
    StockFinderSalesOrderLine,
)

logger = logging.getLogger(__name__)


class StockFinderAPIError(Exception):
    """Exception raised for Stockfinder API errors."""

    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data or {}


class StockFinderOrderService:
    """
    Service for processing orders received from Stockfinder.
    Creates local JobCards, Invoices, and Purchase Orders.
    """

    @transaction.atomic
    def process_sales_order(self, order_data: Dict) -> StockFinderSalesOrder:
        """
        Process a sales order received from Stockfinder.
        Creates local sales order and optionally a JobCard.
        """
        # Check if order already exists
        stockfinder_order_id = order_data.get("stockfinder_order_id")

        if StockFinderSalesOrder.objects.filter(
            stockfinder_order_id=stockfinder_order_id
        ).exists():
            raise StockFinderAPIError(f"Order {stockfinder_order_id} already exists")

        # Create sales order
        order = StockFinderSalesOrder.objects.create(
            stockfinder_order_id=stockfinder_order_id,
            customer_name=order_data.get("customer_name", ""),
            customer_email=order_data.get("customer_email", ""),
            customer_phone=order_data.get("customer_phone", ""),
            vehicle_registration=order_data.get("vehicle_registration", ""),
            vehicle_make=order_data.get("vehicle_make", ""),
            vehicle_model=order_data.get("vehicle_model", ""),
            order_date=order_data.get("order_date"),
            required_date=order_data.get("required_date"),
            notes=order_data.get("notes", ""),
            fitment_center=order_data.get("fitment_center", ""),
            status="pending",
        )

        # Create order lines
        for idx, line_data in enumerate(order_data.get("lines", []), 1):
            self._create_order_line(order, line_data, idx)

        # Calculate totals
        order.subtotal = sum(line.line_total for line in order.lines.all())
        order.tax_amount = sum(line.tax_amount for line in order.lines.all())
        order.total_amount = order.subtotal + order.tax_amount
        order.save()

        return order

    def _create_order_line(
        self, order: StockFinderSalesOrder, line_data: Dict, line_number: int
    ) -> StockFinderSalesOrderLine:
        """Create an order line item."""
        stock_code = line_data.get("stock_code", "")

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
            description=line_data.get("description", ""),
            quantity=Decimal(str(line_data.get("quantity", 1))),
            unit_price=Decimal(str(line_data.get("unit_price", 0))),
            tax_amount=Decimal(str(line_data.get("tax_amount", 0))),
            line_total=Decimal(str(line_data.get("line_total", 0))),
            local_stock_item=local_stock,
        )

    def create_job_card(self, order: StockFinderSalesOrder) -> Optional[JobCard]:
        """Create a local JobCard from the Stockfinder order."""
        if order.local_job_card:
            return order.local_job_card

        try:
            job_card = JobCard.objects.create(
                reference=f"SF-{order.stockfinder_order_id}",
                description=f"Job for {order.customer_name}",
                vehicle_registration=order.vehicle_registration,
                vehicle_make=order.vehicle_make,
                vehicle_model=order.vehicle_model,
                status="pending",
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

            # Update order with local job card
            order.local_job_card = job_card
            order.status = "in_progress"
            order.save()

            return job_card

        except Exception as e:
            logger.error(f"Failed to create local job card: {str(e)}")
            return None

    def create_invoice(self, order: StockFinderSalesOrder):
        """Create a local Invoice from the Stockfinder order."""

        from apps.debtors.models import Debtor
        from apps.pos.models import Invoice, InvoiceLine

        if order.local_invoice:
            return order.local_invoice

        # Generate invoice number
        today = timezone.now().date()
        invoice_count = Invoice.objects.filter(invoice_date=today).count() + 1
        invoice_number = (
            f"SF-INV-{today.year}{today.month:02d}{today.day:02d}-{invoice_count:05d}"
        )

        # Find or create debtor
        debtor, created = Debtor.objects.get_or_create(
            dno="STOCKFINDER",
            defaults={
                "name": "Stockfinder Orders",
                "email": "stockfinder@example.com",
                "status": "ACTIVE",
            },
        )

        # Create invoice
        invoice = Invoice.objects.create(
            debtor=debtor,
            invoice_number=invoice_number,
            invoice_date=today,
            subtotal=order.subtotal,
            tax_amount=order.tax_amount,
            total_amount=order.total_amount,
            status="pending",
            notes=f"From Stockfinder Order: {order.stockfinder_order_id}",
        )

        # Create invoice lines from order lines
        for order_line in order.lines.all():
            InvoiceLine.objects.create(
                invoice=invoice,
                stock_item=order_line.local_stock_item,
                description=order_line.description,
                quantity=order_line.quantity,
                unit_price=order_line.unit_price,
                tax_amount=order_line.tax_amount,
                line_total=order_line.line_total,
            )

        # Update order with local invoice
        order.local_invoice = invoice
        order.save()

        return invoice

    @transaction.atomic
    def process_purchase_order(self, po_data: Dict) -> StockFinderPurchaseOrder:
        """
        Process a purchase order received from Stockfinder.
        """
        stockfinder_po_id = po_data.get("stockfinder_po_id")

        # Create Stockfinder purchase order record
        order = StockFinderPurchaseOrder.objects.create(
            stockfinder_po_id=stockfinder_po_id,
            supplier_name=po_data.get("supplier_name", ""),
            supplier_code=po_data.get("supplier_code", ""),
            order_date=po_data.get("order_date"),
            expected_date=po_data.get("expected_date"),
            notes=po_data.get("notes", ""),
            status="pending",
        )

        # Create PO lines
        for idx, line_data in enumerate(po_data.get("lines", []), 1):
            self._create_po_line(order, line_data, idx)

        # Calculate totals
        order.subtotal = sum(line.line_total for line in order.lines.all())
        order.tax_amount = sum(
            Decimal(str(line.line_total)) * Decimal("0.15")
            for line in order.lines.all()
        )
        order.total_amount = order.subtotal + order.tax_amount
        order.save()

        return order

    def _create_po_line(
        self, order: StockFinderPurchaseOrder, line_data: Dict, line_number: int
    ) -> StockFinderPurchaseOrderLine:
        """Create a purchase order line item."""
        return StockFinderPurchaseOrderLine.objects.create(
            order=order,
            line_number=line_number,
            stock_code=line_data.get("stock_code", ""),
            description=line_data.get("description", ""),
            quantity=Decimal(str(line_data.get("quantity", 1))),
            unit_cost=Decimal(str(line_data.get("unit_cost", 0))),
            line_total=Decimal(str(line_data.get("line_total", 0))),
        )

    def create_local_purchase_order(
        self, sf_po: StockFinderPurchaseOrder
    ) -> Optional[PurchaseOrder]:
        """Create a local PurchaseOrder from Stockfinder PO."""
        try:
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
                notes=sf_po.notes,
                status="pending",
            )

            # Create PO lines
            for sf_line in sf_po.lines.all():
                stock_item = None
                if sf_line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(
                            stock_code=sf_line.stock_code
                        )
                    except StockItem.DoesNotExist:
                        pass

                PurchaseOrderLine.objects.create(
                    purchase_order=po,
                    stock_item=stock_item,
                    description=sf_line.description,
                    quantity=sf_line.quantity,
                    unit_cost=sf_line.unit_cost,
                )

            # Calculate totals
            po.subtotal = sum(line.line_total for line in po.lines.all())
            po.tax_amount = sum(
                line.line_total * Decimal("0.15") for line in po.lines.all()
            )
            po.total_amount = po.subtotal + po.tax_amount
            po.save()

            # Update SF PO with local reference
            sf_po.local_purchase_order = po
            sf_po.save()

            return po

        except Exception as e:
            logger.error(f"Failed to create local purchase order: {str(e)}")
            return None


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify the webhook signature from Stockfinder."""
    if not secret or not signature:
        return False

    expected_signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
