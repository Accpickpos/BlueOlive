"""
Async tasks for BlueOlive application.
Handles:
- Stock transaction processing
- Report generation
- Email notifications
- Bulk operations
"""
import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from core.resilience import retry_with_backoff

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3)
def process_stock_transaction(self, transaction_id):
    """
    Process stock transaction asynchronously.
    Includes retry logic with exponential backoff.
    
    Args:
        transaction_id: ID of the stock transaction to process
    """
    try:
        from apps.stock_control.models import StockTransaction
        
        transaction = StockTransaction.objects.get(id=transaction_id)
        logger.info(f"Processing stock transaction {transaction_id}")
        
        # Simulate transaction processing
        transaction.status = 'processing'
        transaction.save()
        
        # Perform validations and updates
        transaction.status = 'completed'
        transaction.save()
        
        logger.info(f"Stock transaction {transaction_id} processed successfully")
        return {'status': 'success', 'transaction_id': transaction_id}
        
    except Exception as exc:
        logger.error(f"Failed to process stock transaction {transaction_id}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3)
def generate_report(self, report_type, shop_id, filters=None):
    """
    Generate business report asynchronously.
    
    Args:
        report_type: Type of report (sales, inventory, creditors, etc.)
        shop_id: ID of the shop
        filters: Optional filter parameters
    """
    try:
        logger.info(f"Generating {report_type} report for shop {shop_id}")
        
        # Report generation logic would go here
        # This is a placeholder for the actual implementation
        
        logger.info(f"Report {report_type} generated successfully for shop {shop_id}")
        return {
            'status': 'success',
            'report_type': report_type,
            'shop_id': shop_id
        }
        
    except Exception as exc:
        logger.error(f"Failed to generate {report_type} report: {str(exc)}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3)
def send_notification_email(self, recipient, subject, message, html_message=None):
    """
    Send email notification asynchronously.
    
    Args:
        recipient: Email address of recipient
        subject: Email subject
        message: Email body (plain text)
        html_message: HTML email body (optional)
    """
    try:
        logger.info(f"Sending email to {recipient}")
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Email sent successfully to {recipient}")
        return {'status': 'success', 'recipient': recipient}
        
    except Exception as exc:
        logger.error(f"Failed to send email to {recipient}: {str(exc)}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task(bind=True, max_retries=2)
@retry_with_backoff(max_retries=2)
def bulk_create_objects(self, model_name, objects_data):
    """
    Create multiple objects in bulk.
    
    Args:
        model_name: Name of the model (e.g., 'StockItem', 'DebtorTransaction')
        objects_data: List of dictionaries with object data
    """
    try:
        from django.apps import apps
        
        logger.info(f"Bulk creating {len(objects_data)} {model_name} objects")
        
        model = apps.get_model('stock_control', model_name) if hasattr(apps, model_name) else None
        if not model:
            raise ValueError(f"Model {model_name} not found")
        
        # Create objects in batches
        batch_size = 100
        created_count = 0
        
        for i in range(0, len(objects_data), batch_size):
            batch = objects_data[i:i + batch_size]
            objs = [model(**obj_data) for obj_data in batch]
            model.objects.bulk_create(objs, batch_size=batch_size)
            created_count += len(objs)
        
        logger.info(f"Successfully bulk created {created_count} {model_name} objects")
        return {'status': 'success', 'created_count': created_count, 'model': model_name}
        
    except Exception as exc:
        logger.error(f"Failed to bulk create {model_name} objects: {str(exc)}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


@shared_task
def cleanup_old_tasks():
    """
    Periodic task to cleanup old celery task results.
    Should be scheduled to run daily (e.g., 2 AM).
    """
    try:
        from django_celery_results.models import TaskResult
        from django.utils import timezone
        from datetime import timedelta
        
        logger.info("Cleaning up old task results")
        
        # Delete task results older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count, _ = TaskResult.objects.filter(date_done__lt=cutoff_date).delete()
        
        logger.info(f"Cleaned up {deleted_count} old task results")
        return {'status': 'success', 'deleted_count': deleted_count}
        
    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        return {'status': 'failed', 'error': str(exc)}
