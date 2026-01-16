from rest_framework import serializers
from .models import Tenant, Shop
from shop_users.models import ShopUser
from django.utils.text import slugify
import uuid
from django.contrib.auth.hashers import make_password
from tenancy.tenant_context import get_current_tenant
from .utils import create_tenant_database_postgres, register_tenant_connection

class TenantSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Tenant
        fields = ['name', 'phone', 'email', 'password', 'slug', 'subdomain', 'db_name', 'db_user', 'db_password', 'db_host', 'db_port']
        extra_kwargs = {
            'slug': {'required': False},
            'subdomain': {'read_only': True},
            'db_name': {'required': False},
            'db_user': {'required': False, 'default': 'postgres'},
            'db_password': {'required': True},  # Must provide password
            'db_host': {'required': False, 'default': 'localhost'},
            'db_port': {'required': False, 'default': 5432},
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        name = validated_data['name']
        if 'slug' not in validated_data or not validated_data['slug']:
            slug_candidate = slugify(name)
            if not slug_candidate:
                slug_candidate = f"tenant-{uuid.uuid4().hex[:8]}"
            validated_data['slug'] = slug_candidate
        if 'db_name' not in validated_data or not validated_data['db_name']:
            validated_data['db_name'] = slugify(name)
        validated_data['subdomain'] = validated_data['slug']
        tenant = super().create(validated_data)

        # Create the tenant database
        superuser_conn_info = {
            'host': validated_data['db_host'],
            'port': validated_data['db_port'],
            'user': validated_data['db_user'],
            'password': validated_data['db_password'],
            'dbname': 'postgres'  # Connect to default postgres DB to create new DB
        }
        create_tenant_database_postgres(tenant, superuser_conn_info)
        register_tenant_connection(tenant)

        # Create default shop
        shop = Shop.objects.create(
            tenant=tenant,
            name='Main',
            schema_name=f"{validated_data['slug']}_main",
            is_head_office=True
        )

        # Create admin user
        admin_user = ShopUser.objects.create(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=name,
            password=make_password(password),
            is_staff=True,
            is_superuser=False,  # Tenant admin, not global superuser
            role='ADMIN',  # Tenant admin role
            tenant_id=tenant.id
        )

        # Return tenant with additional info for frontend
        tenant_data = super().to_representation(tenant)
        tenant_data['admin_username'] = admin_user.username
        tenant_data['tenant_slug'] = tenant.slug
        return tenant_data


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ['id', 'name', 'schema_name', 'is_head_office']
        read_only_fields = ['schema_name']

    def create(self, validated_data):
        tenant = get_current_tenant()
        if not tenant:
            raise serializers.ValidationError("No tenant context")
        name = validated_data['name']
        schema_name = slugify(f"{tenant.slug}_{name}")
        validated_data['schema_name'] = schema_name
        validated_data['tenant'] = tenant
        try:
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Failed to create shop: {str(e)}")