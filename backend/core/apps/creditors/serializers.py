# backend/core/apps/creditors/serializers.py
from rest_framework import serializers
from .models import (
    Creditor,
    GoodsReceivedNote, GRNLineItem,
    CreditorInvoice, CreditorInvoiceLineItem,
    CreditorCreditNote, CreditorCreditNoteLineItem,
    CreditorPayment,
    CreditorJournal,
    SupplierLedgerEntry,
    CreditorOpenItem, OpenItemAllocation,
    OpenItemAudit,
    RFC, RFCLineItem,
    ExpenseCategoryMonthlyBalance,
    ExpenseCategoryTransaction,
    SupplierPaymentOrder,
    CreditorTransactionLine,
)


# ============================================================================
# CREDITOR (SUPPLIER) MASTER
# ============================================================================

class CreditorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list/search views."""

    class Meta:
        model  = Creditor
        fields = [
            'id', 'supplier_number', 'name', 'telephone', 'email',
            'account_category', 'total_outstanding_balance', 'is_active',
        ]
        read_only_fields = ['id', 'total_outstanding_balance']


class CreditorSerializer(serializers.ModelSerializer):
    """
    Full creditor serializer.
    System-generated balance fields are read-only.
    """

    # Display-only nested label for FKs
    credit_terms_display  = serializers.StringRelatedField(source='credit_terms',  read_only=True)
    sales_area_display    = serializers.StringRelatedField(source='sales_area',    read_only=True)
    effective_terms_days  = serializers.SerializerMethodField()

    class Meta:
        model  = Creditor
        fields = [
            # --- Identification ---
            'id', 'supplier_number', 'name',
            # --- Contact ---
            'contact_person', 'telephone', 'fax', 'email',
            # --- Physical address ---
            'physical_address_line1', 'physical_address_line2', 'physical_address_line3',
            # --- Postal address ---
            'postal_address_line1', 'postal_address_line2', 'postal_address_line3',
            # --- Account settings ---
            'our_account_number', 'credit_terms', 'credit_terms_display',
            'payment_terms_days', 'effective_terms_days',
            'account_category', 'sales_area', 'sales_area_display',
            'update_selling_price_on_receipt', 'prompt_payment_discount_percent',
            # --- Banking ---
            'bank_name', 'branch_code', 'account_number',
            # --- System-generated balances (read-only) ---
            'balance_brought_forward', 'total_outstanding_balance',
            'balance_current', 'balance_30_days', 'balance_60_days',
            'balance_90_days', 'balance_120_days', 'balance_150_days', 'balance_180_days',
            'last_paid_amount', 'last_paid_date',
            'purchases_mtd', 'purchases_ytd',
            # --- Timestamps ---
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id',
            'balance_brought_forward', 'total_outstanding_balance',
            'balance_current', 'balance_30_days', 'balance_60_days',
            'balance_90_days', 'balance_120_days', 'balance_150_days', 'balance_180_days',
            'last_paid_amount', 'last_paid_date',
            'purchases_mtd', 'purchases_ytd',
            'created_at', 'updated_at',
        ]

    def get_effective_terms_days(self, obj):
        return obj.get_effective_terms_days()


# ============================================================================
# GOODS RECEIVED NOTE
# ============================================================================

class GRNLineItemSerializer(serializers.ModelSerializer):
    stock_code = serializers.StringRelatedField(source='stock_item', read_only=True)
    tax_code_display = serializers.StringRelatedField(source='tax_code', read_only=True)

    class Meta:
        model  = GRNLineItem
        fields = [
            'id', 'line_number', 'stock_item', 'stock_code',
            'quantity_received', 'unit_cost', 'tax_code', 'tax_code_display',
            # System-calculated
            'previous_cost', 'line_subtotal', 'tax_amount', 'line_total',
        ]
        read_only_fields = ['id', 'previous_cost', 'line_subtotal', 'tax_amount', 'line_total']


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    creditor_name     = serializers.StringRelatedField(source='creditor', read_only=True)
    line_items        = GRNLineItemSerializer(many=True, read_only=True)

    class Meta:
        model  = GoodsReceivedNote
        fields = [
            'id', 'creditor', 'creditor_name',
            # System-set
            'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'grn_number', 'station', 'created_by_user',
            # User-entered
            'transaction_date', 'transaction_reference', 'additional_reference',
            'supplier_invoice_number', 'inclusive_exclusive', 'surcharge_amount',
            # System-calculated totals
            'subtotal', 'total_vat', 'total_quantity',
            # Aged balances
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            # Posting status
            'is_posted', 'posted_at',
            # Lines
            'line_items',
        ]
        read_only_fields = [
            'id', 'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'grn_number', 'station', 'created_by_user',
            'subtotal', 'total_vat', 'total_quantity',
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
        ]


class GoodsReceivedNoteWriteSerializer(serializers.ModelSerializer):
    """Write serializer — accepts line_items nested for creation."""
    line_items = GRNLineItemSerializer(many=True)

    class Meta:
        model  = GoodsReceivedNote
        fields = [
            'creditor', 'transaction_date', 'transaction_reference', 'additional_reference',
            'supplier_invoice_number', 'inclusive_exclusive', 'surcharge_amount',
            'line_items',
        ]

    def create(self, validated_data):
        lines_data = validated_data.pop('line_items')
        grn = GoodsReceivedNote.objects.create(**validated_data)
        for i, line in enumerate(lines_data, start=1):
            GRNLineItem.objects.create(grn=grn, line_number=i, **line)
        return grn


# ============================================================================
# CREDITOR INVOICE (expense)
# ============================================================================

class CreditorInvoiceLineItemSerializer(serializers.ModelSerializer):
    expense_category_name = serializers.StringRelatedField(source='expense_category', read_only=True)
    tax_code_display      = serializers.StringRelatedField(source='tax_code',         read_only=True)

    class Meta:
        model  = CreditorInvoiceLineItem
        fields = [
            'id', 'line_number', 'expense_category', 'expense_category_name',
            'amount', 'tax_code', 'tax_code_display',
            # System-calculated
            'tax_amount', 'line_total',
        ]
        read_only_fields = ['id', 'tax_amount', 'line_total']


class CreditorInvoiceSerializer(serializers.ModelSerializer):
    creditor_name = serializers.StringRelatedField(source='creditor', read_only=True)
    line_items    = CreditorInvoiceLineItemSerializer(many=True, read_only=True)

    class Meta:
        model  = CreditorInvoice
        fields = [
            'id', 'creditor', 'creditor_name',
            # System-set
            'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'station', 'created_by_user',
            # User-entered
            'transaction_date', 'transaction_reference', 'additional_reference',
            'supplier_invoice_number', 'inclusive_exclusive', 'station_no_area',
            'tax_indicator', 'related_grn',
            # System-calculated
            'subtotal', 'total_vat',
            # Aged balances
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
            'line_items',
        ]
        read_only_fields = [
            'id', 'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'station', 'created_by_user',
            'subtotal', 'total_vat',
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
        ]


class CreditorInvoiceWriteSerializer(serializers.ModelSerializer):
    line_items = CreditorInvoiceLineItemSerializer(many=True)

    class Meta:
        model  = CreditorInvoice
        fields = [
            'creditor', 'transaction_date', 'transaction_reference', 'additional_reference',
            'supplier_invoice_number', 'inclusive_exclusive', 'station_no_area',
            'tax_indicator', 'related_grn',
            'line_items',
        ]

    def create(self, validated_data):
        lines_data = validated_data.pop('line_items')
        invoice = CreditorInvoice.objects.create(**validated_data)
        for i, line in enumerate(lines_data, start=1):
            CreditorInvoiceLineItem.objects.create(invoice=invoice, line_number=i, **line)
        return invoice


# ============================================================================
# CREDITOR CREDIT NOTE
# ============================================================================

class CreditorCreditNoteLineItemSerializer(serializers.ModelSerializer):
    stock_code       = serializers.StringRelatedField(source='stock_item', read_only=True)
    tax_code_display = serializers.StringRelatedField(source='tax_code',   read_only=True)

    class Meta:
        model  = CreditorCreditNoteLineItem
        fields = [
            'id', 'line_number', 'stock_item', 'stock_code',
            'quantity_returned', 'unit_cost', 'tax_code', 'tax_code_display',
            'line_subtotal', 'tax_amount', 'line_total',
        ]
        read_only_fields = ['id', 'line_subtotal', 'tax_amount', 'line_total']


class CreditorCreditNoteSerializer(serializers.ModelSerializer):
    creditor_name = serializers.StringRelatedField(source='creditor',     read_only=True)
    line_items    = CreditorCreditNoteLineItemSerializer(many=True, read_only=True)

    class Meta:
        model  = CreditorCreditNote
        fields = [
            'id', 'creditor', 'creditor_name',
            'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'station', 'created_by_user',
            'transaction_date', 'transaction_reference', 'additional_reference',
            'supplier_credit_note_number', 'inclusive_exclusive', 'original_grn',
            'subtotal', 'total_vat',
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
            'line_items',
        ]
        read_only_fields = [
            'id', 'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'station', 'created_by_user',
            'subtotal', 'total_vat',
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
        ]


class CreditorCreditNoteWriteSerializer(serializers.ModelSerializer):
    line_items = CreditorCreditNoteLineItemSerializer(many=True)

    class Meta:
        model  = CreditorCreditNote
        fields = [
            'creditor', 'transaction_date', 'transaction_reference', 'additional_reference',
            'supplier_credit_note_number', 'inclusive_exclusive', 'original_grn',
            'line_items',
        ]

    def create(self, validated_data):
        lines_data = validated_data.pop('line_items')
        cn = CreditorCreditNote.objects.create(**validated_data)
        for i, line in enumerate(lines_data, start=1):
            CreditorCreditNoteLineItem.objects.create(credit_note=cn, line_number=i, **line)
        return cn


# ============================================================================
# CREDITOR PAYMENT
# ============================================================================

class CreditorPaymentSerializer(serializers.ModelSerializer):
    creditor_name          = serializers.StringRelatedField(source='creditor',        read_only=True)
    payment_method_display = serializers.StringRelatedField(source='payment_method',  read_only=True)

    class Meta:
        model  = CreditorPayment
        fields = [
            'id', 'creditor', 'creditor_name',
            # System-set
            'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'station', 'created_by_user',
            # User-entered
            'transaction_date', 'transaction_reference', 'additional_reference',
            'amount_due', 'amount_paid', 'payment_method', 'payment_method_display',
            'is_unallocated',
            # System-calculated
            'settlement_discount_amount', 'settlement_discount_percent',
            # Aged balances
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
        ]
        read_only_fields = [
            'id', 'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'station', 'created_by_user',
            'settlement_discount_amount', 'settlement_discount_percent',
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
        ]

    def validate(self, data):
        if data.get('amount_paid', 0) > data.get('amount_due', 0):
            raise serializers.ValidationError(
                {'amount_paid': 'Amount paid cannot exceed amount due.'}
            )
        return data


# ============================================================================
# CREDITOR JOURNAL
# ============================================================================

class CreditorJournalSerializer(serializers.ModelSerializer):
    creditor_name = serializers.StringRelatedField(source='creditor', read_only=True)

    class Meta:
        model  = CreditorJournal
        fields = [
            'id', 'creditor', 'creditor_name',
            'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'station', 'created_by_user',
            'transaction_date', 'transaction_reference', 'additional_reference',
            'journal_type', 'journal_amount',
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
        ]
        read_only_fields = [
            'id', 'transaction_number', 'transaction_type', 'due_date',
            'total_amount', 'station', 'created_by_user',
            'age_current', 'age_30', 'age_60', 'age_90', 'age_120', 'age_150', 'age_180',
            'is_posted', 'posted_at',
        ]


# ============================================================================
# SUPPLIER LEDGER ENTRY (raw suptran import)
# ============================================================================

class SupplierLedgerEntrySerializer(serializers.ModelSerializer):
    creditor_name = serializers.StringRelatedField(source='creditor', read_only=True)

    class Meta:
        model  = SupplierLedgerEntry
        fields = [
            'id', 'creditor', 'creditor_name',
            'transaction_number', 'transaction_date', 'due_date',
            'transaction_type', 'subtotal', 'vat_amount', 'total_amount',
            'reference', 'grn_number', 'station', 'created_by_user',
        ]
        # Ledger entries are imported — nothing should be edited through the API
        read_only_fields = '__all__'


# ============================================================================
# OPEN ITEMS
# ============================================================================

class CreditorOpenItemSerializer(serializers.ModelSerializer):
    creditor_name = serializers.StringRelatedField(source='creditor', read_only=True)
    age_bucket    = serializers.SerializerMethodField()

    class Meta:
        model  = CreditorOpenItem
        fields = [
            'id', 'creditor', 'creditor_name',
            'transaction_date', 'due_date', 'transaction_type', 'transaction_number',
            # System-maintained
            'original_amount', 'balance_due', 'age_period', 'ageing_flag',
            'is_fully_allocated', 'is_legacy',
            # FK links to typed transactions
            'grn', 'invoice', 'credit_note', 'journal', 'ledger_entry',
            # Computed
            'age_bucket',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'original_amount', 'balance_due', 'age_period', 'ageing_flag',
            'is_fully_allocated', 'created_at', 'updated_at',
        ]

    def get_age_bucket(self, obj):
        return obj.get_age_bucket()


class OpenItemAllocationSerializer(serializers.ModelSerializer):
    payment_number      = serializers.CharField(source='payment.transaction_number', read_only=True)
    open_item_number    = serializers.CharField(source='open_item.transaction_number', read_only=True)

    class Meta:
        model  = OpenItemAllocation
        fields = [
            'id', 'payment', 'payment_number', 'open_item', 'open_item_number',
            'amount_paid', 'settlement_discount', 'allocated_at',
        ]
        read_only_fields = ['id', 'allocated_at']

    def validate(self, data):
        open_item = data['open_item']
        amount    = data['amount_paid'] + data.get('settlement_discount', 0)
        if amount > open_item.balance_due:
            raise serializers.ValidationError(
                f"Allocation of {amount} exceeds open item balance of {open_item.balance_due}."
            )
        return data


# ============================================================================
# OPEN ITEM AUDIT (read-only)
# ============================================================================

class OpenItemAuditSerializer(serializers.ModelSerializer):
    creditor_number = serializers.CharField(source='creditor.supplier_number', read_only=True)

    class Meta:
        model  = OpenItemAudit
        fields = [
            'id', 'creditor', 'creditor_number',
            'transaction_number', 'transaction_type',
            'this_transaction_type', 'this_transaction_number',
            'transaction_date', 'amount',
            'audit_timestamp', 'audit_notes',
        ]
        read_only_fields = '__all__'


# ============================================================================
# RFC (RETURN FOR CREDIT)
# ============================================================================

class RFCLineItemSerializer(serializers.ModelSerializer):
    stock_code       = serializers.StringRelatedField(source='stock_item', read_only=True)
    tax_code_display = serializers.StringRelatedField(source='tax_code',   read_only=True)

    class Meta:
        model  = RFCLineItem
        fields = [
            'id', 'line_number',
            'stock_item', 'stock_code',
            'quantity_returned', 'quantity_credited', 'quantity_stock',
            'line_value', 'tax_code', 'tax_code_display',
            'rfc_line_date', 'rfc_line_time',
            'original_transaction_type', 'original_transaction_date',
            'supplier_reference_number', 'reason',
            # System-calculated
            'unit_cost', 'line_value_exclusive', 'tax_amount', 'line_value_inclusive',
        ]
        read_only_fields = ['id', 'unit_cost', 'line_value_exclusive', 'tax_amount', 'line_value_inclusive']


class RFCSerializer(serializers.ModelSerializer):
    creditor_name = serializers.StringRelatedField(source='creditor', read_only=True)
    line_items    = RFCLineItemSerializer(many=True, read_only=True)

    class Meta:
        model  = RFC
        fields = [
            'id', 'creditor', 'creditor_name',
            'rfc_number', 'return_date', 'date_sent', 'date_returned', 'status',
            # System-calculated
            'total_value_exclusive', 'total_value_inclusive',
            'created_at', 'updated_at',
            'line_items',
        ]
        read_only_fields = [
            'id', 'total_value_exclusive', 'total_value_inclusive',
            'created_at', 'updated_at',
        ]


class RFCWriteSerializer(serializers.ModelSerializer):
    line_items = RFCLineItemSerializer(many=True)

    class Meta:
        model  = RFC
        fields = [
            'creditor', 'rfc_number', 'return_date', 'date_sent', 'date_returned',
            'status', 'line_items',
        ]

    def create(self, validated_data):
        lines_data = validated_data.pop('line_items')
        rfc = RFC.objects.create(**validated_data)
        for i, line in enumerate(lines_data, start=1):
            RFCLineItem.objects.create(rfc=rfc, line_number=i, **line)
        return rfc

    def update(self, instance, validated_data):
        lines_data = validated_data.pop('line_items', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            instance.line_items.all().delete()
            for i, line in enumerate(lines_data, start=1):
                RFCLineItem.objects.create(rfc=instance, line_number=i, **line)
        return instance


# ============================================================================
# EXPENSE CATEGORY MONTHLY BALANCE
# ============================================================================

class ExpenseCategoryMonthlyBalanceSerializer(serializers.ModelSerializer):
    expense_category_display = serializers.StringRelatedField(source='expense_category', read_only=True)
    annual_total             = serializers.SerializerMethodField()

    class Meta:
        model  = ExpenseCategoryMonthlyBalance
        fields = [
            'id', 'expense_category', 'expense_category_display',
            'expense_category_name', 'year',
            # System-accumulated (read-only)
            'expense_mtd', 'input_vat_mtd',
            'exp_month_1', 'exp_month_2', 'exp_month_3', 'exp_month_4',
            'exp_month_5', 'exp_month_6', 'exp_month_7', 'exp_month_8',
            'exp_month_9', 'exp_month_10', 'exp_month_11', 'exp_month_12',
            'annual_total',
        ]
        read_only_fields = [
            'id',
            'expense_mtd', 'input_vat_mtd',
            'exp_month_1', 'exp_month_2', 'exp_month_3', 'exp_month_4',
            'exp_month_5', 'exp_month_6', 'exp_month_7', 'exp_month_8',
            'exp_month_9', 'exp_month_10', 'exp_month_11', 'exp_month_12',
        ]

    def get_annual_total(self, obj):
        return obj.get_annual_total()


# ============================================================================
# EXPENSE CATEGORY TRANSACTION
# ============================================================================

class ExpenseCategoryTransactionSerializer(serializers.ModelSerializer):
    expense_category_display = serializers.StringRelatedField(source='expense_category', read_only=True)
    creditor_name            = serializers.StringRelatedField(source='creditor',          read_only=True)

    class Meta:
        model  = ExpenseCategoryTransaction
        fields = [
            'id', 'expense_category', 'expense_category_display',
            'creditor', 'creditor_name',
            'transaction_date', 'transaction_number',
            # User/source
            'amount_exclusive', 'tax_indicator', 'source_type', 'grn_number',
            # System-calculated
            'input_vat_amount', 'amount_inclusive',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'input_vat_amount', 'amount_inclusive', 'created_at', 'updated_at']


# ============================================================================
# SUPPLIER PAYMENT ORDER
# ============================================================================

class SupplierPaymentOrderSerializer(serializers.ModelSerializer):
    creditor_name = serializers.StringRelatedField(source='creditor', read_only=True)

    class Meta:
        model  = SupplierPaymentOrder
        fields = [
            'id', 'creditor', 'creditor_name',
            'payment_date', 'amount',
            'detail_line1', 'detail_line2', 'detail_line3',
            # System-set by payment run
            'is_processed', 'processed_date',
        ]
        read_only_fields = ['id', 'is_processed', 'processed_date']

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value


# ============================================================================
# CREDITOR TRANSACTION LINE (generic polymorphic)
# ============================================================================

class CreditorTransactionLineSerializer(serializers.ModelSerializer):
    class Meta:
        model  = CreditorTransactionLine
        fields = [
            'id', 'content_type', 'object_id',
            'line_number', 'stock_item', 'expense_category',
            'quantity', 'unit_cost', 'tax_code',
            'amount_exclusive',
            # System-calculated
            'tax_amount', 'amount_inclusive',
        ]
        read_only_fields = ['id', 'tax_amount', 'amount_inclusive']


# ============================================================================
# AGED BALANCE SUMMARY (read-only, used in dashboard/reporting views)
# ============================================================================

class CreditorAgedBalanceSummarySerializer(serializers.ModelSerializer):
    """Compact aging snapshot for a single creditor — used on statement and age analysis."""

    class Meta:
        model  = Creditor
        fields = [
            'id', 'supplier_number', 'name',
            'balance_current', 'balance_30_days', 'balance_60_days',
            'balance_90_days', 'balance_120_days', 'balance_150_days', 'balance_180_days',
            'total_outstanding_balance',
        ]
        read_only_fields = '__all__'