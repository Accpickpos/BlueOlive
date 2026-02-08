"""
General Ledger URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'master-accounts', views.GLMastViewSet, basename='gl-master')
router.register(r'transactions', views.GLTranViewSet, basename='gl-transaction')
router.register(r'standing-journals', views.GLStJnlViewSet, basename='gl-standing-journal')
router.register(r'spread-sheets', views.GLSpreadViewSet, basename='gl-spread')

app_name = 'general_ledger'

urlpatterns = [
    path('', include(router.urls)),
]