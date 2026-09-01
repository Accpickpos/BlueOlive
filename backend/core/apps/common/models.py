"""
Common App Models
Role x Module x Function access grants — foundation for the module x
function permission hierarchy (manual §8.1 Password Maintenance:
Global/Module/Function tiers). Landed as a standalone, unused-by-any-viewset
table so it changes no existing behavior; a later pass rewires each app's
permission_classes to read from it, module by module.
"""

from apps.settings.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.db import models


class AccessGrant(TimeStampedModel):
    """One (role, module, function_type) access decision."""

    ROLE_CHOICES = [
        ("ADMIN", "Admin - Full tenant access"),
        ("MANAGER", "Manager - Can manage shop users"),
        ("STAFF", "Staff - Staff member with limited access"),
        ("CASHIER", "Cashier - Basic access"),
    ]

    MODULE_CHOICES = [
        ("pos", "Point of Sale"),
        ("debtors", "Debtors"),
        ("creditors", "Creditors"),
        ("cash_book", "Cash Book"),
        ("general_ledger", "General Ledger"),
        ("stock_control", "Stock Control"),
        ("purchase_orders", "Purchase Orders"),
        ("settings", "Utilities"),
    ]

    FUNCTION_TYPE_CHOICES = [
        ("MAINTENANCE", "Maintenance"),
        ("TRANSACTIONS", "Transactions"),
        ("ENQUIRY", "Enquiry"),
        ("REPORT", "Report"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    module = models.CharField(max_length=30, choices=MODULE_CHOICES)
    function_type = models.CharField(max_length=20, choices=FUNCTION_TYPE_CHOICES)
    is_allowed = models.BooleanField(default=False)

    class Meta:
        db_table = "access_grants"
        unique_together = ("role", "module", "function_type")
        ordering = ["role", "module", "function_type"]
        indexes = [
            models.Index(fields=["role", "module", "function_type"]),
        ]
        verbose_name = "Access Grant"
        verbose_name_plural = "Access Grants"

    def __str__(self):
        state = "allowed" if self.is_allowed else "denied"
        return f"{self.role} / {self.module} / {self.function_type}: {state}"

    def clean(self):
        super().clean()
        valid_roles = dict(self.ROLE_CHOICES)
        valid_modules = dict(self.MODULE_CHOICES)
        valid_function_types = dict(self.FUNCTION_TYPE_CHOICES)
        if self.role not in valid_roles:
            raise ValidationError({"role": "Invalid role."})
        if self.module not in valid_modules:
            raise ValidationError({"module": "Invalid module."})
        if self.function_type not in valid_function_types:
            raise ValidationError({"function_type": "Invalid function_type."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @classmethod
    def is_role_allowed(cls, role, module, function_type):
        """True only if an explicit grant row allows this combination."""
        return cls.objects.filter(
            role=role, module=module, function_type=function_type, is_allowed=True
        ).exists()


# apps.cash_book.permissions uses a separate, finer-grained Django-Group
# scheme (Cashier/Accountant/Admin/GLSupervisor) that has no per-user
# equivalent in AccessGrant, which is keyed by the 4 coarse ShopUser roles
# only — there is nowhere to write a per-Group-member migration row against.
# This mapping documents the intended correspondence for the later rollout
# that replaces apps.cash_book.permissions' group checks with
# HasModuleFunctionAccess; it is documentation only, not read anywhere yet.
CASH_BOOK_GROUP_TO_ROLE = {
    "Cashier": "CASHIER",
    "Accountant": "STAFF",  # closest existing role; no dedicated "Accountant" ShopUser role exists
    "GLSupervisor": "MANAGER",
    "Admin": "ADMIN",
    # "FinanceDirector" has no Django Group in the current code — every
    # check for it is actually `is_staff and is_superuser`, i.e. a real
    # Django superuser, not a ShopUser role at all.
}
