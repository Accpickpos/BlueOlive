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
        write_only=True,
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
        
        # Shop model is in public database, not tenant database
        try:
            shops = Shop.objects.using('default').filter(id__in=obj.shop_ids).values('id', 'name', 'subdomain')
        except Exception:
            # If query fails, return empty list
            return []
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
            user.set_password(password)  # Use set_password instead of make_password
        
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
            instance.set_password(password)  # Use set_password instead of make_password
        
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
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        min_length=8,
        help_text='Password must be at least 8 characters long. Use a mix of uppercase, lowercase, numbers, and special characters for better security.'
    )
    confirm_password = serializers.CharField(write_only=True, required=True)
    shop_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    password_display = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ShopUser
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
            'confirm_password',
            'password_display',
            'role',
            'phone',
            'shop_ids',
            'is_active',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined', 'password_display']
    
    def get_password_display(self, obj):
        """
        Return password info message after user creation.
        Note: Actual password is not returned for security reasons.
        Show this message only during creation (when password was just set).
        """
        # This is populated during create() via context
        return self.context.get('password_info', None)
    
    def validate_password(self, value):
        """
        Validate password meets security requirements
        """
        if len(value) < 8:
            raise serializers.ValidationError(
                "Password must be at least 8 characters long."
            )
        
        # Check for at least one uppercase letter
        if not any(char.isupper() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter (A-Z)."
            )
        
        # Check for at least one lowercase letter
        if not any(char.islower() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter (a-z)."
            )
        
        # Check for at least one digit
        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError(
                "Password must contain at least one number (0-9)."
            )
        
        return value
    
    def validate(self, attrs):
        """
        Validate that passwords match
        """
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError({
                "confirm_password": "Password fields didn't match."
            })
        
        # Remove confirm_password from attrs
        attrs.pop('confirm_password', None)
        
        return attrs
    
    def create(self, validated_data):
        """
        Create user with hashed password and tenant from context.
        Returns password info message for display to admin.
        """
        password = validated_data.pop('password')
        shop_ids = validated_data.pop('shop_ids', [])
        
        # Get tenant from context
        tenant = get_current_tenant()
        if not tenant:
            raise serializers.ValidationError("No tenant context available")
        
        # FIX: If no shop_ids provided, auto-assign the first shop from tenant
        if not shop_ids:
            first_shop = tenant.shops.filter(is_active=True).first()
            if first_shop:
                shop_ids = [first_shop.id]
                # Log for debugging
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"[UserCreationSerializer] Auto-assigned shop_id={first_shop.id} ({first_shop.name}) to new user")
            else:
                logger.warning(f"[UserCreationSerializer] No active shops found for tenant {tenant.name}!")
        
        # Set tenant_id and shop_ids
        validated_data['tenant_id'] = tenant.id
        validated_data['shop_ids'] = shop_ids
        
        user = ShopUser(**validated_data)
        user.set_password(password)  # Use set_password instead of make_password
        
        # Save to tenant database
        user.save(using=tenant.db_alias)
        
        # Add password info to context for response
        self.context['password_info'] = {
            'message': 'User created successfully. Password has been securely hashed.',
            'note': 'Password is not stored in plain text and cannot be retrieved. User can reset password if forgotten.',
            'username': user.username,
            'email': user.email
        }
        
        return user