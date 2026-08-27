"""
Point of Sale views.
API viewsets for all POS operations based on PointOfSale.pdf
"""

import logging
from datetime import date
from decimal import Decimal

from apps.shop_filter_mixin import ShopFilterMixin
from django.core.exceptions import ValidationError
from django.db.models import Count, Sum
from django.db.models.functions import ExtractHour
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .calculation_service import CalculationService
from .exceptions import (
    InsufficientStock,
    InvalidDocumentState,
    POSStateException,
    POSValidationException,
)
from .filters import CashSaleFilter, JobCardFilter, LaybyeFilter, QuotationFilter
from .models import (
    CashACheque,
    CashControl,
    CashReturn,
    CashSale,
    CreditNote,
    Invoice,
    InvoiceLine,
    JobCard,
    JobCardLine,
    Laybye,
    Payout,
    Quotation,
    ReceiptOnAccount,
    Repair,
    Tender,
    TransactionQuery,
)
from .permissions import POSPermissionMixin
from .serializers import (
    CashAChequeSerializer,
    CashControlHourlySerializer,
    CashControlSerializer,
    CashControlSummarySerializer,
    CashReturnCreateSerializer,
    CashReturnLineSerializer,
    CashReturnSerializer,
    CashSaleCreateSerializer,
    CashSaleDetailSerializer,
    CashSaleListSerializer,
    CreditNoteCreateSerializer,
    CreditNoteDetailSerializer,
    CreditNoteListSerializer,
    InvoiceCreateUpdateSerializer,
    InvoiceDetailSerializer,
    InvoiceLineSerializer,
    InvoiceListSerializer,
    JobCardDetailSerializer,
    JobCardLineSerializer,
    JobCardListSerializer,
    LaybyeCreateSerializer,
    LaybyeDetailSerializer,
    LaybyeListSerializer,
    PayoutSerializer,
    QuotationCreateSerializer,
    QuotationDetailSerializer,
    QuotationListSerializer,
    ReceiptOnAccountSerializer,
    RepairSerializer,
    TenderSerializer,
    TransactionQuerySerializer,
)
from .services import (
    CashAChequeService,
    CashControlService,
    CashReturnService,
    CashSaleService,
    CreditNoteService,
    LaybyeService,
    QuotationService,
    ReceiptOnAccountService,
    RepairService,
)

logger = logging.getLogger(__name__)


class CashSaleViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet for cash sales.

    Actions:
    - list, create, retrieve, update, destroy
    - post_sale: Post cash sale to update stock
    - cancel_sale: Cancel a cash sale
    """

    queryset = CashSale.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"  # Default lookup by primary key
    lookup_value_regex = "[^/]+"  # Allow both numeric IDs and alphanumeric sale_numbers
    filter_backends = [DjangoFilterBackend]
    filterset_class = CashSaleFilter
    ordering_fields = ["sale_date", "sale_time", "total_amount"]
    ordering = ["-sale_date", "-sale_time"]

    def get_object(self):
        """
        Retrieve the object using either pk or sale_number.
        Allow lookup by both numeric ID and sale_number string.
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        # Try to get the lookup value from the URL
        lookup_value = self.kwargs.get(lookup_url_kwarg)

        if not lookup_value:
            return super().get_object()

        # Check if the lookup value is numeric (pk) or string (sale_number)
        if lookup_value.isdigit():
            # It's a numeric ID - use pk lookup
            self.lookup_field = "pk"
        else:
            # It's a string - try sale_number lookup
            self.lookup_field = "sale_number"

        return super().get_object()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return CashSaleListSerializer
        elif self.action == "create":
            return CashSaleCreateSerializer
        return CashSaleDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create a cash sale and return the detail serializer for response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Use detail serializer for response to properly serialize nested data
        response_serializer = CashSaleDetailSerializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = queryset.select_related("cashier", "sales_area")
        elif self.action == "retrieve":
            queryset = queryset.select_related(
                "cashier", "sales_area"
            ).prefetch_related("lines", "tenders")
        return queryset

    @action(detail=True, methods=["post"])
    def post_sale(self, request, pk=None):
        """Post cash sale to update stock."""
        cash_sale = self.get_object()

        try:
            CashSaleService.post_cash_sale(cash_sale)
            return Response(
                {
                    "status": "success",
                    "message": f"Cash sale {cash_sale.sale_number} posted successfully",
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel_sale(self, request, pk=None):
        """Cancel a cash sale."""
        cash_sale = self.get_object()
        reason = request.data.get("reason", "")

        try:
            CashSaleService.cancel_cash_sale(cash_sale, reason)
            return Response(
                {
                    "status": "success",
                    "message": f"Cash sale {cash_sale.sale_number} cancelled",
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def daily_total(self, request):
        """Get total sales for a specific date."""
        sale_date = request.query_params.get("date", date.today())

        total = CashSale.objects.filter(
            sale_date=sale_date, is_posted=True, is_cancelled=False
        ).aggregate(total=Sum("total_amount"))

        return Response({"date": sale_date, "total_sales": total["total"] or 0})

    @action(detail=False, methods=["post"])
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

        stock_code = request.data.get("stock_code")
        quantity = request.data.get("quantity", 1)
        unit_price = request.data.get("unit_price")
        discount_percent = request.data.get("discount_percent", 0)

        if not stock_code:
            return Response(
                {"error": "stock_code is required"}, status=status.HTTP_400_BAD_REQUEST
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
                    transaction_date=date.today(),
                )

            return Response(
                {
                    "stock_code": stock_code,
                    "available_prices": {
                        "price_level_1": float(prices["selling_price_1"]),
                        "price_level_2": float(prices["selling_price_2"]),
                        "price_level_3": float(prices["selling_price_3"]),
                        "markup_percent_1": float(prices["markup_percent_1"]),
                        "markup_percent_2": float(prices["markup_percent_2"]),
                        "markup_percent_3": float(prices["markup_percent_3"]),
                        "cost_price": float(prices["cost_price"]),
                        "maximum_discount": float(prices["maximum_discount"]),
                    },
                    "validation": validation_result,
                    "has_special_deal": prices.get("special_deal") is not None,
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
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

        stock_code = request.data.get("stock_code")

        if not stock_code:
            return Response(
                {"error": "stock_code is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            analysis = PriceValidationService.get_price_analysis(
                stock_code, date.today()
            )
            return Response(analysis)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LaybyeViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
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
    ordering_fields = ["laybye_date", "expiry_date", "total_amount"]
    ordering = ["-laybye_date"]

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == "list":
            return LaybyeListSerializer
        if self.action == "create":
            return LaybyeCreateSerializer
        return LaybyeDetailSerializer

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("lines", "payments")
        return queryset

    def create(self, request, *args, **kwargs):
        """
        Create a laybye with its stock lines in one request, routed through
        LaybyeService.create_laybye so the lines actually reserve goods into
        "laybye stock" (LAYBYE_IN movement) — LaybyeDetailSerializer marks
        `lines` read_only, so a bare ModelViewSet create() can't do this.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        today = timezone.now().date()
        lines_data = data.pop("lines")
        for line in lines_data:
            line.setdefault("transaction_date", today)
            line.setdefault("transaction_time", timezone.now().time())

        laybye_number = (
            data.pop("laybye_number", "")
            or f"LAY-{int(timezone.now().timestamp() * 1000)}"
        )
        laybye_date = data.pop("laybye_date", None) or today

        laybye_data = {
            **data,
            "laybye_number": laybye_number,
            "laybye_date": laybye_date,
        }

        try:
            laybye = LaybyeService.create_laybye(laybye_data, lines_data)
        except (InsufficientStock, POSValidationException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        station_number = request.data.get("station_number", 1)
        if laybye.deposit_amount:
            CashControlService.record_new_laybye(
                laybye.laybye_date, request.user, station_number, laybye.deposit_amount
            )

        return Response(
            LaybyeDetailSerializer(laybye).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"])
    def make_payment(self, request, pk=None):
        """Make a payment on a laybye."""
        laybye = self.get_object()
        amount = request.data.get("amount")
        sales_area_id = request.data.get("sales_area")

        if not amount:
            return Response(
                {"error": "Amount is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from decimal import Decimal

            amount = Decimal(str(amount))

            from apps.settings.models import SalesArea

            sales_area = (
                SalesArea.objects.get(id=sales_area_id) if sales_area_id else None
            )

            payment, invoice = LaybyeService.make_payment(laybye, amount, sales_area)

            CashControlService.record_laybye_receipt(
                payment.payment_date,
                request.user,
                request.data.get("station_number", 1),
                amount,
            )

            response_data = {
                "status": "success",
                "message": "Payment recorded successfully",
                "new_balance": float(laybye.balance_due),
                "laybye_status": laybye.status,
            }
            if invoice:
                response_data["message"] = (
                    f"Payment recorded — laybye fully paid, invoice {invoice.invoice_number} created"
                )
                response_data["invoice_id"] = invoice.id
                response_data["invoice_number"] = invoice.invoice_number

            return Response(response_data)
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel_laybye(self, request, pk=None):
        """Cancel a laybye."""
        laybye = self.get_object()
        retention_percentage = float(request.data.get("retention_percentage", 0))

        try:
            LaybyeService.cancel_laybye(laybye, retention_percentage)

            if laybye.refund_amount:
                from datetime import date as _date

                CashControlService.record_laybye_cancel(
                    _date.today(),
                    request.user,
                    request.data.get("station_number", 1),
                    laybye.refund_amount,
                )

            return Response(
                {
                    "status": "success",
                    "message": "Laybye cancelled",
                    "refund_amount": float(laybye.refund_amount),
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def check_expired(self, request):
        """Check for and mark expired laybyes."""
        count = LaybyeService.check_expired_laybyes()
        return Response({"status": "success", "expired_count": count})

    @action(detail=True, methods=["post"])
    def convert_to_invoice(self, request, pk=None):
        """Convert laybye to customer invoice."""
        laybye = self.get_object()
        debtor_id = request.data.get("debtor_id")
        debtor_account_number = request.data.get("debtor_account_number")
        debtor = None

        # If debtor_id or debtor_account_number provided, look up debtor
        if debtor_id:
            try:
                from apps.debtors.models import Debtor

                debtor = Debtor.objects.get(id=debtor_id)
            except Debtor.DoesNotExist:
                return Response(
                    {"error": f"Debtor with id {debtor_id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif debtor_account_number:
            try:
                from apps.debtors.models import Debtor

                # Convert string to integer - dno is an IntegerField
                debtor = Debtor.objects.get(dno=int(debtor_account_number))
            except Debtor.DoesNotExist:
                return Response(
                    {
                        "error": f"Debtor with account number {debtor_account_number} not found"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            except (ValueError, TypeError):
                return Response(
                    {
                        "error": f"Invalid account number format: {debtor_account_number}. Must be a number."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Try conversion even without debtor (for manual customer entry)
        try:
            from .services import QuotationService

            invoice = QuotationService.convert_laybye_to_invoice(laybye, debtor)

            # Import the invoice serializer
            from .serializers import InvoiceDetailSerializer

            serializer = InvoiceDetailSerializer(invoice)

            return Response(
                {
                    "status": "success",
                    "message": "Laybye converted to invoice",
                    "invoice": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            return Response(
                {"error": f"Conversion failed: {str(e)}", "details": error_details},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"])
    def active(self, request):
        """Get all active laybyes."""
        active_laybyes = self.get_queryset().filter(status="ACTIVE")

        page = self.paginate_queryset(active_laybyes)
        if page is not None:
            serializer = LaybyeListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = LaybyeListSerializer(active_laybyes, many=True)
        return Response(serializer.data)


class QuotationViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
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
    ordering_fields = ["quotation_date", "expiry_date", "total_amount"]
    ordering = ["-quotation_date"]

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == "list":
            return QuotationListSerializer
        elif self.action == "create":
            return QuotationCreateSerializer
        return QuotationDetailSerializer

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("lines")
        return queryset

    @action(detail=True, methods=["post"])
    def convert_to_invoice(self, request, pk=None):
        """Convert quotation to invoice."""
        quotation = self.get_object()
        debtor_id = request.data.get("debtor_id")
        debtor_account_number = request.data.get("debtor_account_number")
        debtor = None

        # If debtor_id or debtor_account_number provided, look up debtor
        if debtor_id:
            try:
                from apps.debtors.models import Debtor

                debtor = Debtor.objects.get(id=debtor_id)
            except Debtor.DoesNotExist:
                return Response(
                    {"error": f"Debtor with id {debtor_id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif debtor_account_number:
            try:
                from apps.debtors.models import Debtor

                # Convert string to integer - dno is an IntegerField
                debtor = Debtor.objects.get(dno=int(debtor_account_number))
            except Debtor.DoesNotExist:
                return Response(
                    {
                        "error": f"Debtor with account number {debtor_account_number} not found"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            except (ValueError, TypeError):
                return Response(
                    {
                        "error": f"Invalid account number format: {debtor_account_number}. Must be a number."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Try conversion even without debtor (for manual customer entry)
        try:
            invoice = QuotationService.convert_quotation_to_invoice(quotation, debtor)

            # Import the invoice serializer
            from .serializers import InvoiceDetailSerializer

            serializer = InvoiceDetailSerializer(invoice)

            return Response(
                {
                    "status": "success",
                    "message": "Quotation converted to invoice",
                    "invoice": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            return Response(
                {"error": f"Conversion failed: {str(e)}", "details": error_details},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"])
    def convert_to_job(self, request, pk=None):
        """Convert quotation to job card."""
        quotation = self.get_object()

        try:
            job_card = QuotationService.convert_to_job_card(quotation)

            return Response(
                {
                    "status": "success",
                    "message": "Quotation converted to job card",
                    "job_number": job_card.job_number,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PayoutViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for cash payouts."""

    queryset = Payout.objects.all()
    serializer_class = PayoutSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["payout_date", "cashier", "station_number"]
    ordering_fields = ["payout_date", "amount"]
    ordering = ["-payout_date"]

    def perform_create(self, serializer):
        payout = serializer.save(
            cashier=serializer.validated_data.get("cashier") or self.request.user
        )
        CashControlService.record_payout(
            payout.payout_date, payout.cashier, payout.station_number, payout.amount
        )


class RepairViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
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
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "date_required"]
    ordering = ["-created_at"]

    @action(detail=True, methods=["post"])
    def issue_to_supplier(self, request, pk=None):
        """Issue repair to supplier."""
        repair = self.get_object()
        supplier_account = request.data.get("supplier_account")
        transport_mode = request.data.get("transport_mode", "")

        if not supplier_account:
            return Response(
                {"error": "supplier_account is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            RepairService.issue_to_supplier(repair, supplier_account, transport_mode)
            return Response(
                {"status": "success", "message": "Repair issued to supplier"}
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def receive_from_supplier(self, request, pk=None):
        """Receive repaired item from supplier."""
        repair = self.get_object()
        repair_cost = request.data.get("repair_cost")
        supplier_invoice = request.data.get("supplier_invoice", "")

        if not repair_cost:
            return Response(
                {"error": "repair_cost is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from decimal import Decimal

            repair_cost = Decimal(str(repair_cost))

            RepairService.receive_from_supplier(repair, repair_cost, supplier_invoice)
            return Response(
                {"status": "success", "message": "Repair received from supplier"}
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def invoice_customer(self, request, pk=None):
        """
        Charge for the repair. Manual §R '5. Charge for the Repair': Cash
        option ends in a Tender Routine; Account option resolves an
        existing Debtor or captures a new one on the fly. Line items are
        manually re-captured here, not copied from the repair's supplier
        issue/receipt trail.

        POST data:
        {
            "charge_type": "cash" | "account",
            "lines": [{"stock_code": "...", "description": "...", "quantity": 1,
                       "unit_price": "100.00", "discount_percentage": 0,
                       "tax_code": 1, "cost_price": "0.00"}, ...],
            "tenders": [{"tender_type": "CASH", "amount": "100.00"}, ...],  # cash only
            "debtor_id": 1,               # account, existing debtor
            "new_debtor_data": {...}      # account, new debtor on the fly
        }
        """
        repair = self.get_object()
        charge_type = request.data.get("charge_type")
        lines_data = request.data.get("lines", [])
        tenders_data = request.data.get("tenders", [])
        debtor_id = request.data.get("debtor_id")
        new_debtor_data = request.data.get("new_debtor_data")

        if not charge_type:
            return Response(
                {"error": "charge_type is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = RepairService.invoice_customer(
                repair,
                charge_type=charge_type,
                lines_data=lines_data,
                debtor_id=debtor_id,
                new_debtor_data=new_debtor_data,
                tenders_data=tenders_data,
                cashier=(
                    request.user
                    if request.user and request.user.is_authenticated
                    else None
                ),
                station_number=request.data.get("station_number", 1),
            )

            if result["charge_type"] == "cash":
                document_data = CashSaleDetailSerializer(result["document"]).data
            else:
                document_data = InvoiceDetailSerializer(result["document"]).data

            return Response(
                {
                    "status": "success",
                    "message": f'Repair {repair.repair_number} charged ({result["charge_type"]})',
                    "charge_type": result["charge_type"],
                    "document": document_data,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class JobCardViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
    """ViewSet for job cards."""

    queryset = JobCard.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = JobCardFilter
    ordering_fields = ["job_date", "total_amount"]
    ordering = ["-job_date"]

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == "list":
            return JobCardListSerializer
        return JobCardDetailSerializer

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("lines")
        return queryset

    @action(detail=True, methods=["post"], url_path="line-items")
    def add_line_items(self, request, pk=None):
        """Add line items to a job card."""
        job_card = self.get_object()
        line_items_data = request.data

        if not isinstance(line_items_data, list):
            return Response(
                {"error": "line_items must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created_lines = []
        for idx, item_data in enumerate(line_items_data, start=1):
            quantity = Decimal(str(item_data.get("quantity", 1)))
            unit_price = Decimal(str(item_data.get("unit_price", 0)))
            discount_percentage = Decimal(str(item_data.get("discount_percentage", 0)))
            cost_price = Decimal(str(item_data.get("cost_price", 0)))

            # 'STANDARD' was accepted as a tax_code alias for 1 by the old
            # hand-rolled calculation below — normalize before handing off to
            # CalculationService, which only recognizes the int form.
            raw_tax_code = item_data.get("tax_code", 1)
            tax_code = 1 if raw_tax_code == "STANDARD" else raw_tax_code

            calc = CalculationService.calculate_line_totals(
                quantity=quantity,
                unit_price=unit_price,
                discount_percentage=discount_percentage,
                tax_code=tax_code,
                cost_price=cost_price,
            )

            line_item = JobCardLine.objects.create(
                job_card=job_card,
                line_number=item_data.get("line_number", idx),
                stock_code=item_data.get("stock_code", ""),
                description=item_data.get("description", ""),
                quantity=quantity,
                unit_price=unit_price,
                discount_percentage=discount_percentage,
                tax_code=tax_code,
                # NOTE: unlike InvoiceLine, JobCardLine.line_total is
                # VAT-INCLUSIVE — the header rollup below does
                # `line_total - vat_amount` to derive subtotal, so this must
                # stay mapped from the service's VAT-inclusive `line_total`.
                line_total=calc["line_total"],
                vat_amount=calc["vat_amount"],
                cost_price=cost_price,
                line_profit=calc["line_profit"],
            )
            created_lines.append(line_item)

        # Update job card totals
        job_card.refresh_from_db()
        lines = job_card.lines.all()
        job_card.subtotal = sum((line.line_total - line.vat_amount) for line in lines)
        job_card.vat_amount = sum(line.vat_amount for line in lines)
        job_card.total_amount = job_card.subtotal + job_card.vat_amount
        job_card.total_cost = sum((line.quantity * line.cost_price) for line in lines)
        job_card.gross_profit = job_card.subtotal - job_card.total_cost
        job_card.save()

        serializer = JobCardLineSerializer(created_lines, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def apply_subtotal_discount(self, request, pk=None):
        """Manual §J 'Job Costing', Update Transaction 'S' option."""
        job_card = self.get_object()
        percentage = request.data.get("percentage")

        if percentage is None:
            return Response(
                {"error": "percentage is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            job_card.apply_subtotal_discount(Decimal(str(percentage)))
            return Response(
                {
                    "status": "success",
                    "message": f"Subtotal discount of {percentage}% applied to job card {job_card.job_number}",
                    "job_card": JobCardDetailSerializer(job_card).data,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def apply_set_price(self, request, pk=None):
        """Manual §J 'Job Costing', Update Transaction 'Set Price' option."""
        job_card = self.get_object()
        target_total = request.data.get("target_total")

        if target_total is None:
            return Response(
                {"error": "target_total is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            job_card.apply_set_price(Decimal(str(target_total)))
            return Response(
                {
                    "status": "success",
                    "message": f"Job card {job_card.job_number} total set to {target_total}",
                    "job_card": JobCardDetailSerializer(job_card).data,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def convert_to_invoice(self, request, pk=None):
        """Convert job card to customer invoice."""
        job_card = self.get_object()
        debtor_id = request.data.get("debtor_id")
        debtor_account_number = request.data.get("debtor_account_number")
        debtor = None

        # If debtor_id or debtor_account_number provided, look up debtor
        if debtor_id:
            try:
                from apps.debtors.models import Debtor

                debtor = Debtor.objects.get(id=debtor_id)
            except Debtor.DoesNotExist:
                return Response(
                    {"error": f"Debtor with id {debtor_id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif debtor_account_number:
            try:
                from apps.debtors.models import Debtor

                # Convert string to integer - dno is an IntegerField
                debtor = Debtor.objects.get(dno=int(debtor_account_number))
            except Debtor.DoesNotExist:
                return Response(
                    {
                        "error": f"Debtor with account number {debtor_account_number} not found"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
            except (ValueError, TypeError):
                return Response(
                    {
                        "error": f"Invalid account number format: {debtor_account_number}. Must be a number."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Try conversion even without debtor (for manual customer entry)
        try:
            from .services import QuotationService

            invoice = QuotationService.convert_job_card_to_invoice(job_card, debtor)

            # Import the invoice serializer
            from .serializers import InvoiceDetailSerializer

            serializer = InvoiceDetailSerializer(invoice)

            return Response(
                {
                    "status": "success",
                    "message": "Job card converted to invoice",
                    "invoice": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            import traceback

            error_details = traceback.format_exc()
            return Response(
                {"error": f"Conversion failed: {str(e)}", "details": error_details},
                status=status.HTTP_400_BAD_REQUEST,
            )


class CashControlViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for cash control records.
    Read-only as these are generated by the system.
    """

    queryset = CashControl.objects.all()
    serializer_class = CashControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["control_date", "cashier", "station_number", "is_cleared"]
    ordering_fields = ["control_date"]
    ordering = ["-control_date"]

    @action(detail=False, methods=["get"])
    def daily_summary(self, request):
        """Get daily cash control summary."""
        control_date = request.query_params.get("date", date.today())
        cashier_id = request.query_params.get("cashier")
        station_number = request.query_params.get("station_number")

        summary = CashSaleService.get_daily_summary(
            control_date, cashier_id, station_number
        )

        serializer = CashControlSummarySerializer(summary)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def clear(self, request, pk=None):
        """Mark cash control as cleared."""
        cash_control = self.get_object()
        cash_control.is_cleared = True
        cash_control.save()

        return Response({"status": "success", "message": "Cash control cleared"})

    @action(detail=False, methods=["get"])
    def hourly_analysis(self, request):
        """
        Sales movement on a 24-hour basis for a given date, per the legacy
        spec's Hourly Analysis facility. CashControl only stores daily
        aggregates, so this groups CashSale.sale_time by hour directly
        rather than reading from CashControl.
        """
        control_date = request.query_params.get("date", date.today())
        cashier_id = request.query_params.get("cashier")
        station_number = request.query_params.get("station_number")

        queryset = CashSale.objects.filter(sale_date=control_date, is_cancelled=False)
        if cashier_id:
            queryset = queryset.filter(cashier_id=cashier_id)
        if station_number:
            queryset = queryset.filter(station_number=station_number)

        hourly = (
            queryset.annotate(hour=ExtractHour("sale_time"))
            .values("hour")
            .annotate(transaction_count=Count("id"), total_value=Sum("total_amount"))
        )
        hours_by_number = {row["hour"]: row for row in hourly}

        hours = [
            {
                "hour": hour,
                "transaction_count": hours_by_number.get(hour, {}).get(
                    "transaction_count", 0
                ),
                "total_value": hours_by_number.get(hour, {}).get("total_value")
                or Decimal("0.00"),
            }
            for hour in range(24)
        ]

        serializer = CashControlHourlySerializer({"date": control_date, "hours": hours})
        return Response(serializer.data)


class ReceiptOnAccountViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
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
    filterset_fields = [
        "receipt_date",
        "debtor_account",
        "tender_type",
        "is_posted",
        "cashier",
        "station_number",
    ]
    ordering_fields = ["receipt_date", "amount"]
    ordering = ["-receipt_date"]

    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related("cashier")

    @action(detail=True, methods=["post"])
    def post_receipt(self, request, pk=None):
        """
        Post receipt to debtor account. Manual §1 '2. Receipts on Account'
        describes two distinct flows by account category:
        - Balance Brought Forward: amount due + amount tendered are entered;
          the difference is the settlement discount.
        - Open Item: payment is allocated line-by-line against specific
          open transactions; a settlement discount is only permitted on a
          FULL settlement of an item.

        Optional POST data (on top of the existing receipt record):
        {
            "amount_due": "500.00",   # BBF debtors — enables settlement discount
            "allocations": [{"open_item_id": 1, "amount": "100.00",
                              "settlement_discount": "0.00"}, ...]  # Open Item debtors
        }
        """
        receipt = self.get_object()

        if receipt.is_posted:
            return Response(
                {"error": "Receipt already posted"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from apps.debtors.models import Debtopen, Debtor
            from apps.debtors.services import DebtorService

            try:
                debtor = Debtor.objects.get(dno=int(receipt.debtor_account))
            except (Debtor.DoesNotExist, ValueError, TypeError):
                debtor = None

            if debtor:
                amount_due = request.data.get("amount_due")
                allocations = request.data.get("allocations")

                trans = DebtorService.post_receipt(
                    debtor=debtor,
                    amount=receipt.amount,
                    amount_due=(
                        Decimal(str(amount_due)) if amount_due is not None else None
                    ),
                    allocations=allocations,
                    custref=receipt.reference[:10] if receipt.reference else "",
                )
                receipt.debtor_transaction = trans
            else:
                logger.warning(
                    f"Receipt {receipt.receipt_number}: debtor account "
                    f"'{receipt.debtor_account}' not found — posting till/CashControl only"
                )

            receipt.is_posted = True
            receipt.save()

            CashControlService.record_receipt(
                receipt.receipt_date,
                receipt.cashier,
                receipt.station_number,
                receipt.total_amount,
                receipt.tender_type,
            )

            return Response(
                {
                    "status": "success",
                    "message": f"Receipt {receipt.receipt_number} posted successfully",
                }
            )
        except Debtopen.DoesNotExist:
            return Response(
                {
                    "error": "One or more allocations reference an open item not found for this debtor"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (ValueError, KeyError, POSValidationException) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a receipt on account."""
        receipt = self.get_object()
        reason = request.data.get("reason", "")

        try:
            ReceiptOnAccountService.cancel_receipt(receipt, reason)
            return Response(
                {
                    "status": "success",
                    "message": f"Receipt {receipt.receipt_number} cancelled",
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def daily_total(self, request):
        """Get total receipts for a specific date."""
        receipt_date = request.query_params.get("date", date.today())

        from django.db.models import Sum

        total = ReceiptOnAccount.objects.filter(
            receipt_date=receipt_date, is_posted=True
        ).aggregate(total=Sum("total_amount"))

        return Response({"date": receipt_date, "total_receipts": total["total"] or 0})


class CreditNoteViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet for credit notes.

    Actions:
    - list, create, retrieve, update, destroy
    - post_credit: Post credit note
    """

    queryset = CreditNote.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = [
        "credit_date",
        "debtor_account",
        "is_posted",
        "cashier",
        "station_number",
    ]
    ordering_fields = ["credit_date", "total_amount"]
    ordering = ["-credit_date"]

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == "list":
            return CreditNoteListSerializer
        elif self.action == "create":
            return CreditNoteCreateSerializer
        return CreditNoteDetailSerializer

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("lines")
        return queryset.select_related("cashier", "sales_area")

    @action(detail=True, methods=["post"])
    def post_credit(self, request, pk=None):
        """Post credit note to update stock and debtor account."""
        credit_note = self.get_object()

        if credit_note.is_posted:
            return Response(
                {"error": "Credit note already posted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Update stock for each line
            from apps.stock_control.models import StockItem, StockTransaction

            for line in credit_note.lines.all():
                if line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=line.stock_code)
                        stock_item.quantity_on_hand += line.quantity
                        stock_item.save()

                        # Create stock movement. transaction_number is an
                        # IntegerField — credit_number is a string, use
                        # comments instead so this doesn't raise.
                        StockTransaction.objects.create(
                            stock_item=stock_item,
                            transaction_type="RETURN",
                            transaction_date=credit_note.credit_date,
                            comments=credit_note.credit_number[:30],
                            quantity_in=line.quantity,
                            quantity_balance=stock_item.quantity_on_hand,
                            unit_price=line.unit_price,
                            station_number=credit_note.station_number,
                        )
                    except StockItem.DoesNotExist:
                        pass

            credit_note.is_posted = True
            credit_note.save()

            CashControlService.record_credit_note(
                credit_note.credit_date,
                credit_note.cashier,
                credit_note.station_number,
                credit_note.total_amount,
            )

            return Response(
                {
                    "status": "success",
                    "message": f"Credit note {credit_note.credit_number} posted successfully",
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a credit note."""
        credit_note = self.get_object()
        reason = request.data.get("reason", "")

        try:
            CreditNoteService.cancel_credit_note(credit_note, reason)
            return Response(
                {
                    "status": "success",
                    "message": f"Credit note {credit_note.credit_number} cancelled",
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CashReturnViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet for cash returns.

    Actions:
    - list, create, retrieve, update, destroy
    - post_return: Post cash return
    """

    queryset = CashReturn.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["return_date", "is_posted", "cashier", "station_number"]
    ordering_fields = ["return_date", "total_amount"]
    ordering = ["-return_date"]

    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == "create":
            return CashReturnCreateSerializer
        return CashReturnSerializer

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == "retrieve":
            queryset = queryset.prefetch_related("lines")
        return queryset.select_related("cashier")

    @action(detail=True, methods=["post"])
    def post_return(self, request, pk=None):
        """Post cash return to update stock."""
        cash_return = self.get_object()

        if cash_return.is_posted:
            return Response(
                {"error": "Cash return already posted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Update stock for each line
            from apps.stock_control.models import StockItem, StockTransaction

            for line in cash_return.lines.all():
                if line.stock_code:
                    try:
                        stock_item = StockItem.objects.get(stock_code=line.stock_code)
                        stock_item.quantity_on_hand += line.quantity
                        stock_item.save()

                        # Create stock movement. transaction_number is an
                        # IntegerField — return_number is a string, use
                        # comments instead so this doesn't raise.
                        StockTransaction.objects.create(
                            stock_item=stock_item,
                            transaction_type="RETURN",
                            transaction_date=cash_return.return_date,
                            comments=cash_return.return_number[:30],
                            quantity_in=line.quantity,
                            quantity_balance=stock_item.quantity_on_hand,
                            unit_price=line.unit_price,
                            station_number=cash_return.station_number,
                        )
                    except StockItem.DoesNotExist:
                        pass

            cash_return.is_posted = True
            cash_return.save()

            CashControlService.record_cash_return(
                cash_return.return_date,
                cash_return.cashier,
                cash_return.station_number,
                cash_return.total_amount,
            )

            return Response(
                {
                    "status": "success",
                    "message": f"Cash return {cash_return.return_number} posted successfully",
                }
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a cash return."""
        cash_return = self.get_object()
        reason = request.data.get("reason", "")

        try:
            CashReturnService.cancel_cash_return(cash_return, reason)
            return Response(
                {
                    "status": "success",
                    "message": f"Cash return {cash_return.return_number} cancelled",
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CashAChequeViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
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
    filterset_fields = ["transaction_date", "is_processed", "cashier", "station_number"]
    ordering_fields = ["transaction_date", "cheque_amount"]
    ordering = ["-transaction_date"]

    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related("cashier")

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Mark cheque as processed."""
        cheque = self.get_object()

        if cheque.is_processed:
            return Response(
                {"error": "Cheque already processed"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cheque.is_processed = True
        cheque.save()

        CashControlService.record_cashed_cheque(
            cheque.transaction_date,
            cheque.cashier,
            cheque.station_number,
            cheque.cash_paid,
        )

        return Response(
            {
                "status": "success",
                "message": f"Cheque {cheque.cheque_number} marked as processed",
            }
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a cash-a-cheque transaction."""
        cheque = self.get_object()
        reason = request.data.get("reason", "")

        try:
            CashAChequeService.cancel_cash_a_cheque(cheque, reason)
            return Response(
                {
                    "status": "success",
                    "message": f"Cheque {cheque.cheque_number} cancelled",
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def unprocessed(self, request):
        """Get all unprocessed cheques."""
        unprocessed = self.get_queryset().filter(is_processed=False)

        page = self.paginate_queryset(unprocessed)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(unprocessed, many=True)
        return Response(serializer.data)


class TransactionQueryViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
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
    filterset_fields = ["query_date", "transaction_type", "query_status", "assigned_to"]
    ordering_fields = ["query_date"]
    ordering = ["-query_date"]

    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related("assigned_to", "resolved_by")

    # Maps each declared transaction_type choice to how to search it and how
    # to project results into a common shape:
    # {transaction_type, number, date, party_name, total_amount, status}.
    # 'status' is None for types with no status/state-machine field.
    _SEARCH_CONFIG = {
        "CASH_SALE": (
            CashSale,
            "sale_number",
            "sale_date",
            "customer_name",
            "total_amount",
            None,
        ),
        "INVOICE": (
            Invoice,
            "invoice_number",
            "invoice_date",
            None,
            "total_amount",
            "status",
        ),
        "RECEIPT": (
            ReceiptOnAccount,
            "receipt_number",
            "receipt_date",
            "debtor_name",
            "total_amount",
            None,
        ),
        "CREDIT_NOTE": (
            CreditNote,
            "credit_number",
            "credit_date",
            "customer_name",
            "total_amount",
            None,
        ),
        "LAYBYE": (
            Laybye,
            "laybye_number",
            "laybye_date",
            "customer_name",
            "total_amount",
            "status",
        ),
        "QUOTATION": (
            Quotation,
            "quotation_number",
            "quotation_date",
            "customer_name",
            "total_amount",
            "status",
        ),
        "JOB_CARD": (
            JobCard,
            "job_number",
            "job_date",
            "customer_name",
            "total_amount",
            "status",
        ),
        "REPAIR": (
            Repair,
            "repair_number",
            "created_at",
            "customer_name",
            "selling_price",
            "status",
        ),
        "PAYOUT": (Payout, None, "payout_date", "payee", "amount", None),
    }

    @action(detail=False, methods=["post"])
    def search(self, request):
        """
        Search for transactions across any of the 9 documented transaction
        types (manual §1 '6. Transaction Query'). Every branch is projected
        into one common result shape so a single caller can render results
        regardless of query_type.
        """
        query_type = request.data.get("query_type")
        transaction_number = request.data.get("transaction_number", "")
        customer_name = request.data.get("customer_name", "")
        date_from = request.data.get("date_from")
        date_to = request.data.get("date_to")

        config = self._SEARCH_CONFIG.get(query_type)
        if not config:
            return Response(
                {
                    "query_type": query_type,
                    "results_count": 0,
                    "results": [],
                    "error": (
                        f"Unknown or unsupported query_type: {query_type}"
                        if query_type
                        else None
                    ),
                }
            )

        model, number_field, date_field, name_field, amount_field, status_field = config

        qs = model.objects.all()
        if transaction_number and number_field:
            qs = qs.filter(**{f"{number_field}__icontains": transaction_number})
        if customer_name and name_field:
            qs = qs.filter(**{f"{name_field}__icontains": customer_name})
        if date_from:
            qs = qs.filter(**{f"{date_field}__gte": date_from})
        if date_to:
            qs = qs.filter(**{f"{date_field}__lte": date_to})

        results = []
        for obj in qs:
            results.append(
                {
                    "transaction_type": query_type,
                    "number": (
                        getattr(obj, number_field, None)
                        if number_field
                        else str(obj.pk)
                    ),
                    "date": getattr(obj, date_field, None),
                    "party_name": (
                        getattr(obj, name_field, None) if name_field else None
                    ),
                    "total_amount": (
                        getattr(obj, amount_field, None) if amount_field else None
                    ),
                    "status": (
                        getattr(obj, status_field, None) if status_field else None
                    ),
                }
            )

        return Response(
            {
                "query_type": query_type,
                "results_count": len(results),
                "results": results,
            }
        )

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        """Resolve a query."""
        query = self.get_object()
        resolution_notes = request.data.get("resolution_notes", "")

        query.query_status = "RESOLVED"
        query.resolution_notes = resolution_notes
        query.resolved_by = request.user
        query.resolved_date = date.today()
        query.save()

        return Response(
            {"status": "success", "message": f"Query {query.query_number} resolved"}
        )

    @action(detail=True, methods=["post"])
    def assign(self, request, pk=None):
        """Assign query to a user."""
        query = self.get_object()
        assigned_to_id = request.data.get("assigned_to")

        if not assigned_to_id:
            return Response(
                {"error": "assigned_to is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        from django.contrib.auth import get_user_model

        User = get_user_model()
        try:
            user = User.objects.get(id=assigned_to_id)
            query.assigned_to = user
            query.query_status = "IN_PROGRESS"
            query.save()

            return Response(
                {"status": "success", "message": f"Query assigned to {user.username}"}
            )
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )


class InvoiceViewSet(ShopFilterMixin, POSPermissionMixin, viewsets.ModelViewSet):
    """
    ViewSet for customer invoices.

    Actions:
    - list, create, retrieve, update, destroy
    - post: Post invoice to accounts
    - cancel: Cancel invoice
    - void: Void posted invoice
    - apply-payment: Apply payment to invoice
    """

    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = "pk"  # Default lookup by primary key
    lookup_value_regex = (
        "[^/]+"  # Allow both numeric IDs and alphanumeric invoice_numbers
    )
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["status", "invoice_date", "debtor", "is_posted"]
    ordering_fields = ["invoice_date", "invoice_number", "total_amount"]
    ordering = ["-invoice_date", "-invoice_number"]

    def get_object(self):
        """
        Retrieve the object using either pk or invoice_number.
        Allow lookup by both numeric ID and string.
        """
        # Get the lookup value from kwargs
        pk = self.kwargs.get("pk")
        invoice_number = self.kwargs.get("invoice_number")

        # Determine which field to use based on URL parameter
        if pk and pk.isdigit():
            # Numeric ID in URL - use pk lookup
            self.lookup_field = "pk"
            self.lookup_url_kwarg = "pk"
            return super().get_object()
        elif invoice_number:
            # invoice_number in URL
            self.lookup_field = "invoice_number"
            self.lookup_url_kwarg = "invoice_number"
            return super().get_object()
        elif pk:
            # Non-numeric string in pk position (like invoice number)
            self.lookup_field = "invoice_number"
            self.lookup_url_kwarg = (
                "pk"  # Use pk as the URL kwarg but lookup by invoice_number
            )
            return super().get_object()

        # Fallback to default behavior
        return super().get_object()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return InvoiceListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return InvoiceCreateUpdateSerializer
        return InvoiceDetailSerializer

    def create(self, request, *args, **kwargs):
        """Create an invoice and return the detail serializer for response."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        # Use detail serializer for response to properly serialize nested data
        response_serializer = InvoiceDetailSerializer(instance)
        headers = self.get_success_headers(response_serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def get_queryset(self):
        """Optimize queryset."""
        queryset = super().get_queryset()
        if self.action == "list":
            queryset = queryset.select_related("debtor")
        elif self.action == "retrieve":
            # Note: sales_area is a CharField, not a ForeignKey, so cannot use select_related
            queryset = queryset.select_related("debtor").prefetch_related("lines")
        return queryset

    def perform_create(self, serializer):
        """Auto-generate invoice number if not provided."""
        if not serializer.validated_data.get("invoice_number"):
            from django.utils import timezone

            today = timezone.now().date()
            count = Invoice.objects.filter(invoice_date=today).count() + 1
            invoice_number = (
                f"INV-{today.year}{today.month:02d}{today.day:02d}-{count:05d}"
            )
            serializer.save(invoice_number=invoice_number)
        else:
            serializer.save()

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None):
        """Post invoice to accounts."""
        invoice = self.get_object()

        try:
            invoice.post()
            return Response(
                {
                    "status": "success",
                    "message": f"Invoice {invoice.invoice_number} posted successfully",
                    "invoice": InvoiceDetailSerializer(invoice).data,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel invoice."""
        invoice = self.get_object()

        try:
            invoice.cancel()
            return Response(
                {
                    "status": "success",
                    "message": f"Invoice {invoice.invoice_number} cancelled",
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def void(self, request, pk=None):
        """Void posted invoice."""
        invoice = self.get_object()

        try:
            invoice.void()
            return Response(
                {
                    "status": "success",
                    "message": f"Invoice {invoice.invoice_number} voided",
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def apply_payment(self, request, pk=None):
        """Apply payment to invoice."""
        invoice = self.get_object()
        amount = request.data.get("amount")
        payment_date = request.data.get("payment_date")

        if not amount:
            return Response(
                {"error": "amount is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from decimal import Decimal

            amount = Decimal(str(amount))

            if payment_date:
                from datetime import datetime

                payment_date = datetime.strptime(payment_date, "%Y-%m-%d").date()

            invoice.apply_payment(amount, payment_date)
            return Response(
                {
                    "status": "success",
                    "message": f"Payment of {amount} applied to invoice {invoice.invoice_number}",
                    "invoice": InvoiceDetailSerializer(invoice).data,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def next_number(self, request):
        """Get next invoice number."""
        from django.utils import timezone

        today = timezone.now().date()
        count = Invoice.objects.filter(invoice_date=today).count() + 1
        invoice_number = f"INV-{today.year}{today.month:02d}{today.day:02d}-{count:05d}"
        return Response({"invoice_number": invoice_number})

    @action(detail=True, methods=["post"])
    def apply_subtotal_discount(self, request, pk=None):
        """Manual §1 'Invoice - Subtotal Discount Facility'."""
        invoice = self.get_object()
        percentage = request.data.get("percentage")

        if percentage is None:
            return Response(
                {"error": "percentage is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            invoice.apply_subtotal_discount(Decimal(str(percentage)))
            return Response(
                {
                    "status": "success",
                    "message": f"Subtotal discount of {percentage}% applied to invoice {invoice.invoice_number}",
                    "invoice": InvoiceDetailSerializer(invoice).data,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def apply_set_price(self, request, pk=None):
        """Manual §1 'Invoice - Set Selling Price Facility'."""
        invoice = self.get_object()
        target_total = request.data.get("target_total")

        if target_total is None:
            return Response(
                {"error": "target_total is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            invoice.apply_set_price(Decimal(str(target_total)))
            return Response(
                {
                    "status": "success",
                    "message": f"Invoice {invoice.invoice_number} total set to {target_total}",
                    "invoice": InvoiceDetailSerializer(invoice).data,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def tender(self, request, pk=None):
        """
        Manual §1 'Invoice - Cash Debtors': collect a tender against this
        invoice and apply it as a payment, in one step — for Cash Debtors
        (acctype='C', terms=0) this is what "the invoice transaction will
        end with a Tender Routine" means in this API. Not restricted to
        only invoices where requires_cash_tender is true; any invoice may
        be tendered this way if the caller chooses to.
        """
        invoice = self.get_object()
        tenders_data = request.data.get("tenders", [])

        if not tenders_data:
            return Response(
                {"error": "tenders is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            total = Decimal("0.00")
            created_tenders = []
            for tender_data in tenders_data:
                serializer = TenderSerializer(data=tender_data)
                serializer.is_valid(raise_exception=True)
                tender_obj = Tender.objects.create(
                    invoice=invoice, **serializer.validated_data
                )
                created_tenders.append(tender_obj)
                total += tender_obj.amount

            invoice.apply_payment(total)

            return Response(
                {
                    "status": "success",
                    "message": f"Tender of {total} applied to invoice {invoice.invoice_number}",
                    "invoice": InvoiceDetailSerializer(invoice).data,
                }
            )
        except (
            ValueError,
            InvalidDocumentState,
            InsufficientStock,
            POSValidationException,
            POSStateException,
        ) as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
