from rest_framework import serializers
from .models import GLMast, GLTran, GLStJnl, GLSpread


class GLMastSerializer(serializers.ModelSerializer):
    """Serializer for General Ledger Master accounts"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    drorcr_display = serializers.CharField(source='get_drorcr_display', read_only=True)
    
    class Meta:
        model = GLMast
        fields = [
            'id',
            'accno',
            'name',
            'type',
            'type_display',
            'drorcr',
            'drorcr_display',
            'repline',
            'balbfwd',
            'period1', 'period2', 'period3', 'period4', 'period5',
            'period6', 'period7', 'period8', 'period9', 'period10',
            'period11', 'period12', 'period13',
            'budget1', 'budget2', 'budget3', 'budget4', 'budget5',
            'budget6', 'budget7', 'budget8', 'budget9', 'budget10',
            'budget11', 'budget12',
            'lastyear1', 'lastyear2', 'lastyear3', 'lastyear4', 'lastyear5',
            'lastyear6', 'lastyear7', 'lastyear8', 'lastyear9', 'lastyear10',
            'lastyear11', 'lastyear12',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'type_display', 'drorcr_display']
        extra_kwargs = {
            'accno': {'validators': []},
        }


class GLMastDetailSerializer(GLMastSerializer):
    """Detailed serializer with all period and budget information grouped"""
    
    class Meta(GLMastSerializer.Meta):
        pass


class GLMastListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views with essential fields only"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    drorcr_display = serializers.CharField(source='get_drorcr_display', read_only=True)
    
    class Meta:
        model = GLMast
        fields = [
            'id',
            'accno',
            'name',
            'type',
            'type_display',
            'drorcr',
            'drorcr_display',
            'repline',
            'balbfwd',
        ]
        read_only_fields = ['id', 'type_display', 'drorcr_display']


class GLTranSerializer(serializers.ModelSerializer):
    """Serializer for GL Transactions"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)

    class Meta:
        model = GLTran
        fields = [
            'id',
            'accno',
            'batchno',
            'date',
            'time',
            'type',
            'type_display',
            'source',
            'source_display',
            'station',
            'reference',
            'details',
            'amount',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'type_display', 'source_display']


class GLTranListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GL Transaction list views"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)

    class Meta:
        model = GLTran
        fields = [
            'id',
            'accno',
            'batchno',
            'date',
            'type',
            'type_display',
            'source',
            'source_display',
            'reference',
            'details',
            'amount',
        ]
        read_only_fields = ['id', 'type_display', 'source_display']


class GLTranDetailSerializer(GLTranSerializer):
    """Detailed serializer for GL Transactions"""
    
    class Meta(GLTranSerializer.Meta):
        pass


class GLStJnlSerializer(serializers.ModelSerializer):
    """Serializer for GL Standing Journals"""
    drorcr_display = serializers.CharField(source='get_drorcr_display', read_only=True)
    
    class Meta:
        model = GLStJnl
        fields = [
            'id',
            'accno',
            'details',
            'drorcr',
            'drorcr_display',
            'amount',
            'frequency',
            'stperiod',
            'times',
            'timesbal',
            'nextperiod',
            'descriptor',
            'journalno',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'drorcr_display']


class GLStJnlListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GL Standing Journal list views"""
    drorcr_display = serializers.CharField(source='get_drorcr_display', read_only=True)
    
    class Meta:
        model = GLStJnl
        fields = [
            'id',
            'accno',
            'journalno',
            'details',
            'drorcr',
            'drorcr_display',
            'amount',
            'frequency',
            'stperiod',
            'nextperiod',
        ]
        read_only_fields = ['id', 'drorcr_display']


class GLStJnlDetailSerializer(GLStJnlSerializer):
    """Detailed serializer for GL Standing Journals"""
    
    class Meta(GLStJnlSerializer.Meta):
        pass


class GLSpreadSerializer(serializers.ModelSerializer):
    """Serializer for GL Spread Sheets"""
    
    class Meta:
        model = GLSpread
        fields = [
            'id',
            'accno',
            'name',
            'ytddebit',
            'ytdcredit',
            'curdebit',
            'curcredit',
            'curbuddeb',
            'curbudcred',
            'ytdbuddeb',
            'ytdbudcred',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'accno': {'validators': []},
        }


class GLSpreadDetailSerializer(GLSpreadSerializer):
    """Detailed serializer for GL Spread Sheets"""
    
    class Meta(GLSpreadSerializer.Meta):
        pass


class GLSpreadListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GL Spread Sheet list views"""
    
    class Meta:
        model = GLSpread
        fields = [
            'id',
            'accno',
            'name',
            'ytddebit',
            'ytdcredit',
            'curdebit',
            'curcredit',
        ]
        read_only_fields = ['id']