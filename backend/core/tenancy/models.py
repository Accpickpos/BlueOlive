# tenancy/models.py
from django.db import models
from django.core import signing
from django.core.exceptions import ValidationError


class EncryptedCharField(models.CharField):
    """
    A CharField that encrypts/decrypts values automatically.
    """
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return signing.loads(value)
        except signing.BadSignature:
            return value  # Return as-is if decryption fails

    def to_python(self, value):
        if value is None:
            return value
        return str(value)

    def get_prep_value(self, value):
        if value is None:
            return value
        return signing.dumps(str(value))

class Tenant(models.Model):
    name = models.CharField(max_length=200, unique=True)  # Company name
    slug = models.SlugField(unique=True)
    subdomain = models.CharField(max_length=100, unique=True, default='default', help_text="Subdomain for tenant access, e.g., 'tenant1'")
    phone = models.CharField(max_length=20, default='')
    email = models.EmailField(max_length=150, default='')
    db_name = models.CharField(max_length=200)
    db_user = models.CharField(max_length=200, default='postgres')
    db_password = EncryptedCharField(max_length=200)  # Encrypted field
    db_host = models.CharField(max_length=200, default='localhost')
    db_port = models.IntegerField(default=5432)
    is_active = models.BooleanField(default=True, help_text="Whether this tenant is active")
    created_at = models.DateTimeField(auto_now_add=True)
    tenant_control = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tenant"

    @property
    def db_alias(self):
        return f"tenant_{self.id}"

    def clean(self):
        if not self.subdomain:
            raise ValidationError("Subdomain is required for tenant isolation.")

    def __str__(self):
        return self.name


class Shop(models.Model):
    """
    Represents a shop under a tenant.
    The actual shop data tables live in the tenant DB, in a schema named `schema_name`.
    """
    SETUP_STATUS_CHOICES = [
        ('pending', 'Pending Setup'),
        ('ready', 'Ready for Use'),
        ('failed', 'Setup Failed'),
    ]
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=200)
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Shop code (e.g., MS001)",
        null=True,
        blank=True
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Physical address of the shop"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Shop phone number"
    )
    schema_name = models.CharField(max_length=100, unique=True)
    subdomain = models.CharField(max_length=100, blank=True, help_text="Subdomain for shop access, e.g., 'downtown'")
    description = models.TextField(blank=True, null=True)
    is_head_office = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, help_text="Whether this shop is active")
    setup_status = models.CharField(max_length=20, choices=SETUP_STATUS_CHOICES, default='pending', help_text="Status of shop schema setup")
    created_at = models.DateTimeField(auto_now_add=True)

    tenant_control = True

    class Meta:
        verbose_name = "Shop"
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'is_head_office'], 
                condition=models.Q(is_head_office=True), 
                name='unique_head_office_per_tenant'
            ),
            models.UniqueConstraint(
                fields=['tenant', 'subdomain'],
                name='unique_subdomain_per_tenant'
            )
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        
        # Ensure no other head office for this tenant
        if self.is_head_office:
            Shop.objects.filter(tenant=self.tenant, is_head_office=True).exclude(pk=self.pk).update(is_head_office=False)
        
        # Auto-generate subdomain if not provided
        if not self.subdomain:
            subdomain = slugify(self.name)
            
            # Handle edge case: empty slug (shop name with only special characters)
            if not subdomain:
                subdomain = f"shop-{self.id if self.id else 'new'}"
            
            # Ensure uniqueness within tenant
            original_subdomain = subdomain
            counter = 1
            while Shop.objects.filter(tenant=self.tenant, subdomain=subdomain).exclude(pk=self.pk).exists():
                subdomain = f"{original_subdomain}-{counter}"
                counter += 1
            
            self.subdomain = subdomain
        
        super().save(*args, **kwargs)

# Import AuditLog from audit.py to make it accessible
from tenancy.audit import AuditLog  # noqa: E402, F401