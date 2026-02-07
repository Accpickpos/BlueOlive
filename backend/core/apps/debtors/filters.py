"""
Debtors filters.
Django filters for debtor-related models.
"""
import django_filters
from .models import Debtor, DebtorTransaction, Invoice
from django.db import models


class DebtorFilter(django_filters.FilterSet):
    """Filter for Debtor model."""
    
    account_number = django_filters.CharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    search_name = django_filters.CharFilter(lookup_expr='icontains')
    
    # Balance filters
    min_balance = django_filters.NumberFilter(
        field_name='current_balance',
        lookup_expr='gte'
    )
    max_balance = django_filters.NumberFilter(
        field_name='current_balance',
        lookup_expr='lte'
    )
    
    # Credit limit filters
    over_credit_limit = django_filters.BooleanFilter(
        method='filter_over_credit_limit'
    )
    
    # Date filters
    created_after = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Debtor
        fields = {
            'is_active': ['exact'],
            'is_blocked': ['exact'],
            'account_category': ['exact'],
            'sales_area': ['exact'],
            'charge_interest': ['exact'],
            'price_level': ['exact'],
        }
    
    def filter_over_credit_limit(self, queryset, name, value):
        """Filter debtors over their credit limit.
        Checks total balance (not just current) against credit limit.
        """
        if value:
            # Check if total_balance exceeds credit_limit
            return queryset.filter(total_balance__gt=models.F('credit_limit'))
        return queryset


class DebtorTransactionFilter(django_filters.FilterSet):
    """Filter for DebtorTransaction model."""
    
    # Date range filters
    date_from = django_filters.DateFilter(
        field_name='transaction_date',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='transaction_date',
        lookup_expr='lte'
    )
    
    # Amount filters
    min_amount = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte'
    )
    max_amount = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte'
    )
    
    # Reference search
    reference = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = DebtorTransaction
        fields = {
            'debtor': ['exact'],
            'transaction_type': ['exact'],
            'transaction_date': ['exact', 'year', 'month'],
            'is_allocated': ['exact'],
        }


class InvoiceFilter(django_filters.FilterSet):
    """Filter for Invoice model."""
    
    invoice_number = django_filters.CharFilter(lookup_expr='icontains')
    order_number = django_filters.CharFilter(lookup_expr='icontains')
    customer_reference = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters
    date_from = django_filters.DateFilter(
        field_name='invoice_date',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='invoice_date',
        lookup_expr='lte'
    )
    
    # Amount filters
    min_amount = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte'
    )
    max_amount = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte'
    )
    
    # Profit filters
    min_profit = django_filters.NumberFilter(
        field_name='gross_profit',
        lookup_expr='gte'
    )
    
    class Meta:
        model = Invoice
        fields = {
            'debtor': ['exact'],
            'sales_area': ['exact'],
            'is_posted': ['exact'],
            'is_cancelled': ['exact'],
            'invoice_date': ['exact', 'year', 'month'],
        }