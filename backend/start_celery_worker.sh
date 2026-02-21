#!/bin/bash
# Start Celery Worker for BlueOlive on Linux/Mac
# Uses 'prefork' pool for better performance on Unix systems

cd "$(dirname "$0")/core"

# Start Celery worker with verbose logging
# Prefork pool: uses multiprocessing for better performance on Unix
celery -A core worker --pool=prefork --loglevel=info --concurrency=4

# To also run Celery Beat (scheduler), use:
# celery -A core worker --beat --loglevel=info --concurrency=4

# Or in a separate terminal:
# celery -A core beat --loglevel=info
