# tenancy/audit.py
"""
Audit logging for security-critical operations
"""

import logging

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

logger = logging.getLogger(__name__)

User = get_user_model()


class AuditLog(models.Model):
    """
    Model to track security-critical operations:
    - Login/Logout
    - User creation/modification/deletion
    - Permission changes
    - Data access from multiple tenants (potential breach)
    """

    ACTION_CHOICES = [
        ("LOGIN", "User Login"),
        ("LOGOUT", "User Logout"),
        ("LOGIN_FAILED", "Failed Login Attempt"),
        ("USER_CREATE", "User Created"),
        ("USER_UPDATE", "User Updated"),
        ("USER_DELETE", "User Deleted"),
        ("PERMISSION_CHANGE", "Permission Changed"),
        ("ROLE_CHANGE", "Role Changed"),
        ("TENANT_ACCESS", "Cross-Tenant Access Attempt"),
        ("SUPERUSER_IMPERSONATION", "Superuser Tenant Impersonation"),
        ("DATA_ACCESS", "Sensitive Data Access"),
        ("PASSWORD_CHANGE", "Password Changed"),
        ("POS_POSTED", "POS Document Posted"),
        ("POS_CANCELLED", "POS Document Cancelled"),
    ]

    # Not a ForeignKey: AuditLog lives in the shared default database, but the
    # user performing the action is a ShopUser in a per-tenant database.
    # Django's router forbids cross-database relations, so this is a plain
    # soft reference (matches the `user_id INT` column with no FK constraint
    # created in migration 0005_create_auditlog_table).
    user_id = models.IntegerField(null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(
        max_length=50, blank=True, help_text="Model name (e.g., 'ShopUser', 'Shop')"
    )
    resource_id = models.CharField(
        max_length=100, blank=True, help_text="ID of the affected resource"
    )

    # Request context
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    # Tenant context
    tenant_id = models.IntegerField(null=True, blank=True)

    # Details
    details = models.JSONField(
        default=dict, blank=True, help_text="Additional context (JSON)"
    )
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        managed = (
            False  # Table is created manually in migration 0005_create_auditlog_table
        )
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["user_id", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
            models.Index(fields=["tenant_id", "timestamp"]),
        ]

    def __str__(self):
        return (
            f"{self.get_action_display()} by user_id={self.user_id} at {self.timestamp}"
        )

    @classmethod
    def log_action(
        cls,
        action,
        request,
        user=None,
        resource_type=None,
        resource_id=None,
        details=None,
        success=True,
        error_message=None,
    ):
        """
        Helper method to log an action.

        Usage:
            AuditLog.log_action(
                action='LOGIN',
                request=request,
                user=user,
                details={'method': 'password'}
            )
        """
        from tenancy.tenant_context import get_current_tenant

        # Extract request context
        ip_address = get_client_ip(request) if request else None
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:500] if request else ""

        # Get current tenant
        tenant = get_current_tenant()
        tenant_id = tenant.id if tenant else None

        log_details = dict(details or {})
        if user is not None and "username" not in log_details:
            log_details["username"] = getattr(user, "username", "")

        try:
            cls.objects.create(
                user_id=getattr(user, "id", None),
                action=action,
                resource_type=resource_type or "",
                resource_id=resource_id or "",
                ip_address=ip_address,
                user_agent=user_agent,
                tenant_id=tenant_id,
                details=log_details,
                success=success,
                error_message=error_message or "",
            )
            logger.debug(f"Audit log created: {action} by {user}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")


def get_client_ip(request):
    """
    Extract client IP from request, accounting for proxies.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class LoginAuditLog:
    """
    Convenience class for login/logout audit logging
    """

    @staticmethod
    def log_login(request, user):
        """Log successful login"""
        AuditLog.log_action(
            action="LOGIN",
            request=request,
            user=user,
            details={"method": "password"},
        )

    @staticmethod
    def log_login_failed(request, username=None):
        """Log failed login attempt"""
        AuditLog.log_action(
            action="LOGIN_FAILED",
            request=request,
            user=None,
            details={"username": username or "unknown"},
            success=False,
        )

    @staticmethod
    def log_logout(request, user):
        """Log logout"""
        AuditLog.log_action(
            action="LOGOUT",
            request=request,
            user=user,
        )


class UserAuditLog:
    """
    Convenience class for user-related audit logging
    """

    @staticmethod
    def log_create(request, created_user, actor_user):
        """Log user creation"""
        AuditLog.log_action(
            action="USER_CREATE",
            request=request,
            user=actor_user,
            resource_type="ShopUser",
            resource_id=str(created_user.id),
            details={
                "created_user_id": created_user.id,
                "created_user_username": created_user.username,
                "role": created_user.role,
            },
        )

    @staticmethod
    def log_update(request, updated_user, actor_user, changes=None):
        """Log user update"""
        AuditLog.log_action(
            action="USER_UPDATE",
            request=request,
            user=actor_user,
            resource_type="ShopUser",
            resource_id=str(updated_user.id),
            details={
                "updated_user_id": updated_user.id,
                "changes": changes or {},
            },
        )

    @staticmethod
    def log_user_updated(request, user, changes=None):
        """Log a user updating their own profile (self-service update)."""
        UserAuditLog.log_update(
            request, updated_user=user, actor_user=user, changes=changes
        )

    @staticmethod
    def log_delete(request, deleted_user, actor_user):
        """Log user deletion"""
        AuditLog.log_action(
            action="USER_DELETE",
            request=request,
            user=actor_user,
            resource_type="ShopUser",
            resource_id=str(deleted_user.id),
            details={
                "deleted_user_id": deleted_user.id,
                "deleted_user_username": deleted_user.username,
            },
        )

    @staticmethod
    def log_role_change(request, user, old_role, new_role, actor_user):
        """Log role change"""
        AuditLog.log_action(
            action="ROLE_CHANGE",
            request=request,
            user=actor_user,
            resource_type="ShopUser",
            resource_id=str(user.id),
            details={
                "user_id": user.id,
                "old_role": old_role,
                "new_role": new_role,
            },
        )


class TenantAuditLog:
    """
    Convenience class for tenant-related audit logging
    """

    @staticmethod
    def log_superuser_impersonation(request, superuser, target_tenant, reason=None):
        """Log a superuser impersonating a tenant for support/debugging."""
        AuditLog.log_action(
            action="SUPERUSER_IMPERSONATION",
            request=request,
            user=superuser,
            resource_type="Tenant",
            resource_id=str(target_tenant.id),
            details={
                "target_tenant_id": target_tenant.id,
                "target_tenant_slug": getattr(target_tenant, "slug", None),
                "reason": reason or "Not specified",
            },
        )

    @staticmethod
    def log_cross_tenant_access_attempt(
        request, user, attempted_tenant_id, actual_tenant_id
    ):
        """Log when user attempts to access a different tenant's resources"""
        AuditLog.log_action(
            action="TENANT_ACCESS",
            request=request,
            user=user,
            resource_type="CROSS_TENANT_ACCESS",
            resource_id=str(attempted_tenant_id),
            details={
                "attempted_tenant_id": attempted_tenant_id,
                "actual_tenant_id": actual_tenant_id,
                "user_attempted_access_to": f"Tenant {attempted_tenant_id}",
                "user_belongs_to": f"Tenant {actual_tenant_id}",
            },
            success=False,
            error_message=f"Cross-tenant access denied: user belongs to tenant {actual_tenant_id}, attempted tenant {attempted_tenant_id}",
        )
        logger.warning(
            f"Cross-tenant access attempt: user_id={user.id if user else 'unknown'} "
            f"attempted_tenant={attempted_tenant_id}, actual_tenant={actual_tenant_id}"
        )


class POSAuditLog:
    """
    Convenience class for POS financial-document audit logging (sale/credit
    note/cash return/receipt/cheque posting and cancellation). request=None
    is safe here: log_action already guards ip_address/user_agent
    extraction on `if request else None`, and these documents are posted
    from service-layer code that doesn't have the request object threaded
    through — only the acting user.
    """

    @staticmethod
    def log_document_posted(user, document_type, document_number, details=None):
        """Log a POS document (credit note, cash return, ...) being posted."""
        AuditLog.log_action(
            action="POS_POSTED",
            request=None,
            user=user,
            resource_type=document_type,
            resource_id=document_number,
            details=details or {},
        )

    @staticmethod
    def log_document_cancelled(
        user, document_type, document_number, reason, details=None
    ):
        """Log a POS document (sale, credit note, cash return, ...) being cancelled."""
        AuditLog.log_action(
            action="POS_CANCELLED",
            request=None,
            user=user,
            resource_type=document_type,
            resource_id=document_number,
            details={**(details or {}), "reason": reason},
        )
