"""
API Views for Stockfinder integration.
Provides endpoints for receiving orders from Stockfinder.
"""

from apps.debtors.models import Debtor
from apps.pos.models import Invoice, InvoiceLine, JobCard
from apps.purchase_orders.models import PurchaseOrder
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StockFinderPurchaseOrder, StockFinderSalesOrder
from .serializers import (
    StockFinderPurchaseOrderCreateSerializer,
    StockFinderPurchaseOrderSerializer,
    StockFinderSalesOrderCreateSerializer,
    StockFinderSalesOrderSerializer,
)
from .services import (
    StockFinderAPIError,
    StockFinderOrderService,
    verify_webhook_signature,
)


class StockFinderWebhookView(APIView):
    """
    Webhook endpoint for receiving events from Stockfinder.
    This is where Stockfinder sends order data to your app.
    """

    permission_classes = [AllowAny]  # Authentication handled via signature

    def post(self, request):
        """Handle incoming webhook events from Stockfinder."""
        # Verify the HMAC signature before doing anything else — this is the
        # only authentication this endpoint has (permission_classes is
        # AllowAny by necessity, since Stockfinder can't hold a session/JWT).
        signature = request.headers.get("X-Signature", "")
        secret = getattr(settings, "STOCKFINDER_WEBHOOK_SECRET", "")
        if not signature or not verify_webhook_signature(
            request.body, signature, secret
        ):
            return Response(
                {"error": "Invalid or missing webhook signature"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Parse event data
        try:
            event_data = request.data
        except Exception:
            return Response(
                {"error": "Invalid JSON"}, status=status.HTTP_400_BAD_REQUEST
            )

        event_type = event_data.get("event_type")
        order_service = StockFinderOrderService()

        # Process the event
        try:
            if event_type == "order_created":
                order = order_service.process_sales_order(event_data.get("data", {}))

                return Response(
                    {
                        "status": "success",
                        "order_id": order.id,
                        "stockfinder_order_id": order.stockfinder_order_id,
                    }
                )

            elif event_type == "purchase_order_created":
                po = order_service.process_purchase_order(event_data.get("data", {}))

                return Response(
                    {
                        "status": "success",
                        "po_id": po.id,
                        "stockfinder_po_id": po.stockfinder_po_id,
                    }
                )

            else:
                return Response(
                    {
                        "status": "ignored",
                        "message": f"Event type {event_type} not supported",
                    }
                )

        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StockFinderOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sales orders received from Stockfinder.
    """

    serializer_class = StockFinderSalesOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return sales orders."""
        queryset = StockFinderSalesOrder.objects.all()

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by customer
        customer = self.request.query_params.get("customer")
        if customer:
            queryset = queryset.filter(
                Q(customer_name__icontains=customer)
                | Q(vehicle_registration__icontains=customer)
            )

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)

        return queryset.order_by("-order_date")

    def create(self, request, *args, **kwargs):
        """Create a sales order from Stockfinder data."""
        serializer = StockFinderSalesOrderCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            order_service = StockFinderOrderService()
            order = order_service.process_sales_order(serializer.validated_data)

            return Response(
                StockFinderSalesOrderSerializer(order).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def create_job_card(self, request, pk=None):
        """Create a local JobCard from this order."""
        order = self.get_object()

        if order.local_job_card:
            return Response(
                {
                    "error": "Job card already exists",
                    "job_card_id": order.local_job_card.id,
                }
            )

        try:
            order_service = StockFinderOrderService()
            job_card = order_service.create_job_card(order)

            if job_card:
                return Response(
                    {
                        "status": "success",
                        "job_card_id": job_card.id,
                        "job_card_reference": job_card.reference,
                    }
                )
            else:
                return Response(
                    {"error": "Failed to create job card"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def create_invoice(self, request, pk=None):
        """Create a local Invoice from this order."""
        order = self.get_object()

        if order.local_invoice:
            return Response(
                {
                    "error": "Invoice already exists",
                    "invoice_id": order.local_invoice.id,
                }
            )

        try:
            order_service = StockFinderOrderService()
            invoice = order_service.create_invoice(order)

            return Response(
                {
                    "status": "success",
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockFinderPurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing purchase orders received from Stockfinder.
    """

    serializer_class = StockFinderPurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return purchase orders."""
        queryset = StockFinderPurchaseOrder.objects.all()

        # Filter by status
        status_filter = self.request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by supplier
        supplier = self.request.query_params.get("supplier")
        if supplier:
            queryset = queryset.filter(
                Q(supplier_name__icontains=supplier)
                | Q(supplier_code__icontains=supplier)
            )

        # Filter by date range
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)

        return queryset.order_by("-order_date")

    def create(self, request, *args, **kwargs):
        """Create a purchase order from Stockfinder data."""
        serializer = StockFinderPurchaseOrderCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            order_service = StockFinderOrderService()
            po = order_service.process_purchase_order(serializer.validated_data)

            return Response(
                StockFinderPurchaseOrderSerializer(po).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def create_local_po(self, request, pk=None):
        """Create a local PurchaseOrder from this Stockfinder PO."""
        sf_po = self.get_object()

        if sf_po.local_purchase_order:
            return Response(
                {
                    "error": "Local PO already exists",
                    "po_id": sf_po.local_purchase_order.id,
                }
            )

        try:
            order_service = StockFinderOrderService()
            local_po = order_service.create_local_purchase_order(sf_po)

            if local_po:
                return Response(
                    {
                        "status": "success",
                        "po_id": local_po.id,
                        "po_reference": local_po.reference,
                    }
                )
            else:
                return Response(
                    {"error": "Failed to create local purchase order"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
