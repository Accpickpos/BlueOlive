from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SalesDepartmentViewSet, SalesAreaViewSet, StockItemViewSet,
    SpecialDealViewSet, FuturePricingViewSet, ShrinkWrapViewSet,
    PackBundleViewSet, StockTransactionViewSet, StockTakeViewSet,
    ContractPricingViewSet, OneTouchLookupKeyViewSet, StockMonthlyStatisticViewSet
)

router = DefaultRouter()

# Register all viewsets
router.register(r'departments', SalesDepartmentViewSet, basename='department')
router.register(r'sales-areas', SalesAreaViewSet, basename='salesarea')
router.register(r'stock-items', StockItemViewSet, basename='stockitem')
router.register(r'special-deals', SpecialDealViewSet, basename='specialdeal')
router.register(r'future-pricing', FuturePricingViewSet, basename='futurepricing')
router.register(r'shrink-wraps', ShrinkWrapViewSet, basename='shrinkwrap')
router.register(r'pack-bundles', PackBundleViewSet, basename='packbundle')
router.register(r'stock-transactions', StockTransactionViewSet, basename='stocktransaction')
router.register(r'stock-takes', StockTakeViewSet, basename='stocktake')
router.register(r'contract-pricing', ContractPricingViewSet, basename='contractpricing')
router.register(r'lookup-keys', OneTouchLookupKeyViewSet, basename='oneTouchLookupKey')
router.register(r'monthly-statistics', StockMonthlyStatisticViewSet, basename='stockmonthlystatistic')

urlpatterns = [
    path('', include(router.urls)),
]