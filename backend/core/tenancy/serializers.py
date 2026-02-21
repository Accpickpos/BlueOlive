# tenancy/serializers.py
from rest_framework import serializers
from .models import Tenant, Shop
from shop_users.models import ShopUser
from django.utils.text import slugify
import uuid
from django.contrib.auth.hashers import make_password
from tenancy.tenant_context import get_current_tenant
import logging

logger = logging.getLogger(__name__)


class TenantSerializer(serializers.ModelSerializer):
    """
    Serializer for Tenant model with automatic database setup.
    Uses default PostgreSQL credentials from Django settings for all tenants.
    """
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        error_messages={
            'min_length': 'Password must be at least 8 characters long.'
        }
    )

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'phone', 'email', 'password', 'slug', 'subdomain', 
                  'db_name', 'db_user', 'db_password', 'db_host', 'db_port', 'created_at']
        extra_kwargs = {
            'id': {'read_only': True},
            'slug': {'required': False},
            'subdomain': {'read_only': True},
            'db_name': {'required': False},
            'db_user': {'required': False, 'default': 'postgres'},
            'db_password': {'required': False, 'write_only': True},  # Now optional
            'db_host': {'required': False, 'default': 'localhost'},
            'db_port': {'required': False, 'default': 5432},
            'created_at': {'read_only': True},
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
        
        password = validated_data.pop('password')
        name = validated_data['name']
        
        # Use default PostgreSQL credentials from settings
        validated_data['db_user'] = settings.DATABASES['default']['USER']
        validated_data['db_password'] = settings.DATABASES['default']['PASSWORD']
        
        # Generate slug if not provided
        if 'slug' not in validated_data or not validated_data['slug']:
            slug_candidate = slugify(name)
            if not slug_candidate:
                slug_candidate = f"tenant-{uuid.uuid4().hex[:8]}"
            validated_data['slug'] = slug_candidate
        
        # Generate db_name if not provided
        if 'db_name' not in validated_data or not validated_data['db_name']:
            validated_data['db_name'] = f"{slugify(name)}_db"
        
        validated_data['subdomain'] = validated_data['slug']
        
        # Create tenant - signals will handle database creation and migration
        logger.info(f"Creating tenant: {name}")
        tenant = super().create(validated_data)
        logger.info(f"✓ Tenant created: {tenant.name}")

        try:
            # Give signals time to complete
            import time
            time.sleep(1)
            
            # Create default shop - signals will handle schema creation and migration
            logger.info("Creating default shop...")
            shop = Shop.objects.create(
                tenant=tenant,
                name='Main Office',
                schema_name=f"{validated_data['slug']}_main",
                subdomain='main',
                is_head_office=True
            )
            logger.info(f"✓ Default shop created: {shop.name}")
            
            # Give signals time to complete
            time.sleep(1)

            # Run migrations on tenant database before creating users
            logger.info("Running migrations on tenant database...")
            from tenancy.utils import register_tenant_connection
            from tenancy.shop_manager import migrate_tenant_database
            register_tenant_connection(tenant)
            migrate_tenant_database(tenant)
            logger.info("✓ Tenant database migrations completed")

            # Give migrations time to complete
            time.sleep(1)

            # Create admin user in tenant database
            logger.info("Creating admin user...")
            
            # Create in tenant database (authentication backend knows how to find it there)
            admin_user = ShopUser.objects.using(tenant.db_alias).create(
                username=validated_data['email'],
                email=validated_data['email'],
                first_name=name.split()[0] if name else '',
                password=make_password(password),
                is_staff=True,
                is_superuser=False,
                role='ADMIN',
                tenant_id=tenant.id,  # Use tenant_id instead of tenant
                is_active=True,
            )
            logger.info(f"✓ Admin user created: {admin_user.username}")
            
        except Exception as e:
            logger.error(f"Error in post-tenant setup: {str(e)}")
            import traceback
            traceback.print_exc()
            raise serializers.ValidationError(
                f"Tenant created but setup incomplete: {str(e)}"
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
            data['shops'] = [
                {
                    'id': shop.id,
                    'name': shop.name,
                    'subdomain': shop.subdomain,
                    'is_head_office': shop.is_head_office,
                }
                for shop in shops
            ]
        
        # Add user count if database is accessible
        try:
            from tenancy.utils import register_tenant_connection
            register_tenant_connection(instance)
            user_count = ShopUser.objects.using(instance.db_alias).filter(tenant_id=instance.id).count()
            data['user_count'] = user_count
        except:
            data['user_count'] = 0
        
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
        fields = ['id', 'name', 'phone', 'email', 'slug', 'subdomain',
                  'db_name', 'created_at', 'shops', 'user_count']
        read_only_fields = ['id', 'slug', 'subdomain', 'db_name', 'created_at']

    def get_shops(self, obj):
        """
        Get shops for this tenant with basic info.
        """
        shops = obj.shops.all()
        return [
            {
                'id': shop.id,
                'name': shop.name,
                'subdomain': shop.subdomain,
                'is_head_office': shop.is_head_office,
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
        except:
            return 0


class ShopSerializer(serializers.ModelSerializer):
    """
    Serializer for Shop model with automatic schema setup.
    """
    
    class Meta:
        model = Shop
        fields = ['id', 'name', 'code', 'address', 'phone', 'description', 
                  'schema_name', 'subdomain', 'is_head_office', 'is_active', 'setup_status', 'created_at']
        read_only_fields = ['id', 'schema_name', 'setup_status', 'created_at']

    def create(self, validated_data):
        """
        Create shop with automatic schema setup.
        """
        tenant = get_current_tenant()
        if not tenant:
            raise serializers.ValidationError("No tenant context available")
        
        name = validated_data['name']
        subdomain = validated_data.get('subdomain')
        
        # Auto-generate subdomain if not provided
        if not subdomain:
            subdomain = slugify(name)
            if not subdomain:
                subdomain = f"shop-{uuid.uuid4().hex[:8]}"
            validated_data['subdomain'] = subdomain
        
        # Generate schema name from tenant slug and shop subdomain
        schema_name = slugify(f"{tenant.slug}_{subdomain}")
        validated_data['schema_name'] = schema_name
        validated_data['tenant'] = tenant
        
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
        if 'subdomain' in validated_data:
            tenant = instance.tenant
            subdomain = validated_data['subdomain']
            schema_name = slugify(f"{tenant.slug}_{subdomain}")
            validated_data['schema_name'] = schema_name
        
        return super().update(instance, validated_data)