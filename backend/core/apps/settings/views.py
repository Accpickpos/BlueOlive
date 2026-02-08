"""
═══════════════════════════════════════════════════════════════════════════
SETTINGS APP - Django REST Framework Views
ViewSets for all settings models
═══════════════════════════════════════════════════════════════════════════

LOCATION: accpick_project/settings/views.py
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from datetime import datetime
from django.core.management import call_command
from io import StringIO

from .models import (
    SalesDepartment,
    SalesArea,
    IncomeCategory,
    ExpenseCategory,
    TaxCode,
    CostingCategory,
    PaymentMethod,
    CreditTerms,
    SystemConfiguration,
    DepartmentMonthlyStats,
    SalesAreaMonthlyStats,
)
from .serializers import (
    SalesDepartmentSerializer,
    SalesDepartmentListSerializer,
    SalesAreaSerializer,
    SalesAreaListSerializer,
    IncomeCategorySerializer,
    IncomeCategoryListSerializer,
    ExpenseCategorySerializer,
    ExpenseCategoryListSerializer,
    TaxCodeSerializer,
    TaxCodeListSerializer,
    CostingCategorySerializer,
    CostingCategoryListSerializer,
    PaymentMethodSerializer,
    PaymentMethodListSerializer,
    CreditTermsSerializer,
    CreditTermsListSerializer,
    SystemConfigurationSerializer,
    DepartmentMonthlyStatsSerializer,
    SalesAreaMonthlyStatsSerializer,
)


# ═══════════════════════════════════════════════════════════════════════════
# BASE VIEWSET WITH COMMON FUNCTIONALITY
# ═══════════════════════════════════════════════════════════════════════════

class BaseSettingsViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet with common functionality for all settings models
    Handles audit trail (created_by, updated_by)
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    def perform_create(self, serializer):
        """Set created_by on creation"""
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(updated_by=self.request.user)
    
    def get_serializer_class(self):
        """Use list serializer for list action, full serializer otherwise"""
        if self.action == 'list' and hasattr(self, 'list_serializer_class'):
            return self.list_serializer_class
        return self.serializer_class
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Soft delete - mark as inactive"""
        obj = self.get_object()
        obj.is_active = False
        obj.deactivated_at = timezone.now()
        obj.deactivated_by = request.user
        obj.save()
        
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Reactivate an inactive record"""
        obj = self.get_object()
        obj.is_active = True
        obj.deactivated_at = None
        obj.deactivated_by = None
        obj.save()
        
        serializer = self.get_serializer(obj)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active_only(self, request):
        """Get only active records"""
        queryset = self.filter_queryset(self.get_queryset()).filter(is_active=True)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════════════
# SALES DEPARTMENT VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class SalesDepartmentViewSet(BaseSettingsViewSet):
    """
    ViewSet for Sales Departments
    
    List: GET /api/settings/departments/
    Retrieve: GET /api/settings/departments/{id}/
    Create: POST /api/settings/departments/
    Update: PUT/PATCH /api/settings/departments/{id}/
    Delete: DELETE /api/settings/departments/{id}/
    Deactivate: POST /api/settings/departments/{id}/deactivate/
    Activate: POST /api/settings/departments/{id}/activate/
    Active Only: GET /api/settings/departments/active_only/
    Statistics: GET /api/settings/departments/{id}/statistics/
    """
    queryset = SalesDepartment.objects.all()
    serializer_class = SalesDepartmentSerializer
    list_serializer_class = SalesDepartmentListSerializer
    filterset_fields = ['number', 'is_active']
    search_fields = ['name', 'number']
    ordering_fields = ['number', 'name', 'sales_mtd', 'sales_ytd', 'profit_mtd', 'profit_ytd']
    ordering = ['number']
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get department statistics including monthly history"""
        department = self.get_object()
        
        # Current stats
        current_stats = {
            'department': SalesDepartmentListSerializer(department).data,
            'current': {
                'sales_mtd': department.sales_mtd,
                'sales_ytd': department.sales_ytd,
                'profit_mtd': department.profit_mtd,
                'profit_ytd': department.profit_ytd,
                'profit_percent_mtd': department.gross_profit_percent_mtd,
                'profit_percent_ytd': department.gross_profit_percent_ytd,
            }
        }
        
        # Monthly history (last 12 months)
        monthly_stats = DepartmentMonthlyStats.objects.filter(
            department=department
        ).order_by('-year', '-month')[:12]
        
        current_stats['history'] = DepartmentMonthlyStatsSerializer(
            monthly_stats, many=True
        ).data
        
        return Response(current_stats)
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Get top performing departments by sales or profit"""
        metric = request.query_params.get('metric', 'sales_ytd')  # sales_ytd, profit_ytd, sales_mtd, profit_mtd
        limit = int(request.query_params.get('limit', 10))
        
        if metric not in ['sales_ytd', 'profit_ytd', 'sales_mtd', 'profit_mtd']:
            return Response(
                {'error': 'Invalid metric. Use: sales_ytd, profit_ytd, sales_mtd, profit_mtd'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(is_active=True).order_by(f'-{metric}')[:limit]
        serializer = SalesDepartmentListSerializer(queryset, many=True)
        
        return Response({
            'metric': metric,
            'limit': limit,
            'departments': serializer.data
        })


# ═══════════════════════════════════════════════════════════════════════════
# SALES AREA VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class SalesAreaViewSet(BaseSettingsViewSet):
    """
    ViewSet for Sales Areas / Salesmen
    
    List: GET /api/settings/sales-areas/
    Retrieve: GET /api/settings/sales-areas/{id}/
    Create: POST /api/settings/sales-areas/
    Update: PUT/PATCH /api/settings/sales-areas/{id}/
    Delete: DELETE /api/settings/sales-areas/{id}/
    Deactivate: POST /api/settings/sales-areas/{id}/deactivate/
    Activate: POST /api/settings/sales-areas/{id}/activate/
    Active Only: GET /api/settings/sales-areas/active_only/
    Statistics: GET /api/settings/sales-areas/{id}/statistics/
    """
    queryset = SalesArea.objects.all()
    serializer_class = SalesAreaSerializer
    list_serializer_class = SalesAreaListSerializer
    filterset_fields = ['number', 'is_active']
    search_fields = ['name', 'number']
    ordering_fields = ['number', 'name', 'sales_mtd', 'sales_ytd', 'commission_mtd', 'commission_ytd']
    ordering = ['number']
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get sales area statistics including monthly history"""
        sales_area = self.get_object()
        
        # Current stats
        current_stats = {
            'sales_area': SalesAreaListSerializer(sales_area).data,
            'current': {
                'sales_mtd': sales_area.sales_mtd,
                'sales_ytd': sales_area.sales_ytd,
                'profit_mtd': sales_area.profit_mtd,
                'profit_ytd': sales_area.profit_ytd,
                'commission_mtd': sales_area.commission_mtd,
                'commission_ytd': sales_area.commission_ytd,
                'profit_percent_mtd': sales_area.gross_profit_percent_mtd,
                'profit_percent_ytd': sales_area.gross_profit_percent_ytd,
            }
        }
        
        # Monthly history (last 12 months)
        monthly_stats = SalesAreaMonthlyStats.objects.filter(
            sales_area=sales_area
        ).order_by('-year', '-month')[:12]
        
        current_stats['history'] = SalesAreaMonthlyStatsSerializer(
            monthly_stats, many=True
        ).data
        
        return Response(current_stats)
    
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        """Get top performing sales areas by sales, profit, or commission"""
        metric = request.query_params.get('metric', 'sales_ytd')
        limit = int(request.query_params.get('limit', 10))
        
        valid_metrics = ['sales_ytd', 'profit_ytd', 'commission_ytd', 'sales_mtd', 'profit_mtd', 'commission_mtd']
        if metric not in valid_metrics:
            return Response(
                {'error': f'Invalid metric. Use: {", ".join(valid_metrics)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(is_active=True).order_by(f'-{metric}')[:limit]
        serializer = SalesAreaListSerializer(queryset, many=True)
        
        return Response({
            'metric': metric,
            'limit': limit,
            'sales_areas': serializer.data
        })


# ═══════════════════════════════════════════════════════════════════════════
# INCOME CATEGORY VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class IncomeCategoryViewSet(BaseSettingsViewSet):
    """
    ViewSet for Income Categories
    
    List: GET /api/settings/income-categories/
    Retrieve: GET /api/settings/income-categories/{id}/
    Create: POST /api/settings/income-categories/
    Update: PUT/PATCH /api/settings/income-categories/{id}/
    Delete: DELETE /api/settings/income-categories/{id}/
    """
    queryset = IncomeCategory.objects.all()
    serializer_class = IncomeCategorySerializer
    list_serializer_class = IncomeCategoryListSerializer
    filterset_fields = ['number', 'is_active']
    search_fields = ['name', 'number']
    ordering_fields = ['number', 'name', 'total_mtd', 'total_ytd']
    ordering = ['number']


# ═══════════════════════════════════════════════════════════════════════════
# EXPENSE CATEGORY VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class ExpenseCategoryViewSet(BaseSettingsViewSet):
    """
    ViewSet for Expense Categories
    
    List: GET /api/settings/expense-categories/
    Retrieve: GET /api/settings/expense-categories/{id}/
    Create: POST /api/settings/expense-categories/
    Update: PUT/PATCH /api/settings/expense-categories/{id}/
    Delete: DELETE /api/settings/expense-categories/{id}/
    """
    queryset = ExpenseCategory.objects.all()
    serializer_class = ExpenseCategorySerializer
    list_serializer_class = ExpenseCategoryListSerializer
    filterset_fields = ['number', 'category_type', 'is_active']
    search_fields = ['name', 'number']
    ordering_fields = ['number', 'name', 'total_mtd', 'total_ytd']
    ordering = ['number']
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get expense categories filtered by type"""
        category_type = request.query_params.get('type', 'BOTH')
        
        if category_type not in ['BOTH', 'CASHBOOK', 'CREDITORS']:
            return Response(
                {'error': 'Invalid type. Use: BOTH, CASHBOOK, CREDITORS'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            Q(category_type=category_type) | Q(category_type='BOTH'),
            is_active=True
        )
        
        serializer = ExpenseCategoryListSerializer(queryset, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════════════
# TAX CODE VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class TaxCodeViewSet(BaseSettingsViewSet):
    """
    ViewSet for Tax Codes
    
    List: GET /api/settings/tax-codes/
    Retrieve: GET /api/settings/tax-codes/{id}/
    Create: POST /api/settings/tax-codes/
    Update: PUT/PATCH /api/settings/tax-codes/{id}/
    Delete: DELETE /api/settings/tax-codes/{id}/
    Default: GET /api/settings/tax-codes/default/
    """
    queryset = TaxCode.objects.all()
    serializer_class = TaxCodeSerializer
    list_serializer_class = TaxCodeListSerializer
    filterset_fields = ['code', 'is_default', 'is_active']
    search_fields = ['description', 'code']
    ordering_fields = ['code', 'rate']
    ordering = ['code']
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get the default tax code"""
        try:
            tax_code = TaxCode.objects.get(is_default=True, is_active=True)
            serializer = TaxCodeSerializer(tax_code)
            return Response(serializer.data)
        except TaxCode.DoesNotExist:
            return Response(
                {'error': 'No default tax code configured'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set this tax code as default"""
        tax_code = self.get_object()
        
        # Clear existing default
        TaxCode.objects.filter(is_default=True).update(is_default=False)
        
        # Set new default
        tax_code.is_default = True
        tax_code.save()
        
        serializer = TaxCodeSerializer(tax_code)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════════════
# COSTING CATEGORY VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class CostingCategoryViewSet(BaseSettingsViewSet):
    """
    ViewSet for Costing Categories
    
    List: GET /api/settings/costing-categories/
    Retrieve: GET /api/settings/costing-categories/{id}/
    Create: POST /api/settings/costing-categories/
    Update: PUT/PATCH /api/settings/costing-categories/{id}/
    Delete: DELETE /api/settings/costing-categories/{id}/
    """
    queryset = CostingCategory.objects.all()
    serializer_class = CostingCategorySerializer
    list_serializer_class = CostingCategoryListSerializer
    filterset_fields = ['costing_method', 'pricing_method', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'costing_method', 'pricing_method']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def by_methods(self, request):
        """Filter categories by costing and/or pricing method"""
        costing = request.query_params.get('costing')  # A or L
        pricing = request.query_params.get('pricing')  # I or E
        
        queryset = self.get_queryset().filter(is_active=True)
        
        if costing:
            if costing not in ['A', 'L']:
                return Response(
                    {'error': 'Invalid costing method. Use: A (Average) or L (Last)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(costing_method=costing)
        
        if pricing:
            if pricing not in ['I', 'E']:
                return Response(
                    {'error': 'Invalid pricing method. Use: I (Inclusive) or E (Exclusive)'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            queryset = queryset.filter(pricing_method=pricing)
        
        serializer = CostingCategoryListSerializer(queryset, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════════════
# PAYMENT METHOD VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class PaymentMethodViewSet(BaseSettingsViewSet):
    """
    ViewSet for Payment Methods
    
    List: GET /api/settings/payment-methods/
    Retrieve: GET /api/settings/payment-methods/{id}/
    Create: POST /api/settings/payment-methods/
    Update: PUT/PATCH /api/settings/payment-methods/{id}/
    Delete: DELETE /api/settings/payment-methods/{id}/
    """
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    list_serializer_class = PaymentMethodListSerializer
    filterset_fields = ['code', 'is_electronic', 'requires_reference', 'is_active']
    search_fields = ['name', 'code']
    ordering_fields = ['code', 'name']
    ordering = ['code']
    
    @action(detail=False, methods=['get'])
    def electronic(self, request):
        """Get only electronic payment methods"""
        queryset = self.get_queryset().filter(is_electronic=True, is_active=True)
        serializer = PaymentMethodListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def cash_based(self, request):
        """Get only non-electronic payment methods"""
        queryset = self.get_queryset().filter(is_electronic=False, is_active=True)
        serializer = PaymentMethodListSerializer(queryset, many=True)
        return Response(serializer.data)


# ═══════════════════════════════════════════════════════════════════════════
# CREDIT TERMS VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class CreditTermsViewSet(BaseSettingsViewSet):
    """
    ViewSet for Credit Terms
    
    List: GET /api/settings/credit-terms/
    Retrieve: GET /api/settings/credit-terms/{id}/
    Create: POST /api/settings/credit-terms/
    Update: PUT/PATCH /api/settings/credit-terms/{id}/
    Delete: DELETE /api/settings/credit-terms/{id}/
    """
    queryset = CreditTerms.objects.all()
    serializer_class = CreditTermsSerializer
    list_serializer_class = CreditTermsListSerializer
    filterset_fields = ['days', 'is_active']
    search_fields = ['description', 'days']
    ordering_fields = ['days']
    ordering = ['days']


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM CONFIGURATION VIEWSET
# ═══════════════════════════════════════════════════════════════════════════

class SystemConfigurationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for System Configuration (Singleton)
    
    Retrieve: GET /api/settings/system-config/
    Update: PUT/PATCH /api/settings/system-config/
    """
    queryset = SystemConfiguration.objects.all()
    serializer_class = SystemConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        """Always return the singleton instance"""
        return SystemConfiguration.load()
    
    def list(self, request):
        """Return the singleton instance"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request):
        """Not allowed - singleton"""
        return Response(
            {'error': 'System configuration already exists. Use PUT/PATCH to update.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def destroy(self, request, pk=None):
        """Not allowed - singleton"""
        return Response(
            {'error': 'System configuration cannot be deleted'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def perform_update(self, serializer):
        """Set updated_by on update"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def advance_period(self, request):
        """Advance to next accounting period"""
        config = self.get_object()
        
        if config.current_period < 12:
            config.current_period += 1
        else:
            config.current_period = 1
            config.current_financial_year += 1
        
        config.updated_by = request.user
        config.save()
        
        serializer = self.get_serializer(config)
        return Response({
            'message': 'Period advanced successfully',
            'config': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def seed_settings(self, request):
        """Seed settings data (departments, areas, categories, etc.)"""
        try:
            out = StringIO()
            call_command('seed_settings', stdout=out)
            
            return Response({
                'message': 'Settings data seeded successfully',
                'output': out.getvalue()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Failed to seed settings: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def seed_debtors(self, request):
        """Seed sample debtors (customers) data"""
        try:
            out = StringIO()
            call_command('seed_debtors', stdout=out)
            
            return Response({
                'message': 'Debtors data seeded successfully',
                'output': out.getvalue()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Failed to seed debtors: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def seed_creditors(self, request):
        """Seed sample creditors (suppliers) data"""
        try:
            out = StringIO()
            call_command('seed_creditors', stdout=out)
            
            return Response({
                'message': 'Creditors data seeded successfully',
                'output': out.getvalue()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Failed to seed creditors: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def seed_stock_items(self, request):
        """Seed sample stock items data"""
        try:
            out = StringIO()
            call_command('seed_stock_items', stdout=out)
            
            return Response({
                'message': 'Stock items data seeded successfully',
                'output': out.getvalue()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Failed to seed stock items: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def seed_all_data(self, request):
        """Seed all sample data at once"""
        try:
            out = StringIO()
            call_command('seed_all_data', stdout=out)
            
            return Response({
                'message': 'All sample data seeded successfully',
                'output': out.getvalue()
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'Failed to seed all data: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════════════════
# MONTHLY STATISTICS VIEWSETS (READ-ONLY)
# ═══════════════════════════════════════════════════════════════════════════

class DepartmentMonthlyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Department Monthly Statistics
    
    List: GET /api/settings/department-stats/
    Retrieve: GET /api/settings/department-stats/{id}/
    """
    queryset = DepartmentMonthlyStats.objects.all()
    serializer_class = DepartmentMonthlyStatsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['department', 'year', 'month']
    ordering_fields = ['year', 'month', 'sales_value', 'profit_value']
    ordering = ['-year', '-month']
    
    @action(detail=False, methods=['get'])
    def by_year(self, request):
        """Get statistics for a specific year"""
        year = request.query_params.get('year')
        
        if not year:
            return Response(
                {'error': 'Year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(year=year)
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(serializer.data)


class SalesAreaMonthlyStatsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for Sales Area Monthly Statistics
    
    List: GET /api/settings/sales-area-stats/
    Retrieve: GET /api/settings/sales-area-stats/{id}/
    """
    queryset = SalesAreaMonthlyStats.objects.all()
    serializer_class = SalesAreaMonthlyStatsSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['sales_area', 'year', 'month']
    ordering_fields = ['year', 'month', 'sales_value', 'profit_value', 'commission_earned']
    ordering = ['-year', '-month']
    
    @action(detail=False, methods=['get'])
    def by_year(self, request):
        """Get statistics for a specific year"""
        year = request.query_params.get('year')
        
        if not year:
            return Response(
                {'error': 'Year parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(year=year)
        serializer = self.get_serializer(queryset, many=True)
        
        return Response(serializer.data)