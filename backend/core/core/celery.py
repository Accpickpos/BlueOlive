"""
Celery configuration and initialization.
Handles async task execution for:
- Stock transaction processing
- Report generation
- Email notifications
- Bulk operations
"""
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('blueolive')

# Load configuration from Django settings (CELERY_ prefix)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery connection."""
    print(f'Request: {self.request!r}')
