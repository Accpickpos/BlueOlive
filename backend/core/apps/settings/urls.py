"""
═══════════════════════════════════════════════════════════════════════════
SETTINGS APP - URL Configuration
URL patterns for all settings endpoints
═══════════════════════════════════════════════════════════════════════════

LOCATION: accpick_project/settings/urls.py
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalesDepartmentViewSet,
    SalesAreaViewSet,
    IncomeCategoryViewSet,
    ExpenseCategoryViewSet,
    TaxCodeViewSet,
    CostingCategoryViewSet,
    PaymentMethodViewSet,
    CreditTermsViewSet,
    SystemConfigurationViewSet,
    DepartmentMonthlyStatsViewSet,
    SalesAreaMonthlyStatsViewSet,
    APIKeyViewSet,
)
from .api.import_api import ImportViewSet

# Create router
router = DefaultRouter()

# Register viewsets
router.register(r'departments', SalesDepartmentViewSet, basename='department')
router.register(r'sales-areas', SalesAreaViewSet, basename='sales-area')
router.register(r'income-categories', IncomeCategoryViewSet, basename='income-category')
router.register(r'expense-categories', ExpenseCategoryViewSet, basename='expense-category')
router.register(r'tax-codes', TaxCodeViewSet, basename='tax-code')
router.register(r'costing-categories', CostingCategoryViewSet, basename='costing-category')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'credit-terms', CreditTermsViewSet, basename='credit-terms')
router.register(r'system-config', SystemConfigurationViewSet, basename='system-config')
router.register(r'department-stats', DepartmentMonthlyStatsViewSet, basename='department-stats')
router.register(r'sales-area-stats', SalesAreaMonthlyStatsViewSet, basename='sales-area-stats')
router.register(r'import', ImportViewSet, basename='import')
router.register(r'api-keys', APIKeyViewSet, basename='api-key')

app_name = 'settings'

urlpatterns = [
    path('', include(router.urls)),
]


"""
═══════════════════════════════════════════════════════════════════════════
API ENDPOINTS DOCUMENTATION
═══════════════════════════════════════════════════════════════════════════

BASE URL: /api/settings/

SALES DEPARTMENTS (/departments/)
----------------------------------
GET     /departments/                      - List all departments
GET     /departments/active_only/          - List only active departments
GET     /departments/top_performers/       - Get top performing departments
                                            Query params: metric (sales_ytd, profit_ytd, sales_mtd, profit_mtd), limit (default: 10)
GET     /departments/{id}/                 - Get specific department
GET     /departments/{id}/statistics/      - Get department statistics with history
POST    /departments/                      - Create new department
PUT     /departments/{id}/                 - Update department (full)
PATCH   /departments/{id}/                 - Update department (partial)
DELETE  /departments/{id}/                 - Delete department
POST    /departments/{id}/deactivate/      - Deactivate department (soft delete)
POST    /departments/{id}/activate/        - Reactivate department

SALES AREAS (/sales-areas/)
----------------------------
GET     /sales-areas/                      - List all sales areas
GET     /sales-areas/active_only/          - List only active sales areas
GET     /sales-areas/top_performers/       - Get top performing sales areas
                                            Query params: metric, limit
GET     /sales-areas/{id}/                 - Get specific sales area
GET     /sales-areas/{id}/statistics/      - Get sales area statistics with history
POST    /sales-areas/                      - Create new sales area
PUT     /sales-areas/{id}/                 - Update sales area (full)
PATCH   /sales-areas/{id}/                 - Update sales area (partial)
DELETE  /sales-areas/{id}/                 - Delete sales area
POST    /sales-areas/{id}/deactivate/      - Deactivate sales area
POST    /sales-areas/{id}/activate/        - Reactivate sales area

INCOME CATEGORIES (/income-categories/)
---------------------------------------
GET     /income-categories/                - List all income categories
GET     /income-categories/active_only/    - List only active categories
GET     /income-categories/{id}/           - Get specific category
POST    /income-categories/                - Create new category
PUT     /income-categories/{id}/           - Update category (full)
PATCH   /income-categories/{id}/           - Update category (partial)
DELETE  /income-categories/{id}/           - Delete category
POST    /income-categories/{id}/deactivate/ - Deactivate category
POST    /income-categories/{id}/activate/   - Reactivate category

EXPENSE CATEGORIES (/expense-categories/)
-----------------------------------------
GET     /expense-categories/               - List all expense categories
GET     /expense-categories/active_only/   - List only active categories
GET     /expense-categories/by_type/       - Filter by type (BOTH, CASHBOOK, CREDITORS)
GET     /expense-categories/{id}/          - Get specific category
POST    /expense-categories/               - Create new category
PUT     /expense-categories/{id}/          - Update category (full)
PATCH   /expense-categories/{id}/          - Update category (partial)
DELETE  /expense-categories/{id}/          - Delete category
POST    /expense-categories/{id}/deactivate/ - Deactivate category
POST    /expense-categories/{id}/activate/   - Reactivate category

TAX CODES (/tax-codes/)
-----------------------
GET     /tax-codes/                        - List all tax codes
GET     /tax-codes/active_only/            - List only active tax codes
GET     /tax-codes/default/                - Get default tax code
GET     /tax-codes/{id}/                   - Get specific tax code
POST    /tax-codes/                        - Create new tax code
POST    /tax-codes/{id}/set_default/       - Set as default tax code
PUT     /tax-codes/{id}/                   - Update tax code (full)
PATCH   /tax-codes/{id}/                   - Update tax code (partial)
DELETE  /tax-codes/{id}/                   - Delete tax code
POST    /tax-codes/{id}/deactivate/        - Deactivate tax code
POST    /tax-codes/{id}/activate/          - Reactivate tax code

COSTING CATEGORIES (/costing-categories/)
-----------------------------------------
GET     /costing-categories/               - List all costing categories
GET     /costing-categories/active_only/   - List only active categories
GET     /costing-categories/by_methods/    - Filter by costing/pricing method
                                            Query params: costing (A/L), pricing (I/E)
GET     /costing-categories/{id}/          - Get specific category
POST    /costing-categories/               - Create new category
PUT     /costing-categories/{id}/          - Update category (full)
PATCH   /costing-categories/{id}/          - Update category (partial)
DELETE  /costing-categories/{id}/          - Delete category
POST    /costing-categories/{id}/deactivate/ - Deactivate category
POST    /costing-categories/{id}/activate/   - Reactivate category

PAYMENT METHODS (/payment-methods/)
-----------------------------------
GET     /payment-methods/                  - List all payment methods
GET     /payment-methods/active_only/      - List only active methods
GET     /payment-methods/electronic/       - Get electronic payment methods only
GET     /payment-methods/cash_based/       - Get non-electronic methods only
GET     /payment-methods/{id}/             - Get specific method
POST    /payment-methods/                  - Create new method
PUT     /payment-methods/{id}/             - Update method (full)
PATCH   /payment-methods/{id}/             - Update method (partial)
DELETE  /payment-methods/{id}/             - Delete method
POST    /payment-methods/{id}/deactivate/  - Deactivate method
POST    /payment-methods/{id}/activate/    - Reactivate method

CREDIT TERMS (/credit-terms/)
-----------------------------
GET     /credit-terms/                     - List all credit terms
GET     /credit-terms/active_only/         - List only active terms
GET     /credit-terms/{id}/                - Get specific terms
POST    /credit-terms/                     - Create new terms
PUT     /credit-terms/{id}/                - Update terms (full)
PATCH   /credit-terms/{id}/                - Update terms (partial)
DELETE  /credit-terms/{id}/                - Delete terms
POST    /credit-terms/{id}/deactivate/     - Deactivate terms
POST    /credit-terms/{id}/activate/       - Reactivate terms

SYSTEM CONFIGURATION (/system-config/)
--------------------------------------
GET     /system-config/                    - Get system configuration
PUT     /system-config/                    - Update configuration (full)
PATCH   /system-config/                    - Update configuration (partial)
POST    /system-config/advance_period/     - Advance to next accounting period

DEPARTMENT MONTHLY STATS (/department-stats/)
---------------------------------------------
GET     /department-stats/                 - List all department statistics
GET     /department-stats/by_year/         - Get stats for specific year
                                            Query param: year (required)
GET     /department-stats/{id}/            - Get specific stat record

SALES AREA MONTHLY STATS (/sales-area-stats/)
---------------------------------------------
GET     /sales-area-stats/                 - List all sales area statistics
GET     /sales-area-stats/by_year/         - Get stats for specific year
                                            Query param: year (required)
GET     /sales-area-stats/{id}/            - Get specific stat record


FILTERING & SEARCH
------------------
All list endpoints support filtering, searching, and ordering:

Examples:
  /departments/?is_active=true
  /departments/?search=electronics
  /departments/?ordering=-sales_ytd
  /expense-categories/?category_type=CASHBOOK
  /tax-codes/?is_default=true


PAGINATION
----------
All list endpoints are paginated (default: 100 items per page)

Query params:
  ?page=2
  ?page_size=50


AUTHENTICATION
--------------
All endpoints require authentication.
Include token in request header:
  Authorization: Token <your-token>
  or
  Authorization: Bearer <your-token>
"""