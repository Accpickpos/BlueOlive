"""
═══════════════════════════════════════════════════════════════════════════
SETTINGS APP - Django REST Framework Serializers
Serializers for all settings models
═══════════════════════════════════════════════════════════════════════════

LOCATION: accpick_project/settings/serializers.py
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SalesDepartment,
    SalesArea,
    IncomeCategory,
    ExpenseCategory,
    TaxCode,
    CostingCategory,
    PaymentMethod,
    CreditTerms,
    SystemConfiguration,
    DepartmentMonthlyStats,
    SalesAreaMonthlyStats,
    APIKey,
    DayEndReport,
)

User = get_user_model()


# ═══════════════════════════════════════════════════════════════════════════
# USER SERIALIZER (for created_by, updated_by fields)
# ═══════════════════════════════════════════════════════════════════════════

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for audit fields"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = fields


# ═══════════════════════════════════════════════════════════════════════════
# SALES DEPARTMENT SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class SalesDepartmentSerializer(serializers.ModelSerializer):
    """Full serializer with all fields including audit trail"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    deactivated_by = UserBasicSerializer(read_only=True)
    
    # Read-only computed fields
    gross_profit_percent_mtd = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    gross_profit_percent_ytd = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = SalesDepartment
        fields = [
            'id',
            'number',
            'name',
            'sales_mtd',
            'sales_ytd',
            'profit_mtd',
            'profit_ytd',
            'gross_profit_percent_mtd',
            'gross_profit_percent_ytd',
            'sales_p1',
            'sales_p2',
            'sales_p3',
            'sales_p4',
            'sales_p5',
            'sales_p6',
            'sales_p7',
            'sales_p8',
            'sales_p9',
            'sales_p10',
            'sales_p11',
            'sales_p12',
            'is_active',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'sales_mtd',
            'sales_ytd',
            'profit_mtd',
            'profit_ytd',
            'gross_profit_percent_mtd',
            'gross_profit_percent_ytd',
            'sales_p1',
            'sales_p2',
            'sales_p3',
            'sales_p4',
            'sales_p5',
            'sales_p6',
            'sales_p7',
            'sales_p8',
            'sales_p9',
            'sales_p10',
            'sales_p11',
            'sales_p12',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def validate_number(self, value):
        """Ensure number is unique and within range"""
        if value < 1 or value > 999:
            raise serializers.ValidationError("Department number must be between 1 and 999")
        
        # Check uniqueness excluding current instance
        instance = self.instance
        if SalesDepartment.objects.filter(number=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Department number already exists")
        
        return value


class SalesDepartmentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    gross_profit_percent_mtd = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    gross_profit_percent_ytd = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = SalesDepartment
        fields = [
            'id',
            'number',
            'name',
            'sales_mtd',
            'sales_ytd',
            'profit_mtd',
            'profit_ytd',
            'gross_profit_percent_mtd',
            'gross_profit_percent_ytd',
            'sales_p1',
            'sales_p2',
            'sales_p3',
            'sales_p4',
            'sales_p5',
            'sales_p6',
            'sales_p7',
            'sales_p8',
            'sales_p9',
            'sales_p10',
            'sales_p11',
            'sales_p12',
            'is_active',
        ]


# ═══════════════════════════════════════════════════════════════════════════
# SALES AREA SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class SalesAreaSerializer(serializers.ModelSerializer):
    """Full serializer with all fields including audit trail"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    deactivated_by = UserBasicSerializer(read_only=True)
    
    # Read-only computed fields
    gross_profit_percent_mtd = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    gross_profit_percent_ytd = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = SalesArea
        fields = [
            'id',
            'number',
            'name',
            'commission_rate',
            'sales_mtd',
            'sales_ytd',
            'profit_mtd',
            'profit_ytd',
            'commission_mtd',
            'commission_ytd',
            'gross_profit_percent_mtd',
            'gross_profit_percent_ytd',
            'is_active',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'sales_mtd',
            'sales_ytd',
            'profit_mtd',
            'profit_ytd',
            'commission_mtd',
            'commission_ytd',
            'gross_profit_percent_mtd',
            'gross_profit_percent_ytd',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def validate_number(self, value):
        """Ensure number is unique and within range"""
        if value < 1 or value > 99:
            raise serializers.ValidationError("Sales area number must be between 1 and 99")
        
        instance = self.instance
        if SalesArea.objects.filter(number=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Sales area number already exists")
        
        return value
    
    def validate_commission_rate(self, value):
        """Validate commission rate"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Commission rate must be between 0 and 100")
        return value


class SalesAreaListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    gross_profit_percent_mtd = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    gross_profit_percent_ytd = serializers.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = SalesArea
        fields = [
            'id',
            'number',
            'name',
            'commission_rate',
            'sales_mtd',
            'sales_ytd',
            'profit_mtd',
            'profit_ytd',
            'commission_mtd',
            'commission_ytd',
            'gross_profit_percent_mtd',
            'gross_profit_percent_ytd',
            'is_active',
        ]


# ═══════════════════════════════════════════════════════════════════════════
# INCOME CATEGORY SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class IncomeCategorySerializer(serializers.ModelSerializer):
    """Full serializer with all fields"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    deactivated_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = IncomeCategory
        fields = [
            'id',
            'number',
            'name',
            'total_mtd',
            'total_ytd',
            'is_active',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'total_mtd',
            'total_ytd',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def validate_number(self, value):
        """Ensure number is unique and within range"""
        if value < 1 or value > 99999999:
            raise serializers.ValidationError("Income category number must be between 1 and 99999999")
        
        instance = self.instance
        if IncomeCategory.objects.filter(number=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Income category number already exists")
        
        return value


class IncomeCategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    class Meta:
        model = IncomeCategory
        fields = ['id', 'number', 'name', 'total_mtd', 'total_ytd', 'is_active']


# ═══════════════════════════════════════════════════════════════════════════
# EXPENSE CATEGORY SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Full serializer with all fields"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    deactivated_by = UserBasicSerializer(read_only=True)
    category_type_display = serializers.CharField(
        source='get_category_type_display',
        read_only=True
    )
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id',
            'number',
            'name',
            'category_type',
            'category_type_display',
            'total_mtd',
            'total_ytd',
            'is_active',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'category_type_display',
            'total_mtd',
            'total_ytd',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def validate_number(self, value):
        """Ensure number is unique and within range"""
        if value < 1 or value > 99999999:
            raise serializers.ValidationError("Expense category number must be between 1 and 99999999")
        
        instance = self.instance
        if ExpenseCategory.objects.filter(number=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Expense category number already exists")
        
        return value


class ExpenseCategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    category_type_display = serializers.CharField(
        source='get_category_type_display',
        read_only=True
    )
    
    class Meta:
        model = ExpenseCategory
        fields = [
            'id',
            'number',
            'name',
            'category_type',
            'category_type_display',
            'total_mtd',
            'total_ytd',
            'is_active',
        ]


# ═══════════════════════════════════════════════════════════════════════════
# TAX CODE SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class TaxCodeSerializer(serializers.ModelSerializer):
    """Full serializer with all fields"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    deactivated_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = TaxCode
        fields = [
            'id',
            'code',
            'description',
            'rate',
            'is_default',
            'is_active',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def validate_code(self, value):
        """Ensure code is unique"""
        instance = self.instance
        if TaxCode.objects.filter(code=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Tax code already exists")
        return value
    
    def validate_rate(self, value):
        """Validate tax rate"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Tax rate must be between 0 and 100")
        return value


class TaxCodeListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    class Meta:
        model = TaxCode
        fields = ['id', 'code', 'description', 'rate', 'is_default', 'is_active']


# ═══════════════════════════════════════════════════════════════════════════
# COSTING CATEGORY SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class CostingCategorySerializer(serializers.ModelSerializer):
    """Full serializer with all fields"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    deactivated_by = UserBasicSerializer(read_only=True)
    costing_method_display = serializers.CharField(
        source='get_costing_method_display',
        read_only=True
    )
    pricing_method_display = serializers.CharField(
        source='get_pricing_method_display',
        read_only=True
    )
    methods_display = serializers.CharField(
        source='get_methods_display',
        read_only=True
    )
    
    class Meta:
        model = CostingCategory
        fields = [
            'id',
            'name',
            'costing_method',
            'costing_method_display',
            'pricing_method',
            'pricing_method_display',
            'methods_display',
            'description',
            'is_active',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'costing_method_display',
            'pricing_method_display',
            'methods_display',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]


class CostingCategoryListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    costing_method_display = serializers.CharField(
        source='get_costing_method_display',
        read_only=True
    )
    pricing_method_display = serializers.CharField(
        source='get_pricing_method_display',
        read_only=True
    )
    
    class Meta:
        model = CostingCategory
        fields = [
            'id',
            'name',
            'costing_method',
            'costing_method_display',
            'pricing_method',
            'pricing_method_display',
            'is_active',
        ]


# ═══════════════════════════════════════════════════════════════════════════
# PAYMENT METHOD SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class PaymentMethodSerializer(serializers.ModelSerializer):
    """Full serializer with all fields"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    deactivated_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id',
            'code',
            'name',
            'requires_reference',
            'is_electronic',
            'is_active',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def validate_code(self, value):
        """Ensure code is unique"""
        instance = self.instance
        if PaymentMethod.objects.filter(code=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Payment method code already exists")
        return value.upper()


class PaymentMethodListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    class Meta:
        model = PaymentMethod
        fields = [
            'id',
            'code',
            'name',
            'requires_reference',
            'is_electronic',
            'is_active',
        ]


# ═══════════════════════════════════════════════════════════════════════════
# CREDIT TERMS SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class CreditTermsSerializer(serializers.ModelSerializer):
    """Full serializer with all fields"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    deactivated_by = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = CreditTerms
        fields = [
            'id',
            'days',
            'description',
            'is_active',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'deactivated_at',
            'deactivated_by',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def validate_days(self, value):
        """Ensure days is unique and within range"""
        if value < 0 or value > 999:
            raise serializers.ValidationError("Credit days must be between 0 and 999")
        
        instance = self.instance
        if CreditTerms.objects.filter(days=value).exclude(
            pk=instance.pk if instance else None
        ).exists():
            raise serializers.ValidationError("Credit terms with these days already exist")
        
        return value


class CreditTermsListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    class Meta:
        model = CreditTerms
        fields = ['id', 'days', 'description', 'is_active']


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM CONFIGURATION SERIALIZER
# ═══════════════════════════════════════════════════════════════════════════

class SystemConfigurationSerializer(serializers.ModelSerializer):
    """System configuration serializer"""
    created_by = UserBasicSerializer(read_only=True)
    updated_by = UserBasicSerializer(read_only=True)
    default_tax_code_details = TaxCodeListSerializer(
        source='default_tax_code',
        read_only=True
    )
    
    class Meta:
        model = SystemConfiguration
        fields = [
            'id',
            'shop_name',
            'shop_address',
            'shop_phone',
            'shop_email',
            'shop_vat_number',
            'shop_registration_number',
            'default_tax_code',
            'default_tax_code_details',
            'ageing_periods',
            'current_financial_year',
            'current_period',
            # Period end tracking
            'last_day_end_date',
            'last_month_end_date',
            'last_year_end_date',
            # Scheduling settings
            'enable_auto_day_end',
            'day_end_time',
            'day_end_day_of_week',
            'enable_auto_month_end',
            'month_end_day',
            'month_end_time',
            'enable_auto_year_end',
            'year_end_month',
            'year_end_day',
            'year_end_time',
            # Other settings
            'enable_negative_stock',
            'auto_post_transactions',
            'charge_interest_on_overdue',
            'default_interest_rate',
            'date_format',
            'currency_symbol',
            'decimal_places',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
        read_only_fields = [
            'id',
            'default_tax_code_details',
            'last_day_end_date',
            'last_month_end_date',
            'last_year_end_date',
            'created_at',
            'updated_at',
            'created_by',
            'updated_by',
        ]
    
    def validate_current_period(self, value):
        """Validate period is between 1 and 12"""
        if value < 1 or value > 12:
            raise serializers.ValidationError("Period must be between 1 and 12")
        return value
    
    def validate_default_interest_rate(self, value):
        """Validate interest rate"""
        if value < 0 or value > 100:
            raise serializers.ValidationError("Interest rate must be between 0 and 100")
        return value
    
    def validate_decimal_places(self, value):
        """Validate decimal places"""
        if value < 0 or value > 4:
            raise serializers.ValidationError("Decimal places must be between 0 and 4")
        return value
    
    def validate_ageing_periods(self, value):
        """Validate ageing periods"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Ageing periods must be a list")
        
        if not value:
            raise serializers.ValidationError("At least one ageing period is required")
        
        for period in value:
            if not isinstance(period, int) or period <= 0:
                raise serializers.ValidationError("All ageing periods must be positive integers")
        
        return value


# ═══════════════════════════════════════════════════════════════════════════
# MONTHLY STATISTICS SERIALIZERS
# ═══════════════════════════════════════════════════════════════════════════

class DepartmentMonthlyStatsSerializer(serializers.ModelSerializer):
    """Department monthly statistics serializer"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    department_number = serializers.IntegerField(source='department.number', read_only=True)
    
    class Meta:
        model = DepartmentMonthlyStats
        fields = [
            'id',
            'department',
            'department_name',
            'department_number',
            'year',
            'month',
            'sales_value',
            'profit_value',
            'profit_percent',
            'created_at',
        ]
        read_only_fields = fields


class SalesAreaMonthlyStatsSerializer(serializers.ModelSerializer):
    """Sales area monthly statistics serializer"""
    sales_area_name = serializers.CharField(source='sales_area.name', read_only=True)
    sales_area_number = serializers.IntegerField(source='sales_area.number', read_only=True)
    
    class Meta:
        model = SalesAreaMonthlyStats
        fields = [
            'id',
            'sales_area',
            'sales_area_name',
            'sales_area_number',
            'year',
            'month',
            'sales_value',
            'profit_value',
            'profit_percent',
            'commission_earned',
            'created_at',
        ]
        read_only_fields = fields


class DayEndReportSerializer(serializers.ModelSerializer):
    """Persisted Day End Report serializer (manual §8.6 reprint facility)"""

    class Meta:
        model = DayEndReport
        fields = [
            'id',
            'process_date',
            'shop_id',
            'success',
            'message',
            'details',
            'errors',
            'created_at',
        ]
        read_only_fields = fields


class APIKeyListSerializer(serializers.ModelSerializer):
    """Serializer for API key list view."""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = APIKey
        fields = [
            'id',
            'name',
            'tenant',
            'tenant_name',
            'external_service',
            'status',
            'last_used',
            'last_ip',
            'expires_at',
            'is_valid',
            'created_at',
            'created_by_name',
        ]
        read_only_fields = ['id', 'last_used', 'last_ip', 'created_at', 'is_valid', 'created_by_name', 'tenant_name']


class APIKeyDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for API key with all fields."""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = APIKey
        fields = [
            'id',
            'name',
            'key',
            'tenant',
            'tenant_name',
            'external_service',
            'description',
            'allowed_endpoints',
            'allowed_methods',
            'rate_limit_requests',
            'rate_limit_window',
            'status',
            'last_used',
            'last_ip',
            'expires_at',
            'is_valid',
            'created_at',
            'updated_at',
            'created_by_name',
        ]
        read_only_fields = ['id', 'key', 'last_used', 'last_ip', 'created_at', 'updated_at', 'is_valid', 'created_by_name', 'tenant_name']


class APIKeyCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating API keys.
    
    SECURITY: Tenant is automatically set from request context.
    Users cannot create API keys for other tenants.
    """
    # Read-only display of tenant name
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = APIKey
        fields = [
            'tenant',
            'tenant_name',
            'name',
            'external_service',
            'description',
            'allowed_endpoints',
            'allowed_methods',
            'rate_limit_requests',
            'rate_limit_window',
            'expires_at',
        ]
        read_only_fields = ['tenant_name']
    
    def create(self, validated_data):
        """
        Create API key with auto-generated secret.
        
        SECURITY: Automatically binds to current tenant.
        """
        # Get current user and set as created_by
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user:
            validated_data['created_by'] = request.user
        
        # Ensure tenant is set from request context (automatic binding)
        if 'tenant' not in validated_data and request:
            validated_data['tenant'] = request.tenant
        
        # SECURITY: If no tenant in request, raise error
        if not validated_data.get('tenant'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'tenant': 'Tenant context required to create API keys'})
        
        api_key = APIKey.objects.create(**validated_data)
        return api_key
    
    def to_representation(self, instance):
        """Return the created key details."""
        return APIKeyDetailSerializer(instance).data


class APIKeyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating API keys."""
    
    class Meta:
        model = APIKey
        fields = [
            'name',
            'description',
            'allowed_endpoints',
            'allowed_methods',
            'rate_limit_requests',
            'rate_limit_window',
            'status',
            'expires_at',
        ]