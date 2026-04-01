# shop_users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import validate_email
from django.utils import timezone
from datetime import timedelta
import secrets


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
    
    # Role field - simplified to 4 core roles matching API specification
    ROLE_CHOICES = [
        ('ADMIN', 'Admin - Full tenant access'),
        ('MANAGER', 'Manager - Can manage shop users'),
        ('STAFF', 'Staff - Staff member with limited access'),
        ('CASHIER', 'Cashier - Basic access'),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='CASHIER'
    )
    
    # Additional fields
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    # Track who created this user
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        help_text='User who created this account'
    )
    
    # Email verification fields
    is_email_verified = models.BooleanField(
        default=False,
        help_text='Whether the user has verified their email address'
    )
    email_verification_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Token used for email verification (self-generated, not stored from token)'
    )
    email_verification_token_created = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the email verification token was created'
    )
    
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
        # Admins and managers have access to all shops in their tenant
        if self.is_superuser or self.role in ('ADMIN', 'MANAGER'):
            return True
        # Other users only have access to assigned shops
        return shop_id in self.shop_ids
    
    def can_edit_user(self, other_user):
        """
        Check if this user can edit another user.
        - ADMIN can edit all users
        - MANAGER can only edit users they created
        - Other users cannot edit any users
        """
        # ADMIN and superuser can edit all users
        if self.is_superuser or self.role == 'ADMIN':
            return True
        # MANAGER can only edit users they created
        if self.role == 'MANAGER':
            return other_user.created_by_id == self.id
        return False
    
    def can_delete_user(self, other_user):
        """
        Check if this user can delete another user.
        - ADMIN can delete all users
        - MANAGER can only delete users they created
        """
        # ADMIN and superuser can delete all users
        if self.is_superuser or self.role == 'ADMIN':
            return True
        # MANAGER can only delete users they created
        if self.role == 'MANAGER':
            return other_user.created_by_id == self.id
        return False

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
        Override save to ensure tenant_id is set and is_staff is synced with role.
        Superusers can have tenant_id = None.
        """
        # Sync is_staff with role - staff members, managers, and admins have is_staff=True
        role = getattr(self, 'role', 'CASHIER') or 'CASHIER'  # Default to CASHIER if not set
        self.is_staff = role in ('ADMIN', 'MANAGER', 'STAFF')
        
        if not self.tenant_id and not self.is_superuser:
            from tenancy.tenant_context import get_current_tenant
            tenant = get_current_tenant()
            if tenant:
                self.tenant_id = tenant.id
            else:
                raise ValueError("Cannot create user without tenant context")

        super().save(*args, **kwargs)
    
    def generate_email_verification_token(self):
        """Generate and store an email verification token."""
        self.email_verification_token = secrets.token_urlsafe(32)
        self.email_verification_token_created = timezone.now()
        self.save()
        return self.email_verification_token
    
    def verify_email_token(self, token, token_expiry_hours=24):
        """
        Verify email token.
        
        Args:
            token: The token to verify
            token_expiry_hours: How many hours the token is valid (default: 24)
            
        Returns:
            tuple: (is_valid, message)
        """
        if not self.email_verification_token:
            return False, "No verification token found for this user"
        
        if self.email_verification_token != token:
            return False, "Invalid verification token"
        
        if not self.email_verification_token_created:
            return False, "Token creation time missing"
        
        # Check token expiry
        token_age = timezone.now() - self.email_verification_token_created
        if token_age > timedelta(hours=token_expiry_hours):
            self.email_verification_token = None
            self.email_verification_token_created = None
            self.save()
            return False, f"Verification token expired (valid for {token_expiry_hours} hours)"
        
        return True, "Token is valid"
    
    def confirm_email(self, token, token_expiry_hours=24):
        """
        Confirm user email with verification token.
        
        Returns:
            tuple: (success, message)
        """
        is_valid, message = self.verify_email_token(token, token_expiry_hours)
        
        if not is_valid:
            return False, message
        
        # Mark email as verified
        self.is_email_verified = True
        self.email_verification_token = None
        self.email_verification_token_created = None
        self.save()
        
        return True, "Email verified successfully"
    
    def get_active_shops(self):
        """
        Get all active shops user has access to.
        Uses shop_ids JSON field for multi-shop access.
        """
        from tenancy.models import Shop
        import logging
        logger = logging.getLogger(__name__)
        
        # Admins have access to all shops in their tenant
        if self.is_superuser or self.role == 'ADMIN':
            logger.debug(f"[get_active_shops] User {self.id} is admin, returning all tenant shops")
            if not self.tenant_id:
                return Shop.objects.none()
            return Shop.objects.using('default').filter(
                tenant_id=self.tenant_id, 
                is_active=True
            )
        
        # Use shop_ids JSON field for explicit access
        shop_ids_list = getattr(self, 'shop_ids', []) or []
        
        logger.debug(f"[get_active_shops] User {self.id} has shop_ids: {shop_ids_list}")
        
        if not shop_ids_list:
            # No explicit shop assignments - return empty
            logger.warning(f"[get_active_shops] User {self.id} has NO shop_ids assigned!")
            return Shop.objects.none()
        
        return Shop.objects.using('default').filter(
            id__in=shop_ids_list,
            is_active=True,
            tenant_id=self.tenant_id
        )
    
    def get_current_shop(self):
        """
        Get the currently active shop for this user.
        Prefers session-based shop, then falls back to first available.
        """
        from tenancy.models import Shop
        
        # Check if current_shop_id is set
        current_shop_id = getattr(self, 'current_shop_id', None)
        if current_shop_id:
            shop = Shop.objects.using('default').filter(
                id=current_shop_id,
                is_active=True,
                user_associations__user=self,
                user_associations__is_active=True
            ).first()
            if shop:
                return shop
        
        # Fallback to first available shop
        return self.get_active_shops().first()
    
    def can_access_shop(self, shop_id):
        """
        Check if user can access a specific shop.
        
        Args:
            shop_id: ID of the shop to check access for
            
        Returns:
            bool: True if user has access, False otherwise
        """
        from tenancy.models import Shop
        
        # Admins can access any shop in their tenant
        if self.is_superuser or self.role == 'ADMIN':
            shop = Shop.objects.using('default').filter(
                id=shop_id, 
                is_active=True
            ).first()
            return shop and shop.tenant_id == self.tenant_id
        
        # Check shop_ids JSON field
        shop_ids_list = getattr(self, 'shop_ids', []) or []
        return shop_id in shop_ids_list
    
    def get_accessible_shops_list(self):
        """
        Get list of accessible shops as dict for serialization.
        """
        shops = self.get_active_shops()
        current_id = getattr(self, 'current_shop_id', None)
        
        return [{
            'id': shop.id,
            'name': shop.name,
            'schema_name': shop.schema_name,
            'is_head_office': shop.is_head_office,
            'is_current': shop.id == current_id
        } for shop in shops]