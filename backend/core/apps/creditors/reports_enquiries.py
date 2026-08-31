"""
Creditors Reports & Enquiries — read-only, ad hoc aggregation endpoints.

Priority-gap audit: "The entire Reports menu (6 report types) has zero
backend implementation... 5 of 6 Enquiries screens... call unregistered
routes too." The frontend components (frontend/app/dashboard/admin/
creditors/{reports,enquiries}/) were built against a specific, fixed
response shape that was never implemented server-side — this module
supplies exactly that shape.

These are plain function-based views (not ViewSets) because each one
returns a bespoke aggregation payload, not a serialized model list — there
is no single queryset/serializer pair to hang a ViewSet off. All read-only;
no permission tier beyond authentication is needed since none of them
mutate data.
"""

from datetime import date as date_cls
from datetime import datetime
from decimal import Decimal

from apps.pos.models import Payout as PosPayout
from apps.settings.models import ExpenseCategory
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Creditor,
    CreditorCreditNote,
    CreditorInvoice,
    CreditorJournal,
    CreditorPayment,
    ExpenseCategoryMonthlyBalance,
    ExpenseCategoryTransaction,
    GoodsReceivedNote,
    OpenItemAllocation,
)

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
ZERO = Decimal("0")


def _bool(value, default=False):
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes")


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, date_cls):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _today():
    return timezone.now().date()


def _balances_dict(obj):
    return {
        "current": obj.balance_current,
        "30_days": obj.balance_30_days,
        "60_days": obj.balance_60_days,
        "90_days": obj.balance_90_days,
        "120_days": obj.balance_120_days,
        "150_days": obj.balance_150_days,
        "180_days": obj.balance_180_days,
        "total": obj.total_outstanding_balance,
    }


# ============================================================================
# REPORTS
# ============================================================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def account_details_report(request):
    include_postal = _bool(request.query_params.get("include_postal"))
    address_type = request.query_params.get("address_type", "both")
    sequence = request.query_params.get("sequence", "A")
    include_banking = _bool(request.query_params.get("include_banking"))

    qs = Creditor.objects.filter(is_active=True)
    qs = qs.order_by("name" if sequence == "A" else "supplier_number")

    accounts = []
    for c in qs:
        row = {
            "account_number": c.supplier_number,
            "name": c.name,
            "short_name": c.name[:15],
            "account_type": c.account_category,
            "contact_person": c.contact_person,
            "telephone1": c.telephone,
            "telephone2": c.fax,
            "email": c.email,
            "fax": c.fax,
        }
        if include_postal or address_type in ("both", "postal"):
            row["postal_address"] = ", ".join(
                filter(
                    None,
                    [c.postal_address_line1, c.postal_address_line2, c.postal_address_line3],
                )
            )
        if address_type in ("both", "delivery"):
            row["physical_address"] = ", ".join(
                filter(
                    None,
                    [
                        c.physical_address_line1,
                        c.physical_address_line2,
                        c.physical_address_line3,
                    ],
                )
            )
        if include_banking:
            row["banking_details"] = {
                "bank_name": c.bank_name,
                "branch_code": c.branch_code,
                "account_number": c.account_number,
            }
        accounts.append(row)

    return Response(
        {
            "report_title": "Creditors Account Details",
            "report_date": _today().isoformat(),
            "sequence": sequence,
            "address_type": address_type,
            "include_banking_details": include_banking,
            "total_accounts": len(accounts),
            "accounts": accounts,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def age_analysis_report(request):
    report_type = request.query_params.get("report_type", "summary")
    sequence = request.query_params.get("sequence", "A")
    include_zero = _bool(request.query_params.get("include_zero"))
    print_last_paid = _bool(request.query_params.get("print_last_paid"))
    print_banking = _bool(request.query_params.get("print_banking"))
    report_date = request.query_params.get("report_date") or _today().isoformat()

    qs = Creditor.objects.filter(is_active=True)
    if not include_zero:
        qs = qs.exclude(total_outstanding_balance=0)
    qs = qs.order_by("name" if sequence == "A" else "supplier_number")

    totals = {
        "current": ZERO, "30_days": ZERO, "60_days": ZERO, "90_days": ZERO,
        "120_days": ZERO, "150_days": ZERO, "180_days": ZERO, "total": ZERO,
    }
    creditors = []
    for c in qs:
        balances = _balances_dict(c)
        for key in totals:
            totals[key] += balances[key]
        row = {"account_number": c.supplier_number, "name": c.name, "balances": balances}
        if print_last_paid:
            row["last_paid_amount"] = c.last_paid_amount
            row["last_paid_date"] = c.last_paid_date.isoformat() if c.last_paid_date else None
        if print_banking:
            row["banking_details"] = {
                "bank_name": c.bank_name,
                "branch_code": c.branch_code,
                "account_number": c.account_number,
            }
        creditors.append(row)

    return Response(
        {
            "report_title": "Creditors Age Analysis",
            "report_date": report_date,
            "report_type": report_type,
            "sequence": sequence,
            "include_zero_balances": include_zero,
            "summary_totals": totals,
            "creditor_count": len(creditors),
            "creditors": creditors,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def remittance_advices_report(request):
    period_type = request.query_params.get("period_type", "current")
    include_zero = _bool(request.query_params.get("include_zero"))
    sequence = request.query_params.get("sequence", "A")

    qs = Creditor.objects.filter(is_active=True)
    if not include_zero:
        qs = qs.exclude(total_outstanding_balance=0)
    qs = qs.order_by("name" if sequence == "A" else "supplier_number")

    remittances = [
        {
            "supplier_id": c.id,
            "supplier_name": c.name,
            "balances": {"current": c.balance_current, "total": c.total_outstanding_balance},
        }
        for c in qs
    ]

    return Response(
        {
            "report_title": "Remittance Advices",
            "period_type": period_type,
            "total_remittances": len(remittances),
            "remittances": remittances,
        }
    )


_TRANSACTION_MODELS = [
    (GoodsReceivedNote, "GRN"),
    (CreditorInvoice, "Invoice"),
    (CreditorCreditNote, "Credit Note"),
    (CreditorPayment, "Payment"),
    (CreditorJournal, "Journal"),
]


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transactions_report(request):
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")
    report_type = request.query_params.get("report_type", "detailed")

    rows = []
    for model, type_label in _TRANSACTION_MODELS:
        qs = model.objects.select_related("creditor")
        if start_date:
            qs = qs.filter(transaction_date__gte=start_date)
        if end_date:
            qs = qs.filter(transaction_date__lte=end_date)
        for t in qs:
            total = t.total_amount
            vat = getattr(t, "total_vat", ZERO) or ZERO
            rows.append(
                {
                    "date": t.transaction_date.isoformat(),
                    "supplier": t.creditor.name,
                    "type": type_label,
                    "amount_vat_exclusive": total - vat,
                    "amount_vat": vat,
                    "amount_total": total,
                }
            )
    rows.sort(key=lambda r: r["date"])

    totals = {
        "amount_vat_exclusive": sum((r["amount_vat_exclusive"] for r in rows), ZERO),
        "amount_vat": sum((r["amount_vat"] for r in rows), ZERO),
        "amount_total": sum((r["amount_total"] for r in rows), ZERO),
        "transaction_count": len(rows),
    }

    return Response(
        {
            "report_title": "Creditors Transactions",
            "period_from": start_date,
            "period_to": end_date,
            "totals": totals,
            "transactions": [] if report_type == "totals_only" else rows,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def expense_tax_report(request):
    report_type = request.query_params.get("report_type", "monthly_tax")
    sequence = request.query_params.get("sequence", "A")
    report_zero = _bool(request.query_params.get("report_zero"))
    report_date = _parse_date(request.query_params.get("report_date")) or _today()

    qs = ExpenseCategoryTransaction.objects.filter(transaction_date__year=report_date.year)
    if report_type != "ytd":
        qs = qs.filter(transaction_date__month=report_date.month)
    else:
        qs = qs.filter(transaction_date__lte=report_date)

    order_field = "expense_category__name" if sequence == "A" else "expense_category__number"
    agg = (
        qs.values("expense_category__name", "expense_category__number")
        .annotate(excl=Sum("amount_exclusive"), vat=Sum("input_vat_amount"), cnt=Count("id"))
        .order_by(order_field)
    )

    categories = []
    for row in agg:
        excl = row["excl"] or ZERO
        vat = row["vat"] or ZERO
        if not report_zero and excl == 0 and vat == 0:
            continue
        categories.append(
            {
                "category_name": row["expense_category__name"],
                "amount_vat_exclusive": excl,
                "amount_vat": vat,
                "amount_vat_inclusive": excl + vat,
                "transaction_count": row["cnt"],
            }
        )

    return Response(
        {
            "report_title": "Expense & Tax Report",
            "report_type": report_type,
            "categories": categories,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payouts_report(request):
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")

    creditor_qs = CreditorPayment.objects.select_related("creditor")
    pos_qs = PosPayout.objects.all()
    if start_date:
        creditor_qs = creditor_qs.filter(transaction_date__gte=start_date)
        pos_qs = pos_qs.filter(payout_date__gte=start_date)
    if end_date:
        creditor_qs = creditor_qs.filter(transaction_date__lte=end_date)
        pos_qs = pos_qs.filter(payout_date__lte=end_date)

    payouts = []
    creditor_total = ZERO
    for p in creditor_qs:
        creditor_total += p.amount_paid
        payouts.append(
            {
                "date": p.transaction_date.isoformat(),
                "supplier": p.creditor.name,
                "reference": p.transaction_reference or p.transaction_number,
                "source": "Creditors",
                "amount": p.amount_paid,
            }
        )

    pos_total = ZERO
    for p in pos_qs:
        pos_total += p.amount
        payouts.append(
            {
                "date": p.payout_date.isoformat(),
                "supplier": p.payee,
                "reference": p.reference,
                "source": "POS",
                "amount": p.amount,
            }
        )
    payouts.sort(key=lambda r: r["date"])

    return Response(
        {
            "report_title": "Payouts Report",
            "period_from": start_date,
            "period_to": end_date,
            "totals": {
                "creditor_payouts": creditor_total,
                "pos_payouts": pos_total,
                "total_payouts": creditor_total + pos_total,
                "payout_count": len(payouts),
            },
            "payouts": payouts,
        }
    )


# ============================================================================
# ENQUIRIES
# ============================================================================

_ALL_ENTRY_TYPES = [
    "INVOICE_STOCK", "INVOICE_EXPENSE", "CREDIT_STOCK", "CREDIT_EXPENSE",
    "PAYMENT", "SETTLEMENT_DISCOUNT", "DEBIT_JOURNAL", "CREDIT_JOURNAL",
]


def _scroll_row(date_, number, type_, supplier, net, vat, total):
    return {
        "date": date_.isoformat(),
        "transaction_number": number,
        "transaction_type": type_,
        "supplier_name": supplier,
        "net_amount": net,
        "vat_amount": vat,
        "total_amount": total,
    }


def _apply_date_range(qs, start_date, end_date, field="transaction_date"):
    if start_date:
        qs = qs.filter(**{f"{field}__gte": start_date})
    if end_date:
        qs = qs.filter(**{f"{field}__lte": end_date})
    return qs


def _scroll_rows(entry_type, start_date, end_date):
    rows = []
    if entry_type == "INVOICE_STOCK":
        for t in _apply_date_range(GoodsReceivedNote.objects.select_related("creditor"), start_date, end_date):
            rows.append(_scroll_row(t.transaction_date, t.transaction_number, entry_type, t.creditor.name, t.subtotal, t.total_vat, t.total_amount))
    elif entry_type == "INVOICE_EXPENSE":
        for t in _apply_date_range(CreditorInvoice.objects.select_related("creditor"), start_date, end_date):
            rows.append(_scroll_row(t.transaction_date, t.transaction_number, entry_type, t.creditor.name, t.subtotal, t.total_vat, t.total_amount))
    elif entry_type == "CREDIT_STOCK":
        for t in _apply_date_range(CreditorCreditNote.objects.select_related("creditor"), start_date, end_date):
            rows.append(_scroll_row(t.transaction_date, t.transaction_number, entry_type, t.creditor.name, t.subtotal, t.total_vat, t.total_amount))
    elif entry_type == "CREDIT_EXPENSE":
        # No distinct expense credit-note model exists in this schema —
        # expense corrections are posted as CreditorJournal credit journals.
        pass
    elif entry_type == "PAYMENT":
        for t in _apply_date_range(CreditorPayment.objects.select_related("creditor"), start_date, end_date):
            rows.append(_scroll_row(t.transaction_date, t.transaction_number, entry_type, t.creditor.name, t.amount_paid, ZERO, t.amount_paid))
    elif entry_type == "SETTLEMENT_DISCOUNT":
        allocations = OpenItemAllocation.objects.filter(settlement_discount__gt=0).select_related("payment__creditor")
        allocations = _apply_date_range(allocations, start_date, end_date, field="payment__transaction_date")
        for a in allocations:
            rows.append(_scroll_row(a.payment.transaction_date, a.payment.transaction_number, entry_type, a.payment.creditor.name, a.settlement_discount, ZERO, a.settlement_discount))
    elif entry_type in ("DEBIT_JOURNAL", "CREDIT_JOURNAL"):
        jtype = "DJ" if entry_type == "DEBIT_JOURNAL" else "CJ"
        qs = CreditorJournal.objects.filter(journal_type=jtype).select_related("creditor")
        for t in _apply_date_range(qs, start_date, end_date):
            rows.append(_scroll_row(t.transaction_date, t.transaction_number, entry_type, t.creditor.name, t.journal_amount, ZERO, t.journal_amount))
    return rows


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def transaction_scroll_enquiry(request):
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")
    enquiry_type = request.query_params.get("enquiry_type", "scroll")
    entry_types = request.query_params.getlist("entry_types") or _ALL_ENTRY_TYPES

    all_rows = []
    for entry_type in entry_types:
        all_rows.extend(_scroll_rows(entry_type, start_date, end_date))
    all_rows.sort(key=lambda r: r["date"])

    grand_total = {
        "count": len(all_rows),
        "total_exclusive": sum((r["net_amount"] for r in all_rows), ZERO),
        "total_vat": sum((r["vat_amount"] for r in all_rows), ZERO),
        "total_inclusive": sum((r["total_amount"] for r in all_rows), ZERO),
    }

    if enquiry_type == "totals":
        by_type = {}
        for r in all_rows:
            bucket = by_type.setdefault(
                r["transaction_type"],
                {"transaction_type": r["transaction_type"], "count": 0, "total_exclusive": ZERO, "total_vat": ZERO, "total_inclusive": ZERO},
            )
            bucket["count"] += 1
            bucket["total_exclusive"] += r["net_amount"]
            bucket["total_vat"] += r["vat_amount"]
            bucket["total_inclusive"] += r["total_amount"]
        return Response({"totals": list(by_type.values()), "grand_total": grand_total})

    return Response({"count": len(all_rows), "transactions": all_rows, "grand_total": grand_total})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def expenditure_totals_enquiry(request):
    today = _today()
    year = int(request.query_params.get("year") or today.year)
    month = int(request.query_params.get("month") or today.month)

    agg = ExpenseCategoryTransaction.objects.filter(
        transaction_date__year=year, transaction_date__month=month
    ).aggregate(excl=Sum("amount_exclusive"), vat=Sum("input_vat_amount"), cnt=Count("id"))
    excl = agg["excl"] or ZERO
    vat = agg["vat"] or ZERO

    return Response(
        {
            "expenditure": {"total_exclusive": excl, "total_vat": vat, "total_inclusive": excl + vat},
            "transaction_count": agg["cnt"] or 0,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def expense_category_totals_enquiry(request):
    today = _today()
    year = int(request.query_params.get("year") or today.year)
    month = int(request.query_params.get("month") or today.month)

    agg = (
        ExpenseCategoryTransaction.objects.filter(transaction_date__year=year, transaction_date__month=month)
        .values("expense_category__name")
        .annotate(excl=Sum("amount_exclusive"), vat=Sum("input_vat_amount"))
        .order_by("expense_category__name")
    )

    categories = []
    grand_excl = ZERO
    grand_vat = ZERO
    for row in agg:
        excl = row["excl"] or ZERO
        vat = row["vat"] or ZERO
        grand_excl += excl
        grand_vat += vat
        categories.append(
            {"category_name": row["expense_category__name"], "mtd_exclusive": excl, "mtd_vat": vat, "mtd_inclusive": excl + vat}
        )

    return Response(
        {
            "categories": categories,
            "grand_total": {"exclusive": grand_excl, "vat": grand_vat, "inclusive": grand_excl + grand_vat},
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def expense_category_details_enquiry(request):
    category_id = request.query_params.get("category_id")
    today = _today()
    year = int(request.query_params.get("year") or today.year)
    month = int(request.query_params.get("month") or today.month)
    if not category_id:
        return Response({"detail": "category_id query param required."}, status=400)

    category = get_object_or_404(ExpenseCategory, pk=category_id)
    qs = (
        ExpenseCategoryTransaction.objects.filter(
            expense_category_id=category_id, transaction_date__year=year, transaction_date__month=month
        )
        .select_related("creditor")
        .order_by("transaction_date")
    )

    details = []
    excl_total = ZERO
    vat_total = ZERO
    for t in qs:
        excl_total += t.amount_exclusive
        vat_total += t.input_vat_amount
        details.append(
            {
                "date": t.transaction_date.isoformat(),
                "transaction_number": t.transaction_number,
                "supplier_name": t.creditor.name,
                "description": category.name,
                "amount_exclusive": t.amount_exclusive,
                "tax_amount": t.input_vat_amount,
                "amount_inclusive": t.amount_inclusive,
            }
        )

    return Response(
        {
            "category": {"name": category.name},
            "totals": {"exclusive": excl_total, "vat": vat_total, "inclusive": excl_total + vat_total},
            "details": details,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def monthly_expense_details_enquiry(request):
    category_id = request.query_params.get("category_id")
    year = int(request.query_params.get("year") or _today().year)
    if not category_id:
        return Response({"detail": "category_id query param required."}, status=400)

    category = get_object_or_404(ExpenseCategory, pk=category_id)
    balance = ExpenseCategoryMonthlyBalance.objects.filter(
        expense_category_id=category_id, year=year
    ).first()

    monthly_values = [balance.get_month(m) if balance else ZERO for m in range(1, 13)]
    year_total = sum(monthly_values, ZERO)

    monthly_data = []
    for i, value in enumerate(monthly_values, start=1):
        percentage = (value / year_total * 100) if year_total else ZERO
        monthly_data.append(
            {
                "month": MONTH_NAMES[i - 1],
                "month_number": i,
                "exclusive": value,
                "percentage": percentage.quantize(Decimal("0.01")),
            }
        )

    return Response(
        {
            "category": {"id": category.id, "name": category.name},
            "year": year,
            "monthly_data": monthly_data,
            "year_total": year_total,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def purchase_history_enquiry(request):
    year = int(request.query_params.get("year") or _today().year)
    sort_by = request.query_params.get("sort_by", "supplier_number")

    buckets = {}
    for model in (GoodsReceivedNote, CreditorInvoice):
        agg = (
            model.objects.filter(transaction_date__year=year)
            .values("creditor_id", "creditor__supplier_number", "creditor__name")
            .annotate(net=Sum("subtotal"), vat=Sum("total_vat"))
            .order_by()
        )
        for row in agg:
            bucket = buckets.setdefault(
                row["creditor_id"],
                {
                    "supplier_number": row["creditor__supplier_number"],
                    "supplier_name": row["creditor__name"],
                    "net_purchases": ZERO,
                    "vat": ZERO,
                },
            )
            bucket["net_purchases"] += row["net"] or ZERO
            bucket["vat"] += row["vat"] or ZERO

    purchases = []
    for bucket in buckets.values():
        bucket["total_purchases"] = bucket["net_purchases"] + bucket["vat"]
        purchases.append(bucket)

    if sort_by == "total_purchases":
        purchases.sort(key=lambda r: r["total_purchases"], reverse=True)
    else:
        purchases.sort(key=lambda r: r["supplier_number"])

    summary = {
        "net_purchases": sum((p["net_purchases"] for p in purchases), ZERO),
        "vat": sum((p["vat"] for p in purchases), ZERO),
        "total_purchases": sum((p["total_purchases"] for p in purchases), ZERO),
    }

    return Response(
        {
            "year": year,
            "sorted_by": sort_by,
            "purchases": purchases,
            "summary": summary,
            "supplier_count": len(purchases),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def individual_account_enquiry(request):
    supplier_id = request.query_params.get("supplier_id")
    show_archive = _bool(request.query_params.get("show_archive"))
    if not supplier_id:
        return Response({"detail": "supplier_id query param required."}, status=400)

    creditor = get_object_or_404(Creditor, pk=supplier_id)

    statistics = {
        "amount_last_paid": creditor.last_paid_amount,
        "date_last_paid": creditor.last_paid_date.isoformat() if creditor.last_paid_date else None,
        "purchases_mtd": creditor.purchases_mtd,
        "purchases_ytd": creditor.purchases_ytd,
    }

    recent = []
    for model in (GoodsReceivedNote, CreditorInvoice, CreditorCreditNote, CreditorPayment, CreditorJournal):
        for t in model.objects.filter(creditor=creditor).order_by("-transaction_date")[:20]:
            total = t.total_amount
            vat = getattr(t, "total_vat", ZERO) or ZERO
            recent.append(
                {
                    "transaction_date": t.transaction_date.isoformat(),
                    "transaction_number": t.transaction_number,
                    "transaction_type": t.transaction_type,
                    "amount_exclusive": total - vat,
                    "vat_amount": vat,
                    "amount_inclusive": total,
                }
            )
    recent.sort(key=lambda r: r["transaction_date"], reverse=True)
    recent = recent[:20]

    open_items_qs = creditor.open_items.all()
    if not show_archive:
        open_items_qs = open_items_qs.filter(is_fully_allocated=False)
    open_items = [
        {
            "transaction_date": oi.transaction_date.isoformat(),
            "transaction_number": oi.transaction_number,
            "transaction_type": oi.transaction_type,
            "amount_inclusive": oi.original_amount,
            "balance_due": oi.balance_due,
        }
        for oi in open_items_qs.order_by("-transaction_date")
    ]

    return Response(
        {
            "supplier": {
                "account_number": creditor.supplier_number,
                "name": creditor.name,
                "account_type": creditor.account_category,
                "email": creditor.email,
                "telephone": creditor.telephone,
            },
            "balances": _balances_dict(creditor),
            "statistics": statistics,
            "recent_transactions": recent,
            "open_items": open_items,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def expense_categories_list(request):
    """
    Thin list for the expense-category picker dropdowns on the Enquiries
    screens. Aliases ExpenseCategory.name -> category_name to match what the
    frontend reads (frontend/app/dashboard/admin/creditors/enquiries/
    components/ExpenseTaxAnalysis.tsx).
    """
    qs = ExpenseCategory.objects.filter(
        is_active=True, category_type__in=["BOTH", "CREDITORS"]
    ).order_by("name")
    results = [{"id": c.id, "category_name": c.name} for c in qs]
    return Response({"results": results})
