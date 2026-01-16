from django.db import models
from django.contrib.auth.models import AbstractUser
from .managers import TenantUserManager

class ShopUser(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        STAFF = 'STAFF', 'Staff'
        MANAGER = 'MANAGER', 'Manager'
        CUSTOMER = 'CUSTOMER', 'Customer'
    
    # Override username to remove unique constraint from AbstractUser
    username = models.CharField(
        max_length=150,
        unique=False,
        help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
    )
    
    # Store tenant_id and shop_id as integers to avoid cross-schema foreign keys
    # Use integers instead of ForeignKeys to keep shop_users in a tenant schema
    # while maintaining references to tenancy tables in the public schema
    tenant_id = models.IntegerField(
        null=True,
        blank=True,
        db_column='tenant_id',
        help_text="ID of the tenant (stored as integer to avoid cross-schema FK)"
    )
    shop_id = models.IntegerField(
        null=True,
        blank=True,
        db_column='shop_id',
        help_text="ID of the shop (stored as integer to avoid cross-schema FK)"
    )
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        help_text="User role within the tenant"
    )
    
    objects = TenantUserManager()

    class Meta:
        swappable = 'AUTH_USER_MODEL'
        unique_together = [['username', 'tenant_id']]
        indexes = [
            models.Index(fields=['tenant_id', 'role']),
            models.Index(fields=['tenant_id', 'username']),
        ]

    def __str__(self):
        tenant_name = f"Tenant {self.tenant_id}" if self.tenant_id else "Global"
        shop_name = f" - Shop {self.shop_id}" if self.shop_id else ""
        return f"{self.username} ({tenant_name}{shop_name})"
    
    def has_role(self, role):
        """Check if user has a specific role"""
        return self.role == role
    
    def is_admin_user(self):
        """Check if user is an admin within their tenant"""
        return self.role == self.Role.ADMIN
    
    def is_staff_user(self):
        """Check if user is staff or higher"""
        return self.role in [self.Role.ADMIN, self.Role.STAFF, self.Role.MANAGER]
    
    def get_tenant(self):
        """Get the actual Tenant object from public schema"""
        if not self.tenant_id:
            return None
        from tenancy.models import Tenant
        try:
            # Use the default database connection to access tenancy tables
            return Tenant.objects.using('default').get(id=self.tenant_id)
        except Tenant.DoesNotExist:
            return None
    
    def get_shop(self):
        """Get the actual Shop object from public schema"""
        if not self.shop_id:
            return None
        from tenancy.models import Shop
        try:
            # Use the default database connection to access tenancy tables
            return Shop.objects.using('default').get(id=self.shop_id)
        except Shop.DoesNotExist:
            return None
    
    def save(self, *args, **kwargs):
        # Ensure superusers don't have a tenant
        if self.is_superuser and self.tenant_id:
            self.tenant_id = None
            self.shop_id = None
        # Ensure regular users have a tenant
        elif not self.is_superuser and not self.tenant_id:
            raise ValueError("Regular users must belong to a tenant")

            raise ValueError("Shop must belong to the user's tenant")
        super().save(*args, **kwargs)