"""
Custom exception classes for BlueOlive API.

This module provides a hierarchy of exceptions that map to standard HTTP error codes
and can be easily handled by the global exception handler for consistent API responses.

Usage:
    from core.exceptions import ValidationError, NotFoundError

    # In views:
    raise ValidationError("Invalid input", field_errors={"email": "Email is required"})
"""

from typing import Any, Optional


class BlueOliveException(Exception):
    """
    Base exception for all BlueOlive application errors.

    All custom exceptions should inherit from this class to ensure
    consistent error handling across the API.
    """

    # Default values - override in subclasses
    code: str = "BLUEOLIVE_ERROR"
    status_code: int = 500
    message: str = "An internal error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Any = None,
        field_errors: Optional[dict] = None,
    ):
        """
        Initialize exception with optional details.

        Args:
            message: Human-readable error message
            details: Additional error details (dict, list, or other)
            field_errors: Field-specific validation errors
        """
        if message:
            self.message = message

        self.details = details
        self.field_errors = field_errors or {}

        super().__init__(self.message)

    def to_dict(self) -> dict:
        """
        Convert exception to dictionary for JSON response.

        Returns:
            Dictionary representation of the error
        """
        error_dict = {
            "code": self.code,
            "message": self.message,
        }

        if self.details is not None:
            error_dict["details"] = self.details

        if self.field_errors:
            error_dict["field_errors"] = self.field_errors

        return error_dict


# =============================================================================
# Client Error Exceptions (4xx)
# =============================================================================


class BadRequestError(BlueOliveException):
    """400 - The request was invalid or cannot be served."""

    code = "BAD_REQUEST"
    status_code = 400
    message = "Bad request"


class ValidationError(BlueOliveException):
    """400 - Input validation failed."""

    code = "VALIDATION_ERROR"
    status_code = 400
    message = "Validation failed"

    def __init__(
        self,
        message: str = "Validation failed",
        details: Any = None,
        field_errors: Optional[dict] = None,
    ):
        super().__init__(message=message, details=details, field_errors=field_errors)


class AuthenticationError(BlueOliveException):
    """401 - Authentication required or failed."""

    code = "AUTHENTICATION_ERROR"
    status_code = 401
    message = "Authentication required"


class InvalidCredentialsError(AuthenticationError):
    """401 - Invalid username or password."""

    code = "INVALID_CREDENTIALS"
    status_code = 401
    message = "Invalid username or password"


class TokenError(AuthenticationError):
    """401 - Token is invalid, expired, or revoked."""

    code = "TOKEN_ERROR"
    status_code = 401
    message = "Invalid or expired token"


class PermissionError(BlueOliveException):
    """403 - Access denied to the requested resource."""

    code = "PERMISSION_DENIED"
    status_code = 403
    message = "You do not have permission to perform this action"


class TenantAccessError(PermissionError):
    """403 - User does not have access to the requested tenant."""

    code = "TENANT_ACCESS_DENIED"
    status_code = 403
    message = "You do not have access to this tenant"


class ShopAccessError(PermissionError):
    """403 - User does not have access to the requested shop."""

    code = "SHOP_ACCESS_DENIED"
    status_code = 403
    message = "You do not have access to this shop"


class NotFoundError(BlueOliveException):
    """404 - The requested resource was not found."""

    code = "NOT_FOUND"
    status_code = 404
    message = "Resource not found"

    def __init__(self, resource: str = "Resource", identifier: Any = None):
        """
        Initialize NotFoundError with resource information.

        Args:
            resource: Type of resource (e.g., "Invoice", "Customer")
            identifier: The specific identifier that was not found
        """
        if identifier:
            message = f"{resource} not found: {identifier}"
        else:
            message = f"{resource} not found"

        super().__init__(message=message)
        self.resource = resource
        self.identifier = identifier


class ConflictError(BlueOliveException):
    """409 - Request conflicts with current state."""

    code = "CONFLICT"
    status_code = 409
    message = "Request conflicts with current state"


class DuplicateError(ConflictError):
    """409 - Resource already exists."""

    code = "DUPLICATE_ENTRY"
    status_code = 409
    message = "Resource already exists"


class BusinessRuleError(BlueOliveException):
    """
    422 - Request follows wrong business logic/rules.

    Use this for domain-specific validation that isn't just field validation,
    but business rule violations (e.g., "Cannot delete order with pending payments").
    """

    code = "BUSINESS_RULE_VIOLATION"
    status_code = 422
    message = "Business rule violation"


class InvalidStateError(BusinessRuleError):
    """422 - Resource is in invalid state for this operation."""

    code = "INVALID_STATE"
    status_code = 422
    message = "Resource is in invalid state for this operation"


# =============================================================================
# Server Error Exceptions (5xx)
# =============================================================================


class InternalServerError(BlueOliveException):
    """500 - Internal server error."""

    code = "INTERNAL_ERROR"
    status_code = 500
    message = "An internal error occurred"


class ServiceUnavailableError(BlueOliveException):
    """503 - Service is temporarily unavailable."""

    code = "SERVICE_UNAVAILABLE"
    status_code = 503
    message = "Service is temporarily unavailable"


class DatabaseError(InternalServerError):
    """500 - Database operation failed."""

    code = "DATABASE_ERROR"
    status_code = 500
    message = "Database operation failed"


# =============================================================================
# Tenant-Specific Exceptions
# =============================================================================


class TenantNotFoundError(NotFoundError):
    """404 - Tenant not found."""

    code = "TENANT_NOT_FOUND"
    status_code = 404
    message = "Tenant not found"

    def __init__(self, tenant_slug: str):
        super().__init__(resource="Tenant", identifier=tenant_slug)


class TenantInactiveError(PermissionError):
    """403 - Tenant is inactive."""

    code = "TENANT_INACTIVE"
    status_code = 403
    message = "Tenant account is inactive"


class ShopNotFoundError(NotFoundError):
    """404 - Shop not found."""

    code = "SHOP_NOT_FOUND"
    status_code = 404
    message = "Shop not found"

    def __init__(self, shop_identifier: str):
        super().__init__(resource="Shop", identifier=shop_identifier)


# =============================================================================
# Utility Functions
# =============================================================================


def exception_from_django_validation_error(exc) -> ValidationError:
    """
    Convert Django ValidationError to BlueOlive ValidationError.

    Args:
        exc: Django ValidationError

    Returns:
        BlueOlive ValidationError with field errors
    """
    if hasattr(exc, "message_dict"):
        # Form validation error
        return ValidationError(
            message="Validation failed", field_errors=exc.message_dict
        )
    elif hasattr(exc, "message"):
        # Single field error
        return ValidationError(
            message=str(exc.message),
            field_errors={"non_field_errors": [str(exc.message)]},
        )
    else:
        return ValidationError(message=str(exc))
