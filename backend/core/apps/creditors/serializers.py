"""
Enterprise-grade serializers for Creditors module
Features: Comprehensive validation, nested serialization, error handling
"""

from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from datetime import datetime, timedelta

from .models import (
    Creditor, GoodsReceivedNote, GRNLineItem, CreditorInvoice, CreditorInvoiceLineItem,
    CreditorPayment, CreditorJournal, CreditorOpenItem, OpenItemAllocation, RFC, RFCLineItem
)


# ============================================================================
# UTILITY VALIDATION FUNCTIONS
# ============================================================================

def validate_transaction_date(date):
    """Validate that transaction date is not in future"""
    if date > datetime.now().date():
        raise serializers.ValidationError(
            f"Transaction date cannot be in the future. Provided: {date}"
        )
    return date


def validate_amount(amount):
    """Validate amount is positive"""
    if amount <= 0:
        raise serializers.ValidationError("Amount must be greater than zero.")
    return amount


def validate_due_date(due_date, transaction_date):
    """Validate due_date is on or after transaction_date"""
    if due_date < transaction_date:
        raise serializers.ValidationError(
            f"Due date ({due_date}) must be on or after transaction date ({transaction_date})"
        )
    return due_date


# ============================================================================
# CREDITOR SERIALIZERS
# ============================================================================

class CreditorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for supplier lists with balance info"""
    current_balance = serializers.DecimalField(
        source='get_current_balance', read_only=True, max_digits=12, decimal_places=2
    )
    total_overdue = serializers.SerializerMethodField()
    last_transaction_date = serializers.SerializerMethodField()

    class Meta:
        model = Creditor
        fields = [
            'id', 'supplier_number', 'name', 'email', 'telephone',
            'credit_terms', 'current_balance', 'total_overdue',
            'is_active', 'last_transaction_date'
        ]

    def get_total_overdue(self, obj):
        """Sum of 30+ days overdue"""
        return (obj.balance_30_days + obj.balance_60_days + 
                obj.balance_90_days + obj.balance_120_days + 
                obj.balance_150_days + obj.balance_180_days)

    def get_last_transaction_date(self, obj):
        """Get latest transaction date"""
        latest = CreditorInvoice.objects.filter(
            creditor=obj, is_posted=True
        ).latest('transaction_date', default=None)
        return latest.transaction_date if latest else None


class CreditorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with all supplier information and balance details"""
    current_balance = serializers.DecimalField(
        source='get_current_balance', read_only=True, max_digits=12, decimal_places=2
    )
    credit_terms_display = serializers.CharField(
        source='get_credit_terms_display', read_only=True
    )
    days_overdue = serializers.SerializerMethodField()
    aging_summary = serializers.SerializerMethodField()

    class Meta:
        model = Creditor
        fields = [
            'id', 'supplier_number', 'name', 'contact_person', 'email', 'telephone',
            'physical_address_line1', 'physical_address_line2', 'physical_city',
            'postal_address_line1', 'postal_city',
            'credit_terms', 'credit_terms_display', 'is_active',
            'balance_brought_forward', 'current_balance',
            'balance_current', 'balance_30_days', 'balance_60_days',
            'balance_90_days', 'balance_120_days', 'balance_150_days', 'balance_180_days',
            'last_paid_date', 'last_paid_amount',
            'purchases_mtd', 'purchases_ytd',
            'days_overdue', 'aging_summary',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'current_balance', 'balance_current', 'balance_30_days', 'balance_60_days',
            'balance_90_days', 'balance_120_days', 'balance_150_days', 'balance_180_days',
            'last_paid_date', 'last_paid_amount', 'purchases_mtd', 'purchases_ytd',
            'created_at', 'updated_at'
        ]

    def get_days_overdue(self, obj):
        """Calculate days overdue from last transaction"""
        if not obj.last_paid_date:
            return None
        due_date = obj.last_paid_date + timedelta(
            days=obj.credit_terms.credit_days if obj.credit_terms else 0
        )
        days = (datetime.now().date() - due_date).days
        return max(0, days)

    def get_aging_summary(self, obj):
        """Return aging analysis summary"""
        return {
            'current': float(obj.balance_current),
            '30_days': float(obj.balance_30_days),
            '60_days': float(obj.balance_60_days),
            '90_days': float(obj.balance_90_days),
            '120_days': float(obj.balance_120_days),
            '150_days': float(obj.balance_150_days),
            '180_days': float(obj.balance_180_days),
            'total': float(obj.get_current_balance())
        }


class CreditorCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating creditors with validation"""

    class Meta:
        model = Creditor
        fields = [
            'supplier_number', 'name', 'contact_person', 'email', 'telephone',
            'fax', 'physical_address_line1', 'physical_address_line2', 'physical_city',
            'physical_province', 'physical_code',
            'postal_address_line1', 'postal_address_line2', 'postal_city',
            'postal_province', 'postal_code',
            'our_account_number', 'credit_terms', 'account_category',
            'prompt_payment_discount_percent', 'bank_name', 'branch_code', 'account_number',
            'is_active'
        ]

    def validate_supplier_number(self, value):
        """Validate supplier number is unique"""
        instance = self.instance
        exists = Creditor.objects.filter(supplier_number=value)
        if instance:
            exists = exists.exclude(pk=instance.pk)
        if exists.exists():
            raise serializers.ValidationError(
                f"Supplier number '{value}' already exists."
            )
        return value

    def validate_email(self, value):
        """Validate email format"""
        if value and '@' not in value:
            raise serializers.ValidationError("Invalid email format.")
        return value

    def validate_prompt_payment_discount_percent(self, value):
        """Validate discount is between 0-100"""
        if value and (value < 0 or value > 100):
            raise serializers.ValidationError("Discount must be between 0 and 100.")
        return value


# ============================================================================
# GOODS RECEIVED NOTE SERIALIZERS
# ============================================================================

class GRNLineItemSerializer(serializers.ModelSerializer):
    """Serializer for GRN line items with validation"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    tax_rate = serializers.DecimalField(
        source='tax_code.tax_rate', read_only=True, max_digits=5, decimal_places=2
    )

    class Meta:
        model = GRNLineItem
        fields = [
            'id', 'line_number', 'stock_item', 'stock_code', 'stock_description',
            'quantity_received', 'unit_cost', 'tax_code', 'tax_rate',
            'line_subtotal', 'tax_amount', 'line_total'
        ]
        read_only_fields = ['line_subtotal', 'tax_amount', 'line_total']

    def validate_quantity_received(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_unit_cost(self, value):
        """Validate unit cost is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Unit cost cannot be negative.")
        return value


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    """Serializer for GRN with nested line items"""
    creditor_name = serializers.CharField(source='creditor.name', read_only=True)
    line_items = GRNLineItemSerializer(many=True, read_only=True)
    total_amount = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)

    class Meta:
        model = GoodsReceivedNote
        fields = [
            'id', 'transaction_number', 'creditor', 'creditor_name',
            'transaction_date', 'supplier_invoice_number', 'supplier_reference',
            'inclusive_exclusive', 'line_items',
            'subtotal', 'total_vat', 'total_amount',
            'is_posted', 'posted_date', 'posted_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'transaction_number', 'subtotal', 'total_vat', 'total_amount',
            'posted_date', 'posted_by', 'created_at', 'updated_at'
        ]

    def validate_transaction_date(self, value):
        """Validate transaction date"""
        return validate_transaction_date(value)

    def validate_supplier_invoice_number(self, value):
        """Validate supplier invoice number is unique per creditor"""
        instance = self.instance
        creditor = self.initial_data.get('creditor')
        
        exists = GoodsReceivedNote.objects.filter(
            creditor_id=creditor,
            supplier_invoice_number=value
        )
        if instance:
            exists = exists.exclude(pk=instance.pk)
        
        if exists.exists():
            raise serializers.ValidationError(
                f"Invoice number '{value}' already exists for this creditor."
            )
        return value


class GoodsReceivedNoteCreateSerializer(serializers.Serializer):
    """Serializer for creating GRN with line items"""
    creditor = serializers.IntegerField()
    transaction_date = serializers.DateField()
    supplier_invoice_number = serializers.CharField(max_length=50)
    supplier_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    inclusive_exclusive = serializers.ChoiceField(choices=['Inclusive', 'Exclusive'])
    line_items = serializers.ListField(child=GRNLineItemSerializer())

    @transaction.atomic
    def create(self, validated_data):
        """Create GRN with line items"""
        line_items_data = validated_data.pop('line_items')
        
        grn = GoodsReceivedNote.objects.create(**validated_data)
        
        for item_data in line_items_data:
            GRNLineItem.objects.create(grn=grn, **item_data)
        
        return grn


# ============================================================================
# CREDITOR INVOICE SERIALIZERS
# ============================================================================

class CreditorInvoiceLineItemSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items"""
    category_name = serializers.CharField(source='expense_category.category_name', read_only=True)
    tax_rate = serializers.DecimalField(
        source='tax_code.tax_rate', read_only=True, max_digits=5, decimal_places=2
    )

    class Meta:
        model = CreditorInvoiceLineItem
        fields = [
            'id', 'line_number', 'expense_category', 'category_name',
            'amount', 'tax_code', 'tax_rate', 'tax_amount', 'line_total'
        ]
        read_only_fields = ['tax_amount', 'line_total']

    def validate_amount(self, value):
        """Validate amount is positive"""
        return validate_amount(value)


class CreditorInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for creditor invoices"""
    creditor_name = serializers.CharField(source='creditor.name', read_only=True)
    line_items = CreditorInvoiceLineItemSerializer(many=True, read_only=True)
    due_date = serializers.DateField(read_only=True)

    class Meta:
        model = CreditorInvoice
        fields = [
            'id', 'transaction_number', 'creditor', 'creditor_name',
            'transaction_date', 'due_date', 'supplier_invoice_number', 'supplier_reference',
            'inclusive_exclusive', 'line_items',
            'subtotal', 'total_vat', 'total_amount',
            'is_posted', 'posted_date', 'posted_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'transaction_number', 'due_date', 'subtotal', 'total_vat', 'total_amount',
            'posted_date', 'posted_by', 'created_at', 'updated_at'
        ]

    def validate_transaction_date(self, value):
        return validate_transaction_date(value)


# ============================================================================
# CREDITOR PAYMENT SERIALIZERS
# ============================================================================

class CreditorPaymentSerializer(serializers.ModelSerializer):
    """Serializer for creditor payments"""
    creditor_name = serializers.CharField(source='creditor.name', read_only=True)
    payment_method_display = serializers.CharField(
        source='get_payment_method_display', read_only=True
    )

    class Meta:
        model = CreditorPayment
        fields = [
            'id', 'transaction_number', 'creditor', 'creditor_name',
            'transaction_date', 'amount_paid', 'payment_method', 'payment_method_display',
            'cheque_number', 'reference_number', 'remarks',
            'settlement_discount_percent', 'settlement_discount_amount',
            'is_posted', 'posted_date', 'posted_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'transaction_number', 'settlement_discount_amount',
            'posted_date', 'posted_by', 'created_at', 'updated_at'
        ]

    def validate_amount_paid(self, value):
        """Validate payment amount"""
        return validate_amount(value)

    def validate_settlement_discount_percent(self, value):
        """Validate settlement discount"""
        if value and (value < 0 or value > 100):
            raise serializers.ValidationError("Settlement discount must be between 0 and 100.")
        return value


class PaymentAllocationSerializer(serializers.Serializer):
    """Serializer for allocating payment to open items"""
    open_item_id = serializers.IntegerField()
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    settlement_discount = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=0, required=False
    )

    def validate(self, data):
        """Validate allocation amount"""
        open_item_id = data['open_item_id']
        amount_paid = data['amount_paid']
        
        try:
            open_item = CreditorOpenItem.objects.get(id=open_item_id)
        except CreditorOpenItem.DoesNotExist:
            raise serializers.ValidationError("Open item does not exist.")
        
        if amount_paid > open_item.balance_due:
            raise serializers.ValidationError(
                f"Allocation amount ({amount_paid}) exceeds balance due ({open_item.balance_due})"
            )
        
        return data


# ============================================================================
# CREDITOR JOURNAL SERIALIZERS
# ============================================================================

class CreditorJournalSerializer(serializers.ModelSerializer):
    """Serializer for creditor journals"""
    creditor_name = serializers.CharField(source='creditor.name', read_only=True)
    journal_type_display = serializers.CharField(
        source='get_journal_type_display', read_only=True
    )

    class Meta:
        model = CreditorJournal
        fields = [
            'id', 'transaction_number', 'creditor', 'creditor_name',
            'transaction_date', 'journal_type', 'journal_type_display',
            'journal_amount', 'narrative', 'remarks',
            'is_posted', 'posted_date', 'posted_by',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'transaction_number', 'posted_date', 'posted_by', 'created_at', 'updated_at'
        ]

    def validate_journal_amount(self, value):
        """Validate journal amount"""
        return validate_amount(value)


# ============================================================================
# OPEN ITEM SERIALIZERS
# ============================================================================

class OpenItemSerializer(serializers.ModelSerializer):
    """Serializer for open items"""
    creditor_name = serializers.CharField(source='creditor.name', read_only=True)
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', read_only=True
    )
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = CreditorOpenItem
        fields = [
            'id', 'transaction_number', 'creditor', 'creditor_name',
            'transaction_date', 'due_date', 'transaction_type', 'transaction_type_display',
            'original_amount', 'balance_due', 'is_fully_allocated', 'is_overdue',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'transaction_number', 'original_amount', 'balance_due',
            'created_at', 'updated_at'
        ]

    def get_is_overdue(self, obj):
        """Check if item is overdue"""
        if obj.due_date and obj.balance_due > 0:
            return obj.due_date < datetime.now().date()
        return False


class OpenItemAllocationSerializer(serializers.ModelSerializer):
    """Serializer for open item allocations"""
    payment_number = serializers.CharField(source='payment.transaction_number', read_only=True)
    open_item_number = serializers.CharField(source='open_item.transaction_number', read_only=True)

    class Meta:
        model = OpenItemAllocation
        fields = [
            'id', 'payment', 'payment_number', 'open_item', 'open_item_number',
            'amount_paid', 'settlement_discount', 'allocated_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['allocated_at', 'created_at', 'updated_at']


# ============================================================================
# RFC SERIALIZERS
# ============================================================================

class RFCLineItemSerializer(serializers.ModelSerializer):
    """Serializer for RFC line items"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    tax_rate = serializers.DecimalField(
        source='tax_code.tax_rate', read_only=True, max_digits=5, decimal_places=2
    )

    class Meta:
        model = RFCLineItem
        fields = [
            'id', 'line_number', 'stock_item', 'stock_code', 'stock_description',
            'quantity_returned', 'unit_cost', 'tax_code', 'tax_rate',
            'reason', 'line_value_exclusive', 'tax_amount', 'line_value_inclusive',
            'created_at'
        ]
        read_only_fields = [
            'unit_cost', 'tax_amount', 'line_value_exclusive', 'line_value_inclusive'
        ]

    def validate_quantity_returned(self, value):
        """Validate quantity"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value


class RFCSerializer(serializers.ModelSerializer):
    """Serializer for RFC"""
    creditor_name = serializers.CharField(source='creditor.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    line_items = RFCLineItemSerializer(many=True, read_only=True)
    lifecycle_status = serializers.SerializerMethodField()

    class Meta:
        model = RFC
        fields = [
            'id', 'rfc_number', 'creditor', 'creditor_name',
            'return_date', 'status', 'status_display',
            'date_sent', 'date_returned', 'credited_date', 'replaced_date',
            'purchase_order_number', 'purchase_order_line_number',
            'reason_for_return', 'remarks', 'line_items',
            'total_value_exclusive', 'total_vat', 'total_value_inclusive',
            'lifecycle_status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'rfc_number', 'total_value_exclusive', 'total_vat', 'total_value_inclusive',
            'created_at', 'updated_at'
        ]

    def get_lifecycle_status(self, obj):
        """Return lifecycle progress"""
        steps = []
        if obj.date_sent:
            steps.append({'step': 'sent', 'date': obj.date_sent})
        if obj.date_returned:
            steps.append({'step': 'returned', 'date': obj.date_returned})
        if obj.credited_date:
            steps.append({'step': 'credited', 'date': obj.credited_date})
        if obj.replaced_date:
            steps.append({'step': 'replaced', 'date': obj.replaced_date})
        return steps


# ============================================================================
# BULK AND REPORTING SERIALIZERS
# ============================================================================

class AgingAnalysisSerializer(serializers.Serializer):
    """Serializer for aging analysis report"""
    supplier_number = serializers.CharField()
    name = serializers.CharField()
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_30_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_60_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_90_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_120_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_150_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_180_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    last_paid_date = serializers.DateField(allow_null=True)
    credit_terms = serializers.CharField()


class BulkPaymentSerializer(serializers.Serializer):
    """Serializer for bulk payment processing"""
    creditor = serializers.IntegerField()
    transaction_date = serializers.DateField()
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    payment_method = serializers.IntegerField()
    allocations = serializers.ListField(
        child=PaymentAllocationSerializer(),
        required=False,
        allow_empty=True
    )

    def validate_transaction_date(self, value):
        return validate_transaction_date(value)

    def validate_amount_paid(self, value):
        return validate_amount(value)


class BalanceReconciliationSerializer(serializers.Serializer):
    """Serializer for balance reconciliation"""
    creditor = serializers.IntegerField()
    balance_current = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_30_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_60_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_90_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_120_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_150_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_180_days = serializers.DecimalField(max_digits=12, decimal_places=2)
