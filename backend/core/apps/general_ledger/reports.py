"""
General Ledger Reports & Integration endpoints — read-only aggregation
views (Trial Balance / Income Statement / Balance Sheet) plus the two thin
HTTP wrappers around IntegrationTransferService.

Plain function-based views (not ViewSets), mirroring
apps/creditors/reports_enquiries.py's convention: each one returns a bespoke
aggregation payload, not a serialized model list — there's no single
queryset/serializer pair to hang a ViewSet off.
"""

import csv
from decimal import Decimal

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .exceptions import GLIntegrationException
from .integration import IntegrationTransferService
from .models import GLMast, GLParam, GLRep
from .permissions import CanRunGLIntegration


def _int_or_none(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _account_balance(account: GLMast, curperiod: int) -> Decimal:
    """balbfwd + sum(period1..curperiod) — a real point-in-time balance,
    used for both Trial Balance and Balance Sheet Detail rows."""
    total = account.balbfwd
    for p in range(1, curperiod + 1):
        total += getattr(account, f"period{p}")
    return total


def _income_flow(account: GLMast, curperiod: int) -> Decimal:
    """sum(period1..curperiod) only, no balbfwd — Income Statement accounts
    are period flows, not carried balances (their balbfwd is expected to be
    structurally 0 outside the moment-of-transition right after Year End)."""
    total = Decimal("0.00")
    for p in range(1, curperiod + 1):
        total += getattr(account, f"period{p}")
    return total


def _rows_to_csv(filename: str, fieldnames, rows) -> HttpResponse:
    """Shared CSV export for the three report endpoints below (the manual's
    'Export to Spreadsheet' options on Trial Balance/Income Statement/
    Balance Sheet, and the dedicated Utilities > Export Trial Balance to
    Spreadsheet). Plain csv.DictWriter over the same row dicts the JSON
    response already builds — no separate formatting path to keep in sync."""
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.DictWriter(response, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return response


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def trial_balance(request):
    """
    Trial Balance: every GLMast account's balance as of the given period
    (defaults to GLParam.curperiod), split into Debit/Credit display
    columns. period{N} is stored "same-side-positive" (positive = that
    account's own drorcr side — see GLPostingService._apply_period_balance),
    so the split is:
      drorcr == "D": balance >= 0 -> Debit column; balance < 0 -> Credit column (abs)
      drorcr == "C": mirror image
    The two columns must always tie out exactly — it's the same
    double-entry data viewed two ways — surfaced as is_balanced for a
    visible sanity check.
    """
    param = GLParam.objects.first()
    curperiod = _int_or_none(request.query_params.get("as_of_period")) or (
        param.curperiod if param else 12
    )

    rows = []
    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")
    for account in GLMast.objects.all().order_by("accno"):
        balance = _account_balance(account, curperiod)
        if account.drorcr == "D":
            debit = balance if balance >= 0 else Decimal("0.00")
            credit = -balance if balance < 0 else Decimal("0.00")
        else:
            credit = balance if balance >= 0 else Decimal("0.00")
            debit = -balance if balance < 0 else Decimal("0.00")

        total_debit += debit
        total_credit += credit
        rows.append(
            {
                "accno": account.accno,
                "name": account.name,
                "drorcr": account.drorcr,
                "debit": float(debit),
                "credit": float(credit),
            }
        )

    if request.query_params.get("format") == "csv":
        rows.append({"accno": "", "name": "TOTAL", "drorcr": "", "debit": float(total_debit), "credit": float(total_credit)})
        return _rows_to_csv(
            f"trial-balance-period{curperiod}.csv",
            ["accno", "name", "drorcr", "debit", "credit"],
            rows,
        )

    return Response(
        {
            "report_title": "Trial Balance",
            "as_of_period": curperiod,
            "currentyr": param.currentyr if param else None,
            "accounts": rows,
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "is_balanced": total_debit == total_credit,
        }
    )


#: Income Statement display modes documented in the manual (7. General
#: Ledger, Enquiries > 5. Income Statement): Current Period+YTD, Current
#: Period+Last Year, Current Period+Budget, Budgeted Values-12 Months,
#: Budget Variance, Actual Values-12 Months. "current" (this module's
#: original single-column behavior) is kept as the default for backward
#: compatibility with existing callers.
INCOME_STATEMENT_MODES = {
    "current",
    "current_ytd",
    "current_last_year",
    "current_budget",
    "budget_12",
    "variance",
    "actual_12",
}


def _account_columns(account: GLMast, curperiod: int, mode: str) -> dict:
    """
    The named numeric column(s) one GLMast account contributes under a given
    Income Statement mode. Every mode returns a dict (even "current", which
    has always returned a single "amount" key) so _build_income_statement
    can sum columns generically regardless of mode.
    """

    def flow(prefix, n):
        return getattr(account, f"{prefix}{n}")

    def ytd(prefix, upto):
        return sum((flow(prefix, p) for p in range(1, upto + 1)), Decimal("0.00"))

    if mode == "current":
        return {"amount": _income_flow(account, curperiod)}
    if mode == "current_ytd":
        return {"current": flow("period", curperiod), "ytd": ytd("period", curperiod)}
    if mode == "current_last_year":
        return {
            "current": flow("period", curperiod),
            "last_year": flow("lastyear", curperiod),
            "ytd": ytd("period", curperiod),
            "last_year_ytd": ytd("lastyear", curperiod),
        }
    if mode == "current_budget":
        return {
            "current": flow("period", curperiod),
            "budget": flow("budget", curperiod),
            "ytd": ytd("period", curperiod),
            "ytd_budget": ytd("budget", curperiod),
        }
    if mode == "budget_12":
        return {f"month{p}": flow("budget", p) for p in range(1, 13)}
    if mode == "variance":
        return {
            "current_variance": flow("period", curperiod) - flow("budget", curperiod),
            "ytd_variance": ytd("period", curperiod) - ytd("budget", curperiod),
        }
    if mode == "actual_12":
        return {f"month{p}": flow("period", p) for p in range(1, 13)}
    raise ValueError(f"Unknown income statement mode: {mode!r}")


def _build_income_statement(curperiod: int, mode: str):
    """
    Same GLRep report-writer traversal as before (see the namespace-pitfall
    note that used to live on _build_financial_report, still true here: a
    "D" row's start/endcalc are GLMast.repline values; "H"/"T"/"S" rows'
    start/endcalc are GLRep.line values of earlier rows — two independent
    1-9999 namespaces), generalized to sum a dict of named columns per line
    instead of a single amount, so every INCOME_STATEMENT_MODES layout can
    share one traversal.
    """
    rows = list(GLRep.objects.filter(type="I").order_by("line"))
    computed = {}
    output = []

    for rep_row in rows:
        if rep_row.fieldtype == "D":
            accounts = GLMast.objects.filter(
                repline__gte=rep_row.start, repline__lte=rep_row.endcalc
            )
            cols = {}
            for account in accounts:
                for key, val in _account_columns(account, curperiod, mode).items():
                    cols[key] = cols.get(key, Decimal("0.00")) + val
        elif rep_row.fieldtype in ("H", "T", "S"):
            cols = {}
            for line in range(rep_row.start, rep_row.endcalc + 1):
                for key, val in computed.get(line, {}).items():
                    cols[key] = cols.get(key, Decimal("0.00")) + val
        else:
            cols = {}

        computed[rep_row.line] = cols
        output.append(
            {
                "line": rep_row.line,
                "fieldtype": rep_row.fieldtype,
                "name": rep_row.name,
                "printdet": rep_row.printdet,
                **{key: float(val) for key, val in cols.items()},
            }
        )

    return output


def _build_balance_sheet(curperiod: int):
    """Same traversal as _build_income_statement, single "amount" column
    only — the manual doesn't document multiple Balance Sheet layouts the
    way it does for Income Statement."""
    rows = list(GLRep.objects.filter(type="B").order_by("line"))
    computed = {}
    output = []

    for rep_row in rows:
        if rep_row.fieldtype == "D":
            accounts = GLMast.objects.filter(
                repline__gte=rep_row.start, repline__lte=rep_row.endcalc
            )
            amount = sum(
                (_account_balance(a, curperiod) for a in accounts), Decimal("0.00")
            )
        elif rep_row.fieldtype in ("H", "T", "S"):
            amount = sum(
                (computed.get(line, Decimal("0.00")) for line in range(rep_row.start, rep_row.endcalc + 1)),
                Decimal("0.00"),
            )
        else:
            amount = Decimal("0.00")

        computed[rep_row.line] = amount
        output.append(
            {
                "line": rep_row.line,
                "fieldtype": rep_row.fieldtype,
                "name": rep_row.name,
                "printdet": rep_row.printdet,
                "amount": float(amount),
            }
        )

    return output


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def income_statement(request):
    param = GLParam.objects.first()
    curperiod = _int_or_none(request.query_params.get("as_of_period")) or (
        param.curperiod if param else 12
    )
    mode = request.query_params.get("mode", "current")
    if mode not in INCOME_STATEMENT_MODES:
        return Response(
            {"error": f"mode must be one of {sorted(INCOME_STATEMENT_MODES)}"},
            status=400,
        )

    output = _build_income_statement(curperiod, mode)
    net_result = None
    total_rows = [r for r in output if r["fieldtype"] == "T"]
    if total_rows and mode == "current":
        # Only "current" mode has a single "the net result" figure (its one
        # "amount" column) — existing callers depend on this being a plain
        # number. Other modes have several columns on their last Total row
        # (current/ytd/budget/etc, or 12 discrete months) with no single
        # figure that summarizes them; callers wanting those read them from
        # "lines" (the last fieldtype="T" row) instead.
        net_result = total_rows[-1]["amount"]

    if request.query_params.get("format") == "csv":
        columns = sorted({k for r in output for k in r if k not in ("line", "fieldtype", "name", "printdet")})
        return _rows_to_csv(
            f"income-statement-{mode}-period{curperiod}.csv",
            ["line", "fieldtype", "name", *columns],
            output,
        )

    return Response(
        {
            "report_title": "Income Statement",
            "as_of_period": curperiod,
            "mode": mode,
            "currentyr": param.currentyr if param else None,
            "lines": output,
            "net_result": net_result,
            "is_seeded": bool(output),
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def balance_sheet(request):
    param = GLParam.objects.first()
    curperiod = _int_or_none(request.query_params.get("as_of_period")) or (
        param.curperiod if param else 12
    )

    output = _build_balance_sheet(curperiod)

    # Assets == Liabilities+Equity tie-out, derived from the accounting
    # identity rather than from guessing which two GLRep Total rows
    # represent each side of the format (GLRep has no such field - just a
    # free-text `name` - so that would have been guesswork). Double-entry
    # guarantees sum(all Debit-normal balances/flows) ==
    # sum(all Credit-normal balances/flows) across the WHOLE ledger; split
    # by account type that rearranges to:
    #   Total Assets (B, drorcr=D) - Total Liab+Equity (B, drorcr=C)
    #     == Net Income (I, drorcr=C flows - I, drorcr=D flows)
    # i.e. Assets == Liab+Equity + Net Income. The "+ Net Income" term is
    # only zero right after Year End closes P&L into
    # GLParam.retained_earnings_accno - mid-period it's expected to be
    # nonzero, which is why this checks the full identity rather than a bare
    # Assets == Liab+Equity comparison.
    b_accounts = GLMast.objects.filter(type="B")
    total_assets = sum(
        (_account_balance(a, curperiod) for a in b_accounts if a.drorcr == "D"),
        Decimal("0.00"),
    )
    total_liab_equity = sum(
        (_account_balance(a, curperiod) for a in b_accounts if a.drorcr == "C"),
        Decimal("0.00"),
    )
    i_accounts = GLMast.objects.filter(type="I")
    net_income = sum(
        (_income_flow(a, curperiod) for a in i_accounts if a.drorcr == "C"),
        Decimal("0.00"),
    ) - sum(
        (_income_flow(a, curperiod) for a in i_accounts if a.drorcr == "D"),
        Decimal("0.00"),
    )

    if request.query_params.get("format") == "csv":
        return _rows_to_csv(
            f"balance-sheet-period{curperiod}.csv",
            ["line", "fieldtype", "name", "amount"],
            output,
        )

    return Response(
        {
            "report_title": "Balance Sheet",
            "as_of_period": curperiod,
            "currentyr": param.currentyr if param else None,
            "lines": output,
            "total_assets": float(total_assets),
            "total_liabilities_and_equity": float(total_liab_equity),
            "net_income": float(net_income),
            "is_balanced": total_assets == total_liab_equity + net_income,
            "is_seeded": bool(output),
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, CanRunGLIntegration])
def integration_transfer(request):
    """
    Run the Integration Transfer pipeline for one source app, or all of
    them. Body: {"source": "debtors"|"creditors"|"stock_control"|
    "cash_book"|"all", "date_from": "YYYY-MM-DD"?, "date_to": "YYYY-MM-DD"?}
    """
    source = request.data.get("source", "all")
    date_from = request.data.get("date_from")
    date_to = request.data.get("date_to")

    try:
        if source == "all":
            result = IntegrationTransferService.transfer_all(
                date_from=date_from, date_to=date_to
            )
        elif source == "debtors":
            result = {"debtors": IntegrationTransferService.transfer_debtors(
                date_from=date_from, date_to=date_to
            )}
        elif source == "creditors":
            result = {"creditors": IntegrationTransferService.transfer_creditors(
                date_from=date_from, date_to=date_to
            )}
        elif source == "stock_control":
            result = {"stock_control": IntegrationTransferService.transfer_stock_control(
                date_from=date_from, date_to=date_to
            )}
        elif source == "cash_book":
            result = {"cash_book": IntegrationTransferService.transfer_cash_book(
                date_from=date_from, date_to=date_to
            )}
        else:
            return Response(
                {
                    "error": "source must be one of: debtors, creditors, "
                    "stock_control, cash_book, all"
                },
                status=400,
            )
    except GLIntegrationException as e:
        return Response({"error": str(e)}, status=400)

    return Response({"report_title": "Integration Transfer", "results": result})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def integration_outstanding(request):
    """Enquiry: posted/final-state source records not yet transferred into GL."""
    return Response(
        {
            "report_title": "Outstanding Integration Batches",
            "outstanding": IntegrationTransferService.outstanding(),
        }
    )
