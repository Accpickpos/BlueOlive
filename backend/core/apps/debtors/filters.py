"""
Debtors filters.
Django filters for debtor-related models.
"""
import django_filters
from .models import Debtor, DebtorTransaction
from django.db import models
from django.db.models import Q, Sum
from datetime import date, timedelta


class DebtorFilter(django_filters.FilterSet):
    """Filter for Debtor model."""
    
    account_number = django_filters.CharFilter(
        field_name='dno',
        lookup_expr='icontains'
    )
    name = django_filters.CharFilter(lookup_expr='icontains')
    search_name = django_filters.CharFilter(
        field_name='dsname',
        lookup_expr='icontains'
    )
    
    # Balance filters
    min_balance = django_filters.NumberFilter(
        field_name='dcrnt',
        lookup_expr='gte'
    )
    max_balance = django_filters.NumberFilter(
        field_name='dcrnt',
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
            'blockflag': ['exact'],
            'acctype': ['exact'],
            'darea': ['exact'],
            'dintflag': ['exact'],
            'price': ['exact'],
        }
    
    def filter_over_credit_limit(self, queryset, name, value):
        """Filter debtors over their credit limit.
        Checks balance against credit limit.
        """
        if value:
            # Check if any aging balance exceeds credit_limit
            return queryset.filter(
                models.Q(dcrnt__gt=models.F('dclimit')) |
                models.Q(d30__gt=0) |
                models.Q(d60__gt=0)
            )
        return queryset


class DebtorTransactionFilter(django_filters.FilterSet):
    """Filter for DebtorTransaction model with powerful analysis capabilities."""
    
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
    
    # Source filtering
    source_type = django_filters.ChoiceFilter(
        choices=DebtorTransaction.SOURCE_CHOICES
    )
    
    # Aggregation filters for analysis
    has_balance = django_filters.BooleanFilter(
        method='filter_has_balance',
        help_text="Filter to transactions with outstanding balance"
    )
    
    age_bucket = django_filters.ChoiceFilter(
        method='filter_age_bucket',
        choices=[
            ('current', 'Current (0-30 days)'),
            ('30_60', '30-60 Days'),
            ('60_90', '60-90 Days'),
            ('90_plus', '90+ Days'),
        ],
        help_text="Filter by age bucket of transaction"
    )
    
    # Date component filters for analysis
    month = django_filters.NumberFilter(
        field_name='transaction_date',
        lookup_expr='month',
        help_text="Filter by month (1-12)"
    )
    
    year = django_filters.NumberFilter(
        field_name='transaction_date',
        lookup_expr='year',
        help_text="Filter by year"
    )
    
    quarter = django_filters.ChoiceFilter(
        method='filter_quarter',
        choices=[
            (1, 'Q1'),
            (2, 'Q2'),
            (3, 'Q3'),
            (4, 'Q4'),
        ],
        help_text="Filter by fiscal quarter"
    )
    
    class Meta:
        model = DebtorTransaction
        fields = {
            'debtor': ['exact'],
            'transaction_type': ['exact'],
            'transaction_date': ['exact', 'year', 'month'],
            'is_allocated': ['exact'],
            'status': ['exact'],
        }
    
    def filter_has_balance(self, queryset, name, value):
        """Filter transactions with outstanding/unallocated balance."""
        if value:
            return queryset.filter(is_allocated=False)
        return queryset.filter(is_allocated=True)
    
    def filter_age_bucket(self, queryset, name, value):
        """Filter transactions by age bucket based on transaction date."""
        as_of = date.today()
        
        if value == 'current':
            return queryset.filter(
                transaction_date__gte=as_of - timedelta(days=30)
            )
        elif value == '30_60':
            return queryset.filter(
                transaction_date__gte=as_of - timedelta(days=60),
                transaction_date__lt=as_of - timedelta(days=30)
            )
        elif value == '60_90':
            return queryset.filter(
                transaction_date__gte=as_of - timedelta(days=90),
                transaction_date__lt=as_of - timedelta(days=60)
            )
        elif value == '90_plus':
            return queryset.filter(
                transaction_date__lt=as_of - timedelta(days=90)
            )
        return queryset
    
    def filter_quarter(self, queryset, name, value):
        """Filter by fiscal quarter."""
        if value:
            value = int(value)
            return queryset.filter(transaction_date__quarter=value)
        return queryset
