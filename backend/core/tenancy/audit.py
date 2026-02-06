# tenancy/audit.py
"""
Audit logging for security-critical operations
"""
import logging
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

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
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('LOGIN_FAILED', 'Failed Login Attempt'),
        ('USER_CREATE', 'User Created'),
        ('USER_UPDATE', 'User Updated'),
        ('USER_DELETE', 'User Deleted'),
        ('PERMISSION_CHANGE', 'Permission Changed'),
        ('ROLE_CHANGE', 'Role Changed'),
        ('TENANT_ACCESS', 'Cross-Tenant Access Attempt'),
        ('DATA_ACCESS', 'Sensitive Data Access'),
        ('PASSWORD_CHANGE', 'Password Changed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50, blank=True, help_text="Model name (e.g., 'ShopUser', 'Shop')")
    resource_id = models.CharField(max_length=100, blank=True, help_text="ID of the affected resource")
    
    # Request context
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Tenant context
    tenant_id = models.IntegerField(null=True, blank=True)
    
    # Details
    details = models.JSONField(default=dict, blank=True, help_text="Additional context (JSON)")
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        managed = False  # Table is created manually in migration 0005_create_auditlog_table
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['tenant_id', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.user} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, action, request, user=None, resource_type=None, resource_id=None, 
                   details=None, success=True, error_message=None):
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
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500] if request else ''
        
        # Get current tenant
        tenant = get_current_tenant()
        tenant_id = tenant.id if tenant else None
        
        try:
            cls.objects.create(
                user=user,
                action=action,
                resource_type=resource_type or '',
                resource_id=resource_id or '',
                ip_address=ip_address,
                user_agent=user_agent,
                tenant_id=tenant_id,
                details=details or {},
                success=success,
                error_message=error_message or '',
            )
            logger.debug(f"Audit log created: {action} by {user}")
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")


def get_client_ip(request):
    """
    Extract client IP from request, accounting for proxies.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LoginAuditLog:
    """
    Convenience class for login/logout audit logging
    """
    
    @staticmethod
    def log_login(request, user):
        """Log successful login"""
        AuditLog.log_action(
            action='LOGIN',
            request=request,
            user=user,
            details={'method': 'password'},
        )
    
    @staticmethod
    def log_login_failed(request, username=None):
        """Log failed login attempt"""
        AuditLog.log_action(
            action='LOGIN_FAILED',
            request=request,
            user=None,
            details={'username': username or 'unknown'},
            success=False,
        )
    
    @staticmethod
    def log_logout(request, user):
        """Log logout"""
        AuditLog.log_action(
            action='LOGOUT',
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
            action='USER_CREATE',
            request=request,
            user=actor_user,
            resource_type='ShopUser',
            resource_id=str(created_user.id),
            details={
                'created_user_id': created_user.id,
                'created_user_username': created_user.username,
                'role': created_user.role,
            }
        )
    
    @staticmethod
    def log_update(request, updated_user, actor_user, changes=None):
        """Log user update"""
        AuditLog.log_action(
            action='USER_UPDATE',
            request=request,
            user=actor_user,
            resource_type='ShopUser',
            resource_id=str(updated_user.id),
            details={
                'updated_user_id': updated_user.id,
                'changes': changes or {},
            }
        )
    
    @staticmethod
    def log_delete(request, deleted_user, actor_user):
        """Log user deletion"""
        AuditLog.log_action(
            action='USER_DELETE',
            request=request,
            user=actor_user,
            resource_type='ShopUser',
            resource_id=str(deleted_user.id),
            details={
                'deleted_user_id': deleted_user.id,
                'deleted_user_username': deleted_user.username,
            }
        )
    
    @staticmethod
    def log_role_change(request, user, old_role, new_role, actor_user):
        """Log role change"""
        AuditLog.log_action(
            action='ROLE_CHANGE',
            request=request,
            user=actor_user,
            resource_type='ShopUser',
            resource_id=str(user.id),
            details={
                'user_id': user.id,
                'old_role': old_role,
                'new_role': new_role,
            }
        )
