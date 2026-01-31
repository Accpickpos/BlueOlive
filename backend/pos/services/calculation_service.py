"""
Financial calculation service for POS transactions
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaxCode(str, Enum):
    """Tax code values"""
    ZERO = "ZERO"
    STANDARD = "STANDARD"
    REDUCED = "REDUCED"


class CalculationService:
    """Service for financial calculations"""
    
    # Default tax rates
    DEFAULT_TAX_RATES = {
        TaxCode.ZERO: Decimal("0"),
        TaxCode.STANDARD: Decimal("14"),
        TaxCode.REDUCED: Decimal("7"),
    }
    
    def __init__(self, tax_rates: Dict[str, Decimal] = None):
        """Initialize calculation service with optional custom tax rates"""
        self.tax_rates = tax_rates or self.DEFAULT_TAX_RATES
    
    def calculate_line_item(
        self,
        quantity: Decimal,
        selling_price: Decimal,
        discount_percentage: Decimal = Decimal("0"),
        tax_code: TaxCode = TaxCode.STANDARD,
        cost_price: Decimal = Decimal("0")
    ) -> Dict[str, Decimal]:
        """
        Calculate line item totals
        
        Returns:
            Dict with: line_total, discount_amount, tax_amount, gross_profit
        """
        # Basic amount
        line_amount = quantity * selling_price
        
        # Discount
        discount_amount = (line_amount * discount_percentage / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        subtotal = line_amount - discount_amount
        
        # Tax
        tax_rate = self.tax_rates.get(tax_code, Decimal("0"))
        tax_amount = (subtotal * tax_rate / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        # Line total
        line_total = subtotal + tax_amount
        
        # Gross profit
        cost_total = quantity * cost_price
        gross_profit = line_amount - cost_total
        
        return {
            "line_total": line_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "discount_amount": discount_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "tax_amount": tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "gross_profit": gross_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "cost_total": cost_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        }
    
    def calculate_invoice_totals(self, line_items: List[Dict[str, Any]]) -> Dict[str, Decimal]:
        """Calculate invoice totals from line items"""
        subtotal = Decimal("0")
        subtotal_discount = Decimal("0")
        tax_amount = Decimal("0")
        gross_profit = Decimal("0")
        
        for item in line_items:
            subtotal += item.get("line_total", Decimal("0")) - item.get("tax_amount", Decimal("0"))
            subtotal_discount += item.get("discount_amount", Decimal("0"))
            tax_amount += item.get("tax_amount", Decimal("0"))
            gross_profit += item.get("gross_profit", Decimal("0"))
        
        total_amount = subtotal + tax_amount
        
        return {
            "subtotal": subtotal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "subtotal_discount": subtotal_discount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "tax_amount": tax_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "gross_profit": gross_profit.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "total_amount": total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        }
    
    def apply_settlement_discount(
        self,
        amount: Decimal,
        discount_percentage: Decimal
    ) -> Dict[str, Decimal]:
        """Apply settlement discount to amount"""
        discount = (amount * discount_percentage / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        final_amount = (amount - discount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        return {
            "original_amount": amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "discount_amount": discount,
            "final_amount": final_amount,
        }
    
    def apply_price_adjustment(
        self,
        amount: Decimal,
        adjustment_percentage: Decimal,
        adjustment_type: str = "increase"
    ) -> Decimal:
        """Apply price adjustment (increase or decrease)"""
        if adjustment_type == "increase":
            result = amount * (Decimal("1") + adjustment_percentage / Decimal("100"))
        else:
            result = amount * (Decimal("1") - adjustment_percentage / Decimal("100"))
        
        return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    def calculate_cash_rounding(self, amount: Decimal, round_to: Decimal = Decimal("0.01")) -> Dict[str, Decimal]:
        """Calculate cash rounding adjustment"""
        rounded_amount = (amount / round_to).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * round_to
        
        adjustment = (rounded_amount - amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        return {
            "original_amount": amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "rounded_amount": rounded_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "rounding_adjustment": adjustment,
        }
    
    def calculate_laybye_deposit_and_retention(
        self,
        total_amount: Decimal,
        deposit_percentage: Decimal,
        retention_percentage: Decimal = Decimal("0")
    ) -> Dict[str, Decimal]:
        """Calculate laybye deposit and retention amounts"""
        deposit = (total_amount * deposit_percentage / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        balance_for_retention = total_amount - deposit
        retention = (balance_for_retention * retention_percentage / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        
        outstanding = total_amount - deposit - retention
        
        return {
            "total_amount": total_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
            "deposit_amount": deposit,
            "retention_amount": retention,
            "outstanding_amount": outstanding,
        }
    
    def calculate_receipt_age_allocation(
        self,
        receipt_amount: Decimal,
        invoices: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate age allocation for receipt application to invoices
        
        invoices: List of invoice dicts with 'amount', 'date', and 'days_overdue'
        """
        allocated = []
        remaining = receipt_amount
        
        # Sort by date (oldest first)
        sorted_invoices = sorted(invoices, key=lambda x: x.get("date", ""))
        
        for invoice in sorted_invoices:
            if remaining <= Decimal("0"):
                break
            
            invoice_amount = Decimal(str(invoice.get("amount", 0)))
            allocation = min(remaining, invoice_amount)
            
            allocated.append({
                "invoice_number": invoice.get("invoice_number"),
                "allocation_amount": allocation.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "invoice_amount": invoice_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
                "days_overdue": invoice.get("days_overdue", 0),
            })
            
            remaining = (remaining - allocation).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        
        return {
            "allocations": allocated,
            "total_allocated": (receipt_amount - remaining).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "unallocated_balance": remaining,
        }
    
    def calculate_change(
        self,
        tender_amount: Decimal,
        required_amount: Decimal
    ) -> Decimal:
        """Calculate change from tender"""
        change = (tender_amount - required_amount).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return max(change, Decimal("0"))
    
    def calculate_total_from_tenders(self, tenders: List[Dict[str, Decimal]]) -> Decimal:
        """Calculate total amount from tenders"""
        total = Decimal("0")
        for tender in tenders:
            total += Decimal(str(tender.get("amount", 0)))
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    def set_tax_rate(self, tax_code: str, rate: Decimal):
        """Set custom tax rate for code"""
        self.tax_rates[tax_code] = rate
    
    def get_tax_rate(self, tax_code: str) -> Decimal:
        """Get tax rate for code"""
        return self.tax_rates.get(tax_code, Decimal("0"))
