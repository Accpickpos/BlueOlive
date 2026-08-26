"""
Async tasks for BlueOlive application.
Handles:
- Stock transaction processing
- Report generation
- Email notifications
- Bulk operations
"""

import logging
from datetime import date, timedelta

from celery import shared_task
from core.resilience import retry_with_backoff
from django.conf import settings
from django.core.mail import send_mail

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
        transaction.status = "processing"
        transaction.save()

        # Perform validations and updates
        transaction.status = "completed"
        transaction.save()

        logger.info(f"Stock transaction {transaction_id} processed successfully")
        return {"status": "success", "transaction_id": transaction_id}

    except Exception as exc:
        logger.error(
            f"Failed to process stock transaction {transaction_id}: {str(exc)}"
        )
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2**self.request.retries)


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
        return {"status": "success", "report_type": report_type, "shop_id": shop_id}

    except Exception as exc:
        logger.error(f"Failed to generate {report_type} report: {str(exc)}")
        raise self.retry(exc=exc, countdown=2**self.request.retries)


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
        return {"status": "success", "recipient": recipient}

    except Exception as exc:
        logger.error(f"Failed to send email to {recipient}: {str(exc)}")
        raise self.retry(exc=exc, countdown=2**self.request.retries)


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

        model = (
            apps.get_model("stock_control", model_name)
            if hasattr(apps, model_name)
            else None
        )
        if not model:
            raise ValueError(f"Model {model_name} not found")

        # Create objects in batches
        batch_size = 100
        created_count = 0

        for i in range(0, len(objects_data), batch_size):
            batch = objects_data[i : i + batch_size]
            objs = [model(**obj_data) for obj_data in batch]
            model.objects.bulk_create(objs, batch_size=batch_size)
            created_count += len(objs)

        logger.info(f"Successfully bulk created {created_count} {model_name} objects")
        return {
            "status": "success",
            "created_count": created_count,
            "model": model_name,
        }

    except Exception as exc:
        logger.error(f"Failed to bulk create {model_name} objects: {str(exc)}")
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@shared_task
def cleanup_old_tasks():
    """
    Periodic task to cleanup old celery task results.
    Should be scheduled to run daily (e.g., 2 AM).
    """
    try:
        from datetime import timedelta

        from django.utils import timezone
        from django_celery_results.models import TaskResult

        logger.info("Cleaning up old task results")

        # Delete task results older than 7 days
        cutoff_date = timezone.now() - timedelta(days=7)
        deleted_count, _ = TaskResult.objects.filter(date_done__lt=cutoff_date).delete()

        logger.info(f"Cleaned up {deleted_count} old task results")
        return {"status": "success", "deleted_count": deleted_count}

    except Exception as exc:
        logger.error(f"Cleanup task failed: {str(exc)}")
        return {"status": "failed", "error": str(exc)}


# ═══════════════════════════════════════════════════════════════════════════
# PERIOD END TASKS - Day-End, Month-End, Year-End
# ═══════════════════════════════════════════════════════════════════════════


def _check_period_end_enabled(process_type: str) -> bool:
    """
    Check if the given period-end process is enabled in system configuration.

    Args:
        process_type: 'day_end', 'month_end', or 'year_end'

    Returns:
        True if the process is enabled, False otherwise
    """
    try:
        from apps.settings.models import SystemConfiguration

        config = SystemConfiguration.objects.first()
        if not config:
            logger.warning(
                f"No SystemConfiguration found, {process_type} will run anyway"
            )
            return True

        if process_type == "day_end":
            return config.enable_auto_day_end
        elif process_type == "month_end":
            return config.enable_auto_month_end
        elif process_type == "year_end":
            return config.enable_auto_year_end
        return True
    except Exception as e:
        logger.warning(f"Error checking {process_type} config: {e}, running anyway")
        return True


@shared_task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3)
def run_day_end_task(self, process_date: str = None, shop_id: int = None):
    """
    Execute day-end process.

    Args:
        process_date: Date string (YYYY-MM-DD) to process, defaults to yesterday
        shop_id: Optional shop ID to filter by
    """
    # Check if day-end is enabled
    if not _check_period_end_enabled("day_end"):
        logger.info("Day-end process is disabled in configuration, skipping")
        return {"status": "skipped", "message": "Day-end is disabled in configuration"}

    try:
        from datetime import datetime

        from apps.settings.period_end_services import DayEndService

        if process_date:
            process_date = datetime.strptime(process_date, "%Y-%m-%d").date()
        else:
            process_date = date.today() - timedelta(days=1)

        logger.info(f"Running day-end task for {process_date}")

        result = DayEndService.run_day_end(process_date=process_date, shop_id=shop_id)

        logger.info(f"Day-end task completed: {result.message}")
        return result.to_dict()

    except Exception as exc:
        logger.error(f"Day-end task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@shared_task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3)
def run_month_end_task(self, process_date: str = None, advance_period: bool = True):
    """
    Execute month-end process.

    Args:
        process_date: Date string (YYYY-MM-DD) for month-end, defaults to last month
        advance_period: Whether to advance the accounting period
    """
    # Check if month-end is enabled
    if not _check_period_end_enabled("month_end"):
        logger.info("Month-end process is disabled in configuration, skipping")
        return {
            "status": "skipped",
            "message": "Month-end is disabled in configuration",
        }

    try:
        from datetime import datetime

        from apps.settings.period_end_services import MonthEndService

        if process_date:
            process_date = datetime.strptime(process_date, "%Y-%m-%d").date()
        else:
            # Default to last month
            today = date.today()
            if today.month == 1:
                process_date = date(today.year - 1, 12, 1)
            else:
                process_date = date(today.year, today.month - 1, 1)

        logger.info(f"Running month-end task for {process_date}")

        result = MonthEndService.run_month_end(
            process_date=process_date, advance_period=advance_period
        )

        logger.info(f"Month-end task completed: {result.message}")
        return result.to_dict()

    except Exception as exc:
        logger.error(f"Month-end task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@shared_task(bind=True, max_retries=3)
@retry_with_backoff(max_retries=3)
def run_year_end_task(self, process_year: int = None, advance_year: bool = True):
    """
    Execute year-end process.

    Args:
        process_year: Year to process, defaults to previous year
        advance_year: Whether to advance the financial year
    """
    # Check if year-end is enabled
    if not _check_period_end_enabled("year_end"):
        logger.info("Year-end process is disabled in configuration, skipping")
        return {"status": "skipped", "message": "Year-end is disabled in configuration"}

    try:
        from apps.settings.period_end_services import YearEndService

        if process_year is None:
            process_year = date.today().year - 1

        logger.info(f"Running year-end task for {process_year}")

        result = YearEndService.run_year_end(
            process_year=process_year, advance_year=advance_year
        )

        logger.info(f"Year-end task completed: {result.message}")
        return result.to_dict()

    except Exception as exc:
        logger.error(f"Year-end task failed: {str(exc)}")
        raise self.retry(exc=exc, countdown=2**self.request.retries)
