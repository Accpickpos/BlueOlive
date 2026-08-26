"""
Structured JSON logging configuration for production observability.
Provides formatted JSON output for centralized logging systems (ELK, Splunk, CloudWatch, etc.).
"""

import logging
from datetime import datetime

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON formatter that adds contextual information to logs.
    Includes timestamp, log level, logger name, and message fields.
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Add custom fields
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno

        # Add request context if available
        if hasattr(record, "request"):
            log_record["request_method"] = getattr(record.request, "method", None)
            log_record["request_path"] = getattr(record.request, "path", None)
            client_ip = get_client_ip(record.request)
            if client_ip is not None:
                log_record["remote_addr"] = client_ip

        # Add user context if available
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id

        # Add tenant context if available
        if hasattr(record, "tenant_id"):
            log_record["tenant_id"] = record.tenant_id

        # Add shop context if available
        if hasattr(record, "shop_id"):
            log_record["shop_id"] = record.shop_id

        # Remove duplicate fields that jsonlogger adds
        log_record.pop("exc_info", None)
        log_record.pop("stack_info", None)


def get_client_ip(request):
    """
    Extract client IP from request, considering proxy headers.
    Handles both Django HttpRequest objects and other objects gracefully.
    """
    # Check if this is a Django request object with META attribute
    if not hasattr(request, "META"):
        return None

    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


class RequestLoggingMiddleware:
    """
    Middleware to add request context to log records.
    Adds request_method, request_path, and remote_addr to all logs during request handling.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Add request context to logging
        logger = logging.getLogger("django.request")

        try:
            # Store request info in the request object for loggers to access
            request.client_ip = get_client_ip(request)
            request.request_method = request.method
            request.request_path = request.path

            response = self.get_response(request)

            # Log successful request
            try:
                logger.info(
                    f"{request.method} {request.path} - {response.status_code}",
                    extra={
                        "request_method": request.method,
                        "request_path": request.path,
                        "status_code": response.status_code,
                        "remote_addr": request.client_ip,
                    },
                )
            except Exception as log_error:
                logger.warning(f"Failed to log request: {str(log_error)}")

            return response
        except Exception as e:
            # Log the error but don't suppress it - let Django handle the 500 error
            logger.error(f"Middleware error: {str(e)}", exc_info=True)
            raise
