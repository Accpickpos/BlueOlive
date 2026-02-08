"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# Health check endpoints
from core.health_checks import health, ready, metrics

# API versioning
from core.versioning import api_version_info, version_detail

# Import routers from business apps
from apps.debtors.urls import router as debtors_router
from apps.creditors.urls import urlpatterns as creditors_urls
from apps.cash_book.urls import router as cash_book_router
from apps.stock_control.urls import router as stock_control_router
from apps.purchase_orders.urls import router as purchase_orders_router
from apps.pos.urls import router as pos_router
from apps.settings.urls import router as settings_router
from apps.general_ledger.urls import router as general_ledger_router

class LoginRequiredTemplateView(LoginRequiredMixin, TemplateView):
    pass

# API v1 routes - All endpoints versioned under /api/v1/
v1_api_patterns = [
    # Platform Management
    path('tenants/', include('tenancy.urls')),
    path('shops/', include('tenancy.shops_urls')),  # Root-level shops endpoint
    path('users/', include('shop_users.shops_urls')),  # Root-level users endpoint  
    path('users/auth/', include('shop_users.urls')),  # Auth endpoints at /api/v1/users/auth/
    
    # Business Applications
    path('debtors/', include(debtors_router.urls)),
    path('creditors/', include(creditors_urls)),
    path('cash-book/', include(cash_book_router.urls)),
    path('stock-control/', include(stock_control_router.urls)),
    path('purchase-orders/', include(purchase_orders_router.urls)),
    path('pos/', include(pos_router.urls)),
    path('settings/', include(settings_router.urls)),
    path('general-ledger/', include(general_ledger_router.urls)),
]

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Health Checks (Priority: HIGH - for monitoring and orchestration)
    path('health/', health, name='health'),
    path('ready/', ready, name='ready'),
    path('metrics/', metrics, name='metrics'),
    
    # API Schema and Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    
    # API Versioning Information
    path('api/', api_version_info, name='api-version-info'),
    path('api/versions/<str:version>/', version_detail, name='api-version-detail'),
    
    # API v1 - Current version (Priority: HIGH - API versioning)
    path('api/v1/', include(v1_api_patterns)),
    
    # Backward compatibility: also serve under /api/ (will be removed in v2)
    # These redirect or serve v1 endpoints
    path('api/tenants/', include('tenancy.urls')),
    path('api/shops/', include('tenancy.shops_urls')),
    path('api/users/', include('shop_users.shops_urls')),
    path('api/users/auth/', include('shop_users.urls')),  # Auth endpoints for backward compatibility
    path('api/debtors/', include(debtors_router.urls)),
    path('api/creditors/', include(creditors_urls)),
    path('api/cash-book/', include(cash_book_router.urls)),
    path('api/stock-control/', include(stock_control_router.urls)),
    path('api/purchase-orders/', include(purchase_orders_router.urls)),
    path('api/pos/', include(pos_router.urls)),
    path('api/settings/', include(settings_router.urls)),
    path('api/general-ledger/', include(general_ledger_router.urls)),
    
    # Template views for SPA
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='tenant_home'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('dashboard/', LoginRequiredTemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
]
