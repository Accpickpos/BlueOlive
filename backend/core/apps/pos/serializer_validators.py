"""
POS Serializer Validators.
Enhanced validation logic for POS serializers.
"""
from decimal import Decimal
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .exceptions import (
    DuplicateTransaction, PaymentImbalance, POSValidationException
)
from .calculation_service import CalculationService


class LineItemValidator:
    """Validator for line item data."""
    
    @staticmethod
    def validate_line_item(line_data):
        """
        Validate a single line item.
        
        Args:
            line_data: Dictionary with line item data
        
        Raises:
            serializers.ValidationError: If validation fails
        """
        quantity = line_data.get('quantity')
        unit_price = line_data.get('unit_price')
        discount_percentage = line_data.get('discount_percentage', Decimal('0.00'))
        
        if not quantity:
            raise serializers.ValidationError({'quantity': 'This field is required.'})
        if not unit_price:
            raise serializers.ValidationError({'unit_price': 'This field is required.'})
        
        try:
            CalculationService.calculate_line_totals(
                quantity=quantity,
                unit_price=unit_price,
                discount_percentage=discount_percentage
            )
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e.message))
    
    @staticmethod
    def validate_lines_list(lines_data):
        """
        Validate entire lines list.
        
        Args:
            lines_data: List of line item dictionaries
        
        Raises:
            serializers.ValidationError: If validation fails
        """
        if not lines_data:
            raise serializers.ValidationError("At least one line item is required.")
        
        if len(lines_data) > 999:
            raise serializers.ValidationError("Maximum 999 line items per document.")
        
        for idx, line in enumerate(lines_data, start=1):
            try:
                LineItemValidator.validate_line_item(line)
            except serializers.ValidationError as e:
                raise serializers.ValidationError({
                    'lines': {idx: e.detail}
                })


class DocumentValidator:
    """Validator for document headers."""
    
    @staticmethod
    def validate_customer_details(customer_name, telephone=None, address=None):
        """
        Validate customer information.
        
        Args:
            customer_name: Customer name
            telephone: Phone number (optional)
            address: Address (optional)
        
        Raises:
            serializers.ValidationError: If validation fails
        """
        if not customer_name or not customer_name.strip():
            raise serializers.ValidationError({'customer_name': 'Customer name is required.'})
        
        if len(customer_name.strip()) > 200:
            raise serializers.ValidationError({
                'customer_name': 'Customer name must not exceed 200 characters.'
            })
        
        if telephone and len(str(telephone).strip()) > 50:
            raise serializers.ValidationError({
                'telephone': 'Phone number must not exceed 50 characters.'
            })
    
    @staticmethod
    def validate_date_range(from_date, to_date):
        """
        Validate date range logic.
        
        Args:
            from_date: Start date
            to_date: End date
        
        Raises:
            serializers.ValidationError: If dates are invalid
        """
        if from_date > to_date:
            raise serializers.ValidationError(
                "Start date must be before end date."
            )


class PaymentValidator:
    """Validator for payment-related data."""
    
    @staticmethod
    def validate_tenders(tenders_data, transaction_total):
        """
        Validate tender amounts against transaction total.
        
        Args:
            tenders_data: List of tender dictionaries
            transaction_total: Total transaction amount
        
        Raises:
            serializers.ValidationError: If validation fails
        """
        if not tenders_data:
            raise serializers.ValidationError(
                {'tenders': 'At least one payment method is required.'}
            )
        
        tender_total = Decimal('0.00')
        
        for idx, tender in enumerate(tenders_data, start=1):
            if 'amount' not in tender:
                raise serializers.ValidationError({
                    'tenders': {idx: {'amount': 'This field is required.'}}
                })
            
            try:
                amount = Decimal(str(tender['amount']))
            except Exception:
                raise serializers.ValidationError({
                    'tenders': {idx: {'amount': 'Invalid amount format.'}}
                })
            
            if amount <= 0:
                raise serializers.ValidationError({
                    'tenders': {idx: {'amount': 'Amount must be greater than zero.'}}
                })
            
            tender_total += amount
        
        # Check tender balance
        balance, is_balanced = CalculationService.calculate_tender_balance(
            tenders_data, transaction_total
        )
        
        if not is_balanced:
            raise PaymentImbalance(tender_total, transaction_total)
    
    @staticmethod
    def validate_cheque_details(tender_type, cheque_data):
        """
        Validate cheque-specific details.
        
        Args:
            tender_type: Type of tender
            cheque_data: Dictionary with cheque data
        
        Raises:
            serializers.ValidationError: If validation fails
        """
        if tender_type != 'CHEQUE':
            return
        
        required_fields = ['drawer_name', 'bank_name']
        
        for field in required_fields:
            if not cheque_data.get(field):
                raise serializers.ValidationError({
                    field: f'This field is required for cheque tenders.'
                })


class DocumentNumberValidator:
    """Validator for document numbers."""
    
    @staticmethod
    def validate_unique_number(queryset, number_field, number_value, excluded_pk=None):
        """
        Validate document number is unique.
        
        Args:
            queryset: QuerySet to check
            number_field: Name of number field
            number_value: The number value to check
            excluded_pk: PK to exclude from check (for updates)
        
        Raises:
            serializers.ValidationError: If number already exists
        """
        filter_kwargs = {number_field: number_value}
        
        if queryset.filter(**filter_kwargs).exists():
            # If updating, allow if it's the same record
            if excluded_pk:
                if queryset.filter(**filter_kwargs).exclude(pk=excluded_pk).exists():
                    raise serializers.ValidationError({
                        number_field: f'{number_field} already exists.'
                    })
            else:
                raise serializers.ValidationError({
                    number_field: f'{number_field} already exists.'
                })
