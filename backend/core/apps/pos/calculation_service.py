"""
POS Calculation Service.
Handles all mathematical calculations for POS transactions.
"""
from decimal import Decimal
from django.core.exceptions import ValidationError
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class CalculationService:
    """Centralized service for all POS calculations."""
    
    VAT_RATE = Decimal('0.14')
    TAXABLE_TAX_CODES = [1]
    
    @staticmethod
    def calculate_line_totals(quantity: Decimal, unit_price: Decimal, 
                              discount_percentage: Decimal = None, 
                              tax_code: int = 1, 
                              cost_price: Decimal = None) -> Dict[str, Decimal]:
        """
        Calculate complete line item totals.
        
        Args:
            quantity: Item quantity
            unit_price: Price per unit
            discount_percentage: Discount as percentage (default 0)
            tax_code: Tax category (1=taxable, others=exempt)
            cost_price: Cost to business (for profit calculation)
        
        Returns:
            Dictionary with all calculated values
        
        Raises:
            ValidationError: If values are invalid
        """
        # Safe conversion to Decimal
        try:
            quantity = Decimal(str(quantity or 0))
            unit_price = Decimal(str(unit_price or 0))
            discount_percentage = Decimal(str(discount_percentage or 0))
            cost_price = Decimal(str(cost_price or 0))
        except Exception as e:
            raise ValidationError(f"Invalid numeric values: {str(e)}")
        
        # Validation
        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")
        if unit_price < 0:
            raise ValidationError("Unit price cannot be negative")
        if not (0 <= discount_percentage <= 100):
            raise ValidationError("Discount percentage must be between 0 and 100")
        if cost_price < 0:
            raise ValidationError("Cost price cannot be negative")
        
        # Calculations
        subtotal = quantity * unit_price
        discount_amount = subtotal * (discount_percentage / Decimal(100))
        line_total_before_vat = subtotal - discount_amount
        
        # VAT calculation
        is_taxable = tax_code in CalculationService.TAXABLE_TAX_CODES
        vat_amount = line_total_before_vat * CalculationService.VAT_RATE if is_taxable else Decimal(0)
        
        line_total = line_total_before_vat + vat_amount
        line_cost = quantity * cost_price
        line_profit = line_total_before_vat - line_cost
        
        return {
            'subtotal': subtotal.quantize(Decimal('0.01')),
            'discount_amount': discount_amount.quantize(Decimal('0.01')),
            'line_total_before_vat': line_total_before_vat.quantize(Decimal('0.01')),
            'vat_amount': vat_amount.quantize(Decimal('0.01')),
            'line_total': line_total.quantize(Decimal('0.01')),
            'line_cost': line_cost.quantize(Decimal('0.01')),
            'line_profit': line_profit.quantize(Decimal('0.01')),
            'is_taxable': is_taxable,
        }
    
    @staticmethod
    def calculate_document_totals(lines: List[Dict]) -> Dict[str, Decimal]:
        """
        Calculate totals for entire document from lines.
        
        Args:
            lines: List of line dictionaries with calculations
        
        Returns:
            Dictionary with document-level totals
        
        Raises:
            ValidationError: If lines list is empty
        """
        if not lines:
            raise ValidationError("Document must contain at least one line")
        
        subtotal = Decimal(0)
        vat_amount = Decimal(0)
        total_cost = Decimal(0)
        discount_total = Decimal(0)
        
        for line in lines:
            subtotal += Decimal(str(line.get('line_total_before_vat', 0)))
            vat_amount += Decimal(str(line.get('vat_amount', 0)))
            total_cost += Decimal(str(line.get('line_cost', 0)))
            discount_total += Decimal(str(line.get('discount_amount', 0)))
        
        total_amount = subtotal + vat_amount
        gross_profit = subtotal - total_cost
        
        return {
            'subtotal': subtotal.quantize(Decimal('0.01')),
            'discount_total': discount_total.quantize(Decimal('0.01')),
            'vat_amount': vat_amount.quantize(Decimal('0.01')),
            'total_amount': total_amount.quantize(Decimal('0.01')),
            'total_cost': total_cost.quantize(Decimal('0.01')),
            'gross_profit': gross_profit.quantize(Decimal('0.01')),
        }
    
    @staticmethod
    def calculate_change(tendered: Decimal, total: Decimal) -> Decimal:
        """
        Calculate change given to customer.
        
        Args:
            tendered: Amount tendered by customer
            total: Total amount owed
        
        Returns:
            Change amount (negative if underpaid)
        
        Raises:
            ValidationError: If amounts are invalid
        """
        try:
            tendered = Decimal(str(tendered or 0))
            total = Decimal(str(total or 0))
        except Exception as e:
            raise ValidationError(f"Invalid currency amounts: {str(e)}")
        
        if tendered < 0 or total < 0:
            raise ValidationError("Amounts cannot be negative")
        
        change = (tendered - total).quantize(Decimal('0.01'))
        return change
    
    @staticmethod
    def calculate_tender_balance(tenders: List[Dict], total: Decimal) -> Tuple[Decimal, bool]:
        """
        Verify tender amounts balance with transaction total.
        
        Args:
            tenders: List of tender dictionaries with 'amount' key
            total: Total transaction amount
        
        Returns:
            Tuple of (balance_amount, is_balanced)
        """
        tender_total = Decimal(0)
        
        for tender in tenders:
            try:
                amount = Decimal(str(tender.get('amount', 0)))
                if amount < 0:
                    raise ValidationError("Tender amount cannot be negative")
                tender_total += amount
            except Exception as e:
                raise ValidationError(f"Invalid tender amount: {str(e)}")
        
        try:
            total = Decimal(str(total or 0))
        except Exception as e:
            raise ValidationError(f"Invalid total amount: {str(e)}")
        
        balance = (tender_total - total).quantize(Decimal('0.01'))
        is_balanced = balance >= 0
        
        return balance, is_balanced
    
    @staticmethod
    def apply_settlement_discount(amount: Decimal, discount_percentage: Decimal) -> Decimal:
        """
        Calculate settlement discount (early payment discount).
        
        Args:
            amount: Original amount
            discount_percentage: Discount percentage
        
        Returns:
            Discount amount
        
        Raises:
            ValidationError: If values are invalid
        """
        try:
            amount = Decimal(str(amount or 0))
            discount_percentage = Decimal(str(discount_percentage or 0))
        except Exception as e:
            raise ValidationError(f"Invalid numeric values: {str(e)}")
        
        if amount < 0:
            raise ValidationError("Amount cannot be negative")
        if not (0 <= discount_percentage <= 100):
            raise ValidationError("Discount percentage must be between 0 and 100")
        
        discount = (amount * discount_percentage / Decimal(100)).quantize(Decimal('0.01'))
        return discount
    
    @staticmethod
    def calculate_laybye_balance(total_amount: Decimal, deposit_amount: Decimal, 
                                 amount_paid: Decimal = None) -> Dict[str, Decimal]:
        """
        Calculate laybye payment status.
        
        Args:
            total_amount: Total laybye amount
            deposit_amount: Deposit paid
            amount_paid: Total amount paid so far (default = deposit)
        
        Returns:
            Dictionary with balance information
        
        Raises:
            ValidationError: If values are invalid
        """
        try:
            total_amount = Decimal(str(total_amount or 0))
            deposit_amount = Decimal(str(deposit_amount or 0))
            amount_paid = Decimal(str(amount_paid or deposit_amount))
        except Exception as e:
            raise ValidationError(f"Invalid numeric values: {str(e)}")
        
        if total_amount <= 0:
            raise ValidationError("Total amount must be positive")
        if deposit_amount < 0:
            raise ValidationError("Deposit cannot be negative")
        if amount_paid < 0:
            raise ValidationError("Amount paid cannot be negative")
        if amount_paid > total_amount:
            raise ValidationError("Amount paid exceeds total amount")
        
        balance_due = (total_amount - amount_paid).quantize(Decimal('0.01'))
        
        return {
            'total_amount': total_amount.quantize(Decimal('0.01')),
            'amount_paid': amount_paid.quantize(Decimal('0.01')),
            'balance_due': balance_due.quantize(Decimal('0.01')),
            'deposit_percentage': (deposit_amount / total_amount * 100).quantize(Decimal('0.01')),
            'percent_paid': (amount_paid / total_amount * 100).quantize(Decimal('0.01')),
        }
    
    @staticmethod
    def calculate_profit_metrics(total_amount: Decimal, total_cost: Decimal, 
                                 vat_amount: Decimal = None) -> Dict[str, Decimal]:
        """
        Calculate profit and margin metrics.
        
        Args:
            total_amount: Total sale amount
            total_cost: Total cost of goods
            vat_amount: VAT amount (optional)
        
        Returns:
            Dictionary with profit metrics
        """
        try:
            total_amount = Decimal(str(total_amount or 0))
            total_cost = Decimal(str(total_cost or 0))
            vat_amount = Decimal(str(vat_amount or 0))
        except Exception as e:
            raise ValidationError(f"Invalid numeric values: {str(e)}")
        
        # Calculate before VAT for margin
        taxable_amount = total_amount - vat_amount
        
        gross_profit = (taxable_amount - total_cost).quantize(Decimal('0.01'))
        
        # Avoid division by zero
        if taxable_amount == 0:
            profit_margin = Decimal(0)
            markup_percentage = Decimal(0)
        else:
            profit_margin = (gross_profit / taxable_amount * 100).quantize(Decimal('0.01'))
            if total_cost == 0:
                markup_percentage = Decimal(0)
            else:
                markup_percentage = (gross_profit / total_cost * 100).quantize(Decimal('0.01'))
        
        return {
            'gross_profit': gross_profit,
            'profit_margin_percent': profit_margin,
            'markup_percent': markup_percentage,
            'cost_percentage': (total_cost / taxable_amount * 100).quantize(Decimal('0.01')) if taxable_amount > 0 else Decimal(0),
        }
    
    @staticmethod
    def log_calculation(transaction_number: str, operation: str, details: Dict, error: str = None):
        """
        Log calculation operations for audit trail.
        
        Args:
            transaction_number: Transaction identifier
            operation: Type of operation
            details: Calculation details
            error: Error message if calculation failed
        """
        if error:
            logger.error(
                f"Calculation error for {transaction_number} ({operation}): {error}",
                extra={'details': details}
            )
        else:
            logger.info(
                f"Calculation for {transaction_number} ({operation})",
                extra={'details': details}
            )