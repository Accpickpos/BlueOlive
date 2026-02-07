from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalesDepartmentViewSet, SalesAreaViewSet, StockItemViewSet,
    SpecialDealViewSet, FuturePricingViewSet
)

router = DefaultRouter()

# Register all viewsets
router.register(r'departments', SalesDepartmentViewSet, basename='department')
router.register(r'sales-areas', SalesAreaViewSet, basename='salesarea')
router.register(r'stock-items', StockItemViewSet, basename='stockitem')
router.register(r'special-deals', SpecialDealViewSet, basename='specialdeal')
router.register(r'future-pricing', FuturePricingViewSet, basename='futurepricing')

urlpatterns = [
    path('', include(router.urls)),
]