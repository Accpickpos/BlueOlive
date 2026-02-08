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
from django.urls import path, include
from django.views.generic import TemplateView

# Import routers from business apps
from apps.debtors.urls import router as debtors_router
from apps.creditors.urls import urlpatterns as creditors_urls
from apps.cash_book.urls import router as cash_book_router
from apps.stock_control.urls import router as stock_control_router
from apps.purchase_orders.urls import router as purchase_orders_router
from apps.pos.urls import router as pos_router
from apps.settings.urls import router as settings_router

class LoginRequiredTemplateView(LoginRequiredMixin, TemplateView):
    pass

urlpatterns = [
    path('admin/', admin.site.urls),
    # API endpoints - Platform Management
    path('api/', include('tenancy.urls')),
    path('api/', include('shop_users.urls')),
    
    # API endpoints - Business Applications
    path('api/debtors/', include(debtors_router.urls)),
    path('api/creditors/', include(creditors_urls)),
    path('api/cash-book/', include(cash_book_router.urls)),
    path('api/stock-control/', include(stock_control_router.urls)),
    path('api/purchase-orders/', include(purchase_orders_router.urls)),
    path('api/pos/', include(pos_router.urls)),
    path('api/settings/', include(settings_router.urls)),
    
    # Template views for SPA
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('home/', TemplateView.as_view(template_name='home.html'), name='tenant_home'),
    path('login/', TemplateView.as_view(template_name='login.html'), name='login'),
    path('dashboard/', LoginRequiredTemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
]
