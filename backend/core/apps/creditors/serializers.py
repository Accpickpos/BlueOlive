from rest_framework import serializers
from decimal import Decimal
from .models import (
    Creditor, GoodsReceivedNote, GRNLineItem, CreditorInvoice, CreditorInvoiceLineItem,
    CreditorCreditNote, CreditorCreditNoteLineItem, CreditorPayment,
    CreditorJournal, CreditorOpenItem, OpenItemAllocation, RFC, RFCLineItem,
    CreditorTransactionLine, SupplierMonthlyPurchase, ExpenseMonthlyTotal
)
from apps.settings.models import ExpenseCategory, TaxCode


class SupplierListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for supplier lists"""
    total_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = Creditor
        fields = [
            'account_number', 'name', 'short_name', 'telephone1',
            'email', 'credit_terms', 'total_balance', 'is_active'
        ]
    
    def get_total_balance(self, obj):
        return obj.get_total_balance()


class SupplierDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for supplier details"""
    total_balance = serializers.SerializerMethodField()
    total_balance_with_rfc = serializers.SerializerMethodField()
    account_type_display = serializers.CharField(source='get_account_type_display', read_only=True)
    credit_terms_display = serializers.CharField(source='get_credit_terms_display', read_only=True)
    
    class Meta:
        model = Creditor
        fields = '__all__'
        read_only_fields = [
            'balance_current', 'balance_30_days', 'balance_60_days', 'balance_90_days',
            'balance_120_days', 'balance_150_days', 'balance_180_days',
            'amount_last_paid', 'date_last_paid', 'purchases_mtd', 'purchases_ytd',
            'rfc_outstanding_amount', 'created_at', 'updated_at'
        ]
    
    def get_total_balance(self, obj):
        return obj.get_total_balance()
    
    def get_total_balance_with_rfc(self, obj):
        return obj.get_total_balance_with_rfc()


class SupplierCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating suppliers"""
    
    class Meta:
        model = Creditor
        fields = [
            'supplier_number', 'account_number', 'name', 'short_name',
            'physical_address_line1', 'physical_address_line2', 'physical_address_line3',
            'physical_city', 'physical_postal_code',
            'postal_address_line1', 'postal_address_line2', 'postal_address_line3',
            'postal_city', 'postal_postal_code',
            'telephone1', 'telephone2', 'fax', 'email', 'contact_person',
            'account_type', 'our_account_number', 'update_selling_price_on_receipt',
            'credit_terms', 'prompt_payment_discount_percent',
            'bank_name', 'bank_branch_code', 'bank_account_number',
            'vat_number', 'is_active'
        ]


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for expense categories"""
    
    class Meta:
        model = ExpenseCategory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    """Serializer for Goods Received Notes"""
    supplier_name = serializers.CharField(source='creditor.name', read_only=True)
    line_items = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = GoodsReceivedNote
        fields = '__all__'
        read_only_fields = ['transaction_type', 'transaction_number', 'subtotal', 'total_vat',
                           'posted_at', 'posted_by', 'created_at', 'updated_at']
    
    def get_line_items(self, obj):
        from .models import GRNLineItem
        items = GRNLineItem.objects.filter(grn=obj)
        return GRNLineItemSerializer(items, many=True).data


class CreditorInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for Creditor Invoices"""
    supplier_name = serializers.CharField(source='creditor.name', read_only=True)
    line_items = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CreditorInvoice
        fields = '__all__'
        read_only_fields = ['transaction_type', 'transaction_number', 'subtotal', 'total_vat',
                           'posted_at', 'posted_by', 'created_at', 'updated_at']
    
    def get_line_items(self, obj):
        items = CreditorInvoiceLineItem.objects.filter(invoice=obj)
        return CreditorInvoiceLineItemSerializer(items, many=True).data


class CreditorCreditNoteSerializer(serializers.ModelSerializer):
    """Serializer for Creditor Credit Notes"""
    supplier_name = serializers.CharField(source='creditor.name', read_only=True)
    line_items = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = CreditorCreditNote
        fields = '__all__'
        read_only_fields = ['transaction_type', 'transaction_number', 'subtotal', 'total_vat',
                           'posted_at', 'posted_by', 'created_at', 'updated_at']
    
    def get_line_items(self, obj):
        items = CreditorCreditNoteLineItem.objects.filter(credit_note=obj)
        return CreditorCreditNoteLineItemSerializer(items, many=True).data


class CreditorPaymentSerializer(serializers.ModelSerializer):
    """Serializer for Creditor Payments"""
    supplier_name = serializers.CharField(source='creditor.name', read_only=True)
    
    class Meta:
        model = CreditorPayment
        fields = '__all__'
        read_only_fields = ['transaction_type', 'transaction_number', 'settlement_discount_amount',
                           'settlement_discount_percent', 'posted_at', 'posted_by', 'created_at', 'updated_at']


class CreditorJournalSerializer(serializers.ModelSerializer):
    """Serializer for Creditor Journals"""
    supplier_name = serializers.CharField(source='creditor.name', read_only=True)
    journal_type_display = serializers.CharField(source='get_journal_type_display', read_only=True)
    
    class Meta:
        model = CreditorJournal
        fields = '__all__'
        read_only_fields = ['transaction_type', 'transaction_number', 'total_amount',
                           'posted_at', 'posted_by', 'created_at', 'updated_at']


class GRNLineItemSerializer(serializers.ModelSerializer):
    """Serializer for GRN line items"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    
    class Meta:
        model = GRNLineItem
        fields = '__all__'
        read_only_fields = ['created_at', 'previous_cost', 'line_subtotal', 'tax_amount', 'line_total']


class CreditorInvoiceLineItemSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items"""
    category_name = serializers.CharField(source='expense_category.category_name', read_only=True)
    
    class Meta:
        model = CreditorInvoiceLineItem
        fields = '__all__'
        read_only_fields = ['created_at', 'tax_amount', 'line_total']


class CreditorCreditNoteLineItemSerializer(serializers.ModelSerializer):
    """Serializer for credit note line items"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    
    class Meta:
        model = CreditorCreditNoteLineItem
        fields = '__all__'
        read_only_fields = ['created_at', 'line_subtotal', 'tax_amount', 'line_total']


class CreditorTransactionLineSerializer(serializers.ModelSerializer):
    """Serializer for transaction line items"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True, allow_null=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True, allow_null=True)
    category_name = serializers.CharField(source='expense_category.category_name', read_only=True, allow_null=True)
    
    class Meta:
        model = CreditorTransactionLine
        fields = '__all__'
        read_only_fields = ['created_at']


class StockReceivingLineSerializer(serializers.Serializer):
    """Serializer for stock receiving line items"""
    stock_item = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    tax_code = serializers.IntegerField(default=1)


class StockReceivingSerializer(serializers.Serializer):
    """Serializer for receiving stock from supplier"""
    supplier = serializers.IntegerField()
    invoice_date = serializers.DateField()
    invoice_number = serializers.CharField(max_length=50)
    additional_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    inclusive_of_vat = serializers.BooleanField(default=False)
    surcharge = serializers.DecimalField(max_digits=10, decimal_places=2, default=0, required=False)
    line_items = serializers.ListField(child=StockReceivingLineSerializer())
    
    pay_and_update = serializers.BooleanField(default=False, required=False)
    payment_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    payment_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)


class StockReturnLineSerializer(serializers.Serializer):
    """Serializer for stock return line items"""
    stock_item = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    unit_cost = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    tax_code = serializers.IntegerField(default=1)


class StockReturnSerializer(serializers.Serializer):
    """Serializer for returning stock to supplier"""
    supplier = serializers.IntegerField()
    document_date = serializers.DateField()
    document_number = serializers.CharField(max_length=50)
    additional_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    inclusive_of_vat = serializers.BooleanField(default=False)
    line_items = serializers.ListField(child=StockReturnLineSerializer())
    age_to_period = serializers.IntegerField(
        required=False,
        help_text="Period to age credit: 0=Current, 1=30, 2=60, 3=90, 4=120, 5=150, 6=180"
    )


class ExpenseInvoiceLineSerializer(serializers.Serializer):
    """Serializer for expense invoice line items"""
    expense_category = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    tax_code = serializers.IntegerField(default=1)


class ExpenseInvoiceSerializer(serializers.Serializer):
    """Serializer for expense invoice capture"""
    supplier = serializers.IntegerField()
    invoice_date = serializers.DateField()
    invoice_number = serializers.CharField(max_length=50)
    additional_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    inclusive_of_vat = serializers.BooleanField(default=True)
    line_items = serializers.ListField(child=ExpenseInvoiceLineSerializer())
    
    pay_and_update = serializers.BooleanField(default=False, required=False)
    payment_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    payment_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)


class ExpenseCreditNoteSerializer(serializers.Serializer):
    """Serializer for expense credit note"""
    supplier = serializers.IntegerField()
    document_date = serializers.DateField()
    document_number = serializers.CharField(max_length=50)
    additional_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    inclusive_of_vat = serializers.BooleanField(default=True)
    line_items = serializers.ListField(child=ExpenseInvoiceLineSerializer())
    age_to_period = serializers.IntegerField(
        required=False,
        help_text="Period to age credit: 0=Current, 1=30, 2=60, 3=90, 4=120, 5=150, 6=180"
    )


class PaymentSerializer(serializers.Serializer):
    """Serializer for supplier payment"""
    supplier = serializers.IntegerField()
    payment_date = serializers.DateField()
    payment_reference = serializers.CharField(max_length=50)
    additional_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    amount_due = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    
    # For Balance Brought Forward
    age_current = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_30 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_60 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_90 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_120 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_150 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_180 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)


class OpenItemPaymentAllocationSerializer(serializers.Serializer):
    """Serializer for allocating payment to specific invoices"""
    invoice_transaction_id = serializers.IntegerField()
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    settlement_discount = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)


class OpenItemPaymentSerializer(serializers.Serializer):
    """Serializer for Open Item payment"""
    supplier = serializers.IntegerField()
    payment_date = serializers.DateField()
    payment_reference = serializers.CharField(max_length=50)
    additional_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    amount_paid = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    allocations = serializers.ListField(
        child=OpenItemPaymentAllocationSerializer(),
        required=False,
        allow_empty=True
    )
    post_as_unallocated = serializers.BooleanField(default=False)


class JournalSerializer(serializers.Serializer):
    """Serializer for debit/credit journals"""
    
    JOURNAL_TYPE_CHOICES = [
        ('DEBIT', 'Debit Journal'),
        ('CREDIT', 'Credit Journal'),
    ]
    
    journal_type = serializers.ChoiceField(choices=JOURNAL_TYPE_CHOICES)
    supplier = serializers.IntegerField()
    journal_date = serializers.DateField()
    journal_number = serializers.CharField(max_length=50, required=False, allow_blank=True)
    additional_reference = serializers.CharField(max_length=255)
    journal_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    
    # For Balance Brought Forward
    age_current = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_30 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_60 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_90 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_120 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_150 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    age_180 = serializers.DecimalField(max_digits=12, decimal_places=2, default=0, required=False)
    
    # For Open Item (single period allocation)
    age_to_period = serializers.IntegerField(required=False)


class CreditorOpenItemSerializer(serializers.ModelSerializer):
    """Serializer for creditor open items"""
    creditor_name = serializers.CharField(source='creditor.name', read_only=True)
    creditor_account_number = serializers.CharField(source='creditor.account_number', read_only=True)
    
    class Meta:
        model = CreditorOpenItem
        fields = [
            'id', 'creditor', 'creditor_name', 'creditor_account_number',
            'transaction_date', 'transaction_type', 'transaction_number',
            'original_amount', 'balance_due', 'age_period', 'is_fully_allocated'
        ]
        read_only_fields = ['id', 'creditor_name', 'creditor_account_number']


class OpenItemAllocationSerializer(serializers.ModelSerializer):
    """Serializer for open item allocations"""
    transaction_number = serializers.CharField(source='open_item.transaction_number', read_only=True)
    payment_number = serializers.CharField(source='payment.transaction_number', read_only=True)
    
    class Meta:
        model = OpenItemAllocation
        fields = '__all__'
        read_only_fields = ['allocated_at']


class RFCLineItemSerializer(serializers.ModelSerializer):
    """Serializer for RFC line items"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    
    class Meta:
        model = RFCLineItem
        fields = '__all__'
        read_only_fields = ['created_at']


class RFCSerializer(serializers.ModelSerializer):
    """Serializer for RFC"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    line_items = RFCLineItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = RFC
        fields = '__all__'
        read_only_fields = ['rfc_number', 'total_exclusive', 'total_vat', 'total_inclusive', 'created_at', 'updated_at']


class RFCCreateLineSerializer(serializers.Serializer):
    """Serializer for creating RFC line items"""
    stock_item = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    tax_code = serializers.IntegerField(default=1)
    comments = serializers.CharField(required=False, allow_blank=True)
    purchase_date = serializers.DateField(required=False, allow_null=True)
    purchase_reference = serializers.CharField(max_length=50, required=False, allow_blank=True)


class RFCCreateSerializer(serializers.Serializer):
    """Serializer for creating RFC"""
    supplier = serializers.IntegerField()
    return_date = serializers.DateField()
    line_items = serializers.ListField(child=RFCCreateLineSerializer())


class RFCCreditGrantedSerializer(serializers.Serializer):
    """Serializer for processing RFC credit granted"""
    rfc_number = serializers.IntegerField()
    credit_date = serializers.DateField()
    credit_document_number = serializers.CharField(max_length=50)
    additional_reference = serializers.CharField(max_length=255, required=False, allow_blank=True)
    inclusive_of_vat = serializers.BooleanField(default=False)
    age_to_period = serializers.IntegerField(
        required=False,
        help_text="Period to age credit: 0=Current, 1=30, 2=60, 3=90, 4=120, 5=150, 6=180"
    )
    line_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of line items with adjusted quantities/costs"
    )


class RFCStockReplacedSerializer(serializers.Serializer):
    """Serializer for processing RFC stock replacement"""
    rfc_number = serializers.IntegerField()
    replacement_date = serializers.DateField()
    replacement_document_number = serializers.CharField(max_length=50)
    line_items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of line items with quantities replaced"
    )


class SupplierMonthlyPurchaseSerializer(serializers.ModelSerializer):
    """Serializer for monthly purchase statistics"""
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    
    class Meta:
        model = SupplierMonthlyPurchase
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class ExpenseMonthlyTotalSerializer(serializers.ModelSerializer):
    """Serializer for monthly expense totals"""
    category_name = serializers.CharField(source='expense_category.category_name', read_only=True)
    
    class Meta:
        model = ExpenseMonthlyTotal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class BalanceTakeOnSerializer(serializers.Serializer):
    """Serializer for balance take-on"""
    supplier = serializers.IntegerField()
    
    # For Balance Brought Forward
    balance_current = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_30_days = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_60_days = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_90_days = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_120_days = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_150_days = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_180_days = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # For Open Item (list of transactions)
    open_items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )


class AgeAnalysisSerializer(serializers.Serializer):
    """Serializer for age analysis report"""
    account_number = serializers.IntegerField()
    name = serializers.CharField()
    balance_current = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_30_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_60_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_90_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_120_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_150_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_180_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    amount_last_paid = serializers.DecimalField(max_digits=12, decimal_places=2)
    date_last_paid = serializers.DateField(allow_null=True)
    credit_terms = serializers.IntegerField()
    our_account_number = serializers.CharField()
    bank_name = serializers.CharField()
    bank_branch_code = serializers.CharField()
    bank_account_number = serializers.CharField()