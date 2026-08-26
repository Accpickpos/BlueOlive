"""
Cash Book Module URLs
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(
    r"income-categories", views.IncomeCategoryViewSet, basename="income-category"
)
router.register(
    r"transactions", views.CashBookTransactionViewSet, basename="transaction"
)
router.register(r"other-income", views.OtherIncomeViewSet, basename="other-income")
router.register(r"other-expenses", views.OtherExpenseViewSet, basename="other-expense")
router.register(r"bank-deposits", views.BankDepositViewSet, basename="bank-deposit")
router.register(
    r"cash-withdrawals", views.CashWithdrawalViewSet, basename="cash-withdrawal"
)
router.register(r"bank-transfers", views.BankTransferViewSet, basename="bank-transfer")
router.register(r"bank-charges", views.BankChargeViewSet, basename="bank-charge")
router.register(
    r"interest-received", views.InterestReceivedViewSet, basename="interest-received"
)
router.register(
    r"bank-reconciliations",
    views.BankReconciliationViewSet,
    basename="bank-reconciliation",
)
router.register(r"cash-floats", views.CashFloatViewSet, basename="cash-float")
router.register(
    r"expense-category-balances",
    views.ExpenseCategoryBalanceViewSet,
    basename="expense-category-balance",
)
router.register(
    r"income-category-balances",
    views.IncomeCategoryBalanceViewSet,
    basename="income-category-balance",
)
router.register(
    r"unpresented-cheques",
    views.UnpresentedChequeViewSet,
    basename="unpresented-cheque",
)

urlpatterns = [
    path("", include(router.urls)),
]
