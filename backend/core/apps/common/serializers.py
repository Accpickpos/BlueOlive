"""
Common Serializers Module

Shared serializer mixins and base classes for use across all business apps.

Usage:
    from apps.common.serializers import AuditFieldsMixin, TenantMixin
    
    class MySerializer(AuditFieldsMixin, ModelSerializer):
        class Meta:
            model = MyModel
            fields = '__all__'
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class AuditFieldsMixin:
    """
    Mixin that adds audit fields to serializers.
    
    Adds 'created_by' and 'updated_by' fields that are automatically
    populated with the current user.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    updated_by = serializers.StringRelatedField(read_only=True)
    
    def create(self, validated_data):
        """Add created_by field on create."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Add updated_by field on update."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)


class TenantMixin:
    """
    Mixin that ensures objects belong to the user's tenant.
    
    Automatically filters querysets to only return objects
    belonging to the current user's tenant.
    """
    def get_queryset(self):
        """Filter queryset by tenant."""
        queryset = super().get_queryset()
        
        # Get request from context
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return queryset.none()
        
        # Get tenant_id from user
        tenant_id = getattr(request.user, 'tenant_id', None)
        if tenant_id is None:
            return queryset.none()
        
        # Filter by tenant if the model has tenant_id field
        if hasattr(queryset.model, 'tenant_id'):
            return queryset.filter(tenant_id=tenant_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """Set tenant_id on create."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            tenant_id = getattr(request.user, 'tenant_id', None)
            if tenant_id:
                serializer.save(tenant_id=tenant_id)
            else:
                serializer.save()
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        """Ensure tenant_id is preserved on update."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            tenant_id = getattr(request.user, 'tenant_id', None)
            if tenant_id:
                # Check if instance already has tenant_id
                if hasattr(serializer.instance, 'tenant_id'):
                    serializer.save()  # Keep existing tenant_id
                else:
                    serializer.save(tenant_id=tenant_id)
            else:
                serializer.save()
        else:
            serializer.save()


class ReadOnlyFieldsMixin:
    """
    Mixin to make certain fields read-only based on user role.
    
    Usage:
        class MySerializer(ReadOnlyFieldsMixin, ModelSerializer):
            class Meta:
                model = MyModel
                read_only_fields = ['status', 'posted_date']
    """
    def get_read_only_fields(self, request):
        """Return read-only fields based on user role."""
        base_fields = getattr(self.Meta, 'read_only_fields', [])
        
        # Add role-based fields if needed
        user_role = getattr(request.user, 'role', None) if request else None
        
        if user_role == 'clerk':
            # Clerks can't change certain fields
            return base_fields + ['approved_by', 'approval_date']
        
        return base_fields


class ValidationMixin:
    """
    Mixin with common validation methods.
    
    Provides shared validation logic that can be used across serializers.
    """
    def validate_positive_decimal(self, value, field_name='amount'):
        """Validate that a decimal field is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError({field_name: 'Must be a positive value'})
        return value
    
    def validate_date_not_future(self, value, field_name='date'):
        """Validate that a date is not in the future."""
        from django.utils import timezone
        if value and value > timezone.now().date():
            raise serializers.ValidationError({field_name: 'Date cannot be in the future'})
        return value
    
    def validate_required_fields(self, validated_data, required_fields):
        """Validate that all required fields are present."""
        missing = [f for f in required_fields if f not in validated_data]
        if missing:
            raise serializers.ValidationError(
                f"Missing required fields: {', '.join(missing)}"
            )


class BaseModelSerializer(serializers.ModelSerializer, AuditFieldsMixin, ValidationMixin):
    """
    Base serializer that combines common mixins.
    
    Use this as the base class for all model serializers.
    """
    pass


class NestedSerializerMixin:
    """
    Mixin for handling nested serializers with proper validation.
    
    Provides methods to handle create/update for nested relationships.
    """
    def create_nested(self, validated_data, nested_fields, instance=None):
        """
        Handle nested field creation.
        
        Args:
            validated_data: The validated data dictionary
            nested_fields: Dict of {field_name: SerializerClass}
            instance: Existing instance for updates
        
        Returns:
            Updated instance
        """
        for field_name, nested_serializer_class in nested_fields.items():
            nested_data = validated_data.pop(field_name, None)
            if nested_data is None:
                continue
            
            if instance:
                # Update existing nested objects
                nested_qs = getattr(instance, field_name)
                if hasattr(nested_qs, 'all'):
                    nested_qs.all().delete()
                
                nested_objects = []
                for data in nested_data:
                    nested_objects.append(nested_serializer_class(data=data).save())
                setattr(instance, field_name, nested_objects)
            else:
                # Create new nested objects
                nested_objects = [
                    nested_serializer_class(data=data).save()
                    for data in nested_data
                ]
                validated_data[field_name] = nested_objects
        
        return instance


class SummaryFieldsMixin:
    """
    Mixin that adds summary/count fields to serializers.
    
    Useful for list views that need to show related counts.
    """
    def get_summary(self, obj, field_name, related_name):
        """Get count of related objects."""
        if hasattr(obj, related_name):
            return getattr(obj, related_name).count()
        return 0


class ChoicesMixin:
    """
    Mixin that adds choice display values to serializers.
    
    Automatically adds {field}_display fields for choice fields.
    """
    def to_representation(self, instance):
        """Add choice display values."""
        data = super().to_representation(instance)
        
        # Add display values for choice fields
        for field_name in getattr(self.Meta, 'choice_fields', []):
            if field_name in data:
                choice_field = getattr(instance, f'get_{field_name}_display', None)
                if choice_field:
                    data[f'{field_name}_display'] = choice_field()
        
        return data


# Re-export commonly used serializers
__all__ = [
    'AuditFieldsMixin',
    'TenantMixin', 
    'ReadOnlyFieldsMixin',
    'ValidationMixin',
    'BaseModelSerializer',
    'NestedSerializerMixin',
    'SummaryFieldsMixin',
    'ChoicesMixin',
]
