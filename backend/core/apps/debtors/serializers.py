"""
Debtors serializers.
Comprehensive serializers for all debtor-related models.
Based on DMAST, DEBTRAN, DEBTOPEN, DPDC, DEBTORAUD tables.
"""

import logging
from decimal import Decimal

from apps.common.serializers import AuditFieldsMixin, BaseModelSerializer
from django.db import transaction
from rest_framework import serializers

from .models import Darea, Debtopen, Debtor, DebtorAudit, DebtorTransaction, Dpdc

logger = logging.getLogger(__name__)


class DebtorLookupSerializer(serializers.ModelSerializer):
    """
    Thin serializer for the debtor typeahead/lookup endpoint
    (DebtorViewSet.lookup, via LookupActionMixin) — DebtorListSerializer is
    too heavy for a search dropdown (duplicates ~30 fields under two names
    each). Exposes both the raw model field names and the friendly aliases
    the frontend picker components expect, so no field-name-guessing
    fallback chain is needed on the frontend side.
    """

    account_number = serializers.IntegerField(source="dno", read_only=True)
    name = serializers.CharField(source="dname", read_only=True)
    balance = serializers.SerializerMethodField()
    credit_limit = serializers.DecimalField(
        source="dclimit", max_digits=12, decimal_places=2, read_only=True
    )
    is_blocked = serializers.SerializerMethodField()

    class Meta:
        model = Debtor
        fields = [
            "id",
            "dno",
            "dname",
            "dsname",
            "dtel",
            "acctype",
            "blockflag",
            "account_number",
            "name",
            "balance",
            "credit_limit",
            "is_blocked",
        ]

    def get_balance(self, obj):
        try:
            return float(obj.total_balance)
        except (AttributeError, TypeError):
            return 0

    def get_is_blocked(self, obj):
        try:
            return obj.is_blocked
        except (AttributeError, TypeError):
            return False


class DebtorListSerializer(serializers.ModelSerializer):
    """Serializer for debtor list view (DMAST)."""

    id = serializers.IntegerField(source="dno", read_only=True)
    total_balance = serializers.SerializerMethodField()
    overdue_balance = serializers.SerializerMethodField()
    is_blocked_flag = serializers.SerializerMethodField()

    # Backward compatibility aliases for frontend
    customer_number = serializers.IntegerField(source="dno", read_only=True)
    name = serializers.CharField(source="dname", read_only=True)
    short_name = serializers.CharField(source="dsname", read_only=True)
    contact_person = serializers.CharField(source="dcontact", read_only=True)
    phone = serializers.CharField(source="dtel", read_only=True)
    phone2 = serializers.CharField(source="dtel2", read_only=True)
    fax = serializers.CharField(source="dfax", read_only=True)
    area_code = serializers.IntegerField(source="darea", read_only=True)
    account_type = serializers.CharField(source="acctype", read_only=True)
    credit_limit = serializers.DecimalField(
        source="dclimit", max_digits=12, decimal_places=2, read_only=True
    )
    balance_current = serializers.DecimalField(
        source="dcrnt", max_digits=12, decimal_places=2, read_only=True
    )
    balance_brought_forward = serializers.DecimalField(
        source="dbalbfwd", max_digits=12, decimal_places=2, read_only=True
    )

    class Meta:
        model = Debtor
        fields = [
            "id",
            "dno",
            "dname",
            "dsname",
            "dcontact",
            "dtel",
            "dtel2",
            "dfax",
            "email",
            "darea",
            "acctype",
            "dclimit",
            "dcrnt",
            "total_balance",
            "overdue_balance",
            "is_blocked_flag",
            "is_active",
            "created_at",
            # Backward compatibility aliases
            "customer_number",
            "name",
            "short_name",
            "contact_person",
            "phone",
            "phone2",
            "fax",
            "area_code",
            "account_type",
            "credit_limit",
            "balance_current",
            "balance_brought_forward",
        ]

    def to_representation(self, instance):
        """Override to add error handling for serialization."""
        try:
            return super().to_representation(instance)
        except Exception as e:
            logger.error(
                f"[DebtorListSerializer] Error serializing debtor {instance.dno}: {type(e).__name__}: {str(e)}"
            )
            raise

    def get_total_balance(self, obj):
        """Calculate total balance."""
        try:
            return float(obj.total_balance)
        except (AttributeError, TypeError) as e:
            logger.warning(
                f"[DebtorListSerializer] Error getting total_balance for debtor {getattr(obj, 'dno', 'unknown')}: {str(e)}"
            )
            return 0

    def get_overdue_balance(self, obj):
        """Calculate overdue balance (> 30 days)."""
        try:
            return float(obj.overdue_balance)
        except (AttributeError, TypeError) as e:
            logger.warning(
                f"[DebtorListSerializer] Error getting overdue_balance for debtor {getattr(obj, 'dno', 'unknown')}: {str(e)}"
            )
            return 0

    def get_is_blocked_flag(self, obj):
        """Get block status."""
        try:
            return obj.is_blocked
        except (AttributeError, TypeError) as e:
            logger.warning(
                f"[DebtorListSerializer] Error getting is_blocked for debtor {getattr(obj, 'dno', 'unknown')}: {str(e)}"
            )
            return False


class DebtorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for debtor (DMAST)."""

    id = serializers.IntegerField(source="dno", read_only=True)
    total_balance = serializers.SerializerMethodField()
    overdue_balance = serializers.SerializerMethodField()
    is_blocked_flag = serializers.SerializerMethodField()
    available_credit = serializers.SerializerMethodField()
    credit_utilization_pct = serializers.SerializerMethodField()

    # Backward compatibility
    customer_number = serializers.IntegerField(source="dno", read_only=True)
    name = serializers.CharField(source="dname", read_only=True)
    short_name = serializers.CharField(source="dsname", read_only=True)
    contact_person = serializers.CharField(source="dcontact", read_only=True)
    phone = serializers.CharField(source="dtel", read_only=True)
    phone2 = serializers.CharField(source="dtel2", read_only=True)
    fax = serializers.CharField(source="dfax", read_only=True)
    account_type = serializers.CharField(source="acctype", read_only=True)
    price_level = serializers.IntegerField(source="price", read_only=True)
    payment_terms = serializers.IntegerField(source="terms", read_only=True)
    discount_percentage = serializers.DecimalField(
        source="ddiscper", max_digits=10, decimal_places=2, read_only=True
    )
    prompt_payment_discount = serializers.DecimalField(
        source="pdisc", max_digits=10, decimal_places=2, read_only=True
    )
    discount_printable = serializers.CharField(read_only=True)
    credit_limit = serializers.DecimalField(
        source="dclimit", max_digits=12, decimal_places=2, read_only=True
    )
    area_code = serializers.IntegerField(source="darea", read_only=True)
    interest_flag = serializers.CharField(source="dintflag", read_only=True)
    block_flag = serializers.CharField(source="blockflag", read_only=True)
    positive_balance_only = serializers.CharField(source="dposbal", read_only=True)
    balance_brought_forward = serializers.DecimalField(
        source="dbalbfwd", max_digits=12, decimal_places=2, read_only=True
    )
    balance_current = serializers.DecimalField(
        source="dcrnt", max_digits=12, decimal_places=2, read_only=True
    )
    balance_30_days = serializers.DecimalField(
        source="d30", max_digits=12, decimal_places=2, read_only=True
    )
    balance_60_days = serializers.DecimalField(
        source="d60", max_digits=12, decimal_places=2, read_only=True
    )
    balance_90_days = serializers.DecimalField(
        source="d90", max_digits=12, decimal_places=2, read_only=True
    )
    balance_120_days = serializers.DecimalField(
        source="d120", max_digits=12, decimal_places=2, read_only=True
    )
    balance_150_days = serializers.DecimalField(
        source="d150", max_digits=12, decimal_places=2, read_only=True
    )
    balance_180_days = serializers.DecimalField(
        source="d180", max_digits=12, decimal_places=2, read_only=True
    )
    sales_month = serializers.DecimalField(
        source="dsalesm", max_digits=12, decimal_places=2, read_only=True
    )
    sales_year = serializers.DecimalField(
        source="dsalesy", max_digits=12, decimal_places=2, read_only=True
    )
    profit_month = serializers.DecimalField(
        source="dprofitm", max_digits=12, decimal_places=2, read_only=True
    )
    profit_year = serializers.DecimalField(
        source="dprofity", max_digits=12, decimal_places=2, read_only=True
    )
    last_payment_amount = serializers.DecimalField(
        source="damtlpd", max_digits=12, decimal_places=2, read_only=True
    )
    last_payment_date = serializers.DateField(
        source="ddatlpd", read_only=True, allow_null=True
    )
    date_opened = serializers.DateField(
        source="dateopened", read_only=True, allow_null=True
    )

    class Meta:
        model = Debtor
        fields = [
            "id",
            "dno",
            "dname",
            "dsname",
            "dcontact",
            "dtel",
            "dtel2",
            "dfax",
            "email",
            "address_line1",
            "address_line2",
            "address_line3",
            "postal_code",
            "delivery_address1",
            "delivery_address2",
            "delivery_address3",
            "delivery_address4",
            "dtaxno",
            "vatref",
            "acctype",
            "price",
            "terms",
            "ddiscper",
            "pdisc",
            "discount_printable",
            "dclimit",
            "darea",
            "dintflag",
            "blockflag",
            "dposbal",
            "dbalbfwd",
            "dcrnt",
            "d30",
            "d60",
            "d90",
            "d120",
            "d150",
            "d180",
            "dsalesm",
            "dsalesy",
            "dprofitm",
            "dprofity",
            "damtlpd",
            "ddatlpd",
            "dateopened",
            "dscontra",
            "dlimit Adjdate",
            "lastpayment_date",
            "total_balance",
            "overdue_balance",
            "is_blocked_flag",
            "available_credit",
            "credit_utilization_pct",
            "is_active",
            "notes",
            "created_at",
            "updated_at",
            # Backward compatibility
            "customer_number",
            "name",
            "short_name",
            "contact_person",
            "phone",
            "phone2",
            "fax",
            "account_type",
            "price_level",
            "payment_terms",
            "discount_percentage",
            "prompt_payment_discount",
            "credit_limit",
            "area_code",
            "interest_flag",
            "block_flag",
            "positive_balance_only",
            "balance_brought_forward",
            "balance_current",
            "balance_30_days",
            "balance_60_days",
            "balance_90_days",
            "balance_120_days",
            "balance_150_days",
            "balance_180_days",
            "sales_month",
            "sales_year",
            "profit_month",
            "profit_year",
            "last_payment_amount",
            "last_payment_date",
        ]

    def get_total_balance(self, obj):
        try:
            return obj.total_balance
        except (AttributeError, TypeError):
            return Decimal(0)

    def get_overdue_balance(self, obj):
        try:
            return obj.overdue_balance
        except (AttributeError, TypeError):
            return Decimal(0)

    def get_is_blocked_flag(self, obj):
        try:
            return obj.is_blocked
        except (AttributeError, TypeError):
            return False

    def get_available_credit(self, obj):
        try:
            return float(obj.dclimit) - float(obj.total_balance)
        except (AttributeError, TypeError, ZeroDivisionError):
            return 0

    def get_credit_utilization_pct(self, obj):
        try:
            if obj.dclimit > 0:
                return float(obj.total_balance) / float(obj.dclimit) * 100
            return 0
        except (AttributeError, TypeError, ZeroDivisionError):
            return 0


class DebtorCreateUpdateSerializer(serializers.Serializer):
    """Serializer for creating/updating debtor (DMAST)."""

    # Frontend fields
    customer_number = serializers.IntegerField(required=False, allow_null=True)
    name = serializers.CharField(required=False, allow_blank=True)
    short_name = serializers.CharField(required=False, allow_blank=True)
    contact_person = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    phone2 = serializers.CharField(required=False, allow_blank=True)
    fax = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    account_type = serializers.CharField(required=False, allow_blank=True)
    price_level = serializers.IntegerField(required=False, allow_null=True)
    payment_terms = serializers.IntegerField(required=False, allow_null=True)
    discount_percentage = serializers.DecimalField(
        required=False, allow_null=True, max_digits=10, decimal_places=2
    )
    prompt_payment_discount = serializers.DecimalField(
        required=False, allow_null=True, max_digits=10, decimal_places=2
    )
    credit_limit = serializers.DecimalField(
        required=False, allow_null=True, max_digits=12, decimal_places=2
    )
    area_code = serializers.IntegerField(required=False, allow_null=True)
    tax_number = serializers.CharField(required=False, allow_blank=True)
    vat_ref = serializers.CharField(required=False, allow_blank=True)
    # Boolean fields - frontend sends true/false
    interest_flag = serializers.BooleanField(required=False, default=False)
    block_flag = serializers.BooleanField(required=False, default=False)
    positive_balance_only = serializers.BooleanField(required=False, default=False)
    discount_printable = serializers.BooleanField(required=False, default=False)
    is_active = serializers.BooleanField(required=False, default=True)
    # Address fields
    address_line1 = serializers.CharField(required=False, allow_blank=True)
    address_line2 = serializers.CharField(required=False, allow_blank=True)
    address_line3 = serializers.CharField(required=False, allow_blank=True)
    postal_code = serializers.CharField(required=False, allow_blank=True)
    delivery_address1 = serializers.CharField(required=False, allow_blank=True)
    delivery_address2 = serializers.CharField(required=False, allow_blank=True)
    delivery_address3 = serializers.CharField(required=False, allow_blank=True)
    delivery_address4 = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        print(
            f"[DebtorSerializer] validate() called with attrs keys: {list(attrs.keys())}"
        )
        import logging

        logger = logging.getLogger(__name__)
        logger.error(
            f"[DebtorSerializer] validate() called with attrs keys: {list(attrs.keys())}"
        )

        # Map frontend fields to model fields
        field_mapping = {
            "customer_number": "dno",
            "name": "dname",
            "short_name": "dsname",
            "contact_person": "dcontact",
            "phone": "dtel",
            "phone2": "dtel2",
            "fax": "dfax",
            "account_type": "acctype",
            "price_level": "price",
            "payment_terms": "terms",
            "discount_percentage": "ddiscper",
            "prompt_payment_discount": "pdisc",
            "credit_limit": "dclimit",
            "area_code": "darea",
            "tax_number": "dtaxno",
            "vat_ref": "vatref",
        }

        # Apply field mapping
        for frontend_name, model_name in field_mapping.items():
            if frontend_name in attrs:
                attrs[model_name] = attrs.pop(frontend_name)

        print(f"[DebtorSerializer] After mapping, attrs keys: {list(attrs.keys())}")

        # Convert boolean to Y/N for legacy fields
        bool_fields = {
            "interest_flag": "dintflag",
            "block_flag": "blockflag",
            "positive_balance_only": "dposbal",
        }

        for frontend_name, model_name in bool_fields.items():
            if frontend_name in attrs and attrs[frontend_name] is not None:
                attrs[model_name] = "Y" if attrs[frontend_name] else "N"
                attrs.pop(frontend_name, None)

        # Handle discount_printable
        if "discount_printable" in attrs and attrs["discount_printable"] is not None:
            attrs["discount_printable"] = "Y" if attrs["discount_printable"] else "N"

        logger.error(
            f"[DebtorSerializer] After mapping, attrs keys: {list(attrs.keys())}"
        )

        # Auto-generate dno if not provided
        if "dno" not in attrs or attrs.get("dno") is None:
            from django.db.models import Max
            from tenancy.tenant_context import get_current_tenant

            tenant = get_current_tenant()
            if tenant:
                max_dno = Debtor.objects.using(tenant.db_alias).aggregate(Max("dno"))[
                    "dno__max"
                ]
                attrs["dno"] = (max_dno or 0) + 1
            else:
                max_dno = Debtor.objects.aggregate(Max("dno"))["dno__max"]
                attrs["dno"] = (max_dno or 0) + 1

            logger.info(
                f"[DebtorSerializer] Auto-generated dno={attrs['dno']} (max was {max_dno})"
            )
        else:
            # User provided dno - check for duplicates
            provided_dno = attrs.get("dno")
            from tenancy.tenant_context import get_current_tenant

            tenant = get_current_tenant()

            # Check if this dno already exists
            if tenant:
                exists = (
                    Debtor.objects.using(tenant.db_alias)
                    .filter(dno=provided_dno)
                    .exists()
                )
            else:
                exists = Debtor.objects.filter(dno=provided_dno).exists()

            if exists:
                logger.warning(
                    f"[DebtorSerializer] Debtor with dno={provided_dno} already exists!"
                )
                # Try to find next available number
                if tenant:
                    max_dno = Debtor.objects.using(tenant.db_alias).aggregate(
                        Max("dno")
                    )["dno__max"]
                else:
                    max_dno = Debtor.objects.aggregate(Max("dno"))["dno__max"]
                attrs["dno"] = (max_dno or 0) + 1
                logger.info(
                    f"[DebtorSerializer] Using next available dno={attrs['dno']} instead"
                )

        print(
            f"[DebtorSerializer] After dno generation, attrs: dno={attrs.get('dno')}, dname={attrs.get('dname')}"
        )

        # Handle dname - ensure it's not empty
        if not attrs.get("dname") and attrs.get("dsname"):
            attrs["dname"] = attrs["dsname"]

        # Set defaults for required fields that can't be null
        attrs.setdefault("dtel2", "")  # tel2 is required in DB
        attrs.setdefault("dcrnt", Decimal("0.00"))
        attrs.setdefault("d30", Decimal("0.00"))
        attrs.setdefault("d60", Decimal("0.00"))
        attrs.setdefault("d90", Decimal("0.00"))
        attrs.setdefault("d120", Decimal("0.00"))
        attrs.setdefault("d150", Decimal("0.00"))
        attrs.setdefault("d180", Decimal("0.00"))
        attrs.setdefault("dbalbfwd", Decimal("0.00"))
        attrs.setdefault("dsalesm", Decimal("0.00"))
        attrs.setdefault("dsalesy", Decimal("0.00"))
        attrs.setdefault("dprofitm", Decimal("0.00"))
        attrs.setdefault("dprofity", Decimal("0.00"))
        attrs.setdefault("damtlpd", Decimal("0.00"))

        logger.error(
            f"[DebtorSerializer] Final attrs: dno={attrs.get('dno')}, dname={attrs.get('dname')}"
        )

        return attrs

    def create(self, validated_data):
        print(f"[DebtorSerializer] create() called with: {validated_data}")

        # Use objects.create but first ensure all CharField fields have values
        # Create a copy to avoid modifying the original
        data = dict(validated_data)

        # List of fields that need to be empty strings, not None - set defaults explicitly
        string_fields = [
            "dtel2",
            "dfax",
            "dsname",
            "dcontact",
            "email",
            "address_line1",
            "address_line2",
            "address_line3",
            "postal_code",
            "delivery_address1",
            "delivery_address2",
            "delivery_address3",
            "delivery_address4",
            "dtaxno",
            "vatref",
            "notes",
            "acctype",
            "blockflag",
            "dintflag",
            "dposbal",
        ]

        for field in string_fields:
            if field not in data or data.get(field) is None:
                data[field] = ""
                print(f"[DebtorSerializer] Set {field} to empty string in data")

        # Also ensure Decimal fields have defaults
        decimal_fields = [
            "ddiscper",
            "pdisc",
            "dclimit",
            "dcrnt",
            "d30",
            "d60",
            "d90",
            "d120",
            "d150",
            "d180",
            "dbalbfwd",
            "dsalesm",
            "dsalesy",
            "dprofitm",
            "dprofity",
            "damtlpd",
        ]
        for field in decimal_fields:
            if field not in data or data.get(field) is None:
                data[field] = Decimal("0.00")

        print(
            f"[DebtorSerializer] Final data before create: dtel2={repr(data.get('dtel2'))}"
        )

        # Set dtel2 to empty string - either from form or default
        # The database now has DEFAULT '' so this should work
        if not data.get("dtel2"):
            data["dtel2"] = ""

        # Create model instance and save
        logger.debug(
            f"[DebtorSerializer] Creating Debtor with dtel2={repr(data.get('dtel2'))}"
        )
        debtor = Debtor(**data)

        logger.debug(
            f"[DebtorSerializer] After Debtor() creation, dtel2={repr(debtor.dtel2)}"
        )

        debtor.save()
        logger.debug("[DebtorSerializer] After debtor.save(), dtel2 in db will be set")
        return debtor

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# Rest of the serializers would follow the same pattern...
# For brevity, I'll include placeholders that reference the original model fields


class DebtorTransactionSerializer(serializers.ModelSerializer):
    """Serializer for debtor transactions."""

    class Meta:
        model = DebtorTransaction
        fields = "__all__"


class DebteopenSerializer(serializers.ModelSerializer):
    """Serializer for open items."""

    class Meta:
        model = Debtopen
        fields = "__all__"


class DpdcSerializer(serializers.ModelSerializer):
    """Serializer for post-dated cheques."""

    debtor_id = serializers.IntegerField(source="dno_id")
    expected_date = serializers.DateField(source="date")

    class Meta:
        model = Dpdc
        fields = [
            "id",
            "debtor_id",
            "cheque_number",
            "bank",
            "amount",
            "expected_date",
            "received_date",
            "cleared_date",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]

    def update(self, instance, validated_data):
        # updateStatus() on the frontend sends a `status_date` alongside the
        # new status — route it to whichever date field matches the transition.
        status_date = self.initial_data.get("status_date")
        new_status = validated_data.get("status")
        if status_date and new_status == "RECEIVED":
            instance.received_date = status_date
        elif status_date and new_status == "CLEARED":
            instance.cleared_date = status_date
        return super().update(instance, validated_data)


class DebtorAuditSerializer(serializers.ModelSerializer):
    """Serializer for audit records."""

    class Meta:
        model = DebtorAudit
        fields = "__all__"


class DareaSerializer(serializers.ModelSerializer):
    """Serializer for debtor areas/sales regions."""

    class Meta:
        model = Darea
        fields = "__all__"


class AgeAnalysisSerializer(serializers.Serializer):
    """Serializer for age analysis data."""

    customer_number = serializers.IntegerField()
    name = serializers.CharField()
    total_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    current = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_30 = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_60 = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_90 = serializers.DecimalField(max_digits=12, decimal_places=2)
    days_120_plus = serializers.DecimalField(max_digits=12, decimal_places=2)


class DebtorSummarySerializer(serializers.Serializer):
    """Serializer for debtor summary statistics."""

    total_debtors = serializers.IntegerField()
    active_debtors = serializers.IntegerField()
    blocked_debtors = serializers.IntegerField()
    total_balance = serializers.FloatField()
    current_balance = serializers.FloatField()
    overdue_30 = serializers.FloatField()
    overdue_60 = serializers.FloatField()
    overdue_90 = serializers.FloatField()
    overdue_120_plus = serializers.FloatField()


class DebtranListSerializer(serializers.ModelSerializer):
    """Serializer for debtor transaction list view."""

    class Meta:
        model = DebtorTransaction
        fields = [
            "id",
            "transaction_date",
            "transaction_type",
            "reference",
            "debit",
            "credit",
            "outstanding",
        ]


class DebtOpenListSerializer(serializers.ModelSerializer):
    """Serializer for open item list view."""

    class Meta:
        model = Debtopen
        fields = [
            "id",
            "trans_date",
            "reference",
            "debit",
            "credit",
            "outstanding",
            "allocated",
        ]
