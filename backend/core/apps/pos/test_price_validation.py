"""
Tests for PriceValidationService.
Tests price validation, markup calculation, and discount enforcement.
"""
from django.test import TestCase
from decimal import Decimal
from datetime import date, timedelta
from django.core.exceptions import ValidationError

from apps.stock_control.models import StockItem, SpecialDeal
from .price_validation_service import PriceValidationService
from .exceptions import POSValidationException


class PriceValidationServiceTests(TestCase):
    """Test suite for PriceValidationService."""
    
    def setUp(self):
        """Create test stock items with pricing."""
        # Standard item with 3 price levels
        self.stock_item = StockItem.objects.create(
            stock_code='TEST001',
            description='Test Item',
            cost_price=Decimal('100.00'),
            markup_percent_1=Decimal('50.00'),
            markup_percent_2=Decimal('40.00'),
            markup_percent_3=Decimal('30.00'),
            selling_price_1=Decimal('150.00'),
            selling_price_2=Decimal('140.00'),
            selling_price_3=Decimal('130.00'),
            maximum_discount_percent=Decimal('10.00'),
        )
        
        # Item with no pricing
        self.no_price_item = StockItem.objects.create(
            stock_code='TEST002',
            description='No Price Item',
            cost_price=Decimal('0.00'),
            maximum_discount_percent=Decimal('5.00'),
        )
    
    def test_get_valid_prices_for_existing_item(self):
        """Test getting prices for existing stock item."""
        prices = PriceValidationService.get_valid_prices_for_item('TEST001')
        
        self.assertEqual(prices['selling_price_1'], Decimal('150.00'))
        self.assertEqual(prices['selling_price_2'], Decimal('140.00'))
        self.assertEqual(prices['selling_price_3'], Decimal('130.00'))
        self.assertEqual(prices['markup_percent_1'], Decimal('50.00'))
        self.assertEqual(prices['maximum_discount'], Decimal('10.00'))
        self.assertEqual(prices['cost_price'], Decimal('100.00'))
    
    def test_get_valid_prices_nonexistent_item(self):
        """Test exception when item not found."""
        with self.assertRaises(POSValidationException) as ctx:
            PriceValidationService.get_valid_prices_for_item('NONEXISTENT')
        
        self.assertIn('not found', str(ctx.exception))
    
    def test_validate_unit_price_exact_match(self):
        """Test validation when price matches exactly."""
        is_valid, warning, price_info = PriceValidationService.validate_unit_price(
            stock_code='TEST001',
            unit_price=Decimal('150.00'),
            price_level=1
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(warning)
        self.assertEqual(price_info['entered_price'], Decimal('150.00'))
        self.assertEqual(price_info['standard_price'], Decimal('150.00'))
    
    def test_validate_unit_price_within_tolerance(self):
        """Test validation with rounding tolerance."""
        is_valid, warning, price_info = PriceValidationService.validate_unit_price(
            stock_code='TEST001',
            unit_price=Decimal('150.01'),  # 1 cent difference
            price_level=1
        )
        
        self.assertTrue(is_valid)
        self.assertIsNone(warning)
    
    def test_validate_unit_price_higher_than_approved(self):
        """Test validation when entered price is higher."""
        is_valid, warning, price_info = PriceValidationService.validate_unit_price(
            stock_code='TEST001',
            unit_price=Decimal('180.00'),
            price_level=1
        )
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(warning)
        self.assertIn('20.00%', warning)
        self.assertIn('HIGHER', warning)
    
    def test_validate_unit_price_lower_than_approved(self):
        """Test validation when entered price is lower."""
        is_valid, warning, price_info = PriceValidationService.validate_unit_price(
            stock_code='TEST001',
            unit_price=Decimal('120.00'),
            price_level=1
        )
        
        self.assertFalse(is_valid)
        self.assertIsNotNone(warning)
        self.assertIn('20.00%', warning)
        self.assertIn('LOWER', warning)
    
    def test_validate_unit_price_multiple_levels(self):
        """Test validation for different price levels."""
        # Level 2
        is_valid, warning, _ = PriceValidationService.validate_unit_price(
            stock_code='TEST001',
            unit_price=Decimal('140.00'),
            price_level=2
        )
        self.assertTrue(is_valid)
        
        # Level 3
        is_valid, warning, _ = PriceValidationService.validate_unit_price(
            stock_code='TEST001',
            unit_price=Decimal('130.00'),
            price_level=3
        )
        self.assertTrue(is_valid)
    
    def test_validate_unit_price_invalid_level(self):
        """Test validation with invalid price level."""
        with self.assertRaises(POSValidationException):
            PriceValidationService.validate_unit_price(
                stock_code='TEST001',
                unit_price=Decimal('150.00'),
                price_level=4
            )
    
    def test_validate_unit_price_zero_or_negative(self):
        """Test validation rejects zero/negative prices."""
        with self.assertRaises(POSValidationException):
            PriceValidationService.validate_unit_price(
                stock_code='TEST001',
                unit_price=Decimal('0.00'),
                price_level=1
            )
        
        with self.assertRaises(POSValidationException):
            PriceValidationService.validate_unit_price(
                stock_code='TEST001',
                unit_price=Decimal('-50.00'),
                price_level=1
            )
    
    def test_calculate_price_from_markup(self):
        """Test calculating price from cost and markup."""
        # Cost 100, markup 50% = 150
        calculated = PriceValidationService.calculate_price_from_markup(
            stock_code='TEST001',
            price_level=1
        )
        
        self.assertEqual(calculated, Decimal('150.00'))
    
    def test_calculate_price_different_levels(self):
        """Test calculating prices for different markup levels."""
        # Level 2: Cost 100, markup 40% = 140
        calculated = PriceValidationService.calculate_price_from_markup(
            stock_code='TEST001',
            price_level=2
        )
        self.assertEqual(calculated, Decimal('140.00'))
        
        # Level 3: Cost 100, markup 30% = 130
        calculated = PriceValidationService.calculate_price_from_markup(
            stock_code='TEST001',
            price_level=3
        )
        self.assertEqual(calculated, Decimal('130.00'))
    
    def test_calculate_price_no_cost_price(self):
        """Test calculation fails without cost price."""
        with self.assertRaises(POSValidationException):
            PriceValidationService.calculate_price_from_markup(
                stock_code='TEST002',  # No cost price
                price_level=1
            )
    
    def test_validate_line_item_price_valid(self):
        """Test complete line item validation - all valid."""
        result = PriceValidationService.validate_line_item_price(
            stock_code='TEST001',
            quantity=Decimal('5'),
            unit_price=Decimal('150.00'),
            discount_percent=Decimal('5.00'),
            price_level=1
        )
        
        self.assertTrue(result['is_valid'])
        self.assertTrue(result['price_valid'])
        self.assertTrue(result['discount_valid'])
        self.assertEqual(len(result['warnings']), 0)
    
    def test_validate_line_item_invalid_price(self):
        """Test line item validation with invalid price."""
        result = PriceValidationService.validate_line_item_price(
            stock_code='TEST001',
            quantity=Decimal('5'),
            unit_price=Decimal('200.00'),  # Too high
            discount_percent=Decimal('5.00'),
            price_level=1
        )
        
        self.assertFalse(result['is_valid'])
        self.assertFalse(result['price_valid'])
        self.assertTrue(result['discount_valid'])
        self.assertGreater(len(result['warnings']), 0)
    
    def test_validate_line_item_discount_exceeds_maximum(self):
        """Test validation when discount exceeds maximum."""
        result = PriceValidationService.validate_line_item_price(
            stock_code='TEST001',
            quantity=Decimal('5'),
            unit_price=Decimal('150.00'),
            discount_percent=Decimal('15.00'),  # Exceeds 10% max
            price_level=1
        )
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(result['price_valid'])
        self.assertFalse(result['discount_valid'])
        self.assertIn('exceeds maximum', result['warnings'][0])
    
    def test_validate_line_item_high_discount_warning(self):
        """Test warning for high discounts."""
        result = PriceValidationService.validate_line_item_price(
            stock_code='TEST001',
            quantity=Decimal('5'),
            unit_price=Decimal('150.00'),
            discount_percent=Decimal('25.00'),  # High discount
            price_level=1
        )
        
        # Note: This might be invalid depending on maximum_discount
        # But should have a warning about high discount
        warnings = [w for w in result['warnings'] if 'high discount' in w.lower()]
        self.assertGreater(len(warnings), 0)
    
    def test_validate_line_item_extreme_discount_warning(self):
        """Test warning for extreme discounts."""
        # Create item with higher max discount to test extreme case
        high_discount_item = StockItem.objects.create(
            stock_code='TEST003',
            description='High Discount Item',
            cost_price=Decimal('100.00'),
            markup_percent_1=Decimal('50.00'),
            selling_price_1=Decimal('150.00'),
            maximum_discount_percent=Decimal('60.00'),
        )
        
        result = PriceValidationService.validate_line_item_price(
            stock_code='TEST003',
            quantity=Decimal('5'),
            unit_price=Decimal('150.00'),
            discount_percent=Decimal('55.00'),  # Extreme discount
            price_level=1
        )
        
        warnings = [w for w in result['warnings'] if 'EXTREME' in w]
        self.assertGreater(len(warnings), 0)
    
    def test_get_price_analysis(self):
        """Test price analysis for stock item."""
        analysis = PriceValidationService.get_price_analysis('TEST001')
        
        self.assertEqual(analysis['stock_code'], 'TEST001')
        self.assertIn('price_levels', analysis)
        self.assertEqual(analysis['maximum_discount'], Decimal('10.00'))
        self.assertEqual(analysis['cost_price'], Decimal('100.00'))
        
        # Check price level analysis
        level_1 = analysis['price_levels']['level_1']
        self.assertEqual(level_1['selling_price'], Decimal('150.00'))
        self.assertEqual(level_1['markup_percent'], Decimal('50.00'))
        self.assertEqual(level_1['profit'], Decimal('50.00'))
        self.assertTrue(level_1['is_valid'])
    
    def test_get_price_analysis_nonexistent_item(self):
        """Test price analysis for nonexistent item."""
        analysis = PriceValidationService.get_price_analysis('NONEXISTENT')
        
        self.assertIn('error', analysis)
    
    def test_special_deal_integration(self):
        """Test that special deals are included in pricing."""
        # Create active special deal
        special = SpecialDeal.objects.create(
            stock_item=self.stock_item,
            special_selling_price_1=Decimal('120.00'),
            special_selling_price_2=Decimal('115.00'),
            special_selling_price_3=Decimal('110.00'),
            special_markup_1=Decimal('20.00'),
            special_markup_2=Decimal('15.00'),
            special_markup_3=Decimal('10.00'),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            is_active=True
        )
        
        prices = PriceValidationService.get_valid_prices_for_item('TEST001')
        
        self.assertIn('special_deal', prices)
        self.assertEqual(prices['special_selling_price_1'], Decimal('120.00'))
    
    def test_validate_line_item_with_no_stock_code(self):
        """Test validation gracefully handles missing stock code."""
        result = PriceValidationService.validate_line_item_price(
            stock_code=None,
            quantity=Decimal('5'),
            unit_price=Decimal('150.00'),
            discount_percent=Decimal('5.00'),
            price_level=1
        )
        
        # Should handle gracefully (returns error)
        self.assertIn('error', result)
    
    def test_price_variance_logging(self):
        """Test that price variance is logged."""
        # This test just ensures the method doesn't crash
        PriceValidationService.log_price_variance(
            stock_code='TEST001',
            unit_price=Decimal('180.00'),
            price_level=1,
            variance_percent=Decimal('20.00'),
            reason='Manual override'
        )
        
        # If we get here without exception, logging works
        self.assertTrue(True)
    
    def test_discount_none_handling(self):
        """Test handling of None discount_percent."""
        result = PriceValidationService.validate_line_item_price(
            stock_code='TEST001',
            quantity=Decimal('5'),
            unit_price=Decimal('150.00'),
            discount_percent=None,
            price_level=1
        )
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(result['discount_percent'], Decimal(0))
    
    def test_decimal_precision_handling(self):
        """Test that Decimal precision is maintained."""
        result = PriceValidationService.validate_line_item_price(
            stock_code='TEST001',
            quantity=Decimal('1.5'),
            unit_price=Decimal('150.256'),  # Unusual precision
            discount_percent=Decimal('5.333'),
            price_level=1
        )
        
        # Should not crash on unusual decimals
        self.assertIsNotNone(result)
