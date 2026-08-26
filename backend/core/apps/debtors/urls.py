"""
Debtors URL configuration.
Based on DMAST, DEBTRAN, DEBTOPEN, DPDC, DEBTORAUD table models.
"""

from decimal import Decimal

from django.db.models import Sum
from django.urls import include, path

# Create a simple view for generating reports
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.routers import DefaultRouter

from . import views
from .import_csv import analyze_csv, import_csv, list_tenants_and_shops

# Create router and register viewsets
debtors_router = DefaultRouter()
debtors_router.register(r"", views.DebtorViewSet, basename="debtor")
debtors_router.register(
    r"transactions", views.DebtorTransactionViewSet, basename="debtor-transaction"
)
debtors_router.register(r"open-items", views.DebteopenViewSet, basename="debtopen")
debtors_router.register(r"post-dated-cheques", views.DpdcViewSet, basename="dpdc")
debtors_router.register(r"audit", views.DebtorAuditViewSet, basename="debtor-audit")
debtors_router.register(r"sales-areas", views.DareaViewSet, basename="darea")
debtors_router.register(
    r"documents", views.DocumentSearchViewSet, basename="document-search"
)

app_name = "debtors"


@api_view(["POST"])
def generate_debtor_report(request):
    """Generate debtor reports."""
    from .models import Debtor, DebtorTransaction
    from .serializers import DebtorListSerializer

    report_type = request.data.get("reportType", "summary")

    if report_type == "summary":
        debtors = Debtor.objects.all()
        aggregates = debtors.aggregate(
            total_balance=Sum("balance_current"),
            total_30=Sum("balance_30_days"),
            total_60=Sum("balance_60_days"),
            total_90=Sum("balance_90_days"),
        )
        return Response(
            {
                "report_type": "summary",
                "data": {
                    "total_debtors": debtors.count(),
                    "total_balance": float(
                        aggregates["total_balance"] or Decimal("0.00")
                    ),
                    "overdue_30": float(aggregates["total_30"] or Decimal("0.00")),
                    "overdue_60": float(aggregates["total_60"] or Decimal("0.00")),
                    "overdue_90": float(aggregates["total_90"] or Decimal("0.00")),
                },
            }
        )

    return Response({"error": "Unknown report type"}, status=400)


urlpatterns = [
    path("", include(debtors_router.urls)),
    # Reports endpoint
    path("reports/generate/", generate_debtor_report, name="generate-report"),
    # Import endpoints
    path("import/tenants/", list_tenants_and_shops, name="import-tenants"),
    path("import/analyze/", analyze_csv, name="import-analyze"),
    path("import/execute/", import_csv, name="import-execute"),
]
