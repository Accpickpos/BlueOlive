# tenancy/models.py
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core import signing
from django.core.exceptions import ValidationError
from .shop_manager import create_shop_schema
from .utils import register_tenant_connection


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
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="shops")
    name = models.CharField(max_length=200)
    schema_name = models.CharField(max_length=100, unique=True)
    subdomain = models.CharField(max_length=100, blank=True, null=True, help_text="Subdomain for shop access, e.g., 'shop1'")
    description = models.TextField(blank=True, null=True)
    is_head_office = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    tenant_control = True

    class Meta:
        verbose_name = "Shop"
        constraints = [
            models.UniqueConstraint(fields=['tenant', 'is_head_office'], condition=models.Q(is_head_office=True), name='unique_head_office_per_tenant')
        ]

    def __str__(self):
        return f"{self.tenant.name} - {self.name}"

    def save(self, *args, **kwargs):
        if self.is_head_office:
            # Ensure no other head office for this tenant
            Shop.objects.filter(tenant=self.tenant, is_head_office=True).exclude(pk=self.pk).update(is_head_office=False)
        if not self.subdomain:
            from django.utils.text import slugify
            self.subdomain = slugify(self.name)
        super().save(*args, **kwargs)


@receiver(post_save, sender=Shop)
def create_shop_schema_on_save(sender, instance, created, **kwargs):
    if created:
        try:
            register_tenant_connection(instance.tenant)
            create_shop_schema(instance.tenant, instance.schema_name)
        except Exception as e:
            print(f"Warning: Failed to create schema for shop {instance.name}: {e}")
            # Don't raise, allow shop creation to succeed
