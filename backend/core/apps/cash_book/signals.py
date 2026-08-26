"""
Cash Book Module Signals
Handles automatic balance updates, category balance tracking, and transaction validations
Per enterprise implementation: Update category balances on transaction changes
"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import CashBookTransaction, ExpenseCategoryBalance, IncomeCategoryBalance
from .services import BalanceCalculationService


@receiver(post_save, sender=CashBookTransaction)
def update_balances_on_transaction_save(sender, instance, created, **kwargs):
    """
    Update running balances and category balances when a transaction is saved.

    Per specification:
    - Update category MTD balances in real-time (per CBEXP, CBINC)
    - Recalculate running balances from saved transaction onward
    - Track input VAT (expenses) and output VAT (income)
    """
    # Skip if flag is set (for bulk operations)
    if kwargs.get("skip_balance_update", False):
        return

    # Update running cash/bank balances
    BalanceCalculationService.update_running_balances(from_transaction=instance)

    # Update category-level balances (NEW - per enterprise spec)
    if created:
        # Only count new transactions for category balance
        BalanceCalculationService.update_category_balances(
            instance,
            value_excl_vat=instance.value_excl_vat,
            tax_amount=instance.tax_amount,
        )


@receiver(post_delete, sender=CashBookTransaction)
def update_balances_on_transaction_delete(sender, instance, **kwargs):
    """
    Recalculate running balances and adjust category balances when a transaction is deleted.

    - Reverses category MTD balance updates
    - Recalculates running cash/bank balances from next transaction
    """
    # Reverse category balance impact (NEW - per enterprise spec)
    if instance.category_id:
        reverse_amount = -instance.value_excl_vat  # Negative to reverse
        reverse_tax = -instance.tax_amount

        # Update category balance
        if instance.audit_type in [1, 2]:  # Income
            try:
                balance = IncomeCategoryBalance.objects.get(
                    income_category_id=instance.category_id
                )
                balance.balance_month_to_date += reverse_amount
                balance.output_vat_month_to_date += reverse_tax
                balance.save()
            except IncomeCategoryBalance.DoesNotExist:
                pass

        elif instance.audit_type in [3, 4]:  # Expenses
            try:
                balance = ExpenseCategoryBalance.objects.get(
                    expense_category_id=instance.category_id
                )
                balance.balance_month_to_date += reverse_amount
                balance.input_vat_month_to_date += reverse_tax
                balance.save()
            except ExpenseCategoryBalance.DoesNotExist:
                pass

    # Get the first transaction after the deleted one's date
    next_transaction = (
        CashBookTransaction.objects.filter(
            transaction_date__gte=instance.transaction_date
        )
        .order_by("transaction_date", "transaction_number")
        .first()
    )

    if next_transaction:
        # Recalculate from the next transaction
        BalanceCalculationService.update_running_balances(
            from_transaction=next_transaction
        )
    else:
        # If no transactions after deleted one, recalculate all
        BalanceCalculationService.update_running_balances()
