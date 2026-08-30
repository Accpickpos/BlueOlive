from rest_framework import serializers

from .models import (
    GLBatch,
    GLIntegrationLog,
    GLIntegrationSettings,
    GLMast,
    GLParam,
    GLRep,
    GLSpread,
    GLStJnl,
    GLTran,
)


class GLMastSerializer(serializers.ModelSerializer):
    """Serializer for General Ledger Master accounts"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    drorcr_display = serializers.CharField(source="get_drorcr_display", read_only=True)

    class Meta:
        model = GLMast
        fields = [
            "id",
            "accno",
            "name",
            "type",
            "type_display",
            "drorcr",
            "drorcr_display",
            "repline",
            "balbfwd",
            "period1",
            "period2",
            "period3",
            "period4",
            "period5",
            "period6",
            "period7",
            "period8",
            "period9",
            "period10",
            "period11",
            "period12",
            "period13",
            "budget1",
            "budget2",
            "budget3",
            "budget4",
            "budget5",
            "budget6",
            "budget7",
            "budget8",
            "budget9",
            "budget10",
            "budget11",
            "budget12",
            "lastyear1",
            "lastyear2",
            "lastyear3",
            "lastyear4",
            "lastyear5",
            "lastyear6",
            "lastyear7",
            "lastyear8",
            "lastyear9",
            "lastyear10",
            "lastyear11",
            "lastyear12",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "type_display",
            "drorcr_display",
        ]
        extra_kwargs = {
            "accno": {"validators": []},
        }


class GLMastDetailSerializer(GLMastSerializer):
    """Detailed serializer with all period and budget information grouped"""

    class Meta(GLMastSerializer.Meta):
        pass


class GLMastListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views with essential fields only"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    drorcr_display = serializers.CharField(source="get_drorcr_display", read_only=True)

    class Meta:
        model = GLMast
        fields = [
            "id",
            "accno",
            "name",
            "type",
            "type_display",
            "drorcr",
            "drorcr_display",
            "repline",
            "balbfwd",
        ]
        read_only_fields = ["id", "type_display", "drorcr_display"]


class GLTranSerializer(serializers.ModelSerializer):
    """Serializer for GL Transactions"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = GLTran
        fields = [
            "id",
            "accno",
            "batchno",
            "date",
            "time",
            "type",
            "type_display",
            "source",
            "source_display",
            "station",
            "reference",
            "details",
            "amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "type_display",
            "source_display",
        ]


class GLTranListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GL Transaction list views"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = GLTran
        fields = [
            "id",
            "accno",
            "batchno",
            "date",
            "type",
            "type_display",
            "source",
            "source_display",
            "reference",
            "details",
            "amount",
        ]
        read_only_fields = ["id", "type_display", "source_display"]


class GLTranDetailSerializer(GLTranSerializer):
    """Detailed serializer for GL Transactions"""

    class Meta(GLTranSerializer.Meta):
        pass


class GLStJnlSerializer(serializers.ModelSerializer):
    """Serializer for GL Standing Journals"""

    drorcr_display = serializers.CharField(source="get_drorcr_display", read_only=True)

    class Meta:
        model = GLStJnl
        fields = [
            "id",
            "accno",
            "details",
            "drorcr",
            "drorcr_display",
            "amount",
            "frequency",
            "stperiod",
            "times",
            "timesbal",
            "nextperiod",
            "descriptor",
            "journalno",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "drorcr_display"]


class GLStJnlListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GL Standing Journal list views"""

    drorcr_display = serializers.CharField(source="get_drorcr_display", read_only=True)

    class Meta:
        model = GLStJnl
        fields = [
            "id",
            "accno",
            "journalno",
            "details",
            "drorcr",
            "drorcr_display",
            "amount",
            "frequency",
            "stperiod",
            "nextperiod",
        ]
        read_only_fields = ["id", "drorcr_display"]


class GLStJnlDetailSerializer(GLStJnlSerializer):
    """Detailed serializer for GL Standing Journals"""

    class Meta(GLStJnlSerializer.Meta):
        pass


class GLSpreadSerializer(serializers.ModelSerializer):
    """Serializer for GL Spread Sheets"""

    class Meta:
        model = GLSpread
        fields = [
            "id",
            "accno",
            "name",
            "ytddebit",
            "ytdcredit",
            "curdebit",
            "curcredit",
            "curbuddeb",
            "curbudcred",
            "ytdbuddeb",
            "ytdbudcred",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "accno": {"validators": []},
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
            "id",
            "accno",
            "name",
            "ytddebit",
            "ytdcredit",
            "curdebit",
            "curcredit",
        ]
        read_only_fields = ["id"]


class GLBatchSerializer(serializers.ModelSerializer):
    """Serializer for GL Batch staging entries"""

    drorcr_display = serializers.CharField(source="get_drorcr_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = GLBatch
        fields = [
            "id",
            "accno",
            "batchno",
            "capturedat",
            "date",
            "time",
            "drorcr",
            "drorcr_display",
            "source",
            "source_display",
            "station",
            "reference",
            "details",
            "amount",
            "postdate",
            "postime",
            "period",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "postdate",
            "postime",
            "created_at",
            "updated_at",
            "drorcr_display",
            "source_display",
        ]


class GLBatchListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for GL Batch list views"""

    drorcr_display = serializers.CharField(source="get_drorcr_display", read_only=True)

    class Meta:
        model = GLBatch
        fields = [
            "id",
            "accno",
            "batchno",
            "date",
            "drorcr",
            "drorcr_display",
            "reference",
            "details",
            "amount",
            "postdate",
            "period",
        ]
        read_only_fields = ["id", "postdate", "drorcr_display"]


class GLBatchDetailSerializer(GLBatchSerializer):
    """Detailed serializer for GL Batch entries"""

    class Meta(GLBatchSerializer.Meta):
        pass


class GLRepSerializer(serializers.ModelSerializer):
    """Serializer for GL Report Format rows"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    fieldtype_display = serializers.CharField(
        source="get_fieldtype_display", read_only=True
    )
    printdet_display = serializers.CharField(
        source="get_printdet_display", read_only=True
    )

    class Meta:
        model = GLRep
        fields = [
            "id",
            "type",
            "type_display",
            "fieldtype",
            "fieldtype_display",
            "line",
            "printdet",
            "printdet_display",
            "name",
            "start",
            "endcalc",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "type_display",
            "fieldtype_display",
            "printdet_display",
        ]


class GLRepListSerializer(GLRepSerializer):
    """List serializer for GL Report Format rows (same shape — rows are small)"""

    class Meta(GLRepSerializer.Meta):
        pass


class GLRepDetailSerializer(GLRepSerializer):
    """Detailed serializer for GL Report Format rows"""

    class Meta(GLRepSerializer.Meta):
        pass


class GLParamSerializer(serializers.ModelSerializer):
    """Serializer for GL Parameters (singleton — pk is always 1)"""

    adjusted_display = serializers.CharField(
        source="get_adjusted_display", read_only=True
    )

    class Meta:
        model = GLParam
        fields = [
            "id",
            "startper",
            "batchno",
            "curperiod",
            "adjusted",
            "adjusted_display",
            "currentyr",
            "retained_earnings_accno",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "batchno",
            "curperiod",
            "adjusted",
            "currentyr",
            "created_at",
            "updated_at",
            "adjusted_display",
        ]


class GLIntegrationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for GL Integration Settings (singleton — pk is always 1)"""

    class Meta:
        model = GLIntegrationSettings
        fields = [
            "id",
            "debtors_control_accno",
            "creditors_control_accno",
            "bank_control_accno",
            "cash_control_accno",
            "sales_accno",
            "vat_output_accno",
            "vat_input_accno",
            "stock_control_accno",
            "stock_shrinkage_expense_accno",
            "stock_gain_income_accno",
            "debtors_interest_income_accno",
            "debtors_suspense_accno",
            "creditors_discount_received_accno",
            "creditors_suspense_accno",
            "cashbook_default_income_accno",
            "cashbook_default_expense_accno",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class GLIntegrationLogSerializer(serializers.ModelSerializer):
    """Serializer for GL Integration Log entries (read-only audit trail)"""

    source_app_display = serializers.CharField(
        source="get_source_app_display", read_only=True
    )

    class Meta:
        model = GLIntegrationLog
        fields = [
            "id",
            "source_app",
            "source_app_display",
            "source_model",
            "source_pk",
            "gl_batchno",
            "transferred_at",
        ]
        read_only_fields = fields
