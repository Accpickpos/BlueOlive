"""
SaaS Admin URL configuration.
All endpoints require superuser (IsAdminUser) permission.
"""
from django.urls import path
from .import_views import list_tenants_and_shops, analyze_csv, import_csv

app_name = 'saas_admin'

urlpatterns = [
    # CSV Import endpoints
    path('import/tenants/', list_tenants_and_shops, name='import-tenants'),
    path('import/analyze/', analyze_csv, name='import-analyze'),
    path('import/execute/', import_csv, name='import-execute'),
]
