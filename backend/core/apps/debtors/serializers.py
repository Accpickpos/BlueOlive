"""
Debtors serializers.
Comprehensive serializers for all debtor-related models.
"""
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import (
    Debtor, DebtorTransaction, Invoice, InvoiceLine,
    PostDatedCheque
)
from apps.settings.models import SalesArea


class SalesAreaNestedSerializer(serializers.ModelSerializer):
    """Nested serializer for sales area."""
    class Meta:
        model = SalesArea
        fields = ['id', 'number', 'name']


class DebtorListSerializer(serializers.ModelSerializer):
    """Serializer for debtor list view."""
    total_balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    sales_area_name = serializers.CharField(
        source='sales_area.name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = Debtor
        fields = [
            'id',
            'account_number',
            'name',
            'search_name',
            'contact_person',
            'telephone1',
            'email',
            'sales_area',
            'sales_area_name',
            'account_category',
            'credit_limit',
            'current_balance',
            'total_balance',
            'is_active',
            'is_blocked',
            'created_at',
        ]


class DebtorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for debtor."""
    total_balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    sales_area_detail = SalesAreaNestedSerializer(
        source='sales_area',
        read_only=True
    )
    
    class Meta:
        model = Debtor
        fields = '__all__'
        read_only_fields = [
            'current_balance',
            'balance_30_days',
            'balance_60_days',
            'balance_90_days',
            'balance_120_days',
            'balance_150_days',
            'balance_180_days',
            'last_payment_date',
            'last_payment_amount',
            'sales_mtd',
            'sales_ytd',
        ]


class DebtorCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating debtors."""
    
    class Meta:
        model = Debtor
        fields = '__all__'
        read_only_fields = [
            'current_balance',
            'balance_30_days',
            'balance_60_days',
            'balance_90_days',
            'balance_120_days',
            'balance_150_days',
            'balance_180_days',
            'last_payment_date',
            'last_payment_amount',
            'sales_mtd',
            'sales_ytd',
        ]
    
    def validate_account_number(self, value):
        """Ensure account number is unique."""
        instance = self.instance
        if instance and instance.account_number == value:
            return value
        
        if Debtor.objects.filter(account_number=value).exists():
            raise serializers.ValidationError(
                "Account number already exists."
            )
        return value
    
    def validate(self, data):
        """Validate debtor data."""
        # Ensure search name is populated
        if 'name' in data and 'search_name' not in data:
            data['search_name'] = data['name'][:50].upper()
        
        # Validate credit limit
        if data.get('credit_limit', 0) < 0:
            raise serializers.ValidationError({
                'credit_limit': 'Credit limit cannot be negative.'
            })
        
        # Validate discount
        if data.get('trade_discount', 0) > 100:
            raise serializers.ValidationError({
                'trade_discount': 'Trade discount cannot exceed 100%.'
            })
        
        return data


class DebtorTransactionSerializer(serializers.ModelSerializer):
    """Serializer for debtor transactions."""
    debtor_name = serializers.CharField(
        source='debtor.name',
        read_only=True
    )
    debtor_account = serializers.CharField(
        source='debtor.account_number',
        read_only=True
    )
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display',
        read_only=True
    )
    
    class Meta:
        model = DebtorTransaction
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class InvoiceLineSerializer(serializers.ModelSerializer):
    """Serializer for invoice line items."""
    
    class Meta:
        model = InvoiceLine
        fields = [
            'id',
            'line_number',
            'stock_code',
            'description',
            'quantity',
            'unit_price',
            'discount_percentage',
            'tax_code',
            'line_total',
            'vat_amount',
            'cost_price',
            'line_profit',
        ]
        read_only_fields = ['id']
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value
    
    def validate_unit_price(self, value):
        """Validate unit price is not negative."""
        if value < 0:
            raise serializers.ValidationError("Unit price cannot be negative.")
        return value


class InvoiceListSerializer(serializers.ModelSerializer):
    """Serializer for invoice list view."""
    debtor_name = serializers.CharField(
        source='debtor.name',
        read_only=True
    )
    debtor_account = serializers.CharField(
        source='debtor.account_number',
        read_only=True
    )
    line_count = serializers.IntegerField(
        source='lines.count',
        read_only=True
    )
    
    class Meta:
        model = Invoice
        fields = [
            'id',
            'invoice_number',
            'invoice_date',
            'debtor',
            'debtor_name',
            'debtor_account',
            'order_number',
            'customer_reference',
            'subtotal',
            'vat_amount',
            'total_amount',
            'gross_profit',
            'line_count',
            'is_posted',
            'is_cancelled',
            'created_at',
        ]


class InvoiceDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for invoice."""
    debtor_detail = DebtorListSerializer(
        source='debtor',
        read_only=True
    )
    lines = InvoiceLineSerializer(many=True, read_only=True)
    gross_profit_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = [
            'subtotal',
            'discount_amount',
            'vat_amount',
            'total_amount',
            'total_cost',
            'gross_profit',
            'created_at',
            'updated_at',
        ]
    
    def get_gross_profit_percentage(self, obj):
        """Calculate gross profit percentage."""
        if obj.total_amount > 0:
            return round((obj.gross_profit / obj.total_amount) * 100, 2)
        return 0


class InvoiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating invoices."""
    lines = InvoiceLineSerializer(many=True)
    
    class Meta:
        model = Invoice
        fields = [
            'debtor',
            'invoice_number',
            'invoice_date',
            'delivery_name',
            'delivery_address_line1',
            'delivery_address_line2',
            'delivery_telephone',
            'order_number',
            'customer_reference',
            'job_card_number',
            'sales_area',
            'lines',
        ]
    
    def validate_invoice_number(self, value):
        """Ensure invoice number is unique."""
        if Invoice.objects.filter(invoice_number=value).exists():
            raise serializers.ValidationError(
                "Invoice number already exists."
            )
        return value
    
    def validate_lines(self, value):
        """Validate invoice has at least one line."""
        if not value:
            raise serializers.ValidationError(
                "Invoice must have at least one line item."
            )
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        """Create invoice with lines."""
        lines_data = validated_data.pop('lines')
        
        # Create invoice
        invoice = Invoice.objects.create(**validated_data)
        
        # Calculate totals
        subtotal = Decimal('0.00')
        total_vat = Decimal('0.00')
        total_cost = Decimal('0.00')
        
        # Create lines
        for idx, line_data in enumerate(lines_data, start=1):
            line_data['invoice'] = invoice
            line_data['line_number'] = idx
            
            # Calculate line totals
            quantity = line_data['quantity']
            unit_price = line_data['unit_price']
            discount_pct = line_data.get('discount_percentage', Decimal('0.00'))
            tax_code = line_data.get('tax_code', 1)
            cost_price = line_data.get('cost_price', Decimal('0.00'))
            
            # Line total after discount
            line_total = quantity * unit_price * (1 - discount_pct / 100)
            
            # VAT calculation (14% for tax code 1)
            vat_rate = Decimal('0.14') if tax_code == 1 else Decimal('0.00')
            vat_amount = line_total * vat_rate
            
            # Profit calculation
            line_cost = quantity * cost_price
            line_profit = line_total - line_cost
            
            line_data['line_total'] = line_total
            line_data['vat_amount'] = vat_amount
            line_data['line_profit'] = line_profit
            
            InvoiceLine.objects.create(**line_data)
            
            # Add to totals
            subtotal += line_total
            total_vat += vat_amount
            total_cost += line_cost
        
        # Update invoice totals
        invoice.subtotal = subtotal
        invoice.vat_amount = total_vat
        invoice.total_amount = subtotal + total_vat
        invoice.total_cost = total_cost
        invoice.gross_profit = subtotal - total_cost
        invoice.save()
        
        return invoice


class InvoiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating invoices."""
    lines = InvoiceLineSerializer(many=True, required=False)
    
    class Meta:
        model = Invoice
        fields = [
            'delivery_name',
            'delivery_address_line1',
            'delivery_address_line2',
            'delivery_telephone',
            'order_number',
            'customer_reference',
            'job_card_number',
            'sales_area',
            'lines',
        ]
    
    def validate(self, data):
        """Prevent updating posted invoices."""
        if self.instance and self.instance.is_posted:
            raise serializers.ValidationError(
                "Cannot modify a posted invoice."
            )
        return data
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Update invoice and recalculate if lines changed."""
        lines_data = validated_data.pop('lines', None)
        
        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # If lines were provided, recreate them
        if lines_data is not None:
            # Delete existing lines
            instance.lines.all().delete()
            
            # Recalculate totals (same logic as create)
            subtotal = Decimal('0.00')
            total_vat = Decimal('0.00')
            total_cost = Decimal('0.00')
            
            for idx, line_data in enumerate(lines_data, start=1):
                line_data['invoice'] = instance
                line_data['line_number'] = idx
                
                quantity = line_data['quantity']
                unit_price = line_data['unit_price']
                discount_pct = line_data.get('discount_percentage', Decimal('0.00'))
                tax_code = line_data.get('tax_code', 1)
                cost_price = line_data.get('cost_price', Decimal('0.00'))
                
                line_total = quantity * unit_price * (1 - discount_pct / 100)
                vat_rate = Decimal('0.14') if tax_code == 1 else Decimal('0.00')
                vat_amount = line_total * vat_rate
                line_cost = quantity * cost_price
                line_profit = line_total - line_cost
                
                line_data['line_total'] = line_total
                line_data['vat_amount'] = vat_amount
                line_data['line_profit'] = line_profit
                
                InvoiceLine.objects.create(**line_data)
                
                subtotal += line_total
                total_vat += vat_amount
                total_cost += line_cost
            
            # Update totals
            instance.subtotal = subtotal
            instance.vat_amount = total_vat
            instance.total_amount = subtotal + total_vat
            instance.total_cost = total_cost
            instance.gross_profit = subtotal - total_cost
            instance.save()
        
        return instance


class PostDatedChequeSerializer(serializers.ModelSerializer):
    """Serializer for post-dated cheques."""
    debtor_name = serializers.CharField(
        source='debtor.name',
        read_only=True
    )
    debtor_account = serializers.CharField(
        source='debtor.account_number',
        read_only=True
    )
    
    class Meta:
        model = PostDatedCheque
        fields = '__all__'
        read_only_fields = ['is_processed', 'processed_date']
    
    def validate(self, data):
        """Validate PDC data."""
        # Check if debtor is blocked
        debtor = data.get('debtor')
        if debtor and debtor.is_blocked:
            raise serializers.ValidationError({
                'debtor': 'Cannot process PDC for blocked debtor.'
            })
        
        return data


class AgeAnalysisSerializer(serializers.Serializer):
    """Serializer for age analysis report."""
    account_number = serializers.CharField()
    name = serializers.CharField()
    contact_person = serializers.CharField()
    telephone1 = serializers.CharField()
    credit_limit = serializers.DecimalField(max_digits=12, decimal_places=2)
    current = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_30 = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_60 = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_90 = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_120 = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_150 = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_180 = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    last_payment_date = serializers.DateField(allow_null=True)
    last_payment_amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class DebtorStatementSerializer(serializers.Serializer):
    """Serializer for debtor statement."""
    debtor = DebtorDetailSerializer()
    opening_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    transactions = DebtorTransactionSerializer(many=True)
    closing_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_30_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_60_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_90_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_120_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_150_days = serializers.DecimalField(max_digits=12, decimal_places=2)
    balance_180_days = serializers.DecimalField(max_digits=12, decimal_places=2)


class DebtorSummarySerializer(serializers.Serializer):
    """Serializer for debtors summary."""
    total_debtors = serializers.IntegerField()
    active_debtors = serializers.IntegerField()
    blocked_debtors = serializers.IntegerField()
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_30 = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_60 = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_90 = serializers.DecimalField(max_digits=12, decimal_places=2)
    overdue_120_plus = serializers.DecimalField(max_digits=12, decimal_places=2)