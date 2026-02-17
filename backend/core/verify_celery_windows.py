#!/usr/bin/env python
"""
Windows-specific Celery verification script.
Ensures Celery is configured correctly with the solo pool for Windows.

Run from: cd backend/core && python verify_celery_windows.py
"""

import os
import sys
import django
import platform

# Add the core project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core.celery import app as celery_app
from django.conf import settings

print("=" * 70)
print("Windows Celery Configuration Verification")
print("=" * 70)

# Check OS
print(f"\n[1] Detected OS: {platform.system()}")
if platform.system() == 'Windows':
    print("    ✓ Windows detected - Solo pool should be enabled")
else:
    print(f"    ℹ {platform.system()} detected - Prefork pool should be enabled")

# Check Pool Configuration
print("\n[2] Celery Worker Pool Configuration:")
print(f"    Pool Type: {getattr(settings, 'CELERY_WORKER_POOL', 'default (prefork)')}")
print(f"    Prefetch: {getattr(settings, 'CELERY_WORKER_PREFETCH_MULTIPLIER', 4)}")

if platform.system() == 'Windows':
    expected_pool = 'solo'
    if getattr(settings, 'CELERY_WORKER_POOL', None) != 'solo':
        print("    ⚠ WARNING: CELERY_WORKER_POOL is not set to 'solo' for Windows!")
        sys.exit(1)
    print("    ✓ Correctly configured for Windows")

# Check Broker/Results
print("\n[3] Celery Broker & Results Backend:")
print(f"    Broker: {celery_app.conf.broker_url}")
print(f"    Results: {celery_app.conf.result_backend}")

if 'redis://' in celery_app.conf.broker_url:
    print("    ✓ Using Redis broker")
else:
    print("    ⚠ Not using Redis broker")

# Check Core Settings
print("\n[4] Celery Settings:")
print(f"    Task Serializer: {celery_app.conf.task_serializer}")
print(f"    Result Serializer: {celery_app.conf.result_serializer}")
print(f"    Accept Content: {celery_app.conf.accept_content}")
print(f"    UTC Enabled: {celery_app.conf.enable_utc}")
print(f"    Broker Retry on Startup: {getattr(settings, 'CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP', 'not set')}")

# Test Import
print("\n[5] Testing Task Discovery:")
try:
    from core.celery import debug_task
    print("    ✓ Core debug_task imported successfully")
except ImportError as e:
    print(f"    ✗ Failed to import debug_task: {e}")

# Summary
print("\n" + "=" * 70)
print("Configuration Ready for Windows Celery Worker")
print("=" * 70)

if platform.system() == 'Windows':
    print("\n✓ Your system is Windows")
    print("\nTo start the Celery worker, use:\n")
    print("    cd backend\\core")
    print("    celery -A core worker --pool=solo --loglevel=info")
    print("\nOr run the provided batch file:")
    print("    backend\\start_celery_worker.bat")
    print("\n" + "=" * 70)
else:
    print("\n✓ Your system is Unix/Linux")
    print("\nTo start the Celery worker, use:\n")
    print("    cd backend/core")
    print("    celery -A core worker --pool=prefork --loglevel=info --concurrency=4")
    print("\nOr run the provided shell script:")
    print("    bash backend/start_celery_worker.sh")
    print("\n" + "=" * 70)
