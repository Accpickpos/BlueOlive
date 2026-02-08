from rest_framework import serializers
from .models import (
    SalesDepartment, SalesArea, StockItem, SpecialDeal, FuturePricing,
    ShrinkWrap, PackBundle, PackBundleIngredient, StockTransaction,
    StockTake, StockTakeItem, ContractPricing, OneTouchLookupKey,
    StockMonthlyStatistic
)
from decimal import Decimal


class SalesDepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Sales Departments"""
    
    class Meta:
        model = SalesDepartment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SalesAreaSerializer(serializers.ModelSerializer):
    """Serializer for Sales Areas/Salesmen"""
    
    class Meta:
        model = SalesArea
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class StockItemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for stock item lists"""
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    stock_value = serializers.SerializerMethodField()
    available_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = StockItem
        fields = [
            'stock_code', 'description', 'department', 'department_name',
            'supplier', 'supplier_name', 'cost_price', 'selling_price_1',
            'quantity_on_hand', 'quantity_allocated', 'quantity_sale_order',
            'available_quantity', 'stock_value', 'is_active'
        ]
    
    def get_stock_value(self, obj):
        return obj.quantity_on_hand * obj.cost_price
    
    def get_available_quantity(self, obj):
        return obj.available_quantity


class StockItemDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for stock items"""
    department_name = serializers.CharField(source='department.department_name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    
    # Calculated fields
    markup_percent_1 = serializers.SerializerMethodField()
    markup_percent_2 = serializers.SerializerMethodField()
    markup_percent_3 = serializers.SerializerMethodField()
    gross_profit_1 = serializers.SerializerMethodField()
    gross_profit_2 = serializers.SerializerMethodField()
    gross_profit_3 = serializers.SerializerMethodField()
    stock_value = serializers.SerializerMethodField()
    available_quantity = serializers.SerializerMethodField()
    needs_reordering = serializers.SerializerMethodField()
    
    class Meta:
        model = StockItem
        fields = '__all__'
        read_only_fields = [
            'created_at', 'updated_at', 'sales_mtd_quantity', 'sales_mtd_value',
            'sales_ytd_quantity', 'sales_ytd_value', 'date_last_purchased', 'date_last_sold'
        ]
    
    def get_markup_percent_1(self, obj):
        return obj.calculate_markup(1)
    
    def get_markup_percent_2(self, obj):
        return obj.calculate_markup(2)
    
    def get_markup_percent_3(self, obj):
        return obj.calculate_markup(3)
    
    def get_gross_profit_1(self, obj):
        return obj.calculate_gross_profit(1)
    
    def get_gross_profit_2(self, obj):
        return obj.calculate_gross_profit(2)
    
    def get_gross_profit_3(self, obj):
        return obj.calculate_gross_profit(3)
    
    def get_stock_value(self, obj):
        return obj.quantity_on_hand * obj.cost_price
    
    def get_available_quantity(self, obj):
        return obj.available_quantity
    
    def get_needs_reordering(self, obj):
        return obj.needs_reordering()


class StockItemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating stock items"""
    
    class Meta:
        model = StockItem
        fields = [
            'stock_code', 'description', 'department', 'supplier', 'supplier_code',
            'tax_code', 'cost_price', 'selling_price_1', 'selling_price_2', 'selling_price_3',
            'markup_1', 'markup_2', 'markup_3', 'reorder_quantity', 'default_selling_quantity',
            'quantity_allocated', 'quantity_sale_order',
            'allow_negative_quantities', 'maximum_discount_percent', 'bin_number', 'is_active'
        ]
    
    def validate(self, data):
        """Validate stock item data"""
        # Ensure at least one selling price is set
        if not any([data.get('selling_price_1'), data.get('selling_price_2'), data.get('selling_price_3')]):
            raise serializers.ValidationError("At least one selling price must be set")
        
        # Validate that allocated + sale_order don't exceed QOH
        stock_code = data.get('stock_code')
        if stock_code:
            try:
                item = StockItem.objects.get(stock_code=stock_code)
                qty_allocated = data.get('quantity_allocated', item.quantity_allocated)
                qty_sale_order = data.get('quantity_sale_order', item.quantity_sale_order)
                qty_on_hand = item.quantity_on_hand
                
                if (qty_allocated + qty_sale_order) > qty_on_hand:
                    raise serializers.ValidationError(
                        "Allocated + Sale Order quantities cannot exceed Quantity on Hand"
                    )
            except StockItem.DoesNotExist:
                pass
        
        return data


class SpecialDealSerializer(serializers.ModelSerializer):
    """Serializer for Special Deals"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    is_currently_valid = serializers.SerializerMethodField()
    
    class Meta:
        model = SpecialDeal
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_is_currently_valid(self, obj):
        return obj.is_valid_today()


class FuturePricingSerializer(serializers.ModelSerializer):
    """Serializer for Future Pricing"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    
    class Meta:
        model = FuturePricing
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'is_applied']


class ShrinkWrapSerializer(serializers.ModelSerializer):
    """Serializer for Shrink Wrap relationships"""
    bulk_description = serializers.CharField(source='bulk_pack_code.description', read_only=True)
    shrink_description = serializers.CharField(source='shrink_pack_code.description', read_only=True)
    
    class Meta:
        model = ShrinkWrap
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PackBundleIngredientSerializer(serializers.ModelSerializer):
    """Serializer for Pack/Bundle ingredients"""
    ingredient_code = serializers.CharField(source='ingredient_stock.stock_code', read_only=True)
    ingredient_description = serializers.CharField(source='ingredient_stock.description', read_only=True)
    current_cost = serializers.DecimalField(source='ingredient_stock.cost_price', read_only=True, max_digits=10, decimal_places=2)
    ingredient_value = serializers.SerializerMethodField()
    
    class Meta:
        model = PackBundleIngredient
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'cost_at_creation']
    
    def get_ingredient_value(self, obj):
        return obj.get_ingredient_value()


class PackBundleSerializer(serializers.ModelSerializer):
    """Serializer for Pack/Bundle"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    ingredients = PackBundleIngredientSerializer(many=True, read_only=True)
    calculated_total_cost = serializers.SerializerMethodField()
    
    class Meta:
        model = PackBundle
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'total_cost']
    
    def get_calculated_total_cost(self, obj):
        return obj.calculate_total_cost()


class PackBundleCreateSerializer(serializers.Serializer):
    """Serializer for creating a pack/bundle with ingredients"""
    stock_item = serializers.PrimaryKeyRelatedField(queryset=StockItem.objects.all())
    ingredients = serializers.ListField(
        child=serializers.DictField(),
        write_only=True
    )
    
    def validate_ingredients(self, value):
        """Validate ingredients list"""
        if not value:
            raise serializers.ValidationError("At least one ingredient is required")
        
        for ingredient in value:
            if 'ingredient_stock' not in ingredient or 'quantity' not in ingredient:
                raise serializers.ValidationError("Each ingredient must have 'ingredient_stock' and 'quantity'")
        
        return value
    
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        pack_bundle = PackBundle.objects.create(**validated_data)
        
        for ingredient_data in ingredients_data:
            PackBundleIngredient.objects.create(
                pack_bundle=pack_bundle,
                ingredient_stock_id=ingredient_data['ingredient_stock'],
                quantity=ingredient_data['quantity'],
                cost_at_creation=StockItem.objects.get(pk=ingredient_data['ingredient_stock']).cost_price
            )
        
        pack_bundle.calculate_total_cost()
        return pack_bundle


class StockTransactionSerializer(serializers.ModelSerializer):
    """Serializer for Stock Transactions"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
    class Meta:
        model = StockTransaction
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'quantity_balance']


class StockTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating stock transactions"""
    
    class Meta:
        model = StockTransaction
        fields = [
            'transaction_type', 'stock_item', 'transaction_date', 'transaction_number',
            'quantity_in', 'quantity_out', 'unit_cost', 'unit_price', 'reference', 'station_number'
        ]
    
    def validate(self, data):
        """Validate transaction data"""
        if data.get('quantity_in', 0) > 0 and data.get('quantity_out', 0) > 0:
            raise serializers.ValidationError("Transaction cannot have both quantity_in and quantity_out")
        
        if data.get('quantity_in', 0) == 0 and data.get('quantity_out', 0) == 0:
            raise serializers.ValidationError("Transaction must have either quantity_in or quantity_out")
        
        return data
    
    def create(self, validated_data):
        """Create transaction and update stock balance"""
        stock_item = validated_data['stock_item']
        
        # Calculate new balance
        current_balance = stock_item.quantity_on_hand
        quantity_in = validated_data.get('quantity_in', 0)
        quantity_out = validated_data.get('quantity_out', 0)
        new_balance = current_balance + quantity_in - quantity_out
        
        # Create transaction
        validated_data['quantity_balance'] = new_balance
        transaction = StockTransaction.objects.create(**validated_data)
        
        # Update stock item
        stock_item.quantity_on_hand = new_balance
        
        # Update average cost for incoming stock
        if quantity_in > 0 and validated_data.get('unit_cost', 0) > 0:
            total_value = (current_balance * stock_item.average_cost) + (quantity_in * validated_data['unit_cost'])
            total_quantity = current_balance + quantity_in
            if total_quantity > 0:
                stock_item.average_cost = total_value / total_quantity
        
        stock_item.save()
        
        return transaction


class StockTakeItemSerializer(serializers.ModelSerializer):
    """Serializer for Stock Take Items"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    
    class Meta:
        model = StockTakeItem
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'variance_quantity', 'variance_value']


class StockTakeSerializer(serializers.ModelSerializer):
    """Serializer for Stock Take"""
    items = StockTakeItemSerializer(many=True, read_only=True)
    total_variance_value = serializers.SerializerMethodField()
    items_counted = serializers.SerializerMethodField()
    total_items = serializers.SerializerMethodField()
    
    class Meta:
        model = StockTake
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'completed_at']
    
    def get_total_variance_value(self, obj):
        return sum(item.variance_value for item in obj.items.all())
    
    def get_items_counted(self, obj):
        return obj.items.filter(is_counted=True).count()
    
    def get_total_items(self, obj):
        return obj.items.count()


class StockTakeCountSerializer(serializers.Serializer):
    """Serializer for counting stock during stock take"""
    stock_item = serializers.PrimaryKeyRelatedField(queryset=StockItem.objects.all())
    quantity_counted = serializers.DecimalField(max_digits=10, decimal_places=2)
    add_to_previous = serializers.BooleanField(default=False)


class ContractPricingSerializer(serializers.ModelSerializer):
    """Serializer for Contract Pricing"""
    debtor_name = serializers.CharField(source='debtor.name', read_only=True)
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.department_name', read_only=True, allow_null=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True, allow_null=True)
    
    class Meta:
        model = ContractPricing
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def validate(self, data):
        """Validate contract pricing data"""
        if data.get('pricing_method') == 'ACTUAL' and not data.get('contract_price'):
            raise serializers.ValidationError("Contract price is required for ACTUAL pricing method")
        
        if data.get('pricing_method') == 'COST_MARKUP' and not data.get('markup_percent'):
            raise serializers.ValidationError("Markup percent is required for COST_MARKUP pricing method")
        
        # Must have at least one: stock_item, department, or supplier
        if not any([data.get('stock_item'), data.get('department'), data.get('supplier')]):
            raise serializers.ValidationError("Must specify at least one: stock_item, department, or supplier")
        
        return data


class OneTouchLookupKeySerializer(serializers.ModelSerializer):
    """Serializer for One-Touch Lookup Keys"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    
    class Meta:
        model = OneTouchLookupKey
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class StockMonthlyStatisticSerializer(serializers.ModelSerializer):
    """Serializer for Monthly Statistics"""
    stock_code = serializers.CharField(source='stock_item.stock_code', read_only=True)
    stock_description = serializers.CharField(source='stock_item.description', read_only=True)
    
    class Meta:
        model = StockMonthlyStatistic
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class PriceAdjustmentSerializer(serializers.Serializer):
    """Serializer for bulk price adjustments"""
    
    ADJUSTMENT_TYPE_CHOICES = [
        ('INCREASE', 'Increase'),
        ('DECREASE', 'Decrease'),
    ]
    
    VALUE_TYPE_CHOICES = [
        ('PERCENTAGE', 'Percentage'),
        ('RAND', 'Rand Value'),
    ]
    
    PRICE_TYPE_CHOICES = [
        ('COST', 'Cost Price'),
        ('SELLING', 'Selling Price'),
    ]
    
    adjustment_type = serializers.ChoiceField(choices=ADJUSTMENT_TYPE_CHOICES)
    value_type = serializers.ChoiceField(choices=VALUE_TYPE_CHOICES)
    price_type = serializers.ChoiceField(choices=PRICE_TYPE_CHOICES)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_levels = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=3),
        required=False
    )
    department = serializers.PrimaryKeyRelatedField(
        queryset=SalesDepartment.objects.all(),
        required=False,
        allow_null=True
    )
    supplier = serializers.PrimaryKeyRelatedField(
        queryset=None,  # Will be set in view
        required=False,
        allow_null=True,
        read_only=True
    )


class StockValuationSerializer(serializers.Serializer):
    """Serializer for stock valuation reports"""
    stock_code = serializers.CharField()
    description = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2)
    cost_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    department = serializers.CharField()


class ManufactureItemSerializer(serializers.Serializer):
    """Serializer for manufacturing pack/bundle items"""
    pack_bundle = serializers.PrimaryKeyRelatedField(queryset=PackBundle.objects.all())
    quantity = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    manufacture_date = serializers.DateField()
    warn_on_out_of_stock = serializers.BooleanField(default=True)