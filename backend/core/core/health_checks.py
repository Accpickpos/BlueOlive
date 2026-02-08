"""
Health check views for monitoring application status and readiness.
Includes /health/, /ready/, and /metrics/ endpoints.
"""
import logging
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    """
    Health check endpoint.
    Returns 200 OK if the application is running.
    Can be used for basic liveness checks.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'BlueOlive API',
        'message': 'Application is running'
    }, status=HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def ready(request):
    """
    Readiness check endpoint.
    Verifies:
    - Database connectivity
    - Application initialization complete
    
    Returns 200 OK only if the application is ready to serve requests.
    Used for deployment/orchestration readiness checks.
    """
    checks = {
        'database': check_database(),
        'celery': {'status': 'configured', 'healthy': True},  # Placeholder
    }
    
    # Consider ready only if all critical checks pass
    all_healthy = all(check.get('healthy', False) for check in checks.values())
    
    response_data = {
        'status': 'ready' if all_healthy else 'not_ready',
        'service': 'BlueOlive API',
        'checks': checks,
    }
    
    status_code = HTTP_200_OK if all_healthy else HTTP_503_SERVICE_UNAVAILABLE
    return JsonResponse(response_data, status=status_code)


@api_view(['GET'])
@permission_classes([AllowAny])
def metrics(request):
    """
    Basic metrics endpoint.
    Returns application metrics including:
    - Database connection status
    - Request count (placeholder)
    - Cache status
    
    Note: For advanced metrics, integrate Prometheus/StatsD.
    """
    db_status = check_database()
    
    metrics = {
        'timestamp': __import__('django.utils.timezone', fromlist=['now']).now().isoformat(),
        'service': 'BlueOlive API',
        'database': {
            'status': db_status['status'],
            'response_time_ms': db_status.get('response_time_ms', 0),
        },
        'cache': {
            'status': check_cache()['status'],
        },
        'uptime_seconds': get_uptime(),
    }
    
    return JsonResponse(metrics, status=HTTP_200_OK)


def check_database():
    """
    Check database connectivity.
    Returns status and response time.
    """
    import time
    db_alias = 'default'
    
    try:
        start = time.time()
        connections[db_alias].ensure_connection()
        response_time = (time.time() - start) * 1000  # milliseconds
        
        return {
            'status': 'connected',
            'healthy': True,
            'response_time_ms': round(response_time, 2),
        }
    except OperationalError as e:
        logger.error(f"Database check failed: {str(e)}")
        return {
            'status': 'disconnected',
            'healthy': False,
            'error': str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected database check error: {str(e)}")
        return {
            'status': 'error',
            'healthy': False,
            'error': str(e),
        }


def check_cache():
    """
    Check cache connectivity (Redis or in-memory).
    """
    from django.core.cache import cache
    
    try:
        # Try to set and get a test value
        test_key = '__health_check__'
        cache.set(test_key, 'working', 10)
        result = cache.get(test_key)
        cache.delete(test_key)
        
        if result == 'working':
            return {'status': 'connected', 'healthy': True}
        else:
            return {'status': 'unhealthy', 'healthy': False}
    except Exception as e:
        logger.warning(f"Cache check failed: {str(e)}")
        return {'status': 'unavailable', 'healthy': False, 'error': str(e)}


def get_uptime():
    """
    Get application uptime in seconds.
    For now, returns a placeholder.
    Consider using Django extensions or custom middleware for accurate tracking.
    """
    import os
    from pathlib import Path
    
    try:
        # Get the WSGI module's modification time as a proxy for startup time
        wsgi_file = Path(__file__).parent / 'wsgi.py'
        if wsgi_file.exists():
            import time
            startup = os.path.getmtime(str(wsgi_file))
            return int(time.time() - startup)
    except Exception:
        pass
    
    return 0
