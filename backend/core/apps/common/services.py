"""
Common Services Module

Shared service classes that can be used across all business apps.
Services contain business logic that doesn't fit in models or views.

Usage:
    from apps.common.services import BaseService, TenantService
    
    class MyService(BaseService):
        def do_something(self):
            pass
"""

from django.db import transaction
from django.utils import timezone
from typing import Optional, Any, Dict, List
from decimal import Decimal


class BaseService:
    """
    Base service class that provides common functionality.
    
    All business logic services should inherit from this class.
    """
    
    def __init__(self, user=None, tenant_id=None):
        """
        Initialize the service.
        
        Args:
            user: The user performing the action
            tenant_id: The tenant context for the operation
        """
        self.user = user
        self.tenant_id = tenant_id
        self.errors = []
        self.warnings = []
    
    def add_error(self, message: str, field: str = None):
        """Add an error message."""
        if field:
            self.errors.append({'field': field, 'message': message})
        else:
            self.errors.append({'message': message})
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def get_errors(self) -> List[Dict]:
        """Get all errors."""
        return self.errors
    
    def clear_errors(self):
        """Clear all errors."""
        self.errors = []
    
    def validate(self) -> bool:
        """
        Override this method to add validation logic.
        
        Returns:
            True if validation passes, False otherwise
        """
        return True
    
    def execute(self) -> Any:
        """
        Execute the service operation.
        
        Override this method to implement the main business logic.
        
        Returns:
            The result of the operation
        """
        raise NotImplementedError("Subclasses must implement execute()")
    
    def run(self) -> Dict[str, Any]:
        """
        Run the service with validation and error handling.
        
        Returns:
            Dict with 'success', 'data', 'errors', 'warnings' keys
        """
        self.clear_errors()
        
        if not self.validate():
            return {
                'success': False,
                'data': None,
                'errors': self.get_errors(),
                'warnings': self.warnings
            }
        
        try:
            result = self.execute()
            return {
                'success': True,
                'data': result,
                'errors': [],
                'warnings': self.warnings
            }
        except Exception as e:
            self.add_error(str(e))
            return {
                'success': False,
                'data': None,
                'errors': self.get_errors(),
                'warnings': self.warnings
            }


class TenantService(BaseService):
    """
    Service class that operates within a tenant context.
    
    All services that need tenant isolation should inherit from this class.
    """
    
    def get_tenant_id(self) -> Optional[int]:
        """Get the tenant ID, from service or user."""
        if self.tenant_id:
            return self.tenant_id
        if self.user:
            return getattr(self.user, 'tenant_id', None)
        return None
    
    def get_queryset_filter(self):
        """Get the base filter for tenant isolation."""
        tenant_id = self.get_tenant_id()
        if tenant_id:
            return {'tenant_id': tenant_id}
        return {}


class TransactionService(BaseService):
    """
    Base service for transaction operations.
    
    Provides common functionality for financial transactions:
    - Posting
    - Validation
    - Audit trail
    """
    
    @transaction.atomic
    def execute(self):
        """Execute transaction in an atomic block."""
        # Validate before posting
        if not self.validate():
            raise ValueError(f"Validation failed: {self.get_errors()}")
        
        # Perform the transaction
        result = self._execute_transaction()
        
        # Create audit trail
        self._create_audit_trail(result)
        
        return result
    
    def _execute_transaction(self):
        """Override this to implement transaction logic."""
        raise NotImplementedError("Subclasses must implement _execute_transaction()")
    
    def _create_audit_trail(self, result):
        """Create audit trail entry. Override in subclasses."""
        pass
    
    def validate_transaction_date(self, date) -> bool:
        """Validate that transaction date is valid."""
        if date > timezone.now().date():
            self.add_error("Transaction date cannot be in the future", "transaction_date")
            return False
        return True
    
    def validate_amount(self, amount: Decimal, field_name: str = "amount") -> bool:
        """Validate that amount is positive."""
        if amount <= 0:
            self.add_error(f"{field_name} must be positive", field_name)
            return False
        return True


class BalanceService(TenantService):
    """
    Service for balance calculations.
    
    Common service for calculating account balances,
    aging, and reconciliation.
    """
    
    def calculate_balance(self, account_id: int, model_class) -> Decimal:
        """
        Calculate the current balance for an account.
        
        Args:
            account_id: The account ID
            model_class: The model class to query
            
        Returns:
            Decimal balance amount
        """
        from django.db.models import Sum
        
        filter_dict = self.get_queryset_filter()
        filter_dict['account_id'] = account_id
        
        result = model_class.objects.filter(**filter_dict).aggregate(
            total=Sum('amount')
        )
        return result['total'] or Decimal('0.00')
    
    def calculate_aging(self, account_id: int, model_class, 
                        aging_days: List[int] = [30, 60, 90, 120]) -> Dict[str, Decimal]:
        """
        Calculate aging buckets for an account.
        
        Args:
            account_id: The account ID
            model_class: The model class to query
            aging_days: List of aging day thresholds
            
        Returns:
            Dict with 'current', '30_days', '60_days', '90_days', 'over_120' keys
        """
        from django.db.models import Q, Sum
        from datetime import timedelta
        from django.utils import timezone
        
        today = timezone.now().date()
        filter_dict = self.get_queryset_filter()
        filter_dict['account_id'] = account_id
        filter_dict['balance__gt'] = 0
        
        aging = {}
        
        # Current (0-30 days)
        aging['current'] = model_class.objects.filter(
            **filter_dict,
            transaction_date__gte=today - timedelta(days=aging_days[0])
        ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
        
        # 30-60 days
        if len(aging_days) > 1:
            aging['30_days'] = model_class.objects.filter(
                **filter_dict,
                transaction_date__lt=today - timedelta(days=aging_days[0]),
                transaction_date__gte=today - timedelta(days=aging_days[1])
            ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
        
        # 60-90 days
        if len(aging_days) > 2:
            aging['60_days'] = model_class.objects.filter(
                **filter_dict,
                transaction_date__lt=today - timedelta(days=aging_days[1]),
                transaction_date__gte=today - timedelta(days=aging_days[2])
            ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
        
        # Over 90 days
        if len(aging_days) > 3:
            aging['90_days'] = model_class.objects.filter(
                **filter_dict,
                transaction_date__lt=today - timedelta(days=aging_days[2]),
                transaction_date__gte=today - timedelta(days=aging_days[3])
            ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
            
            aging['over_90'] = model_class.objects.filter(
                **filter_dict,
                transaction_date__lt=today - timedelta(days=aging_days[3])
            ).aggregate(total=Sum('balance'))['total'] or Decimal('0.00')
        
        return aging


class VATService(TenantService):
    """
    Service for VAT/Tax calculations.
    
    Common service for calculating VAT on transactions.
    """
    
    def calculate_vat(self, amount: Decimal, vat_rate: Decimal, 
                      inclusive: bool = False) -> Dict[str, Decimal]:
        """
        Calculate VAT amount.
        
        Args:
            amount: The base amount
            vat_rate: The VAT rate (e.g., 0.15 for 15%)
            inclusive: If True, amount includes VAT
            
        Returns:
            Dict with 'net', 'vat', 'gross' keys
        """
        if inclusive:
            # Amount includes VAT
            net = amount / (1 + vat_rate)
            vat = amount - net
            gross = amount
        else:
            # Amount excludes VAT
            net = amount
            vat = amount * vat_rate
            gross = amount + vat
        
        return {
            'net': net.quantize(Decimal('0.01')),
            'vat': vat.quantize(Decimal('0.01')),
            'gross': gross.quantize(Decimal('0.01'))
        }
    
    def get_vat_rate(self, tax_code_id: int) -> Decimal:
        """Get VAT rate for a tax code."""
        # This would typically fetch from settings
        # Placeholder implementation
        return Decimal('0.15')


class NumberSequenceService(TenantService):
    """
    Service for generating transaction numbers.
    
    Provides consistent numbering across all transaction types.
    """
    
    def generate_number(self, prefix: str, model_class, 
                        number_field: str = 'transaction_number') -> str:
        """
        Generate a unique transaction number.
        
        Args:
            prefix: The prefix for the number (e.g., 'INV', 'DN')
            model_class: The model class to check for existing numbers
            number_field: The field name to store the number
            
        Returns:
            Generated unique number string
        """
        from django.db.models import Max
        from datetime import datetime
        
        today = datetime.now()
        year = today.strftime('%y')
        month = today.strftime('%m')
        
        # Find existing max number for this prefix and period
        filter_dict = self.get_queryset_filter()
        filter_dict[f'{number_field}__startswith'] = f'{prefix}{year}{month}'
        
        max_obj = model_class.objects.filter(**filter_dict).aggregate(
            max_num=Max(number_field)
        )
        
        max_num = max_obj['max_num']
        if max_num:
            # Extract sequence number and increment
            try:
                seq = int(max_num[-5:]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        
        return f'{prefix}{year}{month}{seq:05d}'


class ReconciliationService(TransactionService):
    """
    Service for reconciliation operations.
    
    Common service for bank reconciliation, etc.
    """
    
    def reconcile(self, statement_items: List[Dict], 
                  transactions: List[Any]) -> Dict[str, Any]:
        """
        Match statement items with transactions.
        
        Args:
            statement_items: List of bank statement items
            transactions: List of system transactions
            
        Returns:
            Dict with matched, unmatched_statement, unmatched_system
        """
        matched = []
        unmatched_statement = []
        unmatched_system = list(transactions)
        
        for stmt_item in statement_items:
            found = False
            for trans in unmatched_system:
                if self._matches(stmt_item, trans):
                    matched.append({
                        'statement_item': stmt_item,
                        'transaction': trans
                    })
                    unmatched_system.remove(trans)
                    found = True
                    break
            
            if not found:
                unmatched_statement.append(stmt_item)
        
        return {
            'matched': matched,
            'unmatched_statement': unmatched_statement,
            'unmatched_system': unmatched_system,
            'matched_total': sum(m['statement_item'].get('amount', 0) for m in matched)
        }
    
    def _matches(self, stmt_item: Dict, transaction: Any) -> bool:
        """Check if statement item matches transaction."""
        # Override in subclasses for specific matching logic
        return (
            stmt_item.get('amount') == getattr(transaction, 'amount', None) and
            stmt_item.get('date') == getattr(transaction, 'transaction_date', None)
        )


# Re-export commonly used services
__all__ = [
    'BaseService',
    'TenantService',
    'TransactionService',
    'BalanceService',
    'VATService',
    'NumberSequenceService',
    'ReconciliationService',
]
