from apps.debtors.models import Debtor
from apps.stock_control.models import StockItem
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .exceptions import RentalException
from .models import RentalTransaction
from .permissions import (
    ACCOUNTANT_GATED_STATES,
    GasFeatureEnabled,
    IsGasAccountant,
    IsGasCashier,
)
from .serializers import (
    RentalCheckoutSerializer,
    RentalReturnSerializer,
    RentalTransactionSerializer,
)
from .services import RentalService


class RentalTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only list/detail on RentalTransaction. Mutation happens only through
    the checkout/return actions below (never a raw PATCH/PUT) — the lifecycle
    is enforced entirely by RentalService, not by generic model field writes.
    """

    queryset = RentalTransaction.objects.select_related("debtor", "stock_item").all()
    serializer_class = RentalTransactionSerializer
    permission_classes = [IsAuthenticated, GasFeatureEnabled]

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, GasFeatureEnabled, IsGasCashier],
    )
    def checkout(self, request):
        serializer = RentalCheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            # 'debtor' is the account number (dno), not the internal pk — matches
            # DebtorViewSet.lookup_field='dno' and what DebtorPicker/search return.
            debtor = Debtor.objects.get(dno=data["debtor"])
        except Debtor.DoesNotExist:
            return Response(
                {"error": "Debtor not found"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            stock_item = StockItem.objects.get(pk=data["stock_item"])
        except StockItem.DoesNotExist:
            return Response(
                {"error": "Stock item not found"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rental = RentalService.checkout_cylinder(
                debtor=debtor,
                stock_item=stock_item,
                quantity=data["quantity"],
                deposit_amount=data["deposit_amount"],
                user=request.user,
                reference=data.get("reference", ""),
            )
        except RentalException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            RentalTransactionSerializer(rental).data, status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsAuthenticated, GasFeatureEnabled, IsGasCashier],
    )
    def returned(self, request, pk=None):
        serializer = RentalReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data["reconciliation_state"] in ACCOUNTANT_GATED_STATES:
            if not IsGasAccountant().has_permission(request, self):
                return Response(
                    {
                        "error": "You don't have permission to write off or dispute a deposit — "
                        "this requires an Accountant or Admin role."
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            rental = RentalService.return_cylinder(
                rental_id=pk,
                reconciliation_state=data["reconciliation_state"],
                user=request.user,
                replacement_unit_price=data.get("replacement_unit_price"),
                reference=data.get("reference", ""),
            )
        except RentalException as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(RentalTransactionSerializer(rental).data)
