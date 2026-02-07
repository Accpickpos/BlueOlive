"""
Management command to archive old cash book transactions
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from apps.cash_book.models import CashBookTransaction


class Command(BaseCommand):
    help = 'Archive cash book transactions older than specified month'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--month',
            type=str,
            default=None,
            help='Month to archive in format YYYY-MM (defaults to previous month)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be archived without making changes'
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Proceed without confirmation prompt'
        )
    
    def handle(self, *args, **options):
        # Determine archive month
        if options['month']:
            try:
                archive_date = timezone.datetime.strptime(options['month'], '%Y-%m').date()
                # Use last day of the month
                next_month = archive_date.replace(day=1) + timedelta(days=32)
                archive_date = (next_month - timedelta(days=next_month.day)).replace(day=1)
            except ValueError:
                raise CommandError('Invalid month format. Use YYYY-MM')
        else:
            # Use previous month
            today = timezone.now().date()
            archive_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        
        # Get transactions to archive
        cutoff_date = archive_date.replace(day=1)
        transactions = CashBookTransaction.objects.filter(
            transaction_date__lt=cutoff_date,
            is_archived=False
        )
        
        count = transactions.count()
        
        if count == 0:
            self.stdout.write(self.style.WARNING('No transactions to archive'))
            return
        
        self.stdout.write(
            f'Found {count} transactions to archive for month {archive_date.strftime("%Y-%m")}'
        )
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('[DRY RUN] No changes made'))
            return
        
        if not options['confirm']:
            response = input(f'Archive these {count} transactions? (yes/no): ')
            if response.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Aborted'))
                return
        
        # Archive transactions
        updated = transactions.update(
            is_archived=True,
            archive_month=archive_date
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully archived {updated} transactions')
        )
