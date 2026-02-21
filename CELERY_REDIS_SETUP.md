# Celery & Redis Configuration Guide

## Overview
Your BlueOlive application is now configured to use **Celery** with **Redis** as the message broker and result backend.

## Current Configuration

### Redis Setup (Docker)
- **Host**: localhost
- **Port**: 6379
- **Database 0**: Celery broker & results
- **Database 1**: Cache backend

### Celery Configuration
- **Broker**: `redis://127.0.0.1:6379/0`
- **Result Backend**: `redis://127.0.0.1:6379/0`
- **Task Serialization**: JSON
- **Windows Pool**: `solo` (single-threaded, no multiprocessing)
- **Unix/Linux Pool**: `prefork` (multiprocessing for better performance)
- **Beat Scheduler**: Database-backed (django_celery_beat)

### Environment Variables
The following have been added to `.env`:
```
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
CACHE_BACKEND=redis
REDIS_URL=redis://127.0.0.1:6379/1
```

### Django Apps Added
- `django_celery_beat`: Scheduled task management
- `django_celery_results`: Task result storage

## Critical Fix: Windows Compatibility

### Issue
Celery's default `prefork` pool uses multiprocessing and doesn't work on Windows because Windows doesn't support the `fork()` system call. This caused:
- `PermissionError` on worker pool processes
- Worker crashes with semlock errors
- Worker unable to process any tasks

### Solution Applied
Updated `core/settings.py` to automatically detect the OS and use:
- **Windows**: `solo` pool (single-threaded, suitable for development)
- **Unix/Linux**: `prefork` pool (multiprocessing, better performance)

Code excerpt from settings.py:
```python
if platform.system() == 'Windows' or sys.platform == 'win32':
    CELERY_WORKER_POOL = 'solo'  # Single-threaded (Windows doesn't support fork)
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
else:
    CELERY_WORKER_POOL = 'prefork'  # Use multiprocessing (Unix/Linux)
    CELERY_WORKER_PREFETCH_MULTIPLIER = 4
```

## Starting Celery (Corrected for Windows)

### Option 1: Celery Worker Only (Windows)
```bash
cd backend/core
celery -A core worker --pool=solo --loglevel=info
```

Or use the provided script:
```bash
backend\start_celery_worker.bat
```

### Option 2: Celery Worker + Beat (Windows)
```bash
cd backend/core
celery -A core worker --beat --pool=solo --loglevel=info
```

### Option 3: Celery Beat Separately (Windows)
**Terminal 1: Worker**
```bash
cd backend/core
celery -A core worker --pool=solo --loglevel=info
```

**Terminal 2: Beat**
```bash
cd backend/core
celery -A core beat --loglevel=info
```

### For Linux/Mac
The startup scripts automatically use `--pool=prefork` for better performance.

```bash
# Linux/Mac worker
celery -A core worker --pool=prefork --loglevel=info --concurrency=4

# Or using the script
bash backend/start_celery_worker.sh
```

## Testing the Setup

### Test Redis & Celery Connection
```bash
cd backend/core
python test_celery_redis.py
```

Expected output:
```
============================================================
Testing Celery & Redis Configuration
============================================================

[1] Testing Redis Connection...
✓ Redis connection successful

[2] Celery Configuration:
  Broker URL: redis://127.0.0.1:6379/0
  Result Backend: redis://127.0.0.1:6379/0
  Task Serializer: json

[3] Testing Celery Debug Task...
✓ Debug task submitted (Task ID: xxx)

[4] Checking Task Result Backend...
✓ Task queued (worker may not be running yet)

============================================================
Configuration Summary:
============================================================
✓ Redis is running and accessible
✓ Celery is configured to use Redis on port 6379
✓ Database 0 is used for broker and results
✓ Database 1 is used for caching
```

## Using Celery in Your Code

### Define a Task
```python
# In any app's tasks.py file
from celery import shared_task

@shared_task
def my_async_task(data):
    """Async task that runs in a worker."""
    return f"Processed: {data}"
```

### Call a Task
```python
from apps.myapp.tasks import my_async_task

# Asynchronously (returns immediately)
result = my_async_task.delay(data="example")
print(f"Task ID: {result.id}")

# Get result later
from celery.result import AsyncResult
async_result = AsyncResult(result.id)
print(f"Status: {async_result.status}")
print(f"Result: {async_result.result}")
```

### Schedule Periodic Tasks
Use Django admin to create scheduled tasks via `django_celery_beat`:
1. Go to `/admin/django_celery_beat/periodictask/`
2. Create new periodic tasks
3. Celery Beat will execute them according to the schedule

## Troubleshooting

### Error: PermissionError in Worker Pool (Windows)
**Cause**: Using `prefork` pool on Windows (not compatible)
**Solution**: Use `--pool=solo` flag when starting worker

### Redis Connection Issues
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check specific database
redis-cli -n 0 INFO
```

### Celery Worker Not Processing Tasks
1. Ensure Redis is running: `redis-cli ping`
2. Check worker is actually running: `celery -A core inspect active`
3. Check for errors in worker logs
4. Verify task is in queue: `redis-cli -n 0 LLEN celery`

### Database Warnings During Startup
Fixed by:
- Updated `tenancy/apps.py` to skip database access during celery worker startup
- Updated `core/settings.py` to detect Windows vs Unix/Linux

### Celery 6.0 Deprecation Warning
The warning about `broker_connection_retry` has been suppressed by adding:
```python
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True
```

## Database Migrations

After adding django_celery_beat and django_celery_results, run:
```bash
cd backend/core
python manage.py migrate django_celery_beat
python manage.py migrate django_celery_results
```

## Performance Considerations

### Windows Development (Solo Pool)
- Single-threaded, processes one task at a time
- Perfect for development and testing
- No multiprocessing overhead
- Good for I/O-bound tasks (API calls, file operations)

### Production (Prefork Pool - Unix/Linux)
For production deployments on Unix/Linux, you can increase concurrency:
```bash
celery -A core worker --pool=prefork --loglevel=info --concurrency=8
```

### Monitor Tasks with Flower
```bash
pip install flower
celery -A core flower
# Access at http://localhost:5555
```

## Version Info
- **Celery**: 5.3.0
- **Redis**: 5.0.1+
- **Django**: 5.2.7
- **Python**: 3.11+

## Important Notes

### Windows-Specific
- Use `--pool=solo` for Windows (automatically set in settings.py)
- Soft timeouts are not supported on Windows (they require SIGUSR1 signal)
- For production on Windows, consider using Docker or WSL2

### Task IDs
All task IDs can be queried via Redis:
```bash
redis-cli -n 0
> KEYS celery*
> LRANGE celery 0 -1  # View queue
```

### Celery Command Reference
```bash
# Worker commands
celery -A core worker              # Start worker
celery -A core worker --beat       # Worker + Beat
celery -A core worker --autoscale=10,3  # Auto-scaling

# Beat commands
celery -A core beat                # Start scheduler
celery -A core beat -s celery_beat.db  # Use database scheduler

# Inspect commands
celery -A core inspect active      # Active tasks
celery -A core inspect stats       # Worker stats
celery -A core inspect registered  # Registered tasks
celery -A core purge               # Clear all queued tasks
```

## Resources
- [Celery Documentation](https://docs.celeryproject.org/)
- [Celery Windows Support](https://docs.celeryproject.org/en/stable/getting-started/brokers/redis.html#windows-support)
- [Redis Documentation](https://redis.io/docs/)
- [django_celery_beat](https://github.com/celery/django-celery-beat/)

