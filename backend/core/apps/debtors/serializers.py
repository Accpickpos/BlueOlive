"""
Debtors serializers.
Comprehensive serializers for all debtor-related models.
Based on DMAST, DEBTRAN, DEBTOPEN, DPDC, DEBTORAUD tables.
"""
from rest_framework import serializers
from django.db import transaction
from decimal import Decimal
from .models import (
    Debtor, DebtorTransaction, DebtorAudit,
    Debtopen, Dpdc, Darea
)


class DebtorListSerializer(serializers.ModelSerializer):
    """Serializer for debtor list view (DMAST)."""
    
    total_balance = serializers.SerializerMethodField()
    overdue_balance = serializers.SerializerMethodField()
    is_blocked_flag = serializers.SerializerMethodField()
    
    class Meta:
        model = Debtor
        fields = [
            'dno',
            'dname',
            'dsname',
            'dcontact',
            'dtel',
            'darea',
            'acctype',
            'dclimit',
            'dcrnt',
            'total_balance',
            'overdue_balance',
            'is_blocked_flag',
            'is_active',
            'created_at',
        ]
    
    def get_total_balance(self, obj):
        """Calculate total balance."""
        try:
            return obj.get_total_balance()
        except (AttributeError, TypeError) as e:
            # Handle missing fields or calculation errors
            return Decimal(0)
    
    def get_overdue_balance(self, obj):
        """Calculate overdue balance (> 30 days)."""
        try:
            return obj.get_overdue_balance()
        except (AttributeError, TypeError) as e:
            # Handle missing fields or calculation errors
            return Decimal(0)
    
    def get_is_blocked_flag(self, obj):
        """Get block status."""
        try:
            return obj.is_blocked()
        except (AttributeError, TypeError) as e:
            # Handle missing field or method error
            return False


class DebtorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for debtor (DMAST)."""
    
    total_balance = serializers.SerializerMethodField()
    overdue_balance = serializers.SerializerMethodField()
    is_blocked_flag = serializers.SerializerMethodField()
    available_credit = serializers.SerializerMethodField()
    credit_utilization_pct = serializers.SerializerMethodField()
    
    class Meta:
        model = Debtor
        fields = [
            'dno',
            'dname',
            'dsname',
            'dcontact',
            'dtel',
            'dfax',
            'dadd1',
            'dadd2',
            'dadd3',
            'dpcode',
            'delad1',
            'delad2',
            'delad3',
            'delad4',
            'dtaxno',
            'acctype',
            'price',
            'terms',
            'ddiscper',
            'pdisc',
            'discprn',
            'dclimit',
            'darea',
            'dintflag',
            'blockflag',
            'dposbal',
            'dbalbfwd',
            'dcrnt',
            'd30',
            'd60',
            'd90',
            'd120',
            'd150',
            'd180',
            'total_balance',
            'overdue_balance',
            'available_credit',
            'credit_utilization_pct',
            'is_blocked_flag',
            'dsalesm',
            'dsalesy',
            'dprofitm',
            'dprofity',
            'damtlpd',
            'ddatlpd',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'dcrnt',
            'd30',
            'd60',
            'd90',
            'd120',
            'd150',
            'd180',
            'dsalesm',
            'dsalesy',
            'dprofitm',
            'dprofity',
            'damtlpd',
            'ddatlpd',
        ]
    
    def get_total_balance(self, obj):
        try:
            return obj.get_total_balance()
        except (AttributeError, TypeError):
            return Decimal(0)
    
    def get_overdue_balance(self, obj):
        try:
            return obj.get_overdue_balance()
        except (AttributeError, TypeError):
            return Decimal(0)
    
    def get_available_credit(self, obj):
        try:
            return obj.dclimit - obj.get_total_balance()
        except (AttributeError, TypeError):
            return Decimal(0)
    
    def get_credit_utilization_pct(self, obj):
        try:
            total = obj.get_total_balance()
            if obj.dclimit > 0:
                return round((total / obj.dclimit) * 100, 2)
            return 0
        except (AttributeError, TypeError, ZeroDivisionError):
            return 0
    
    def get_is_blocked_flag(self, obj):
        try:
            return obj.is_blocked()
        except (AttributeError, TypeError):
            return False


class DebtorCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating debtor (DMAST)."""
    
    class Meta:
        model = Debtor
        fields = [
            'dno',
            'dname',
            'dsname',
            'dcontact',
            'dtel',
            'dfax',
            'dadd1',
            'dadd2',
            'dadd3',
            'dpcode',
            'delad1',
            'delad2',
            'delad3',
            'delad4',
            'dtaxno',
            'acctype',
            'price',
            'terms',
            'ddiscper',
            'pdisc',
            'discprn',
            'dclimit',
            'darea',
            'dintflag',
            'blockflag',
            'dposbal',
            'is_active',
        ]
        read_only_fields = []
    
    def validate_dno(self, value):
        """Ensure account number is unique."""
        instance = self.instance
        if instance and instance.dno == value:
            return value
        
        if Debtor.objects.filter(dno=value).exists():
            raise serializers.ValidationError("Account number already exists.")
        return value
    
    def validate_dsname(self, value):
        """Ensure short name is populated."""
        if not value:
            raise serializers.ValidationError("Short name is required.")
        return value[:5].upper()
    
    def validate(self, data):
        """Validate debtor data."""
        # Validate credit limit
        if data.get('dclimit', 0) < 0:
            raise serializers.ValidationError({'dclimit': 'Credit limit cannot be negative.'})
        
        # Validate discounts
        if not 0 <= data.get('ddiscper', 0) <= 100:
            raise serializers.ValidationError({'ddiscper': 'Discount % must be 0-100.'})
        
        if not 0 <= data.get('pdisc', 0) <= 100:
            raise serializers.ValidationError({'pdisc': 'Prompt discount must be 0-100.'})
        
        # Cash customers should not have credit limit
        if data.get('acctype') == 'C' and data.get('dclimit', 0) > 0:
            raise serializers.ValidationError({'dclimit': 'Cash customers should not have credit limit.'})
        
        return data


class DebtorTransactionSerializer(serializers.ModelSerializer):
    """Serializer for debtor transactions (DEBTRAN)."""
    
    debtor_name = serializers.CharField(
        source='dno.dname',
        read_only=True
    )
    debtor_account = serializers.CharField(
        source='dno.dno',
        read_only=True
    )
    dtype_display = serializers.CharField(
        source='get_dtype_display',
        read_only=True
    )
    
    class Meta:
        model = DebtorTransaction
        fields = [
            'dno',
            'debtor_account',
            'debtor_name',
            'dtrano',
            'dtype',
            'dtype_display',
            'dtdate',
            'time',
            'dtsub',
            'dtgst',
            'dttot',
            'dtaxstat',
            'source',
            'ordno',
            'custref',
            'del1',
            'del2',
            'del3',
            'del4',
            'created_at',
        ]
        read_only_fields = ['created_at']


class DebteopenSerializer(serializers.ModelSerializer):
    """Serializer for open item transactions (DEBTOPEN)."""
    
    debtor_name = serializers.CharField(
        source='dno.dname',
        read_only=True
    )
    debtor_account = serializers.CharField(
        source='dno.dno',
        read_only=True
    )
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )
    ageflag_display = serializers.CharField(
        source='get_ageflag_display',
        read_only=True
    )
    allocated_amount = serializers.SerializerMethodField()
    is_fully_allocated = serializers.SerializerMethodField()
    
    class Meta:
        model = Debtopen
        fields = [
            'dno',
            'debtor_account',
            'debtor_name',
            'dtrano',
            'type',
            'type_display',
            'date',
            'total',
            'balancedue',
            'allocated_amount',
            'is_fully_allocated',
            'ageflag',
            'ageflag_display',
            'posted',
            'created_at',
        ]
        read_only_fields = ['created_at']
    
    def get_allocated_amount(self, obj):
        return obj.get_allocated_amount()
    
    def get_is_fully_allocated(self, obj):
        return obj.is_fully_allocated()


class DpdcSerializer(serializers.ModelSerializer):
    """Serializer for post-dated cheques (DPDC)."""
    
    debtor_name = serializers.CharField(
        source='dno.dname',
        read_only=True
    )
    debtor_account = serializers.CharField(
        source='dno.dno',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Dpdc
        fields = [
            'dno',
            'debtor_account',
            'debtor_name',
            'date',
            'amount',
            'status',
            'status_display',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['created_at']
    
    def get_is_active(self, obj):
        return obj.status == 'A'


class DebtorAuditSerializer(serializers.ModelSerializer):
    """Serializer for debtor audit records (DEBTORAUD)."""
    
    debtor_account = serializers.CharField(
        source='dno.dno',
        read_only=True
    )
    type_display = serializers.CharField(
        source='get_type_display',
        read_only=True
    )
    thistype_display = serializers.CharField(
        source='get_thistype_display',
        read_only=True
    )
    
    class Meta:
        model = DebtorAudit
        fields = [
            'dno',
            'debtor_account',
            'dtrano',
            'type',
            'type_display',
            'thistype',
            'thistype_display',
            'thistran',
            'date',
            'amount',
            'created_at',
        ]
        read_only_fields = ['created_at']


class DareaSerializer(serializers.ModelSerializer):
    """Serializer for sales area (DAREA)."""
    
    total_sales = serializers.SerializerMethodField()
    
    class Meta:
        model = Darea
        fields = [
            'darea',
            'dareaname',
            'arsls1',
            'arsls2',
            'arsls3',
            'arsls4',
            'arsls5',
            'arsls6',
            'arsls7',
            'arsls8',
            'arsls9',
            'arsls10',
            'arsls11',
            'arsls12',
            'total_sales',
            'created_at',
        ]
        read_only_fields = ['created_at']
    
    def get_total_sales(self, obj):
        return obj.get_total_sales()


class PaginatedDebtorTransactionSerializer(serializers.Serializer):
    """Helper serializer for paginated transactions."""
    debtor_transactions = DebtorTransactionSerializer(many=True)
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_vat = serializers.DecimalField(max_digits=14, decimal_places=2)
    transaction_count = serializers.IntegerField()


class AgeAnalysisSerializer(serializers.Serializer):
    """Serializer for age analysis report."""
    dno = serializers.IntegerField()
    dname = serializers.CharField()
    dcontact = serializers.CharField()
    dtel = serializers.CharField()
    dclimit = serializers.DecimalField(max_digits=12, decimal_places=2)
    current = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_30 = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_60 = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_90 = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_120 = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_150 = serializers.DecimalField(max_digits=10, decimal_places=2)
    days_180 = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    ddatlpd = serializers.DateField(allow_null=True)
    damtlpd = serializers.DecimalField(max_digits=10, decimal_places=2)


class DebtorSummarySerializer(serializers.Serializer):
    """Serializer for debtors summary report."""
    total_debtors = serializers.IntegerField()
    active_debtors = serializers.IntegerField()
    blocked_debtors = serializers.IntegerField()
    total_balance = serializers.DecimalField(max_digits=14, decimal_places=2)
    current_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_30 = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_60 = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_90 = serializers.DecimalField(max_digits=10, decimal_places=2)
    overdue_120_plus = serializers.DecimalField(max_digits=10, decimal_places=2)


class DebtranListSerializer(serializers.ModelSerializer):
    """Simple list serializer for DEBTRAN transactions."""
    
    class Meta:
        model = DebtorTransaction
        fields = [
            'dtrano',
            'dtype',
            'dtdate',
            'dtsub',
            'dtgst',
            'dttot',
        ]


class DebtOpenListSerializer(serializers.ModelSerializer):
    """Simple list serializer for DEBTOPEN items."""
    
    class Meta:
        model = Debtopen
        fields = [
            'dtrano',
            'type',
            'date',
            'total',
            'balancedue',
            'ageflag',
            'posted',
        ]