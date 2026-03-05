# tenancy/models.py
from django.db import models
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator


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
    db_host = models.CharField(max_length=200, default='postgres')
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


class ShopConfiguration(models.Model):
    """
    Per-shop configuration for period-end processes.
    Stored in the tenant database (public), not in shop schemas.
    """
    shop = models.OneToOneField(
        Shop,
        on_delete=models.CASCADE,
        related_name='configuration'
    )
    
    # === PERIOD END TRACKING ===
    last_day_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last successful day-end process"
    )
    last_month_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last successful month-end process"
    )
    last_year_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date of last successful year-end process"
    )
    
    # === AUTOMATED SCHEDULING SETTINGS ===
    # Day-end scheduling
    enable_auto_day_end = models.BooleanField(
        default=False,
        help_text="Enable automatic day-end process"
    )
    day_end_time = models.TimeField(
        default='23:59',
        help_text="Time to run automatic day-end (HH:MM)"
    )
    day_end_day_of_week = models.JSONField(
        default=list,
        help_text="Days of week to run day-end [0=Mon, 6=Sun]"
    )
    
    # Month-end scheduling
    enable_auto_month_end = models.BooleanField(
        default=False,
        help_text="Enable automatic month-end process"
    )
    month_end_day = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(28)],
        help_text="Day of month to run month-end (1-28)"
    )
    month_end_time = models.TimeField(
        default='23:00',
        help_text="Time to run automatic month-end (HH:MM)"
    )
    
    # Year-end scheduling
    enable_auto_year_end = models.BooleanField(
        default=False,
        help_text="Enable automatic year-end process"
    )
    year_end_month = models.PositiveIntegerField(
        default=12,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Month to run year-end (1-12)"
    )
    year_end_day = models.PositiveIntegerField(
        default=31,
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Day of month to run year-end"
    )
    year_end_time = models.TimeField(
        default='22:00',
        help_text="Time to run automatic year-end (HH:MM)"
    )
    
    # === ACCOUNTING PERIOD ===
    current_financial_year = models.PositiveIntegerField(
        default=2024,
        help_text="Current financial year (e.g., 2024)"
    )
    current_period = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Current accounting period (1-12)"
    )
    
    class Meta:
        db_table = 'shop_configuration'
        verbose_name = 'Shop Configuration'
        verbose_name_plural = 'Shop Configurations'
    
    def __str__(self):
        return f"Config - {self.shop.name}"


# Import AuditLog from audit.py to make it accessible
from tenancy.audit import AuditLog  # noqa: E402, F401