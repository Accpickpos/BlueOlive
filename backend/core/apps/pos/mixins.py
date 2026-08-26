"""
POS Mixins for shared functionality across line item models.
Provides calculation and validation logic for line items.
"""

from decimal import Decimal

from django.db import models


class LineItemCalculationMixin:
    """
    Mixin for calculating line item totals, VAT, and profit.
    Assumes model has: quantity, unit_price, discount_percentage, tax_code, cost_price
    """

    VAT_RATE = Decimal("0.14")  # 14% VAT
    TAXABLE_CODES = [1]  # Tax codes that are taxable

    @classmethod
    def calculate_line_totals(
        cls,
        quantity,
        unit_price,
        discount_percentage=Decimal("0.00"),
        tax_code=1,
        cost_price=Decimal("0.00"),
    ):
        """
        Calculate line totals, VAT, and profit.

        Args:
            quantity: Decimal - Item quantity
            unit_price: Decimal - Unit price
            discount_percentage: Decimal - Discount percentage (default 0%)
            tax_code: int - Tax code (1 for taxable, others for non-taxable)
            cost_price: Decimal - Cost price of item

        Returns:
            dict: {
                'subtotal': subtotal before discount,
                'discount_amount': discount amount,
                'line_total_before_vat': total before VAT,
                'vat_amount': VAT amount,
                'line_total': total including VAT,
                'line_cost': total cost,
                'line_profit': gross profit
            }
        """
        # Ensure Decimal types
        quantity = Decimal(str(quantity))
        unit_price = Decimal(str(unit_price))
        discount_percentage = Decimal(str(discount_percentage))
        cost_price = Decimal(str(cost_price))

        # Calculate subtotal
        subtotal = quantity * unit_price

        # Calculate discount
        discount_amount = subtotal * (discount_percentage / 100)

        # Total before VAT
        line_total_before_vat = subtotal - discount_amount

        # Calculate VAT
        vat_rate = cls.VAT_RATE if tax_code in cls.TAXABLE_CODES else Decimal("0.00")
        vat_amount = line_total_before_vat * vat_rate

        # Total including VAT
        line_total = line_total_before_vat + vat_amount

        # Calculate cost and profit
        line_cost = quantity * cost_price
        line_profit = line_total_before_vat - line_cost

        return {
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "line_total_before_vat": line_total_before_vat,
            "vat_amount": vat_amount,
            "line_total": line_total,
            "line_cost": line_cost,
            "line_profit": line_profit,
        }

    @classmethod
    def validate_line_item(
        cls, quantity, unit_price, discount_percentage=Decimal("0.00")
    ):
        """
        Validate line item values.

        Args:
            quantity: Decimal - Item quantity
            unit_price: Decimal - Unit price
            discount_percentage: Decimal - Discount percentage

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            quantity = Decimal(str(quantity))
            unit_price = Decimal(str(unit_price))
            discount_percentage = Decimal(str(discount_percentage))

            if quantity <= 0:
                return False, "Quantity must be greater than zero"

            if unit_price < 0:
                return False, "Unit price cannot be negative"

            if discount_percentage < 0 or discount_percentage > 100:
                return False, "Discount percentage must be between 0 and 100"

            return True, None

        except Exception as e:
            return False, f"Invalid numeric value: {str(e)}"


class DocumentHeaderCalculationMixin:
    """
    Mixin for calculating document header totals (subtotal, VAT, totals).
    Used by CashSale, Laybye, Quotation, JobCard, CreditNote, CashReturn, etc.
    """

    @classmethod
    def calculate_header_totals(cls, lines_data):
        """
        Calculate header totals from line items.

        Args:
            lines_data: List of dictionaries with line item calculations

        Returns:
            dict: {
                'subtotal': sum of all line totals before VAT,
                'vat_amount': sum of all VAT amounts,
                'total_amount': sum of all line totals with VAT,
                'total_cost': sum of all costs,
                'gross_profit': total profit
            }
        """
        subtotal = Decimal("0.00")
        vat_amount = Decimal("0.00")
        total_cost = Decimal("0.00")

        for line in lines_data:
            subtotal += line.get("line_total_before_vat", Decimal("0.00"))
            vat_amount += line.get("vat_amount", Decimal("0.00"))
            total_cost += line.get("line_cost", Decimal("0.00"))

        total_amount = subtotal + vat_amount
        gross_profit = subtotal - total_cost

        return {
            "subtotal": subtotal,
            "vat_amount": vat_amount,
            "total_amount": total_amount,
            "total_cost": total_cost,
            "gross_profit": gross_profit,
        }

    @classmethod
    def validate_document_totals(cls, document, expected_totals):
        """
        Validate document totals match expected values.

        Args:
            document: Document instance
            expected_totals: dict with expected total_amount

        Returns:
            tuple: (is_valid, discrepancy_amount)
        """
        discrepancy = abs(
            document.total_amount - expected_totals.get("total_amount", Decimal("0.00"))
        )

        # Allow small rounding differences (e.g., due to Decimal precision)
        tolerance = Decimal("0.01")

        return discrepancy <= tolerance, discrepancy
