# tenancy/serializers.py
import logging
import uuid

from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from shop_users.models import ShopUser
from tenancy.tenant_context import get_current_tenant

from .models import (
    Shop,
    ShopConfiguration,
    Subscription,
    SubscriptionPayment,
    SubscriptionPlan,
    Tenant,
)

logger = logging.getLogger(__name__)


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant model with automatic database setup.
    Uses default PostgreSQL credentials from Django settings for all tenants.
    """

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={"min_length": "Password must be at least 8 characters long."},
    )

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "password",
            "slug",
            "subdomain",
            "company_name",
            "company_address",
            "vat_number",
            "registration_number",
            "currency_symbol",
            "currency_code",
            "decimal_places",
            "default_interest_rate",
            "charge_interest_on_overdue",
            "financial_year_start_month",
            "db_name",
            "db_user",
            "db_password",
            "db_host",
            "db_port",
            "setup_status",
            "created_at",
        ]
        extra_kwargs = {
            "id": {"read_only": True},
            "slug": {"required": False},
            "subdomain": {"read_only": True},
            "db_name": {"required": False},
            "db_user": {"required": False, "default": "postgres"},
            "db_password": {"required": False, "write_only": True},  # Now optional
            "db_host": {"required": False, "default": "postgres"},
            "db_port": {"required": False, "default": 5432},
            "setup_status": {"read_only": True},
            "created_at": {"read_only": True},
        }

    def validate_password(self, value):
        """Validate password strength requirements"""
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one digit."
            )
        if not any(char.isalpha() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one letter."
            )
        return value

    def create(self, validated_data):
        """
        Create tenant with automatic database and migration setup.
        Uses default PostgreSQL credentials from Django settings.
        """
        from django.conf import settings

        password = validated_data.pop("password")
        name = validated_data["name"]

        # Use default PostgreSQL credentials from settings
        validated_data["db_user"] = settings.DATABASES["default"]["USER"]
        validated_data["db_password"] = settings.DATABASES["default"]["PASSWORD"]

        # Generate slug if not provided
        if "slug" not in validated_data or not validated_data["slug"]:
            slug_candidate = slugify(name)
            if not slug_candidate:
                slug_candidate = f"tenant-{uuid.uuid4().hex[:8]}"
            validated_data["slug"] = slug_candidate

        # Generate db_name if not provided
        if "db_name" not in validated_data or not validated_data["db_name"]:
            validated_data["db_name"] = f"{slugify(name)}_db"

        validated_data["subdomain"] = validated_data["slug"]

        # Create tenant row. Tenant's post_save signal queues async physical
        # database creation + migrations (tenancy.tasks.setup_tenant_database_async).
        # Hash the password now - it must never be sent as plaintext through the
        # Celery broker - and queue the default shop + admin user creation to run
        # once that database provisioning finishes (see complete_tenant_signup_async,
        # which itself retries until setup_status reflects the DB being ready).
        logger.info(f"Creating tenant: {name}")
        tenant = super().create(validated_data)
        logger.info(
            f"✓ Tenant created: {tenant.name} (setup_status={tenant.setup_status})"
        )

        admin_password_hash = make_password(password)
        from tenancy.tasks import complete_tenant_signup_async

        transaction.on_commit(
            lambda: complete_tenant_signup_async.delay(tenant.pk, admin_password_hash)
        )

        return tenant

    def to_representation(self, instance):
        """
        Custom representation with additional info.
        """
        data = super().to_representation(instance)

        # Add shop info if available
        shops = instance.shops.all()
        if shops.exists():
            data["shops"] = [
                {
                    "id": shop.id,
                    "name": shop.name,
                    "subdomain": shop.subdomain,
                    "is_head_office": shop.is_head_office,
                }
                for shop in shops
            ]

        # Add user count if database is accessible
        try:
            from tenancy.utils import register_tenant_connection

            register_tenant_connection(instance)
            user_count = (
                ShopUser.objects.using(instance.db_alias)
                .filter(tenant_id=instance.id)
                .count()
            )
            data["user_count"] = user_count
        except Exception:
            data["user_count"] = 0

        return data


class TenantListSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for Tenant model.
    Used for list and retrieve operations (excludes password field).
    """

    shops = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "slug",
            "subdomain",
            "company_name",
            "company_address",
            "vat_number",
            "registration_number",
            "currency_symbol",
            "currency_code",
            "decimal_places",
            "default_interest_rate",
            "charge_interest_on_overdue",
            "financial_year_start_month",
            "db_name",
            "setup_status",
            "created_at",
            "shops",
            "user_count",
        ]
        read_only_fields = [
            "id",
            "slug",
            "subdomain",
            "db_name",
            "setup_status",
            "created_at",
        ]

    def get_shops(self, obj):
        """
        Get shops for this tenant with basic info.
        """
        shops = obj.shops.all()
        return [
            {
                "id": shop.id,
                "name": shop.name,
                "subdomain": shop.subdomain,
                "is_head_office": shop.is_head_office,
            }
            for shop in shops
        ]

    def get_user_count(self, obj):
        """
        Get count of users in this tenant.
        """
        try:
            from tenancy.utils import register_tenant_connection

            register_tenant_connection(obj)
            return ShopUser.objects.using(obj.db_alias).filter(tenant_id=obj.id).count()
        except Exception:
            return 0


class ShopSerializer(serializers.ModelSerializer):
    """
    Serializer for Shop model with automatic schema setup.
    """

    class Meta:
        model = Shop
        fields = [
            "id",
            "name",
            "code",
            "address",
            "phone",
            "logo",
            "description",
            "schema_name",
            "subdomain",
            "is_head_office",
            "is_active",
            "setup_status",
            "created_at",
        ]
        read_only_fields = ["id", "schema_name", "setup_status", "created_at"]

    def create(self, validated_data):
        """
        Create shop with automatic schema setup.
        """
        tenant = get_current_tenant()
        if not tenant:
            raise serializers.ValidationError("No tenant context available")

        name = validated_data["name"]
        subdomain = validated_data.get("subdomain")

        # Auto-generate subdomain if not provided
        if not subdomain:
            subdomain = slugify(name)
            if not subdomain:
                subdomain = f"shop-{uuid.uuid4().hex[:8]}"
            validated_data["subdomain"] = subdomain

        # Generate schema name from tenant slug and shop subdomain
        schema_name = slugify(f"{tenant.slug}_{subdomain}")
        validated_data["schema_name"] = schema_name
        validated_data["tenant"] = tenant

        logger.info(f"Creating shop: {name} with schema: {schema_name}")

        # Create shop - signals will handle schema creation and migration
        shop = super().create(validated_data)

        logger.info(f"✓ Shop created: {shop.name}")
        return shop

    def update(self, instance, validated_data):
        """
        Update shop - regenerate schema_name if subdomain changes.
        """
        # If subdomain is being updated, regenerate schema_name
        if "subdomain" in validated_data:
            tenant = instance.tenant
            subdomain = validated_data["subdomain"]
            schema_name = slugify(f"{tenant.slug}_{subdomain}")
            validated_data["schema_name"] = schema_name

        return super().update(instance, validated_data)


class ShopConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for per-shop period-end configuration.
    """

    shop_name = serializers.CharField(source="shop.name", read_only=True)

    class Meta:
        model = ShopConfiguration
        fields = [
            "id",
            "shop",
            "shop_name",
            # Period end tracking
            "last_day_end_date",
            "last_month_end_date",
            "last_year_end_date",
            # Scheduling settings
            "enable_auto_day_end",
            "day_end_time",
            "day_end_day_of_week",
            "enable_auto_month_end",
            "month_end_day",
            "month_end_time",
            "enable_auto_year_end",
            "year_end_month",
            "year_end_day",
            "year_end_time",
            # Accounting period
            "current_financial_year",
            "current_period",
        ]
        read_only_fields = [
            "id",
            "last_day_end_date",
            "last_month_end_date",
            "last_year_end_date",
        ]


# ============================================================================
# SUBSCRIPTION SERIALIZERS
# ============================================================================


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for subscription plans.
    """

    billing_period_display = serializers.CharField(
        source="get_billing_period_days_display", read_only=True
    )

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "price",
            "setup_fee",
            "billing_period_days",
            "billing_period_display",
            "max_shops",
            "max_users",
            "max_invoices_per_month",
            "features",
            "is_active",
            "is_trial",
            "sort_order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SubscriptionPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer for subscription payments.
    """

    status_display = serializers.CharField(source="get_status_display", read_only=True)
    payment_method_display = serializers.CharField(
        source="get_payment_method_display", read_only=True
    )

    class Meta:
        model = SubscriptionPayment
        fields = [
            "id",
            "subscription",
            "amount",
            "currency",
            "payment_method",
            "payment_method_display",
            "status",
            "status_display",
            "gateway_payment_id",
            "gateway_reference",
            "paid_at",
            "failed_at",
            "description",
            "invoice_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for subscriptions.
    """

    plan = SubscriptionPlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(), source="plan", write_only=True
    )
    tenant_name = serializers.CharField(source="tenant.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    # Computed properties
    is_active_display = serializers.BooleanField(source="is_active", read_only=True)
    is_trial_display = serializers.BooleanField(source="is_trial", read_only=True)
    is_expired_display = serializers.BooleanField(source="is_expired", read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)

    payments = SubscriptionPaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "plan",
            "plan_id",
            "status",
            "status_display",
            "start_date",
            "end_date",
            "trial_end_date",
            "cancelled_at",
            "auto_renew",
            "current_period_start",
            "current_period_end",
            "invoices_this_period",
            "gateway_customer_id",
            "gateway_subscription_id",
            # Computed
            "is_active_display",
            "is_trial_display",
            "is_expired_display",
            "days_remaining",
            # Related
            "payments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        """
        Create a new subscription.
        Sets up the initial billing period based on the plan.
        """
        from datetime import timedelta

        from django.utils import timezone

        plan = validated_data["plan"]
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=plan.billing_period_days)

        # Check if there's a trial period
        trial_end_date = None
        status = "ACTIVE"

        # If it's a trial plan, set trial end date
        if plan.is_trial:
            trial_end_date = start_date + timedelta(days=14)  # 14-day trial
            status = "TRIAL"

        validated_data["start_date"] = start_date
        validated_data["end_date"] = end_date
        validated_data["trial_end_date"] = trial_end_date
        validated_data["status"] = status
        validated_data["current_period_start"] = start_date
        validated_data["current_period_end"] = end_date

        return super().create(validated_data)


class SubscriptionDetailSerializer(SubscriptionSerializer):
    """
    Detailed serializer for subscriptions with full information.
    Includes tenant and plan details.
    """

    from tenancy.serializers import TenantSerializer

    tenant_detail = TenantSerializer(source="tenant", read_only=True)
    plan_detail = SubscriptionPlanSerializer(source="plan", read_only=True)

    class Meta(SubscriptionSerializer.Meta):
        fields = SubscriptionSerializer.Meta.fields + [
            "tenant_detail",
            "plan_detail",
        ]


class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new subscriptions.
    """

    class Meta:
        model = Subscription
        fields = [
            "tenant",
            "plan",
            "auto_renew",
            "gateway_customer_id",
            "gateway_subscription_id",
        ]

    def create(self, validated_data):
        """
        Create a new subscription with proper billing period setup.
        """
        from datetime import timedelta

        from django.utils import timezone

        tenant = validated_data["tenant"]
        plan = validated_data["plan"]

        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=plan.billing_period_days)

        # Check if there's a trial period
        trial_end_date = None
        status = "ACTIVE"

        if plan.is_trial:
            trial_end_date = start_date + timedelta(days=14)
            status = "TRIAL"

        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            status=status,
            start_date=start_date,
            end_date=end_date,
            trial_end_date=trial_end_date,
            current_period_start=start_date,
            current_period_end=end_date,
            auto_renew=validated_data.get("auto_renew", True),
            gateway_customer_id=validated_data.get("gateway_customer_id", ""),
            gateway_subscription_id=validated_data.get("gateway_subscription_id", ""),
        )

        return subscription


class SubscriptionCancelSerializer(serializers.Serializer):
    """
    Serializer for cancelling a subscription.
    """

    immediately = serializers.BooleanField(
        default=False,
        help_text="If true, cancel immediately. If false, cancel at end of billing period.",
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text="Reason for cancellation",
    )
