# shop_users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import validate_email


class ShopUser(AbstractUser):
    """
    Custom user model for multi-tenant system.
    Each user belongs to a specific tenant (referenced by ID, not ForeignKey).
    Users can be assigned to one or more shops within a tenant.
    """
    
    # Make username unique
    username = models.CharField(
        max_length=150,
        unique=True,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
    )
    
    email = models.EmailField(
        unique=True,
        validators=[validate_email],
        help_text='Required. Valid email address.'
    )
    
    # Tenant relationship - use IntegerField instead of ForeignKey
    # This avoids cross-database foreign key issues
    tenant_id = models.IntegerField(
        null=True,
        blank=True,
        help_text='ID of the tenant this user belongs to (null for superusers)'
    )
    
    # Shop IDs - store as JSON array to avoid cross-database FK issues
    # Stores a list of shop IDs this user is assigned to
    shop_ids = models.JSONField(
        default=list,
        blank=True,
        help_text='List of shop IDs this user is assigned to'
    )
    
    # Role field
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('CASHIER', 'Cashier'),
        ('STAFF', 'Staff'),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='STAFF'
    )
    
    # Additional fields
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Shop User'
        verbose_name_plural = 'Shop Users'
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.username} (Tenant: {self.tenant_id})"
    
    def assign_shop(self, shop_id):
        """Assign a shop to this user."""
        if shop_id not in self.shop_ids:
            self.shop_ids.append(shop_id)
    
    def unassign_shop(self, shop_id):
        """Remove a shop assignment from this user."""
        if shop_id in self.shop_ids:
            self.shop_ids.remove(shop_id)
    
    def has_shop_access(self, shop_id):
        """Check if user has access to a specific shop."""
        # Admins have access to all shops in their tenant
        if self.is_superuser or self.role == 'ADMIN':
            return True
        # Other users only have access to assigned shops
        return shop_id in self.shop_ids

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    @property
    def tenant(self):
        """
        Get the tenant object (requires accessing blue_olive database).
        This is a helper property for convenience.
        """
        from tenancy.models import Tenant
        try:
            return Tenant.objects.using('default').get(id=self.tenant_id)
        except Tenant.DoesNotExist:
            return None
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure tenant_id is set.
        Superusers can have tenant_id = None.
        """
        if not self.tenant_id and not self.is_superuser:
            from tenancy.tenant_context import get_current_tenant
            tenant = get_current_tenant()
            if tenant:
                self.tenant_id = tenant.id
            else:
                raise ValueError("Cannot create user without tenant context")

        super().save(*args, **kwargs)