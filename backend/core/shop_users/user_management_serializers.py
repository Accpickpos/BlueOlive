"""
Admin user management serializer.
Used by superusers to manage other superusers.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserManagementSerializer(serializers.ModelSerializer):
    """
    Serializer for managing superusers.
    Only superusers can access this.
    Allows editing: username, email, password, first_name, last_name
    """
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'is_active', 'is_superuser', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def validate_password(self, value):
        """Validate password strength if provided."""
        if value:
            try:
                validate_password(value)
            except serializers.ValidationError as e:
                raise serializers.ValidationError(str(e))
        return value
    
    def update(self, instance, validated_data):
        """Update user, handling password separately."""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance
    
    def create(self, validated_data):
        """Create new superuser."""
        password = validated_data.pop('password', None)
        
        user = User.objects.create_user(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user


class UserListSerializer(serializers.ModelSerializer):
    """Read-only serializer for listing users."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_superuser', 'date_joined']
        read_only_fields = fields
