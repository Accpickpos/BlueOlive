"""
Point of Sale filters.
Django filters for POS models.
"""
import django_filters
from .models import CashSale, Laybye, Quotation, JobCard, Repair


class CashSaleFilter(django_filters.FilterSet):
    """Filter for CashSale model."""
    
    sale_number = django_filters.CharFilter(lookup_expr='icontains')
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters
    date_from = django_filters.DateFilter(
        field_name='sale_date',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='sale_date',
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
    
    class Meta:
        model = CashSale
        fields = {
            'cashier': ['exact'],
            'station_number': ['exact'],
            'sales_area': ['exact'],
            'is_posted': ['exact'],
            'is_cancelled': ['exact'],
            'sale_date': ['exact', 'year', 'month', 'day'],
        }


class LaybyeFilter(django_filters.FilterSet):
    """Filter for Laybye model."""
    
    laybye_number = django_filters.CharFilter(lookup_expr='icontains')
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    telephone = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters
    date_from = django_filters.DateFilter(
        field_name='laybye_date',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='laybye_date',
        lookup_expr='lte'
    )
    
    expiry_from = django_filters.DateFilter(
        field_name='expiry_date',
        lookup_expr='gte'
    )
    expiry_to = django_filters.DateFilter(
        field_name='expiry_date',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Laybye
        fields = {
            'status': ['exact'],
            'sales_area': ['exact'],
            'laybye_date': ['exact', 'year', 'month'],
            'expiry_date': ['exact'],
        }


class QuotationFilter(django_filters.FilterSet):
    """Filter for Quotation model."""
    
    quotation_number = django_filters.CharFilter(lookup_expr='icontains')
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters
    date_from = django_filters.DateFilter(
        field_name='quotation_date',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='quotation_date',
        lookup_expr='lte'
    )
    
    class Meta:
        model = Quotation
        fields = {
            'status': ['exact'],
            'sales_area': ['exact'],
            'quotation_date': ['exact', 'year', 'month'],
            'price_level': ['exact'],
        }


class JobCardFilter(django_filters.FilterSet):
    """Filter for JobCard model."""
    
    job_number = django_filters.CharFilter(lookup_expr='icontains')
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    registration_number = django_filters.CharFilter(lookup_expr='icontains')
    
    # Date range filters
    date_from = django_filters.DateFilter(
        field_name='job_date',
        lookup_expr='gte'
    )
    date_to = django_filters.DateFilter(
        field_name='job_date',
        lookup_expr='lte'
    )
    
    class Meta:
        model = JobCard
        fields = {
            'status': ['exact'],
            'sales_area': ['exact'],
            'operator_number': ['exact'],
            'job_date': ['exact', 'year', 'month'],
        }


class RepairFilter(django_filters.FilterSet):
    """Filter for Repair model."""
    
    repair_number = django_filters.CharFilter(lookup_expr='icontains')
    customer_name = django_filters.CharFilter(lookup_expr='icontains')
    supplier_number = django_filters.NumberFilter()
    
    class Meta:
        model = Repair
        fields = {
            'status': ['exact'],
            'date_required': ['exact', 'gte', 'lte'],
        }