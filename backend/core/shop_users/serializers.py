# shop_users/serializers.py
from rest_framework import serializers
from .models import ShopUser
from django.contrib.auth.hashers import make_password
from tenancy.tenant_context import get_current_tenant
from tenancy.models import Shop


class ShopUserSerializer(serializers.ModelSerializer):
    """
    Serializer for ShopUser model (using tenant_id and shop_ids)
    """
    password = serializers.CharField(write_only=True, required=False)
    tenant_name = serializers.SerializerMethodField(read_only=True)
    shops = serializers.SerializerMethodField(read_only=True)
    shop_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=False,
        required=False
    )
    
    class Meta:
        model = ShopUser
        fields = [
            'id', 
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'password',
            'role',
            'tenant_id',
            'tenant_name',
            'shop_ids',
            'shops',
            'phone',
            'is_active',
            'is_staff',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined', 'tenant_name', 'shops']
        extra_kwargs = {
            'password': {'write_only': True},
            'tenant_id': {'read_only': True},  # Set automatically from context
        }
    
    def get_tenant_name(self, obj):
        """Get tenant name for display"""
        from tenancy.models import Tenant
        try:
            tenant = Tenant.objects.get(id=obj.tenant_id)
            return tenant.name
        except Tenant.DoesNotExist:
            return None
    
    def get_shops(self, obj):
        """Get shop details for the assigned shops"""
        if not obj.shop_ids:
            return []
        
        shops = Shop.objects.filter(id__in=obj.shop_ids).values('id', 'name', 'subdomain')
        return list(shops)
    
    def create(self, validated_data):

        """
        Create a new user with hashed password and tenant from context
        """
        password = validated_data.pop('password', None)
        
        # Get tenant from context
        tenant = get_current_tenant()
        if not tenant:
            raise serializers.ValidationError("No tenant context available")
        
        # Set tenant_id
        validated_data['tenant_id'] = tenant.id
        
        user = ShopUser(**validated_data)
        
        if password:
            user.password = make_password(password)
        
        # Save to tenant database
        user.save(using=tenant.db_alias)
        return user
    
    def update(self, instance, validated_data):
        """
        Update user, hash password if provided
        """
        password = validated_data.pop('password', None)
        tenant = get_current_tenant()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.password = make_password(password)
        
        # Save to tenant database
        if tenant:
            instance.save(using=tenant.db_alias)
        else:
            instance.save()
        return instance


class ShopUserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users (includes password requirement)
    """
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = ShopUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'confirm_password',
            'role',
            'phone',
        ]
    
    def validate(self, attrs):
        """
        Validate that passwords match
        """
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        """
        Create user with hashed password and tenant from context
        """
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        # Get tenant from context
        tenant = get_current_tenant()
        if not tenant:
            raise serializers.ValidationError("No tenant context available")
        
        # Set tenant_id
        validated_data['tenant_id'] = tenant.id
        
        user = ShopUser(**validated_data)
        user.password = make_password(password)
        user.save()
        
        return user