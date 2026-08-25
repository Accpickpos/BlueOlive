"""
Rentals URL configuration.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'rentals', views.RentalTransactionViewSet, basename='rental-transaction')

app_name = 'rentals'

urlpatterns = [
    path('', include(router.urls)),
]
