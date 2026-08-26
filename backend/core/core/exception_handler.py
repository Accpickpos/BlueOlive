"""
Global exception handler for BlueOlive API.

This module provides centralized exception handling that ensures all API errors
return a consistent format. It handles both custom BlueOlive exceptions and
standard Django/DRF exceptions.

Standard Error Response Format:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {...},  // Optional additional details
        "field_errors": {...}  // Optional field-specific errors
    }
}

Usage:
    Add to REST_FRAMEWORK settings:
    'EXCEPTION_HANDLER': 'core.exception_handler.custom_exception_handler'
"""

import logging
import traceback
from typing import Any, Dict, Optional

from core.exceptions import (
    BlueOliveException,
    BusinessRuleError,
    ConflictError,
    DuplicateError,
    InternalServerError,
    NotFoundError,
    PermissionError,
    TokenError,
)
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
)
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied
from rest_framework.exceptions import (
    Throttled,
)
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(
    exc: Exception, context: Dict[str, Any]
) -> Optional[Response]:
    """
    Custom exception handler for DRF that provides consistent error responses.

    This handler:
    1. Handles custom BlueOliveException subclasses with standardized format
    2. Converts standard DRF exceptions to the standard format
    3. Catches any unhandled exceptions and returns a generic 500 error

    Args:
        exc: The exception that was raised
        context: Context dictionary containing view info

    Returns:
        Response object with standardized error format, or None
    """
    # First, try the custom BlueOlive exceptions
    if isinstance(exc, BlueOliveException):
        return _handle_blueolive_exception(exc)

    # Handle Django exceptions
    if isinstance(exc, Http404):
        return _handle_not_found(exc)

    if isinstance(exc, PermissionDenied):
        return _handle_permission_denied(exc)

    if isinstance(exc, ValidationError):
        return _handle_django_validation_error(exc)

    if isinstance(exc, DatabaseError):
        return _handle_database_error(exc)

    # Handle DRF exceptions
    response = exception_handler(exc, context)

    if response is not None:
        return _handle_drf_exception(exc, response)

    # Handle uncaught exceptions
    return _handle_uncaught_exception(exc, context)


def _handle_blueolive_exception(exc: BlueOliveException) -> Response:
    """
    Handle custom BlueOlive exceptions.

    Args:
        exc: BlueOliveException instance

    Returns:
        Response with standardized error format
    """
    logger.warning(
        f"BlueOlive exception: {exc.code} - {exc.message}",
        extra={
            "error_code": exc.code,
            "error_details": exc.details,
            "field_errors": exc.field_errors,
        },
    )

    response_data = {"error": exc.to_dict()}

    return Response(response_data, status=exc.status_code)


def _handle_not_found(exc: Http404) -> Response:
    """Handle Django Http404 exception."""
    response_data = {
        "error": {
            "code": "NOT_FOUND",
            "message": str(exc) or "Resource not found",
        }
    }
    return Response(response_data, status=status.HTTP_404_NOT_FOUND)


def _handle_permission_denied(exc: PermissionDenied) -> Response:
    """Handle Django PermissionDenied exception."""
    response_data = {
        "error": {
            "code": "PERMISSION_DENIED",
            "message": str(exc) or "You do not have permission to perform this action",
        }
    }
    return Response(response_data, status=status.HTTP_403_FORBIDDEN)


def _handle_django_validation_error(exc: ValidationError) -> Response:
    """Handle Django ValidationError."""
    field_errors = {}

    if hasattr(exc, "message_dict"):
        # Form/Model validation error with field-specific messages
        field_errors = exc.message_dict
        message = "Validation failed"
    elif hasattr(exc, "message"):
        message = str(exc.message)
    else:
        message = "Validation failed"

    response_data = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": message,
            "field_errors": field_errors if field_errors else None,
        }
    }

    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


def _handle_database_error(exc: DatabaseError) -> Response:
    """Handle database errors."""
    logger.error(f"Database error: {str(exc)}", exc_info=True)

    response_data = {
        "error": {
            "code": "DATABASE_ERROR",
            "message": "A database error occurred. Please try again later.",
        }
    }
    return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _handle_drf_exception(exc: APIException, response: Response) -> Response:
    """
    Handle standard DRF exceptions with consistent format.

    Args:
        exc: DRF APIException instance
        response: Original response from DRF

    Returns:
        Response with standardized error format
    """
    # Determine the error code based on exception type
    if isinstance(exc, NotAuthenticated):
        code = "AUTHENTICATION_REQUIRED"
        message = str(exc.detail) if exc.detail else "Authentication required"
    elif isinstance(exc, AuthenticationFailed):
        code = "AUTHENTICATION_FAILED"
        message = str(exc.detail) if exc.detail else "Authentication failed"
    elif isinstance(exc, DRFPermissionDenied):
        code = "PERMISSION_DENIED"
        message = str(exc.detail) if exc.detail else "Permission denied"
    elif isinstance(exc, NotFound):
        code = "NOT_FOUND"
        message = str(exc.detail) if exc.detail else "Resource not found"
    elif isinstance(exc, DRFValidationError):
        code = "VALIDATION_ERROR"
        message = _get_validation_message(exc.detail)
        field_errors = _get_field_errors(exc.detail)
    elif isinstance(exc, Throttled):
        code = "RATE_LIMITED"
        message = str(exc.detail) if exc.detail else "Rate limit exceeded"
    else:
        code = exc.__class__.__name__.upper().replace("_", "")
        message = str(exc.detail) if exc.detail else "An error occurred"

    # Build standardized response
    error_response = {
        "error": {
            "code": code,
            "message": message,
        }
    }

    # Add field errors for validation errors
    if isinstance(exc, DRFValidationError):
        field_errors = _get_field_errors(exc.detail)
        if field_errors:
            error_response["error"]["field_errors"] = field_errors

    return Response(error_response, status=response.status_code)


def _handle_uncaught_exception(exc: Exception, context: Dict[str, Any]) -> Response:
    """
    Handle any uncaught exceptions.

    This is the fallback handler for exceptions not caught by any other handler.
    It logs the full traceback and returns a generic 500 error.

    Args:
        exc: Uncaught exception
        context: Exception context

    Returns:
        Response with generic 500 error
    """
    # Get view information for logging
    view = context.get("view", None)
    view_name = view.__class__.__name__ if view else "Unknown"

    # Log the full traceback
    logger.error(
        f"Unhandled exception in {view_name}: {type(exc).__name__}: {str(exc)}",
        exc_info=True,
        extra={
            "view": view_name,
            "exception_type": type(exc).__name__,
        },
    )

    # Return generic error in production, detailed error in debug
    from django.conf import settings

    response_data = {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An internal error occurred. Please try again later.",
        }
    }

    if settings.DEBUG:
        response_data["error"]["details"] = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        }

    return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _get_validation_message(detail: Any) -> str:
    """Extract a human-readable message from validation error detail."""
    if isinstance(detail, str):
        return detail
    elif isinstance(detail, list):
        if detail:
            return str(detail[0])
        return "Validation failed"
    elif isinstance(detail, dict):
        # Get first field error
        for key, value in detail.items():
            return _get_validation_message(value)
    return "Validation failed"


def _get_field_errors(detail: Any) -> Optional[Dict[str, Any]]:
    """Extract field errors from validation error detail."""
    if isinstance(detail, dict):
        # Check if it's field-specific errors
        errors = {}
        for key, value in detail.items():
            if isinstance(value, list):
                errors[key] = [str(v) for v in value]
            elif isinstance(value, dict):
                errors[key] = _get_field_errors(value)
            else:
                errors[key] = [str(value)]
        return errors if errors else None
    return None


# =============================================================================
# Exception Handler for OpenAPI Schema Documentation
# =============================================================================


def get_error_schema() -> Dict[str, Any]:
    """
    Get OpenAPI schema for error responses.

    This can be used with drf-spectacular to document error responses.

    Returns:
        OpenAPI schema for error responses
    """
    return {
        "type": "object",
        "properties": {
            "error": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Error code for programmatic handling",
                        "example": "VALIDATION_ERROR",
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable error message",
                        "example": "Validation failed",
                    },
                    "details": {
                        "type": "object",
                        "description": "Additional error details",
                        "example": {"reason": "Invalid format"},
                    },
                    "field_errors": {
                        "type": "object",
                        "description": "Field-specific validation errors",
                        "example": {"email": ["Email is required"]},
                    },
                },
                "required": ["code", "message"],
            }
        },
        "required": ["error"],
    }
