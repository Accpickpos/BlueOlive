"""
Cash Book Module Signals
Handles automatic balance updates and transaction validations
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import CashBookTransaction
from .services import BalanceCalculationService


@receiver(post_save, sender=CashBookTransaction)
def update_balances_on_transaction_save(sender, instance, created, **kwargs):
    """
    Update running balances when a transaction is saved.
    
    This signal is triggered whenever a CashBookTransaction is created or updated.
    It recalculates running balances from the saved transaction onward.
    """
    # Only recalculate if transaction is not already being updated by bulk operations
    if not kwargs.get('skip_balance_update', False):
        BalanceCalculationService.update_running_balances(from_transaction=instance)


@receiver(post_delete, sender=CashBookTransaction)
def update_balances_on_transaction_delete(sender, instance, **kwargs):
    """
    Recalculate running balances when a transaction is deleted.
    
    Resets all balances from the first remaining transaction onward.
    """
    # Get the first transaction after the deleted one's date
    next_transaction = CashBookTransaction.objects.filter(
        transaction_date__gte=instance.transaction_date
    ).order_by('transaction_date', 'transaction_number').first()
    
    if next_transaction:
        # Recalculate from the next transaction
        BalanceCalculationService.update_running_balances(from_transaction=next_transaction)
    else:
        # If no transactions after deleted one, recalculate all
        BalanceCalculationService.update_running_balances()
