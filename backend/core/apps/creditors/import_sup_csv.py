import csv
import io
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.db import connections, transaction
from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from tenancy.models import Shop, Tenant
from tenancy.tenant_context import clear_current, set_current_shop, set_current_tenant
from tenancy.utils import register_tenant_connection

from .models import (
    RFC,
    Creditor,
    CreditorInvoice,
    CreditorInvoiceLineItem,
    CreditorOpenItem,
    ExpenseCategoryMonthlyBalance,
    OpenItemAudit,
    RFCLineItem,
    SupplierLedgerEntry,
    SupplierPaymentOrder,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Column maps: CSV header (uppercase) → field name / semantic tag
# ============================================================================

SUPMAST_MAP = {
    "SUPNO": "supplier_number",
    "SUPNAME": "name",
    "SUPCONT": "contact_person",
    "SUPTEL": "telephone",
    "SUPFAX": "fax",
    "EMAIL": "email",
    "SUPADD1": "physical_address_line1",
    "SUPADD2": "physical_address_line2",
    "SUPADD3": "physical_address_line3",
    "SUPPADD1": "postal_address_line1",
    "SUPPADD2": "postal_address_line2",
    "SUPPADD3": "postal_address_line3",
    "SUPOURACC": "our_account_number",
    "SUPTERMS": "payment_terms_days",
    "SUPDISC": "prompt_payment_discount_percent",
    "SUPBALBFWD": "balance_brought_forward",
    "SUPCRNT": "balance_current",
    "SUP30": "balance_30_days",
    "SUP60": "balance_60_days",
    "SUP90": "balance_90_days",
    "SUP120": "balance_120_days",
    "SUP150": "balance_150_days",
    "SUPPMT": "last_paid_amount",
    "SUPPMTDATE": "last_paid_date",
    "SUPURCHMTD": "purchases_mtd",
    "SUPURCHYTD": "purchases_ytd",
    "BANK": "bank_name",
    "BANKCODE": "branch_code",
    "BANKACC": "account_number",
    "UPDSTKSP": "update_selling_price_on_receipt",
    "ACCTYPE": "account_category",
}

SUPTRAN_MAP = {
    "SUPNO": "supno",  # resolved to Creditor FK
    "STRANO": "transaction_number",
    "STDATE": "transaction_date",
    "SDUEDATE": "due_date",
    "STYPE": "transaction_type",
    "STSUB": "subtotal",
    "STGST": "vat_amount",
    "STTOT": "total_amount",
    "STREF": "reference",
    "GRNNO": "grn_number",
    "STATION": "station",
    "USER": "created_by_user",
}

SUPOPEN_MAP = {
    "SUPNO": "supno",
    "TRANO": "transaction_number",
    "TYPE": "transaction_type",
    "DATE": "transaction_date",
    "TOTAL": "original_amount",
    "BALANCEDUE": "balance_due",
    "AGEFLAG": "ageing_flag",
}

SUPOAUD_MAP = {
    "SUPNO": "supno",
    "TRANO": "transaction_number",
    "TYPE": "transaction_type",
    "THISTYPE": "this_transaction_type",
    "THISTRAN": "this_transaction_number",
    "DATE": "transaction_date",
    "AMOUNT": "amount",
}

SUPCRMAS_MAP = {
    "RFCNO": "rfc_number",
    "SUPNO": "supno",
    "DATESENT": "date_sent",
    "DATERETN": "date_returned",
    "STATUS": "status",
}

SUPCRTRN_MAP = {
    "RFCNO": "rfcno",  # resolved to RFC FK
    "TYPE": "original_transaction_type",
    "CODE": "stock_code",  # resolved to StockItem FK
    "DATE": "rfc_line_date",
    "TIME": "original_transaction_time",
    "QTY": "quantity_stock",
    "VAL": "line_value_exclusive",
    "QTYRFC": "quantity_returned",
    "QTYCRED": "quantity_credited",
    "COMMENT": "reason",
    "PURCHDATE": "original_transaction_date",
    "SUPREFNO": "supplier_reference_number",
}

SUPEXP_MAP = {
    "EXPCAT": "expcat",  # resolved to ExpenseCategory FK
    "EXPCATNAME": "category_name",  # informational only
    "EXPMTD": "expense_mtd",
    "EXPINVAT": "input_vat_mtd",
    "EXP1": "exp_month_1",
    "EXP2": "exp_month_2",
    "EXP3": "exp_month_3",
    "EXP4": "exp_month_4",
    "EXP5": "exp_month_5",
    "EXP6": "exp_month_6",
    "EXP7": "exp_month_7",
    "EXP8": "exp_month_8",
    "EXP9": "exp_month_9",
    "EXP10": "exp_month_10",
    "EXP11": "exp_month_11",
    "EXP12": "exp_month_12",
}

SUPEXPT_MAP = {
    "EXPCAT": "expcat",
    "DATE": "transaction_date",
    "TRANO": "supplier_invoice_number",
    "SUPNO": "supno",
    "VALUE": "subtotal",
    "INVAT": "total_vat",
    "TOTAL": "total_amount",
    "SOURCE": "station_no_area",
    "GRNNO": "grn_number",
    "TAXIND": "tax_indicator",
}

SUPPO_MAP = {
    "DATE": "payment_date",
    "AMOUNT": "amount",
    "DETAIL1": "detail_line1",
    "DETAIL2": "detail_line2",
    "DETAIL3": "detail_line3",
}

ALL_MAPS = {
    "supmast": SUPMAST_MAP,
    "suptran": SUPTRAN_MAP,
    "supopen": SUPOPEN_MAP,
    "supoaud": SUPOAUD_MAP,
    "supcrmas": SUPCRMAS_MAP,
    "supcrtrn": SUPCRTRN_MAP,
    "supexp": SUPEXP_MAP,
    "supexpt": SUPEXPT_MAP,
    "suppo": SUPPO_MAP,
}

# ============================================================================
# Value parsers
# ============================================================================

_DECIMAL_FIELDS = {
    "prompt_payment_discount_percent",
    "balance_brought_forward",
    "balance_current",
    "balance_30_days",
    "balance_60_days",
    "balance_90_days",
    "balance_120_days",
    "balance_150_days",
    "last_paid_amount",
    "purchases_mtd",
    "purchases_ytd",
    "subtotal",
    "vat_amount",
    "total_amount",
    "original_amount",
    "balance_due",
    "amount",
    "line_value_exclusive",
    "quantity_returned",
    "quantity_credited",
    "quantity_stock",
    "expense_mtd",
    "input_vat_mtd",
    "exp_month_1",
    "exp_month_2",
    "exp_month_3",
    "exp_month_4",
    "exp_month_5",
    "exp_month_6",
    "exp_month_7",
    "exp_month_8",
    "exp_month_9",
    "exp_month_10",
    "exp_month_11",
    "exp_month_12",
    "total_vat",
}
_INTEGER_FIELDS = {
    "payment_terms_days",
    "grn_number",
    "this_transaction_number",
    "tax_indicator",
}
_DATE_FIELDS = {
    "last_paid_date",
    "transaction_date",
    "due_date",
    "date_sent",
    "date_returned",
    "rfc_line_date",
    "original_transaction_date",
    "payment_date",
}
_TIME_FIELDS = {"original_transaction_time"}
_BOOL_FIELDS = {"update_selling_price_on_receipt"}


def _to_decimal(v):
    try:
        return Decimal(str(v).replace(",", "").strip())
    except (InvalidOperation, ValueError):
        return None


def _to_int(v):
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return None


def _to_date(v):
    v = str(v).strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(v, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


def _to_time(v):
    v = str(v).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(v, fmt).time()
        except (ValueError, TypeError):
            continue
    return None


def _to_bool(v):
    return str(v).strip().upper() in ("Y", "YES", "TRUE", "1")


def _parse_value(raw, field_name, skip_empty=True):
    """Convert a raw CSV string to the appropriate Python type."""
    if raw is None:
        return None
    v = str(raw).strip()
    if v == "" or v.upper() == "N/A":
        return None if skip_empty else _empty_default(field_name)

    if field_name in _DECIMAL_FIELDS:
        return _to_decimal(v)
    if field_name in _INTEGER_FIELDS:
        return _to_int(v)
    if field_name in _DATE_FIELDS:
        return _to_date(v)
    if field_name in _TIME_FIELDS:
        return _to_time(v)
    if field_name in _BOOL_FIELDS:
        return _to_bool(v)

    # Special cases
    if field_name == "account_category":
        # Map legacy single-char or blank to model choices
        mapping = {"B": "BBF", "O": "OI", "BBF": "BBF", "OI": "OI", "": ""}
        return mapping.get(v.upper(), "BBF")

    if field_name == "status" and v.upper() == "A":
        # Legacy RFC status 'A' (Active) → 'PENDING'
        return "PENDING"

    return v


def _empty_default(field_name):
    if field_name in _DECIMAL_FIELDS:
        return Decimal("0")
    if field_name in _INTEGER_FIELDS:
        return 0
    if field_name in _DATE_FIELDS:
        return None
    if field_name in _BOOL_FIELDS:
        return False
    return ""


# ============================================================================
# Shared helpers
# ============================================================================


def _detect_delimiter(text):
    first = text.split("\n")[0]
    return ";" if ";" in first and first.count(";") > first.count(",") else ","


def _read_csv(file_obj):
    """Read file → (headers_uppercase, rows, delimiter, error_str)."""
    try:
        file_obj.seek(0)
        text = file_obj.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return None, None, None, str(e)
    delim = _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delim)
    try:
        headers = [h.strip().upper() for h in next(reader)]
    except StopIteration:
        return None, None, None, "CSV file is empty"
    return headers, list(reader), delim, None


def _resolve_tenant_shop(request):
    tid = request.data.get("tenant_id")
    sid = request.data.get("shop_id")
    if not tid or not sid:
        return (
            None,
            None,
            Response({"error": "tenant_id and shop_id are required"}, status=400),
        )

    # First, get the shop to find its tenant (allows importing to any shop regardless of tenant_id param)
    try:
        shop = Shop.objects.select_related("tenant").get(id=sid, is_active=True)
    except Shop.DoesNotExist:
        return None, None, Response({"error": f"Shop {sid} not found"}, status=404)

    # Use the shop's actual tenant - this ensures we import to the correct tenant
    # regardless of what tenant_id was sent in the request
    tenant = shop.tenant

    # Verify the tenant is active
    if not tenant.is_active:
        return (
            None,
            None,
            Response({"error": f"Tenant for shop {sid} is not active"}, status=400),
        )

    return tenant, shop, None


def _set_schema(tenant, shop):
    register_tenant_connection(tenant)
    db_alias = tenant.db_alias
    set_current_tenant(tenant)
    set_current_shop(shop.schema_name)
    with connections[db_alias].cursor() as cursor:
        cursor.execute(f'SET search_path TO "{shop.schema_name}", public')
    return db_alias


def _parse_bool_param(value):
    if isinstance(value, bool):
        return value
    return str(value).lower() in ("true", "1", "yes")


def _parse_row(row, header_idx, col_map, skip_empty=True):
    """Map a raw CSV row → {model_field: typed_value}."""
    record = {}
    for csv_col, field_name in col_map.items():
        idx = header_idx.get(csv_col)
        if idx is not None and idx < len(row):
            val = _parse_value(row[idx], field_name, skip_empty)
            if val is not None:
                record[field_name] = val
    return record


def _build_summary(created, updated, skipped, errors, tenant, shop, total):
    return {
        "success": True,
        "tenant": tenant.name,
        "shop": shop.name,
        "schema": shop.schema_name,
        "total_rows": total,
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "message": (
            f"Import complete: {created} created, {updated} updated, "
            f'{skipped} skipped into "{shop.schema_name}"'
        ),
    }


def _creditor_map(db_alias):
    """Return {supplier_number: creditor_pk} lookup."""
    return dict(Creditor.objects.using(db_alias).values_list("supplier_number", "pk"))


def _add_error(errors, row_num, msg):
    errors.append(f"Row {row_num}: {msg}")
    return len(errors) >= 50


# ============================================================================
# Utility endpoints
# ============================================================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_tenants_and_shops(request):
    """GET /api/v1/creditors/import/tenants/"""
    tenants = Tenant.objects.filter(is_active=True).order_by("name")
    return Response(
        [
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "shops": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "code": s.code,
                        "schema_name": s.schema_name,
                    }
                    for s in Shop.objects.filter(tenant=t, is_active=True).order_by(
                        "name"
                    )
                ],
            }
            for t in tenants
        ]
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def analyze_csv(request):
    """
    POST /api/v1/creditors/import/analyze/
    Upload a CSV, get back headers, sample rows, and suggested field mappings.
    Pass ?table=supmast|suptran|supopen|... for targeted suggestions.
    """
    if "file" not in request.FILES:
        return Response({"error": "No file provided"}, status=400)

    file_obj = request.FILES["file"]
    headers, rows, delim, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    table_hint = (
        request.data.get("table", "")
        or file_obj.name.lower().replace(".csv", "").replace(".dbf", "")
    ).lower()

    col_map = ALL_MAPS.get(table_hint, SUPMAST_MAP)
    suggested = {h: col_map[h] for h in headers if h in col_map}

    return Response(
        {
            "headers": headers,
            "total_rows": len(rows),
            "sample_rows": rows[:5],
            "suggested_mappings": suggested,
            "available_model_fields": sorted(set(col_map.values())),
            "delimiter": delim,
            "detected_table": table_hint,
        }
    )


# ============================================================================
# supmast → Creditor
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_supmast(request):
    """
    POST /api/v1/creditors/import/supmast/
    Import supmast.csv → Creditor

    Body (multipart/form-data):
        file        : CSV
        tenant_id   : int
        shop_id     : int
        mode        : create_or_update* | create_only | update_only
        skip_empty  : true* | false
        import_year : int (default: current year — used to infer which year
                      the balance figures belong to)
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    mode = request.data.get("mode", "create_or_update")
    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)
    created = updated = skipped = 0
    errors = []

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPMAST_MAP, skip_empty)
                    sup_no = record.get("supplier_number")
                    if not sup_no:
                        if _add_error(errors, row_num, "Missing SUPNO — skipped"):
                            break
                        skipped += 1
                        continue

                    # Editable=False fields need to bypass model validation
                    # Use update_or_create with direct field assignment
                    balance_fields = {
                        k: record.pop(k, Decimal("0"))
                        for k in (
                            "balance_brought_forward",
                            "balance_current",
                            "balance_30_days",
                            "balance_60_days",
                            "balance_90_days",
                            "balance_120_days",
                            "balance_150_days",
                            "last_paid_amount",
                            "purchases_mtd",
                            "purchases_ytd",
                        )
                    }
                    last_paid_date = record.pop("last_paid_date", None)

                    # Separate lookup key
                    defaults = {
                        k: v for k, v in record.items() if k != "supplier_number"
                    }
                    defaults["is_active"] = True

                    if mode == "create_only":
                        if (
                            Creditor.objects.using(db_alias)
                            .filter(supplier_number=sup_no)
                            .exists()
                        ):
                            skipped += 1
                            continue
                        obj = Creditor.objects.using(db_alias).create(
                            supplier_number=sup_no, **defaults
                        )
                        created += 1
                    elif mode == "update_only":
                        n = (
                            Creditor.objects.using(db_alias)
                            .filter(supplier_number=sup_no)
                            .update(**defaults)
                        )
                        updated += n or 0
                        skipped += 0 if n else 1
                        obj = (
                            Creditor.objects.using(db_alias)
                            .filter(supplier_number=sup_no)
                            .first()
                        )
                    else:
                        obj, was_created = Creditor.objects.using(
                            db_alias
                        ).update_or_create(supplier_number=sup_no, defaults=defaults)
                        created += was_created
                        updated += not was_created

                    # Write balance fields bypassing editable=False
                    if obj:
                        for field, value in balance_fields.items():
                            setattr(obj, field, value or Decimal("0"))
                        if last_paid_date:
                            obj.last_paid_date = last_paid_date
                        obj.total_outstanding_balance = sum(
                            balance_fields.get(f, Decimal("0"))
                            for f in (
                                "balance_current",
                                "balance_30_days",
                                "balance_60_days",
                                "balance_90_days",
                                "balance_120_days",
                                "balance_150_days",
                            )
                        )
                        Creditor.objects.using(db_alias).filter(pk=obj.pk).update(
                            **{
                                k: getattr(obj, k)
                                for k in list(balance_fields.keys())
                                + ["last_paid_date", "total_outstanding_balance"]
                            }
                        )

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, updated, skipped, errors, tenant, shop, len(rows))
    )


# ============================================================================
# suptran → SupplierLedgerEntry
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_suptran(request):
    """
    POST /api/v1/creditors/import/suptran/
    Import suptran.csv → SupplierLedgerEntry (raw ledger).
    Import supmast BEFORE this.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    mode = request.data.get("mode", "create_or_update")
    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)
    cred_map = _creditor_map(db_alias)

    created = updated = skipped = 0
    errors = []

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPTRAN_MAP, skip_empty)

                    raw_supno = record.pop("supno", None)
                    tran_no = record.get("transaction_number")
                    if not raw_supno or not tran_no:
                        skipped += 1
                        continue

                    cred_pk = cred_map.get(str(raw_supno).strip())
                    if not cred_pk:
                        if _add_error(
                            errors,
                            row_num,
                            f"SUPNO {raw_supno} not in Creditor table — skipped",
                        ):
                            break
                        skipped += 1
                        continue

                    defaults = {
                        k: v for k, v in record.items() if k != "transaction_number"
                    }
                    defaults["creditor_id"] = cred_pk

                    if mode == "create_only":
                        if (
                            SupplierLedgerEntry.objects.using(db_alias)
                            .filter(creditor_id=cred_pk, transaction_number=tran_no)
                            .exists()
                        ):
                            skipped += 1
                            continue
                        SupplierLedgerEntry.objects.using(db_alias).create(
                            creditor_id=cred_pk, transaction_number=tran_no, **defaults
                        )
                        created += 1
                    elif mode == "update_only":
                        n = (
                            SupplierLedgerEntry.objects.using(db_alias)
                            .filter(creditor_id=cred_pk, transaction_number=tran_no)
                            .update(**defaults)
                        )
                        updated += n or 0
                        skipped += 0 if n else 1
                    else:
                        _, was_created = SupplierLedgerEntry.objects.using(
                            db_alias
                        ).update_or_create(
                            creditor_id=cred_pk,
                            transaction_number=tran_no,
                            defaults=defaults,
                        )
                        created += was_created
                        updated += not was_created

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, updated, skipped, errors, tenant, shop, len(rows))
    )


# ============================================================================
# supopen → CreditorOpenItem
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_supopen(request):
    """
    POST /api/v1/creditors/import/supopen/
    Import supopen.csv → CreditorOpenItem (is_legacy=True — skips FK validation).
    Import supmast BEFORE this.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    mode = request.data.get("mode", "create_or_update")
    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)
    cred_map = _creditor_map(db_alias)

    created = updated = skipped = 0
    errors = []

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPOPEN_MAP, skip_empty)

                    raw_supno = record.pop("supno", None)
                    tran_no = record.get("transaction_number")
                    tran_type = record.get("transaction_type", "")
                    if not raw_supno or not tran_no:
                        skipped += 1
                        continue

                    cred_pk = cred_map.get(str(raw_supno).strip())
                    if not cred_pk:
                        if _add_error(
                            errors, row_num, f"SUPNO {raw_supno} not found — skipped"
                        ):
                            break
                        skipped += 1
                        continue

                    # Ensure required fields have fallback values
                    record.setdefault("original_amount", Decimal("0"))
                    record.setdefault("balance_due", Decimal("0"))
                    record.setdefault("transaction_date", date.today())

                    defaults = {
                        k: v
                        for k, v in record.items()
                        if k not in ("transaction_number", "transaction_type")
                    }
                    defaults["creditor_id"] = cred_pk
                    defaults["is_legacy"] = True

                    if mode == "create_only":
                        if (
                            CreditorOpenItem.objects.using(db_alias)
                            .filter(
                                creditor_id=cred_pk,
                                transaction_number=tran_no,
                                transaction_type=tran_type,
                            )
                            .exists()
                        ):
                            skipped += 1
                            continue
                        CreditorOpenItem.objects.using(db_alias).create(
                            creditor_id=cred_pk,
                            transaction_number=tran_no,
                            transaction_type=tran_type,
                            **defaults,
                        )
                        created += 1
                    elif mode == "update_only":
                        n = (
                            CreditorOpenItem.objects.using(db_alias)
                            .filter(
                                creditor_id=cred_pk,
                                transaction_number=tran_no,
                                transaction_type=tran_type,
                            )
                            .update(**defaults)
                        )
                        updated += n or 0
                        skipped += 0 if n else 1
                    else:
                        _, was_created = CreditorOpenItem.objects.using(
                            db_alias
                        ).update_or_create(
                            creditor_id=cred_pk,
                            transaction_number=tran_no,
                            transaction_type=tran_type,
                            defaults=defaults,
                        )
                        created += was_created
                        updated += not was_created

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, updated, skipped, errors, tenant, shop, len(rows))
    )


# ============================================================================
# supoaud → OpenItemAudit  (insert-only — audit trail must never be updated)
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_supoaud(request):
    """
    POST /api/v1/creditors/import/supoaud/
    Import supoaud.csv → OpenItemAudit.
    Insert-only — audit records are never overwritten.
    Import supmast BEFORE this.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)
    cred_map = _creditor_map(db_alias)

    created = skipped = 0
    errors = []

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPOAUD_MAP, skip_empty)

                    raw_supno = record.pop("supno", None)
                    if not raw_supno:
                        skipped += 1
                        continue

                    cred_pk = cred_map.get(str(raw_supno).strip())
                    if not cred_pk:
                        if _add_error(
                            errors, row_num, f"SUPNO {raw_supno} not found — skipped"
                        ):
                            break
                        skipped += 1
                        continue

                    record.setdefault("transaction_date", date.today())
                    record.setdefault("amount", Decimal("0"))
                    record.setdefault("this_transaction_number", 0)

                    OpenItemAudit.objects.using(db_alias).create(
                        creditor_id=cred_pk, **record
                    )
                    created += 1

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, 0, skipped, errors, tenant, shop, len(rows))
    )


# ============================================================================
# supcrmas → RFC
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_supcrmas(request):
    """
    POST /api/v1/creditors/import/supcrmas/
    Import supcrmas.csv → RFC.
    Legacy STATUS 'A' is automatically mapped to 'PENDING'.
    Import supmast BEFORE this.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    mode = request.data.get("mode", "create_or_update")
    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)
    cred_map = _creditor_map(db_alias)

    created = updated = skipped = 0
    errors = []

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPCRMAS_MAP, skip_empty)

                    raw_supno = record.pop("supno", None)
                    rfc_number = record.get("rfc_number")
                    if not raw_supno or not rfc_number:
                        skipped += 1
                        continue

                    cred_pk = cred_map.get(str(raw_supno).strip())
                    if not cred_pk:
                        if _add_error(
                            errors, row_num, f"SUPNO {raw_supno} not found — skipped"
                        ):
                            break
                        skipped += 1
                        continue

                    # Use date_sent as return_date (FIX #5 — no return_date in DBF)
                    if "date_sent" in record and "return_date" not in record:
                        record["return_date"] = record["date_sent"]

                    # Map legacy status 'A' → 'PENDING' (FIX #8)
                    record.setdefault("status", "PENDING")

                    defaults = {k: v for k, v in record.items() if k != "rfc_number"}
                    defaults["creditor_id"] = cred_pk

                    if mode == "create_only":
                        if (
                            RFC.objects.using(db_alias)
                            .filter(rfc_number=rfc_number)
                            .exists()
                        ):
                            skipped += 1
                            continue
                        RFC.objects.using(db_alias).create(
                            rfc_number=rfc_number, **defaults
                        )
                        created += 1
                    elif mode == "update_only":
                        n = (
                            RFC.objects.using(db_alias)
                            .filter(rfc_number=rfc_number)
                            .update(**defaults)
                        )
                        updated += n or 0
                        skipped += 0 if n else 1
                    else:
                        _, was_created = RFC.objects.using(db_alias).update_or_create(
                            rfc_number=rfc_number, defaults=defaults
                        )
                        created += was_created
                        updated += not was_created

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, updated, skipped, errors, tenant, shop, len(rows))
    )


# ============================================================================
# supcrtrn → RFCLineItem
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_supcrtrn(request):
    """
    POST /api/v1/creditors/import/supcrtrn/
    Import supcrtrn.csv → RFCLineItem.
    Import supcrmas AND stock items BEFORE this.
    Stock items are looked up by stock_code. Rows with unknown stock codes are skipped.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    mode = request.data.get("mode", "create_or_update")
    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)

    # Pre-load lookup maps
    rfc_map = dict(RFC.objects.using(db_alias).values_list("rfc_number", "pk"))
    # StockItem uses stock_code as PK so the map is code → pk (which is the same value)
    try:
        from stock_control.models import StockItem

        stock_map = dict(
            StockItem.objects.using(db_alias).values_list("stock_code", "stock_code")
        )
    except Exception:
        stock_map = {}

    # Default tax code for RFC lines (first available)
    from apps.settings.models import TaxCode as TC

    default_tax = TC.objects.using(db_alias).first()
    if not default_tax:
        clear_current()
        return Response(
            {
                "error": "No TaxCode records found — seed tax codes before importing RFC lines"
            },
            status=400,
        )

    created = updated = skipped = 0
    errors = []

    # Track line numbers per RFC
    rfc_line_counters = {}

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPCRTRN_MAP, skip_empty)

                    raw_rfcno = record.pop("rfcno", None)
                    stock_code = record.pop("stock_code", None)
                    if not raw_rfcno or not stock_code:
                        skipped += 1
                        continue

                    rfc_pk = rfc_map.get(str(raw_rfcno).strip())
                    if not rfc_pk:
                        if _add_error(
                            errors,
                            row_num,
                            f"RFCNO {raw_rfcno} not in RFC table — skipped",
                        ):
                            break
                        skipped += 1
                        continue

                    if stock_code not in stock_map:
                        if _add_error(
                            errors,
                            row_num,
                            f"Stock code {stock_code} not found — skipped",
                        ):
                            break
                        skipped += 1
                        continue

                    # Auto-assign line_number per RFC
                    rfc_line_counters[rfc_pk] = rfc_line_counters.get(rfc_pk, 0) + 1
                    line_num = rfc_line_counters[rfc_pk]

                    record.setdefault("quantity_returned", Decimal("0"))
                    record.setdefault("quantity_stock", Decimal("0"))

                    defaults = dict(record)
                    defaults["rfc_id"] = rfc_pk
                    defaults["stock_item_id"] = stock_code
                    defaults["tax_code_id"] = default_tax.pk

                    if mode == "create_only":
                        if (
                            RFCLineItem.objects.using(db_alias)
                            .filter(rfc_id=rfc_pk, line_number=line_num)
                            .exists()
                        ):
                            skipped += 1
                            continue
                        RFCLineItem.objects.using(db_alias).create(
                            line_number=line_num, **defaults
                        )
                        created += 1
                    elif mode == "update_only":
                        n = (
                            RFCLineItem.objects.using(db_alias)
                            .filter(rfc_id=rfc_pk, line_number=line_num)
                            .update(**defaults)
                        )
                        updated += n or 0
                        skipped += 0 if n else 1
                    else:
                        _, was_created = RFCLineItem.objects.using(
                            db_alias
                        ).update_or_create(
                            rfc_id=rfc_pk, line_number=line_num, defaults=defaults
                        )
                        created += was_created
                        updated += not was_created

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, updated, skipped, errors, tenant, shop, len(rows))
    )


# ============================================================================
# supexp → ExpenseCategoryMonthlyBalance
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_supexp(request):
    """
    POST /api/v1/creditors/import/supexp/
    Import supexp.csv → ExpenseCategoryMonthlyBalance.

    Requires ExpenseCategory records to exist (seeded separately).
    Pass import_year in request body (default: current year).
    supexp has no year column — the year must be supplied explicitly.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    mode = request.data.get("mode", "create_or_update")
    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))
    import_year = int(request.data.get("import_year", datetime.now().year))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)

    # Pre-load expense category map: legacy_code → pk
    from apps.settings.models import ExpenseCategory as EC

    exp_cat_map = dict(EC.objects.using(db_alias).values_list("legacy_code", "pk"))
    # Fallback: try matching by pk directly
    exp_cat_pk_map = dict(EC.objects.using(db_alias).values_list("pk", "pk"))

    created = updated = skipped = 0
    errors = []

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPEXP_MAP, skip_empty)

                    raw_expcat = record.pop("expcat", None)
                    record.pop("category_name", None)  # informational only
                    if not raw_expcat:
                        skipped += 1
                        continue

                    raw_expcat_int = _to_int(raw_expcat)
                    # Try legacy_code match first, then PK match
                    exp_cat_pk = exp_cat_map.get(str(raw_expcat)) or exp_cat_pk_map.get(
                        raw_expcat_int
                    )
                    if not exp_cat_pk:
                        if _add_error(
                            errors,
                            row_num,
                            f"EXPCAT {raw_expcat} not in ExpenseCategory — skipped",
                        ):
                            break
                        skipped += 1
                        continue

                    defaults = dict(record)
                    defaults["expense_category_id"] = exp_cat_pk

                    if mode == "create_only":
                        if (
                            ExpenseCategoryMonthlyBalance.objects.using(db_alias)
                            .filter(expense_category_id=exp_cat_pk, year=import_year)
                            .exists()
                        ):
                            skipped += 1
                            continue
                        ExpenseCategoryMonthlyBalance.objects.using(db_alias).create(
                            expense_category_id=exp_cat_pk, year=import_year, **defaults
                        )
                        created += 1
                    elif mode == "update_only":
                        n = (
                            ExpenseCategoryMonthlyBalance.objects.using(db_alias)
                            .filter(expense_category_id=exp_cat_pk, year=import_year)
                            .update(**defaults)
                        )
                        updated += n or 0
                        skipped += 0 if n else 1
                    else:
                        _, was_created = ExpenseCategoryMonthlyBalance.objects.using(
                            db_alias
                        ).update_or_create(
                            expense_category_id=exp_cat_pk,
                            year=import_year,
                            defaults=defaults,
                        )
                        created += was_created
                        updated += not was_created

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, updated, skipped, errors, tenant, shop, len(rows))
    )


# ============================================================================
# supexpt → CreditorInvoice + CreditorInvoiceLineItem
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_supexpt(request):
    """
    POST /api/v1/creditors/import/supexpt/
    Import supexpt.csv → CreditorInvoice + one CreditorInvoiceLineItem per row.
    Each supexpt row is one invoice with a single expense category line.
    Import supmast AND expense categories BEFORE this.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    mode = request.data.get("mode", "create_or_update")
    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)
    cred_map = _creditor_map(db_alias)

    from apps.settings.models import ExpenseCategory as EC
    from apps.settings.models import TaxCode as TC

    exp_cat_map = dict(EC.objects.using(db_alias).values_list("pk", "pk"))
    exp_cat_legacy = dict(EC.objects.using(db_alias).values_list("legacy_code", "pk"))
    default_tax = TC.objects.using(db_alias).first()
    if not default_tax:
        clear_current()
        return Response(
            {"error": "No TaxCode records — seed tax codes first"}, status=400
        )

    created = updated = skipped = 0
    errors = []

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPEXPT_MAP, skip_empty)

                    raw_supno = record.pop("supno", None)
                    raw_expcat = record.pop("expcat", None)
                    tran_no = record.get("supplier_invoice_number")
                    if not raw_supno or not tran_no:
                        skipped += 1
                        continue

                    cred_pk = cred_map.get(str(raw_supno).strip())
                    if not cred_pk:
                        if _add_error(
                            errors, row_num, f"SUPNO {raw_supno} not found — skipped"
                        ):
                            break
                        skipped += 1
                        continue

                    # Resolve expense category
                    raw_expcat_int = _to_int(raw_expcat) if raw_expcat else None
                    exp_cat_pk = exp_cat_legacy.get(str(raw_expcat)) or exp_cat_map.get(
                        raw_expcat_int
                    )

                    # Invoice-level defaults
                    inv_defaults = {
                        "transaction_date": record.get(
                            "transaction_date", date.today()
                        ),
                        "station_no_area": record.get("station_no_area", ""),
                        "tax_indicator": record.get("tax_indicator", 1),
                        "subtotal": record.get("subtotal", Decimal("0")),
                        "total_vat": record.get("total_vat", Decimal("0")),
                        "total_amount": record.get("total_amount", Decimal("0")),
                        "grn_number": record.get("grn_number"),
                        "transaction_type": "INV",
                        "creditor_id": cred_pk,
                        "is_active": True,
                    }

                    if mode == "create_only":
                        # Use supplier_invoice_number as a proxy unique key
                        if (
                            CreditorInvoice.objects.using(db_alias)
                            .filter(
                                creditor_id=cred_pk, supplier_invoice_number=tran_no
                            )
                            .exists()
                        ):
                            skipped += 1
                            continue
                        inv_obj = CreditorInvoice.objects.using(db_alias).create(
                            supplier_invoice_number=tran_no, **inv_defaults
                        )
                        created += 1
                    elif mode == "update_only":
                        n = (
                            CreditorInvoice.objects.using(db_alias)
                            .filter(
                                creditor_id=cred_pk, supplier_invoice_number=tran_no
                            )
                            .update(**inv_defaults)
                        )
                        inv_obj = (
                            CreditorInvoice.objects.using(db_alias)
                            .filter(
                                creditor_id=cred_pk, supplier_invoice_number=tran_no
                            )
                            .first()
                        )
                        updated += n or 0
                        skipped += 0 if n else 1
                    else:
                        inv_obj, was_created = CreditorInvoice.objects.using(
                            db_alias
                        ).update_or_create(
                            creditor_id=cred_pk,
                            supplier_invoice_number=tran_no,
                            defaults=inv_defaults,
                        )
                        created += was_created
                        updated += not was_created

                    # Create/update the line item if we have an expense category
                    if inv_obj and exp_cat_pk:
                        line_defaults = {
                            "amount": record.get("subtotal", Decimal("0")),
                            "tax_code_id": default_tax.pk,
                            "expense_category_id": exp_cat_pk,
                        }
                        CreditorInvoiceLineItem.objects.using(
                            db_alias
                        ).update_or_create(
                            invoice_id=inv_obj.pk, line_number=1, defaults=line_defaults
                        )

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, updated, skipped, errors, tenant, shop, len(rows))
    )


# ============================================================================
# suppo → SupplierPaymentOrder
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_suppo(request):
    """
    POST /api/v1/creditors/import/suppo/
    Import suppo.csv → SupplierPaymentOrder.

    Note: suppo.dbf has no SUPNO — creditor_id will be null for all legacy records.
    No FK dependencies; can be imported in any order.
    """
    file_obj = request.FILES.get("file")
    if not file_obj:
        return Response({"error": "No file provided"}, status=400)

    tenant, shop, err = _resolve_tenant_shop(request)
    if err:
        return err

    mode = request.data.get("mode", "create_or_update")
    skip_empty = _parse_bool_param(request.data.get("skip_empty", "true"))

    headers, rows, _, err = _read_csv(file_obj)
    if err:
        return Response({"error": err}, status=400)

    header_idx = {h: i for i, h in enumerate(headers)}
    db_alias = _set_schema(tenant, shop)

    created = updated = skipped = 0
    errors = []

    try:
        with transaction.atomic(using=db_alias):
            with connections[db_alias].cursor() as cur:
                cur.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):
                try:
                    record = _parse_row(row, header_idx, SUPPO_MAP, skip_empty)

                    pay_date = record.get("payment_date")
                    amount = record.get("amount")
                    if not pay_date or not amount:
                        skipped += 1
                        continue

                    defaults = {
                        k: v
                        for k, v in record.items()
                        if k not in ("payment_date", "amount")
                    }
                    defaults["creditor"] = None  # no SUPNO in suppo.dbf

                    if mode == "create_only":
                        SupplierPaymentOrder.objects.using(db_alias).create(
                            payment_date=pay_date, amount=amount, **defaults
                        )
                        created += 1
                    elif mode == "update_only":
                        n = (
                            SupplierPaymentOrder.objects.using(db_alias)
                            .filter(payment_date=pay_date, amount=amount)
                            .update(**defaults)
                        )
                        updated += n or 0
                        skipped += 0 if n else 1
                    else:
                        _, was_created = SupplierPaymentOrder.objects.using(
                            db_alias
                        ).update_or_create(
                            payment_date=pay_date, amount=amount, defaults=defaults
                        )
                        created += was_created
                        updated += not was_created

                except Exception as e:
                    if _add_error(errors, row_num, str(e)):
                        break

    except Exception as e:
        clear_current()
        return Response({"error": f"Import failed (rolled back): {e}"}, status=500)
    finally:
        clear_current()

    return Response(
        _build_summary(created, updated, skipped, errors, tenant, shop, len(rows))
    )
