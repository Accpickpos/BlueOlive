"""
General Ledger Reports & Integration endpoints — read-only aggregation
views (Trial Balance / Income Statement / Balance Sheet) plus the two thin
HTTP wrappers around IntegrationTransferService.

Plain function-based views (not ViewSets), mirroring
apps/creditors/reports_enquiries.py's convention: each one returns a bespoke
aggregation payload, not a serialized model list — there's no single
queryset/serializer pair to hang a ViewSet off.
"""

from decimal import Decimal

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


def _build_financial_report(report_type: str, curperiod: int):
    """
    The Pastel-style report-writer traversal shared by Income Statement and
    Balance Sheet. GLRep rows for the requested type are walked in strictly
    ascending `line` order, maintaining computed[line_number] for every row
    already processed.

    THE CRITICAL PITFALL (spelled out because it's the classic bug in this
    kind of report-writer): a "D" (Detail) row's start/endcalc are GLMast
    .repline values — the chart of accounts' own numbering. A row of type
    "H"/"T"/"S" (Heading/Total/Subtotal)'s start/endcalc are GLRep.line
    values of OTHER, EARLIER report rows — the report layout's own
    numbering. These are two independent 1-9999 namespaces that only
    coincidentally share the same validator range. Summing GLMast.repline
    for a Total row (or vice versa) silently produces a nonsense number
    that still looks plausible — always branch on fieldtype before deciding
    which namespace start/endcalc refers to.
    """
    rows = list(GLRep.objects.filter(type=report_type).order_by("line"))
    computed = {}
    output = []

    for rep_row in rows:
        if rep_row.fieldtype == "D":
            accounts = GLMast.objects.filter(
                repline__gte=rep_row.start, repline__lte=rep_row.endcalc
            )
            if report_type == "I":
                amount = sum(
                    _income_flow(a, curperiod) for a in accounts
                ) or Decimal("0.00")
            else:
                amount = sum(
                    _account_balance(a, curperiod) for a in accounts
                ) or Decimal("0.00")
        elif rep_row.fieldtype in ("H", "T", "S"):
            amount = sum(
                computed.get(line, Decimal("0.00"))
                for line in range(rep_row.start, rep_row.endcalc + 1)
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

    return output, computed


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def income_statement(request):
    param = GLParam.objects.first()
    curperiod = _int_or_none(request.query_params.get("as_of_period")) or (
        param.curperiod if param else 12
    )

    output, computed = _build_financial_report("I", curperiod)
    net_result = None
    total_rows = [r for r in output if r["fieldtype"] == "T"]
    if total_rows:
        net_result = total_rows[-1]["amount"]

    return Response(
        {
            "report_title": "Income Statement",
            "as_of_period": curperiod,
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

    output, computed = _build_financial_report("B", curperiod)

    return Response(
        {
            "report_title": "Balance Sheet",
            "as_of_period": curperiod,
            "currentyr": param.currentyr if param else None,
            "lines": output,
            # A real Assets == Liabilities+Equity tie-out requires knowing
            # which two Total rows represent each side of the format, which
            # is a convention of the seeded GLRep data, not something this
            # traversal can infer generically. Left as a TODO until
            # Maintenance data for GLRep (type="B") is seeded and that
            # convention is confirmed.
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
