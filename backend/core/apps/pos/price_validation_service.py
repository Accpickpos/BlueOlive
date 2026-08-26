"""
POS Price Validation Service.
Validates POS transaction prices against StockItem price levels and markup rules.
"""

import logging
from datetime import date
from decimal import Decimal
from typing import Dict, Optional, Tuple

from apps.stock_control.models import SpecialDeal, StockItem
from django.core.exceptions import ValidationError

from .exceptions import POSValidationException

logger = logging.getLogger(__name__)


class PriceValidationService:
    """Validate prices against stock item price levels and markup rules."""

    @staticmethod
    def get_valid_prices_for_item(
        stock_code: str, quantity: Decimal = None, transaction_date: date = None
    ) -> Dict:
        """
        Get valid price levels for a stock item.

        Args:
            stock_code: Stock item code
            quantity: Quantity (for special deal checking)
            transaction_date: Date of transaction (for future prices and deals)

        Returns:
            Dictionary with:
                - selling_price_1, 2, 3: Standard prices
                - markup_percent_1, 2, 3: Markups
                - special_deal: Any active special deal
                - maximum_discount: Max allowed discount %
                - cost_price: Current cost

        Raises:
            POSValidationException: If stock item not found
        """
        try:
            stock_item = StockItem.objects.get(stock_code=stock_code)
        except StockItem.DoesNotExist:
            raise POSValidationException(f"Stock item {stock_code} not found")

        if not transaction_date:
            transaction_date = date.today()

        # Get base prices
        prices = {
            "selling_price_1": stock_item.selling_price_1,
            "selling_price_2": stock_item.selling_price_2,
            "selling_price_3": stock_item.selling_price_3,
            "markup_percent_1": stock_item.markup_1,  # Fixed: was markup_percent_1
            "markup_percent_2": stock_item.markup_2,  # Fixed: was markup_percent_2
            "markup_percent_3": stock_item.markup_3,  # Fixed: was markup_percent_3
            "cost_price": stock_item.cost_price,
            "maximum_discount": stock_item.maximum_discount_percent,
            "stock_item": stock_item,
        }

        # Check for special deals (overrides base pricing)
        special_deal = SpecialDeal.objects.filter(
            stock_item=stock_item,
            start_date__lte=transaction_date,
            end_date__gte=transaction_date,
            is_active=True,
        ).first()

        if special_deal:
            prices["special_deal"] = special_deal
            prices["special_selling_price_1"] = special_deal.special_selling_price_1
            prices["special_selling_price_2"] = special_deal.special_selling_price_2
            prices["special_selling_price_3"] = special_deal.special_selling_price_3
            prices["special_markup_1"] = special_deal.special_markup_1
            prices["special_markup_2"] = special_deal.special_markup_2
            prices["special_markup_3"] = special_deal.special_markup_3

        return prices

    @staticmethod
    def validate_unit_price(
        stock_code: str,
        unit_price: Decimal,
        price_level: int = 1,
        transaction_date: date = None,
    ) -> Tuple[bool, Optional[str], Dict]:
        """
        Validate if a unit price matches approved price levels.

        Args:
            stock_code: Stock item code
            unit_price: Unit price entered in POS
            price_level: Which price level to check (1, 2, or 3)
            transaction_date: Date of transaction

        Returns:
            Tuple of (is_valid, warning_message, price_info)
            - is_valid: Boolean indicating if price is acceptable
            - warning_message: Message if price differs from approved
            - price_info: Dictionary with price details
        """
        try:
            unit_price = Decimal(str(unit_price))
        except Exception:
            raise POSValidationException(f"Invalid unit price: {unit_price}")

        if unit_price <= 0:
            raise POSValidationException("Unit price must be greater than zero")

        try:
            prices = PriceValidationService.get_valid_prices_for_item(
                stock_code, transaction_date=transaction_date
            )
        except POSValidationException:
            raise

        if not (1 <= price_level <= 3):
            raise POSValidationException("Price level must be 1, 2, or 3")

        # Get the appropriate price from stock item
        special_deal = prices.get("special_deal")

        if special_deal:
            # Use special deal prices if active
            special_price = prices.get(
                f"special_selling_price_{price_level}", Decimal(0)
            )
            normal_price = prices.get(f"selling_price_{price_level}", Decimal(0))
        else:
            # Use normal prices
            special_price = None
            normal_price = prices.get(f"selling_price_{price_level}", Decimal(0))

        # Check for exact match or small tolerance (rounding)
        tolerance = Decimal("0.01")

        price_info = {
            "entered_price": unit_price,
            "standard_price": normal_price,
            "special_price": special_price,
            "price_level": price_level,
            "markup_percent": prices.get(f"markup_percent_{price_level}"),
            "cost_price": prices.get("cost_price"),
            "maximum_discount": prices.get("maximum_discount"),
            "has_special_deal": special_deal is not None,
        }

        # Check if price matches standard price
        if special_price and abs(unit_price - special_price) <= tolerance:
            return True, None, price_info

        if normal_price and abs(unit_price - normal_price) <= tolerance:
            return True, None, price_info

        # Price doesn't match - return warning
        target_price = special_price if special_price else normal_price

        if target_price == 0:
            warning = f"No price level {price_level} configured for this item"
        elif unit_price > target_price:
            difference = unit_price - target_price
            pct_higher = (difference / target_price * 100).quantize(Decimal("0.01"))
            warning = (
                f"Price is {pct_higher}% HIGHER than configured "
                f"(entered: {unit_price}, configured: {target_price})"
            )
        else:
            difference = target_price - unit_price
            pct_lower = (difference / target_price * 100).quantize(Decimal("0.01"))
            warning = (
                f"Price is {pct_lower}% LOWER than configured "
                f"(entered: {unit_price}, configured: {target_price})"
            )

        return False, warning, price_info

    @staticmethod
    def calculate_price_from_markup(
        stock_code: str, price_level: int = 1, transaction_date: date = None
    ) -> Decimal:
        """
        Calculate selling price from cost price and markup percentage.

        Args:
            stock_code: Stock item code
            price_level: Which price level to use (1, 2, or 3)
            transaction_date: Date of transaction

        Returns:
            Calculated selling price

        Raises:
            POSValidationException: If calculation fails
        """
        try:
            prices = PriceValidationService.get_valid_prices_for_item(
                stock_code, transaction_date=transaction_date
            )
        except POSValidationException:
            raise

        cost_price = prices.get("cost_price", Decimal(0))
        markup_percent = prices.get(f"markup_percent_{price_level}", Decimal(0))

        if cost_price == 0:
            raise POSValidationException(
                f"Cost price not set for {stock_code}, cannot calculate markup"
            )

        # Calculate: Selling Price = Cost Price * (1 + Markup% / 100)
        calculated_price = cost_price * (1 + markup_percent / 100)

        return calculated_price.quantize(Decimal("0.01"))

    @staticmethod
    def validate_line_item_price(
        stock_code: str,
        quantity: Decimal,
        unit_price: Decimal,
        discount_percent: Decimal = None,
        price_level: int = 1,
        transaction_date: date = None,
        enforce: bool = False,
    ) -> Dict:
        """
        Comprehensive price validation for a line item.

        Args:
            stock_code: Stock item code
            quantity: Quantity being sold
            unit_price: Unit price entered
            discount_percent: Discount percentage applied
            price_level: Which price level used
            transaction_date: Transaction date
            enforce: When True, raise POSValidationException instead of
                only returning warnings if the submitted unit_price
                doesn't match a configured price level (or active special
                deal) or the discount exceeds the item's maximum allowed
                discount. Only applies once a StockItem has actually been
                located for stock_code — a line for a stock_code that
                doesn't exist (a manual/non-inventory entry) is never
                blocked here, matching how callers already treat "not
                found" as a legitimate manual entry. There is no
                manager-override concept elsewhere in this codebase; a
                deliberate reduction off the configured price should go
                through discount_percent (still capped by
                maximum_discount_percent), not by tampering with
                unit_price directly.

        Returns:
            Dictionary with validation results:
                - is_valid: Overall validity
                - price_valid: Unit price matches approved
                - discount_valid: Discount within limits
                - warnings: List of warning messages
                - suggestions: List of suggestions
                - price_info: Pricing details

        Raises:
            POSValidationException: If enforce=True and the price/discount
                is invalid for a StockItem that was found.
        """
        warnings = []
        suggestions = []

        try:
            prices = PriceValidationService.get_valid_prices_for_item(
                stock_code, quantity, transaction_date
            )
        except POSValidationException as e:
            return {
                "is_valid": False,
                "price_valid": False,
                "discount_valid": False,
                "error": str(e),
                "warnings": [],
                "suggestions": [],
                "price_info": {},
            }

        # Validate unit price
        price_valid, price_warning, price_info = (
            PriceValidationService.validate_unit_price(
                stock_code, unit_price, price_level, transaction_date
            )
        )

        if not price_valid and price_warning:
            warnings.append(price_warning)

        # Below-cost warning (manual: "Where a stock item is sold below
        # cost, a warning is sounded and displayed" — informational, not a
        # hard block, matching how price/discount warnings behave here).
        cost_price = prices.get("cost_price", Decimal(0))
        below_cost = cost_price > 0 and unit_price < cost_price
        if below_cost:
            warnings.append(
                f"Sold BELOW COST: selling price {unit_price} is less than cost price {cost_price}"
            )

        # Validate discount
        if discount_percent is None:
            discount_percent = Decimal(0)
        else:
            discount_percent = Decimal(str(discount_percent))

        max_discount = prices.get("maximum_discount", Decimal(0))
        discount_valid = discount_percent <= max_discount

        if not discount_valid:
            warnings.append(
                f"Discount {discount_percent}% exceeds maximum {max_discount}% "
                f"for this item"
            )

        if discount_percent > 0:
            if discount_percent > 20:
                warnings.append(f"High discount of {discount_percent}% applied")

            if discount_percent > 50:
                warnings.append(
                    f"EXTREME discount of {discount_percent}% - "
                    f"verify customer authorization"
                )

        # Suggestions
        if not price_valid:
            calculated = PriceValidationService.calculate_price_from_markup(
                stock_code, price_level, transaction_date
            )
            suggestions.append(
                f"Use calculated price from markup: {calculated} "
                f"(Cost: {prices['cost_price']}, Markup: {prices.get(f'markup_percent_{price_level}')}%)"
            )

            for level in [1, 2, 3]:
                level_price = prices.get(f"selling_price_{level}", Decimal(0))
                if level_price > 0 and level != price_level:
                    suggestions.append(f"Price level {level}: {level_price}")

        result = {
            "is_valid": price_valid and discount_valid,
            "price_valid": price_valid,
            "discount_valid": discount_valid,
            "warnings": warnings,
            "suggestions": suggestions,
            "price_info": price_info,
            "discount_percent": discount_percent,
            "max_discount_allowed": max_discount,
        }

        if enforce and not result["is_valid"]:
            raise POSValidationException(
                f"Price validation failed for {stock_code}: "
                + "; ".join(
                    warnings or ["submitted price/discount does not match configured pricing"]
                )
            )

        return result

    @staticmethod
    def get_price_analysis(stock_code: str, transaction_date: date = None) -> Dict:
        """
        Get detailed price analysis for a stock item.
        Shows all available prices and markups.

        Args:
            stock_code: Stock item code
            transaction_date: Transaction date

        Returns:
            Dictionary with complete price analysis
        """
        try:
            prices = PriceValidationService.get_valid_prices_for_item(
                stock_code, transaction_date=transaction_date
            )
        except POSValidationException as e:
            return {"error": str(e)}

        cost_price = prices["cost_price"]
        stock_item = prices["stock_item"]

        analysis = {
            "stock_code": stock_code,
            "description": stock_item.description,
            "cost_price": cost_price,
            "price_levels": {},
            "maximum_discount": prices["maximum_discount"],
            "has_special_deal": "special_deal" in prices,
        }

        # Analyze each price level
        for level in [1, 2, 3]:
            markup = prices.get(f"markup_percent_{level}")
            selling_price = prices.get(f"selling_price_{level}")

            if selling_price and selling_price > 0:
                profit = selling_price - cost_price
                profit_margin = (profit / selling_price * 100).quantize(Decimal("0.01"))

                analysis["price_levels"][f"level_{level}"] = {
                    "selling_price": selling_price,
                    "markup_percent": markup,
                    "profit": profit.quantize(Decimal("0.01")),
                    "profit_margin_percent": profit_margin,
                    "is_valid": selling_price >= cost_price,
                }

        # Special deal if active
        if "special_deal" in prices:
            special = prices["special_deal"]
            analysis["special_deal"] = {
                "start_date": special.start_date,
                "end_date": special.end_date,
                "prices": {
                    "price_1": prices.get("special_selling_price_1"),
                    "price_2": prices.get("special_selling_price_2"),
                    "price_3": prices.get("special_selling_price_3"),
                },
            }

        return analysis

    @staticmethod
    def log_price_variance(
        stock_code: str,
        unit_price: Decimal,
        price_level: int,
        variance_percent: Decimal,
        reason: str = None,
    ):
        """
        Log price variance for audit trail.

        Args:
            stock_code: Stock item code
            unit_price: Price used
            price_level: Price level
            variance_percent: Percentage variance from approved
            reason: Reason for variance
        """
        logger.warning(
            f"Price variance for {stock_code}: "
            f"{variance_percent}% from level {price_level} price. "
            f"Used: {unit_price}. Reason: {reason or 'Not specified'}",
            extra={
                "stock_code": stock_code,
                "unit_price": unit_price,
                "price_level": price_level,
                "variance_percent": variance_percent,
                "reason": reason,
            },
        )
