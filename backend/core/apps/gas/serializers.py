from decimal import Decimal

from rest_framework import serializers

from .models import RentalTransaction


class RentalTransactionSerializer(serializers.ModelSerializer):
    debtor_name = serializers.CharField(source='debtor.dname', read_only=True)
    stock_item_description = serializers.CharField(source='stock_item.description', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = RentalTransaction
        fields = [
            'id', 'debtor', 'debtor_name', 'stock_item', 'stock_item_description',
            'quantity', 'deposit_amount', 'status', 'checkout_date', 'due_date',
            'returned_date', 'reconciliation_state', 'is_overdue',
            'is_reconciled', 'reconciled_at', 'gl_batchno_checkout', 'gl_batchno_return',
            'notes', 'created_at',
        ]
        read_only_fields = [
            'id', 'status', 'returned_date', 'reconciliation_state', 'is_overdue',
            'is_reconciled', 'reconciled_at', 'gl_batchno_checkout', 'gl_batchno_return',
            'created_at',
        ]


class RentalCheckoutSerializer(serializers.Serializer):
    debtor = serializers.IntegerField(help_text="Debtor account number (dno) — matches DebtorViewSet's lookup field")
    stock_item = serializers.CharField(help_text="StockItem stock_code")
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=Decimal('0.01'))
    deposit_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'))
    reference = serializers.CharField(required=False, allow_blank=True, default='')


class RentalReturnSerializer(serializers.Serializer):
    reconciliation_state = serializers.ChoiceField(
        choices=RentalTransaction.RECONCILIATION_STATE_CHOICES,
    )
    replacement_unit_price = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False, allow_null=True, default=None,
    )
    reference = serializers.CharField(required=False, allow_blank=True, default='')
