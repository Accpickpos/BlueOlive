"""
General Ledger URL configuration.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import reports, views

# Create router and register viewsets
router = DefaultRouter()
router.register(r"master-accounts", views.GLMastViewSet, basename="gl-master")
router.register(r"transactions", views.GLTranViewSet, basename="gl-transaction")
router.register(
    r"standing-journals", views.GLStJnlViewSet, basename="gl-standing-journal"
)
router.register(r"spread-sheets", views.GLSpreadViewSet, basename="gl-spread")
router.register(r"batches", views.GLBatchViewSet, basename="gl-batch")
router.register(r"report-formats", views.GLRepViewSet, basename="gl-report-format")
router.register(r"parameters", views.GLParamViewSet, basename="gl-parameter")
router.register(
    r"integration-settings",
    views.GLIntegrationSettingsViewSet,
    basename="gl-integration-settings",
)

app_name = "general_ledger"

reports_urls = [
    path("reports/trial-balance/", reports.trial_balance, name="trial-balance"),
    path("reports/income-statement/", reports.income_statement, name="income-statement"),
    path("reports/balance-sheet/", reports.balance_sheet, name="balance-sheet"),
]

integration_urls = [
    path("integration/transfer/", reports.integration_transfer, name="integration-transfer"),
    path("integration/outstanding/", reports.integration_outstanding, name="integration-outstanding"),
]

urlpatterns = [
    path("", include(router.urls)),
    *reports_urls,
    *integration_urls,
]

# COMPLETE URL REFERENCE
#
# Master Accounts (GLMast):
#   GET/POST      /master-accounts/
#   GET/PATCH/DELETE /master-accounts/{id}/
#   GET  /master-accounts/summary/
#   GET  /master-accounts/by_account_type/?type=I|B
#   GET  /master-accounts/balance_summary/
#   GET  /master-accounts/{id}/account_history/
#
# Transactions (GLTran) — read-only via the API; direct create() is blocked:
#   GET  /transactions/
#   GET  /transactions/{id}/
#   PATCH /transactions/{id}/  (immutable fields enforced)
#   GET  /transactions/by_batch/?batchno=
#   GET  /transactions/by_account/?accno=
#   GET  /transactions/by_date_range/?start_date=&end_date=
#   GET  /transactions/batch_summary/?batchno=
#   GET  /transactions/daily_summary/?date=
#
# Batches (GLBatch) — the staging/balance-check/post workflow:
#   GET/POST      /batches/
#   GET/PATCH/DELETE /batches/{id}/   (blocked once postdate is set)
#   GET  /batches/balance_check/?batchno=
#   POST /batches/post/   body: {"batchno": N}
#
# Standing Journals (GLStJnl):
#   GET/POST      /standing-journals/
#   GET/PATCH/DELETE /standing-journals/{id}/   (balance-validated on write)
#   GET  /standing-journals/validate_balance/?journalno=
#   POST /standing-journals/post_due/
#   GET  /standing-journals/by_account/?accno=
#   GET  /standing-journals/by_journal/?journalno=
#   GET  /standing-journals/active_journals/
#   GET  /standing-journals/by_period/?stperiod=
#
# Spread Sheets (GLSpread):
#   GET/POST/PATCH/DELETE /spread-sheets/...
#   GET  /spread-sheets/summary/
#   GET  /spread-sheets/by_account/?accno=
#   GET  /spread-sheets/variance_analysis/
#
# Report Formats (GLRep) — Maintenance CRUD only:
#   GET/POST/PATCH/DELETE /report-formats/...
#
# Parameters (GLParam) — singleton:
#   GET/PATCH /parameters/1/  (or any id — always resolves to the one row)
#   GET  /parameters/system_status/
#   POST /parameters/period_end/
#   POST /parameters/year_end/
#
# Integration Settings (GLIntegrationSettings) — singleton:
#   GET/PATCH /integration-settings/1/
#
# Reports (function-based, read-only):
#   GET /reports/trial-balance/?as_of_period=&format=csv
#   GET /reports/income-statement/?as_of_period=&mode=current|current_ytd|current_last_year|current_budget|budget_12|variance|actual_12&format=csv
#   GET /reports/balance-sheet/?as_of_period=&format=csv
#
# Integration Transfer:
#   POST /integration/transfer/   body: {"source": "debtors"|"creditors"|"stock_control"|"cash_book"|"all", "date_from":, "date_to":}
#   GET  /integration/outstanding/
