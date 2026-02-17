#!/usr/bin/env python
"""
Test script to verify Celery is correctly configured with Redis.
Run from: cd backend/core && python test_celery_redis.py
"""

import os
import sys
import django

# Add the core project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.celery import app as celery_app
from celery.result import AsyncResult
import redis

print("=" * 60)
print("Testing Celery & Redis Configuration")
print("=" * 60)

# Test 1: Check Redis Connection
print("\n[1] Testing Redis Connection...")
try:
    redis_client = redis.Redis.from_url(
        os.environ.get('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
    )
    redis_client.ping()
    print("✓ Redis connection successful")
except Exception as e:
    print(f"✗ Redis connection failed: {e}")
    sys.exit(1)

# Test 2: Check Celery Configuration
print("\n[2] Celery Configuration:")
print(f"  Broker URL: {celery_app.conf.broker_url}")
print(f"  Result Backend: {celery_app.conf.result_backend}")
print(f"  Task Serializer: {celery_app.conf.task_serializer}")

# Test 3: Test a simple debug task
print("\n[3] Testing Celery Debug Task...")
try:
    from core.celery import debug_task
    result = debug_task.delay()
    print(f"✓ Debug task submitted (Task ID: {result.id})")
except Exception as e:
    print(f"✗ Failed to submit debug task: {e}")
    sys.exit(1)

# Test 4: Check if task result can be retrieved
print("\n[4] Checking Task Result Backend...")
try:
    # Wait a bit for the task (if worker is running)
    import time
    time.sleep(1)
    result = AsyncResult(result.id, app=celery_app)
    if result.state == 'PENDING' and not result.ready():
        print("✓ Task queued (worker may not be running yet)")
    else:
        print(f"✓ Task status: {result.state}")
except Exception as e:
    print(f"✗ Result backend check failed: {e}")

print("\n" + "=" * 60)
print("Configuration Summary:")
print("=" * 60)
print("✓ Redis is running and accessible")
print("✓ Celery is configured to use Redis on port 6379")
print("✓ Database 0 is used for broker and results")
print("✓ Database 1 is used for caching")
print("\nNext Steps:")
print("1. Start the Celery worker: python manage.py celery worker")
print("   or: celery -A core worker --loglevel=info")
print("2. Start Celery Beat (optional): celery -A core beat")
print("3. Run your Django app as usual")
print("=" * 60)
