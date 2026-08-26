"""
SaaS Admin — Unified CSV Import API

Imports legacy DBF-exported CSV data into the correct Django models for a
specific tenant/shop schema. Restricted to superusers (SaaS administrators).

Supported model_type values and their target models/tables:

  MASTER DATA (direct field mapping):
    debtor       → Debtor            (db_table: dmast)
    creditor     → Creditor          (db_table: creditors)
    stock        → StockItem         (db_table: stock_items)
    department   → SalesDepartment   (db_table: as configured)

  DEBTOR TRANSACTIONS:
    debtran      → DebtorTransaction (db_table: debtran)
                   NOTE: dtran.csv is a subset of debtran — use model_type=debtran for both.
    debtopen     → DebtorOpenItem    (db_table: debtopen)
    debtoaud     → DebtorAudit       (db_table: debtoraud)
    dpdc         → Dpdc              (db_table: as configured)

  CREDITOR/SUPPLIER TRANSACTIONS:
    suptran      → SupplierLedgerEntry           (db_table: supplier_ledger_entries)
    supopen      → CreditorOpenItem              (db_table: creditor_open_items)
    supoaud      → OpenItemAudit                 (db_table: open_item_audits)
    supcrmas     → RFC                           (db_table: rfcs)
    supcrtrn     → RFCLineItem                   (db_table: rfc_line_items)
    suppo        → SupplierPaymentOrder          (db_table: supplier_payment_orders)
    supexp       → ExpenseCategoryMonthlyBalance (db_table: expense_category_monthly_balances)
    supexpt      → ExpenseCategoryTransaction    (db_table: expense_category_transactions)

  STOCK TRANSACTIONS:
    stran        → StockTransaction  (db_table: stock_transactions)

IMPORTANT — system-generated fields:
  Many fields on these models are marked editable=False (e.g. balance buckets,
  calculated totals, auto-generated transaction numbers). The import bypasses
  model.save() validation by using QuerySet.update() for the update path and
  Model.objects.create() only for the create path, so these values ARE written
  from the CSV during migration. After migration, the application's normal
  save() logic takes over for new records.
"""

import csv
import io
import json
import threading as _threading
from datetime import datetime
from decimal import Decimal, InvalidOperation

# Creditor/supplier transaction models
from apps.creditors.models import (
    RFC,
    Creditor,
    CreditorOpenItem,
    ExpenseCategoryMonthlyBalance,
    ExpenseCategoryTransaction,
    OpenItemAudit,
    RFCLineItem,
    SupplierLedgerEntry,
    SupplierPaymentOrder,
)

# Debtor transaction models
# Master data models
from apps.debtors.models import (
    Debtor,
    DebtorAudit,
    DebtorOpenItem,
    DebtorTransaction,
    Dpdc,
)
from apps.settings.models import ExpenseCategory, SalesDepartment, TaxCode
from apps.stock_control.models import StockItem, StockTransaction
from django.db import connections, transaction
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from tenancy.models import Shop, Tenant
from tenancy.tenant_context import clear_current, set_current_shop, set_current_tenant
from tenancy.utils import register_tenant_connection

_tl = _threading.local()

# ============================================================
# CSV → model field maps
# Only columns that map to writable fields are listed here.
# FK columns are resolved inside each _import_*_record().
# ============================================================

DEBTOR_CSV_TO_MODEL_FIELD_MAP = {
    "DNO": "dno",
    "DNAME": "dname",
    "DSNAME": "dsname",
    "DCONTACT": "dcontact",
    "DTEL": "dtel",
    "TEL2": "dtel2",
    "DFAX": "dfax",
    "EMAIL": "email",
    "DADD1": "address_line1",
    "DADD2": "address_line2",
    "DADD3": "address_line3",
    "DPCODE": "postal_code",
    "DELAD1": "delivery_address1",
    "DELAD2": "delivery_address2",
    "DELAD3": "delivery_address3",
    "DELAD4": "delivery_address4",
    "DTAXNO": "dtaxno",  # Legacy field name
    "VATREF": "vatref",  # Legacy field name
    "DAREA": "darea",  # Legacy field name
    "DBALBFWD": "dbalbfwd",  # Legacy field name
    "DCRNT": "dcrnt",  # Legacy field name
    "D30": "d30",  # Legacy field name
    "D60": "d60",  # Legacy field name
    "D90": "d90",  # Legacy field name
    "D120": "d120",  # Legacy field name
    "D150": "d150",  # Legacy field name
    "D180": "d180",  # Legacy field name
    "DSALESM": "dsalesm",  # Legacy field name
    "DSALESY": "dsalesy",  # Legacy field name
    "DPROFITM": "dprofitm",  # Legacy field name
    "DPROFITY": "dprofity",  # Legacy field name
    "DAMTLPD": "damtlpd",  # Legacy field name
    "DDATLPD": "ddatlpd",  # Legacy field name
    "DATEOPENED": "dateopened",  # Legacy field name
    "DDISCPER": "ddiscper",  # Legacy field name
    "DCLIMIT": "dclimit",  # Legacy field name
    "DINTFLAG": "dintflag",  # Legacy field name
    "PRICE": "price",  # Legacy field name
    "ACCTYPE": "acctype",  # Legacy field name
    "TERMS": "terms",  # Legacy field name
    "PDISC": "pdisc",  # Legacy field name
    "DISCPRN": "discount_printable",
    "DPOSBAL": "dposbal",  # Legacy field name
    "BLOCKFLAG": "blockflag",  # Legacy field name
    "NOTES": "notes",
}

CREDITOR_CSV_TO_MODEL_FIELD_MAP = {
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
    "ACCTYPE": "account_category",
    "SUPDISC": "prompt_payment_discount_percent",
    "BANK": "bank_name",
    "BANKCODE": "branch_code",
    "BANKACC": "account_number",
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
    "UPDSTKSP": "update_selling_price_on_receipt",
}

STOCK_CSV_TO_MODEL_FIELD_MAP = {
    "CODE": "stock_code",
    "DESCRIP": "description",
    "DEPT": "department",  # FK resolved in _import_stock_record
    "SUPNO": "supplier",  # FK resolved in _import_stock_record
    "SUPCODE": "supplier_code",
    "TAXCODE": "tax_code",  # FK resolved in _import_stock_record
    "CPRICE": "cost_price",
    "AVGCOST": "average_cost",
    "SPRICE": "selling_price_1",
    "SPRICE1": "selling_price_2",
    "SPRICE2": "selling_price_3",
    "MARKUP": "markup_1",
    "MARKUP1": "markup_2",
    "MARKUP2": "markup_3",
    "QOH": "quantity_on_hand",
    "QTYBYSTOCK": "quantity_allocated",
    "QTYSORD": "quantity_sale_order",
    "REORDERQTY": "reorder_quantity",
    "QTYONORDER": "quantity_on_order",
    "DEFAULTQTY": "default_selling_quantity",
    "ALLOWNEG": "allow_negative_quantities",
    "MAXDISC": "maximum_discount_percent",
    "SALESMTDQ": "sales_mtd_quantity",
    "SALESMTDV": "sales_mtd_value",
    "SALESYTDQ": "sales_ytd_quantity",
    "SALESYTDV": "sales_ytd_value",
    "GPMTD": "gross_profit_mtd",
    "GPYTD": "gross_profit_ytd",
    "PURMTDQ": "purchased_mtd_quantity",
    "PURYTDQ": "purchased_ytd_quantity",
    "BALBFWDQ": "balance_bfwd_quantity",
    "BALBFWDV": "balance_bfwd_value",
    "CLOSING": "closing_stock_balance",
    "LASTPUDATE": "date_last_purchased",
    "LASTSOLDATE": "date_last_sold",
    "BIN": "bin_number",
    "WEIGHT": "weight",
    "STKCNTFLAG": "stock_count_flag",
    "ACTIVE": "is_active",
}

DEPARTMENT_CSV_TO_MODEL_FIELD_MAP = {
    "DEPT": "number",
    "DEPTNAME": "name",
    "SLSMTD": "sales_mtd",
    "SLSYTD": "sales_ytd",
}

# debtran.csv AND dtran.csv both map to DebtorTransaction.
# dtran has fewer columns (no STATION/VATREF) but the same model.
# DNO resolves to debtor FK in _import_debtran_record.
# DEL1-4 map to description_line1-4 (NOT delivery_address).
# SOURCE maps to source_station (NOT source).
# DTAXSTAT maps to vat_status (NOT tax_status).
DEBTRAN_CSV_TO_MODEL_FIELD_MAP = {
    "DNO": "debtor",  # FK — customer_number lookup
    "DTRANO": "transaction_number",
    "DTDATE": "transaction_date",
    "TIME": "transaction_time",
    "DTYPE": "transaction_type",
    "DTSUB": "subtotal",
    "DTGST": "vat_amount",
    "DTTOT": "total_amount",
    "DTAXSTAT": "vat_status",
    "SOURCE": "source_station",
    "ORDNO": "order_number",
    "CUSTREF": "customer_reference",
    "DEL1": "description_line1",
    "DEL2": "description_line2",
    "DEL3": "description_line3",
    "DEL4": "description_line4",
    "STATION": "station",
    "VATREF": "vat_reference",
}

# debtopen.csv → DebtorOpenItem
# TOTAL maps to original_amount (the model field name), NOT total_amount.
# AGEFLAG is CharField '0'-'4', not integer.
DEBTOPEN_CSV_TO_MODEL_FIELD_MAP = {
    "DNO": "debtor",  # FK — customer_number lookup
    "DTRANO": "transaction_number",
    "TYPE": "transaction_type",
    "DATE": "transaction_date",
    "TOTAL": "original_amount",
    "BALANCEDUE": "balance_due",
    "AGEFLAG": "age_flag",
    "POSTED": "posted",
}

# debtoaud.csv → DebtorAudit
# THISTYPE → current_type. THISTRAN → current_transaction.
DEBTOAUD_CSV_TO_MODEL_FIELD_MAP = {
    "DNO": "debtor",  # FK — customer_number lookup
    "DTRANO": "transaction_number",
    "TYPE": "transaction_type",
    "THISTYPE": "current_type",
    "THISTRAN": "current_transaction",
    "DATE": "audit_date",
    "AMOUNT": "amount",
}

# dpdc.csv → Dpdc
# The FK field on Dpdc is named 'dno', not 'debtor'.
DPDC_CSV_TO_MODEL_FIELD_MAP = {
    "DNO": "dno",  # FK — customer_number lookup
    "DATE": "date",
    "AMOUNT": "amount",
    "STATUS": "status",
}

# suptran.csv → SupplierLedgerEntry (direct 1:1 DBF mapping, no validation on save)
SUPTRAN_CSV_TO_MODEL_FIELD_MAP = {
    "SUPNO": "creditor",  # FK — supplier_number lookup
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

# supopen.csv → CreditorOpenItem (is_legacy=True skips FK link validation)
# TOTAL → original_amount. AGEFLAG → ageing_flag (CharField).
SUPOPEN_CSV_TO_MODEL_FIELD_MAP = {
    "SUPNO": "creditor",  # FK — supplier_number lookup
    "TRANO": "transaction_number",
    "TYPE": "transaction_type",
    "DATE": "transaction_date",
    "TOTAL": "original_amount",
    "BALANCEDUE": "balance_due",
    "AGEFLAG": "ageing_flag",
}

# supoaud.csv → OpenItemAudit
# THISTYPE → this_transaction_type. THISTRAN → this_transaction_number (IntegerField).
SUPOAUD_CSV_TO_MODEL_FIELD_MAP = {
    "SUPNO": "creditor",  # FK — supplier_number lookup
    "TRANO": "transaction_number",
    "TYPE": "transaction_type",
    "THISTYPE": "this_transaction_type",
    "THISTRAN": "this_transaction_number",
    "DATE": "transaction_date",
    "AMOUNT": "amount",
}

# supcrmas.csv → RFC
# STATUS: DBF A/C/R/X → Django PE/CR/RE/CA (mapped in RFC_STATUS_MAP).
# return_date is not in DBF — set from date_sent in record fn.
SUPCRMAS_CSV_TO_MODEL_FIELD_MAP = {
    "RFCNO": "rfc_number",
    "SUPNO": "creditor",  # FK — supplier_number lookup
    "DATESENT": "date_sent",
    "DATERETN": "date_returned",
    "STATUS": "status",  # mapped via RFC_STATUS_MAP
}

# supcrtrn.csv → RFCLineItem
# RFCNO → rfc FK. CODE → stock_item FK.
# QTY → quantity_stock. VAL → line_value. COMMENT → reason.
SUPCRTRN_CSV_TO_MODEL_FIELD_MAP = {
    "RFCNO": "rfc",  # FK — rfc_number lookup
    "TYPE": "original_transaction_type",
    "CODE": "stock_item",  # FK — stock_code lookup
    "DATE": "rfc_line_date",
    "TIME": "rfc_line_time",
    "QTY": "quantity_stock",
    "VAL": "line_value",
    "QTYRFC": "quantity_returned",
    "QTYCRED": "quantity_credited",
    "COMMENT": "reason",
    "PURCHDATE": "original_transaction_date",
    "SUPREFNO": "supplier_reference_number",
}

# suppo.csv → SupplierPaymentOrder
# No SUPNO in DBF — creditor is always null on legacy records.
SUPPO_CSV_TO_MODEL_FIELD_MAP = {
    "DATE": "payment_date",
    "AMOUNT": "amount",
    "DETAIL1": "detail_line1",
    "DETAIL2": "detail_line2",
    "DETAIL3": "detail_line3",
}

# supexp.csv → ExpenseCategoryMonthlyBalance
# EXPCAT → expense_category FK. All EXP1-12 / EXPMTD fields are editable=False
# on the model but we write them anyway via _uoc (QuerySet.update bypass).
# 'year' is Django-only — passed as extra kwarg to import fn.
SUPEXP_CSV_TO_MODEL_FIELD_MAP = {
    "EXPCAT": "expense_category",  # FK — pk lookup
    "EXPCATNAME": "expense_category_name",
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

# supexpt.csv → ExpenseCategoryTransaction
# EXPCAT → expense_category FK. SUPNO → creditor FK.
# INVAT and TOTAL are editable=False (system-calculated) — excluded from import.
SUPEXPT_CSV_TO_MODEL_FIELD_MAP = {
    "EXPCAT": "expense_category",  # FK — pk lookup
    "DATE": "transaction_date",
    "TRANO": "transaction_number",
    "SUPNO": "creditor",  # FK — supplier_number lookup
    "VALUE": "amount_exclusive",
    "SOURCE": "source_type",
    "GRNNO": "grn_number",
    "TAXIND": "tax_indicator",
}

# stran.csv → StockTransaction
# CODE → stock_item FK. DEPT → department FK. TAXIND → tax_code FK.
# DNO → debtor FK (optional). SUPNO → supplier FK (optional).
# QTY → split into quantity_in/quantity_out based on transaction_type.
# TYPE legacy codes mapped via STRAN_TYPE_MAP.
# COST → unit_cost. STDPRICE → unit_price. SOURCE → station_number.
STRAN_CSV_TO_MODEL_FIELD_MAP = {
    "TRANO": "transaction_number",
    "CODE": "stock_item",  # FK — stock_code lookup
    "QTY": "_qty",  # special — split in _import_stran_record
    "DISCOUNT": "discount",
    "VAL": "value",
    "TYPE": "transaction_type",  # mapped via STRAN_TYPE_MAP
    "DATE": "transaction_date",
    "TIME": "transaction_time",
    "DEPT": "department",  # FK — SalesDepartment number lookup
    "COST": "unit_cost",
    "TAXIND": "tax_code",  # FK — TaxCode code lookup
    "SOURCE": "station_number",
    "DNO": "debtor",  # FK — customer_number lookup (optional)
    "SUPNO": "supplier",  # FK — supplier_number lookup (optional)
    "COMMENTS": "comments",
    "STDPRICE": "unit_price",
}

# Legacy STRAN TYPE codes → StockTransaction.TRANSACTION_TYPES choices
STRAN_TYPE_MAP = {
    "SI": "INCOMING",
    "IN": "INCOMING",
    "SO": "SALE",
    "SA": "SALE",
    "SR": "SALE_RETURN",
    "RT": "RETURN",
    "AD": "ADJUSTMENT",
    "ST": "STOCK_TAKE",
    "MN": "MANUFACTURE",
    "BU": "BUNDLE_USE",
    "BI": "BULK_ISSUE",
    "LI": "LAYBYE_IN",
    "LO": "LAYBYE_OUT",
    "JI": "JOB_IN",
    "JO": "JOB_OUT",
    "RI": "RFC_IN",
    "RO": "RFC_OUT",
}

# RFC STATUS: DBF single-char → Django choices
RFC_STATUS_MAP = {
    "A": "PE",
    "C": "CR",
    "R": "RE",
    "X": "CA",
    # Pass-through if already mapped
    "PE": "PE",
    "CR": "CR",
    "RE": "RE",
    "CA": "CA",
}


# ============================================================
# Field type sets — drive _parse_value() type conversions
# ============================================================

DECIMAL_FIELDS = {
    # Debtor
    "dbalbfwd",
    "dcrnt",
    "d30",
    "d60",
    "d90",
    "d120",
    "d150",
    "d180",
    "dsalesm",
    "dsalesy",
    "dprofitm",
    "dprofity",
    "damtlpd",
    "ddiscper",
    "dclimit",
    "pdisc",
    # Creditor
    "total_outstanding_balance",
    "last_paid_amount",
    "purchases_mtd",
    "purchases_ytd",
    "prompt_payment_discount_percent",
    # Stock
    "cost_price",
    "average_cost",
    "selling_price_1",
    "selling_price_2",
    "selling_price_3",
    "markup_1",
    "markup_2",
    "markup_3",
    "quantity_on_hand",
    "quantity_allocated",
    "quantity_sale_order",
    "quantity_counted",
    "reorder_quantity",
    "quantity_on_order",
    "default_selling_quantity",
    "maximum_discount_percent",
    "sales_mtd_quantity",
    "sales_mtd_value",
    "sales_ytd_quantity",
    "sales_ytd_value",
    "gross_profit_mtd",
    "gross_profit_ytd",
    "purchased_mtd_quantity",
    "purchased_ytd_quantity",
    "balance_bfwd_quantity",
    "balance_bfwd_value",
    "closing_stock_balance",
    "weight",
    # Department
    "sales_mtd",
    "sales_month_1",
    "sales_month_2",
    "sales_month_3",
    "sales_month_4",
    "sales_month_5",
    "sales_month_6",
    "sales_month_7",
    "sales_month_8",
    "sales_month_9",
    "sales_month_10",
    "sales_month_11",
    "sales_month_12",
    # DebtorTransaction
    "subtotal",
    "vat_amount",
    "total_amount",
    # DebtorOpenItem / CreditorOpenItem
    "original_amount",
    "balance_due",
    # DebtorAudit / OpenItemAudit / Dpdc / SupplierPaymentOrder
    "amount",
    # RFC / RFCLineItem
    "line_value",
    "quantity_returned",
    "quantity_credited",
    "quantity_stock",
    # ExpenseCategoryMonthlyBalance
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
    # ExpenseCategoryTransaction
    "amount_exclusive",
    # StockTransaction / SupplierLedgerEntry
    "discount",
    "value",
    "unit_cost",
    "unit_price",
}

INTEGER_FIELDS = {
    "dno",
    "darea",
    "price",
    "terms",
    "payment_terms_days",
    # Department
    "number",
    # StockTransaction
    "transaction_number",
    "station_number",
    # SupplierLedgerEntry / ExpenseCategoryTransaction
    "grn_number",
    # OpenItemAudit (THISTRAN N(6))
    "this_transaction_number",
    # ExpenseCategoryTransaction
    "tax_indicator",
    # StockItem
    "bin_number",
    "station_number",
}

DATE_FIELDS = {
    "ddatlpd",
    "last_paid_date",
    "dateopened",
    "date_last_purchased",
    "date_last_sold",
    "transaction_date",
    "audit_date",
    "date",
    "due_date",
    "date_sent",
    "date_returned",
    "rfc_line_date",
    "original_transaction_date",
    "payment_date",
}

# CharField Y/N fields
YN_FIELDS = {
    "dintflag",
    "discount_printable",
    "dposbal",
    "serial_tracking",
    "charge_scrap",
    "posted",
}

# Python bool fields
BOOL_FIELDS = {
    "update_selling_price_on_receipt",
    "allow_negative_quantities",
    "is_active",
}

EMAIL_FIELDS = {"email"}


# ============================================================
# Master lookup table and constants
# ============================================================

_ALL_MAPS = {
    "debtor": DEBTOR_CSV_TO_MODEL_FIELD_MAP,
    "creditor": CREDITOR_CSV_TO_MODEL_FIELD_MAP,
    "stock": STOCK_CSV_TO_MODEL_FIELD_MAP,
    "department": DEPARTMENT_CSV_TO_MODEL_FIELD_MAP,
    "debtran": DEBTRAN_CSV_TO_MODEL_FIELD_MAP,
    "debtopen": DEBTOPEN_CSV_TO_MODEL_FIELD_MAP,
    "debtoaud": DEBTOAUD_CSV_TO_MODEL_FIELD_MAP,
    "dpdc": DPDC_CSV_TO_MODEL_FIELD_MAP,
    "suptran": SUPTRAN_CSV_TO_MODEL_FIELD_MAP,
    "supopen": SUPOPEN_CSV_TO_MODEL_FIELD_MAP,
    "supoaud": SUPOAUD_CSV_TO_MODEL_FIELD_MAP,
    "supcrmas": SUPCRMAS_CSV_TO_MODEL_FIELD_MAP,
    "supcrtrn": SUPCRTRN_CSV_TO_MODEL_FIELD_MAP,
    "suppo": SUPPO_CSV_TO_MODEL_FIELD_MAP,
    "supexp": SUPEXP_CSV_TO_MODEL_FIELD_MAP,
    "supexpt": SUPEXPT_CSV_TO_MODEL_FIELD_MAP,
    "stran": STRAN_CSV_TO_MODEL_FIELD_MAP,
}

VALID_MODEL_TYPES = set(_ALL_MAPS.keys())

# The field that uniquely identifies each record, used to validate mappings
REQUIRED_FIELD_MAP = {
    "debtor": "dno",
    "creditor": "supplier_number",
    "stock": "stock_code",
    "department": "number",
    "debtran": "transaction_number",
    "debtopen": "transaction_number",
    "debtoaud": "transaction_number",
    "dpdc": "dno",
    "suptran": "transaction_number",
    "supopen": "transaction_number",
    "supoaud": "transaction_number",
    "supcrmas": "rfc_number",
    "supcrtrn": "rfc",
    "suppo": "payment_date",
    "supexp": "expense_category",
    "supexpt": "transaction_number",
    "stran": "transaction_number",
}


# ============================================================
# Helpers
# ============================================================


def _detect_delimiter(text):
    first_line = text.split("\n")[0]
    if ";" in first_line and first_line.count(";") > first_line.count(","):
        return ";"
    return ","


def _parse_value(value, field_name):
    """Convert a raw CSV string to the correct Python type for the given model field."""
    if value is None:
        return None
    value = str(value).strip()

    if value == "" or value.upper() == "N/A":
        if field_name in DECIMAL_FIELDS:
            return Decimal("0.00")
        if field_name in INTEGER_FIELDS:
            return 0
        if field_name in DATE_FIELDS:
            return None
        if field_name in YN_FIELDS:
            return "N"
        if field_name in BOOL_FIELDS:
            return False
        if field_name in EMAIL_FIELDS:
            return ""
        if field_name == "block_flag":
            return "0"
        # Empty ACCTYPE/acctype — return '' (CharField blank=True) so the field
        # is set to empty string rather than left as None on a non-null column.
        if field_name in ("acctype", "account_type"):
            return ""
        # Empty DATEOPENED — field is nullable on the model; return None explicitly.
        if field_name == "dateopened":
            return None
        return ""

    if field_name in INTEGER_FIELDS:
        try:
            return int(float(value))
        except Exception:
            return 0

    if field_name in DECIMAL_FIELDS:
        try:
            return Decimal(value.replace(",", ""))
        except Exception:
            return Decimal("0.00")

    if field_name in DATE_FIELDS:
        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except Exception:  # nosec - trying next date format is expected
                continue
        return None

    if field_name in YN_FIELDS:
        return "Y" if value.upper() in ("Y", "YES", "TRUE", "1") else "N"

    if field_name in BOOL_FIELDS:
        return value.upper() in ("Y", "YES", "TRUE", "1")

    if field_name in EMAIL_FIELDS:
        return value.lower() if "@" in value and "." in value.split("@")[-1] else ""

    if field_name == "blockflag":
        if value in ("0", "1", "2", "3", "Y", "N"):
            return value
        if value.upper() in ("YES", "TRUE"):
            return "Y"
        return "0"

    if field_name == "account_type":
        v = value.upper().strip()
        return v if v in ("", "O", "C", "N", "B") else ""

    if field_name == "account_category":
        v = value.upper().strip()
        return v if v in ("BBF", "OI", "") else "BBF"

    if field_name == "vat_status":
        v = value.upper().strip()
        return v if v in ("S", "E", "Z") else "S"

    if field_name == "age_flag":
        v = str(value).strip()
        return v if v in ("0", "1", "2", "3", "4") else "0"

    if field_name == "transaction_type":
        upper = value.upper()
        return STRAN_TYPE_MAP.get(upper, value)

    if field_name == "status":
        return RFC_STATUS_MAP.get(value.upper(), value)

    if field_name == "rfc_line_time":
        return value[:5] if value else ""

    return value


def _set_schema_context(tenant, shop):
    register_tenant_connection(tenant, shop=shop)
    db_alias = tenant.db_alias
    set_current_tenant(tenant)
    set_current_shop(shop.schema_name)
    return db_alias


def _apply_search_path(db_alias, schema_name):
    """
    Patch every shop model's db_table to be schema-qualified and return
    a restore function. Uses thread-locals so concurrent requests don't
    interfere with each other's patches.
    """
    from django.apps import apps as django_apps
    from django.conf import settings as _settings

    schema_app_labels = set(getattr(_settings, "SHOP_APP_LABELS", []))

    # Patch OPTIONS on the live settings_dict
    conn = connections[db_alias]
    opts = conn.settings_dict.setdefault("OPTIONS", {})
    opts["options"] = f"-c search_path={schema_name},public"

    # Build a thread-local patch map for this import only
    patched = {}
    for app_label in schema_app_labels:
        try:
            app_config = django_apps.get_app_config(app_label)
        except LookupError:
            continue
        for model in app_config.get_models():
            original = model._meta.db_table
            if '"' in original or original.startswith(schema_name):
                continue
            model._meta.db_table = f'"{schema_name}"."{original}"'
            patched[model] = original

    # Store in thread-local so _remove_schema_patch restores the right ones
    _tl.patched_models = patched


def _remove_schema_patch():
    """Restore all model db_table values patched by _apply_search_path."""
    patched = getattr(_tl, "patched_models", {})
    for model, original in patched.items():
        model._meta.db_table = original
    _tl.patched_models = {}


def _get_csv_to_model_map(model_type):
    return _ALL_MAPS.get(model_type, {})


def _get_available_fields(model_type):
    return sorted(set(_ALL_MAPS.get(model_type, {}).values()))


# ============================================================
# _uoc — update-or-create bypassing model.save() validation
#
# Many models (Creditor, DebtorTransaction, DebtorOpenItem, etc.)
# call full_clean() inside save(), which rejects historical data.
# For the update path we use QuerySet.filter().update() which goes
# straight to SQL and skips all Python-level validation.
# For the create path we use Model(**fields).save() only where the
# model has no problematic save() — otherwise use bulk_create.
# ============================================================


def _uoc(manager, lookup, defaults, mode, schema_name=None):
    """
    Safe update_or_create using a direct psycopg2 connection when schema_name
    is provided. This bypasses Django's connection pool entirely, which is
    necessary because middleware resets the search_path between rows during
    StreamingHttpResponse streaming.

    Falls back to ORM for models without a schema_name (default DB models).
    """
    from django.db import IntegrityError

    db_alias = manager.db
    db_table = manager.model._meta.db_table
    # Strip any schema prefix that may have been patched onto db_table
    bare_table = db_table.replace('"', "").split(".")[-1]

    if schema_name:
        import psycopg2 as _psycopg2

        _sd = connections[db_alias].settings_dict
        _raw = _psycopg2.connect(
            dbname=_sd["NAME"],
            user=_sd["USER"],
            password=_sd["PASSWORD"],
            host=_sd["HOST"],
            port=int(_sd["PORT"]),
            options=f"-c search_path={schema_name},public -c statement_timeout=0",
            connect_timeout=10,
        )
        # Timestamp columns from TimeStampedModel — not in CSV, use NOW()
        _TS_COLS = {"created_at", "updated_at"}

        # autocommit must be set before ANY query — psycopg2 implicitly starts
        # a transaction on the first cursor execute, after which set_session fails.
        _raw.autocommit = True

        # Query the table's NOT NULL columns once and fill missing ones with
        # sensible defaults so we never hit NOT NULL constraint violations.
        # Exclude: auto-increment PKs (serial/bigserial have nextval defaults
        # that don't show in column_default for identity columns), and any
        # column that already has a sequence/default we can't see plainly.
        with _raw.cursor() as _info:
            _info.execute(
                """
                SELECT c.column_name, c.data_type
                FROM information_schema.columns c
                WHERE c.table_schema = %s
                  AND c.table_name   = %s
                  AND c.is_nullable  = 'NO'
                  AND c.column_default IS NULL
                  AND c.is_identity   = 'NO'
                  AND c.column_name NOT IN (
                      SELECT kcu.column_name
                      FROM information_schema.table_constraints tc
                      JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                       AND tc.table_schema    = kcu.table_schema
                      WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_schema    = %s
                        AND tc.table_name      = %s
                  )
            """,
                [schema_name, bare_table, schema_name, bare_table],
            )
            _not_null_cols = {row[0]: row[1] for row in _info.fetchall()}

            # NOT NULL foreign-key columns must never be auto-filled with a
            # fabricated int. Unlike a plain data column, "0" isn't a safe
            # placeholder for a FK - it either violates the FK constraint
            # (if no row 0 exists) or, worse, silently wires the row to
            # whatever unrelated record has that PK. A row with a required
            # relationship we couldn't resolve should fail loudly (NOT NULL
            # error) rather than insert a fabricated reference.
            _info.execute(
                """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                 AND tc.table_schema    = kcu.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema    = %s
                  AND tc.table_name      = %s
            """,
                [schema_name, bare_table],
            )
            for (_fk_col,) in _info.fetchall():
                _not_null_cols.pop(_fk_col, None)

        # Now switch to manual transaction mode for the actual DML
        _raw.autocommit = False

        def _apply_not_null_defaults(fields):
            for col, dtype in _not_null_cols.items():
                if col in _TS_COLS:
                    continue  # handled by NOW()
                if col not in fields:
                    if (
                        "int" in dtype
                        or "numeric" in dtype
                        or "decimal" in dtype
                        or "real" in dtype
                        or "double" in dtype
                    ):
                        fields[col] = 0
                    elif dtype in ("boolean",):
                        fields[col] = False
                    else:
                        fields[col] = ""

        def _resolve_fields(fields):
            """Translate FK model instances to _id columns and unwrap their PK values."""
            from django.db.models import Model

            resolved = {}
            for k, v in fields.items():
                if isinstance(v, Model):
                    resolved[f"{k}_id"] = v.pk
                else:
                    resolved[k] = v
            return resolved

        def _build_insert(all_fields):
            all_fields = _resolve_fields(all_fields)
            _apply_not_null_defaults(all_fields)
            cols = list(all_fields.keys())
            col_names = ", ".join(f'"{c}"' for c in cols)
            placeholders = ", ".join("NOW()" if c in _TS_COLS else "%s" for c in cols)
            vals = [v for c, v in zip(cols, all_fields.values()) if c not in _TS_COLS]
            return col_names, placeholders, vals

        def _build_update(fields):
            fields = _resolve_fields(fields)
            cols = list(fields.keys())
            set_parts = [
                f'"{c}" = NOW()' if c in _TS_COLS else f'"{c}" = %s' for c in cols
            ]
            set_clause = ", ".join(set_parts)
            vals = [v for c, v in zip(cols, fields.values()) if c not in _TS_COLS]
            return set_clause, vals

        # Every f-string below interpolates only identifiers, never values
        # (values always go through %s placeholders in the params list).
        # `bare_table` comes from manager.model._meta.db_table (a hardcoded
        # Model.Meta attribute). The column names inside lookup_clause/
        # set_clause/col_names come from `lookup`/`defaults` keys, which
        # import_csv() validates against _get_available_fields(model_type)
        # before this is ever reached - so these can't carry attacker-
        # controlled identifiers despite `mappings` being client-supplied.
        try:
            with _raw.cursor() as _cur:
                resolved_lookup = _resolve_fields(lookup)
                lookup_clause = " AND ".join(f'"{k}" = %s' for k in resolved_lookup)
                lookup_vals = list(resolved_lookup.values())

                # Always include created_at/updated_at in inserts
                defaults.setdefault("created_at", None)
                defaults.setdefault("updated_at", None)

                if mode == "create_only":
                    _cur.execute(
                        f'SELECT 1 FROM "{bare_table}" WHERE {lookup_clause}',  # nosec B608
                        lookup_vals,
                    )
                    if _cur.fetchone():
                        return "skipped"
                    all_fields = {**lookup, **defaults}
                    col_names, placeholders, vals = _build_insert(all_fields)
                    _cur.execute(
                        f'INSERT INTO "{bare_table}" ({col_names}) VALUES ({placeholders})',  # nosec B608
                        vals,
                    )
                    _raw.commit()
                    return "created"

                elif mode == "update_only":
                    if not defaults:
                        return "skipped"
                    defaults["updated_at"] = None  # force updated_at = NOW()
                    set_clause, update_vals = _build_update(defaults)
                    _cur.execute(
                        f'UPDATE "{bare_table}" SET {set_clause} WHERE {lookup_clause}',  # nosec B608
                        update_vals + lookup_vals,
                    )
                    updated = _cur.rowcount
                    _raw.commit()
                    return "updated" if updated else "skipped"

                else:  # create_or_update
                    _cur.execute(
                        f'SELECT 1 FROM "{bare_table}" WHERE {lookup_clause}',  # nosec B608
                        lookup_vals,
                    )
                    if _cur.fetchone():
                        defaults["updated_at"] = None  # force updated_at = NOW()
                        set_clause, update_vals = _build_update(defaults)
                        if update_vals or "updated_at" in defaults:
                            _cur.execute(
                                f'UPDATE "{bare_table}" SET {set_clause} WHERE {lookup_clause}',  # nosec B608
                                update_vals + lookup_vals,
                            )
                        _raw.commit()
                        return "updated"
                    else:
                        all_fields = {**lookup, **defaults}
                        col_names, placeholders, vals = _build_insert(all_fields)
                        _cur.execute(
                            f'INSERT INTO "{bare_table}" ({col_names}) VALUES ({placeholders})',  # nosec B608
                            vals,
                        )
                        _raw.commit()
                        return "created"
        except Exception:
            _raw.rollback()
            raise
        finally:
            _raw.close()

    else:
        # No schema — use ORM directly (default DB models)
        if mode == "create_only":
            if manager.filter(**lookup).exists():
                return "skipped"
            try:
                obj = manager.model(**lookup, **defaults)
                manager.bulk_create([obj])
                return "created"
            except IntegrityError:
                return "skipped"
        elif mode == "update_only":
            rows = manager.filter(**lookup).update(**defaults)
            return "updated" if rows else "skipped"
        else:
            obj, created = manager.update_or_create(**lookup, defaults=defaults)
            return "created" if created else "updated"


# ============================================================
# API Views — SaaS Admin only (superuser)
# ============================================================


@api_view(["GET"])
@permission_classes([IsAdminUser])
def list_tenants_and_shops(request):
    """
    Return all tenants with their shops for the import UI dropdown.
    GET /api/v1/saas-admin/import/tenants/
    """
    tenants = Tenant.objects.filter(is_active=True).order_by("name")
    data = []
    for t in tenants:
        shops = Shop.objects.filter(tenant=t, is_active=True).order_by("name")
        data.append(
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
                    for s in shops
                ],
            }
        )
    return Response(data)


@api_view(["POST"])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def analyze_csv(request):
    """
    Upload and analyze a CSV file — return headers, sample rows, and suggested mappings.
    POST /api/v1/saas-admin/import/analyze/
    Body: multipart/form-data  'file' + optional 'model_type'
    """
    if "file" not in request.FILES:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    file_obj = request.FILES["file"]
    if not file_obj.name.lower().endswith(".csv"):
        return Response(
            {"error": "Only CSV files are supported"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    model_type = request.data.get("model_type", "debtor").lower()
    if model_type not in VALID_MODEL_TYPES:
        return Response(
            {
                "error": f'Invalid model_type. Must be one of: {", ".join(sorted(VALID_MODEL_TYPES))}'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        file_obj.seek(0)
        text = file_obj.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return Response(
            {"error": f"Cannot read file: {e}"}, status=status.HTTP_400_BAD_REQUEST
        )

    delimiter = _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    try:
        headers = [h.strip() for h in next(reader)]
    except StopIteration:
        return Response({"error": "File is empty"}, status=status.HTTP_400_BAD_REQUEST)

    sample_rows = []
    total_rows = 0
    for row in reader:
        total_rows += 1
        if len(sample_rows) < 5:
            sample_rows.append(row)

    csv_to_model_map = _get_csv_to_model_map(model_type)
    suggested = {
        col: csv_to_model_map[col.upper().strip()]
        for col in headers
        if col.upper().strip() in csv_to_model_map
    }

    return Response(
        {
            "headers": headers,
            "total_rows": total_rows,
            "sample_rows": sample_rows,
            "suggested_mappings": suggested,
            "available_model_fields": _get_available_fields(model_type),
            "delimiter": delimiter,
            "model_type": model_type,
        }
    )


@api_view(["POST"])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def import_csv(request):
    """
    Import a CSV file into the correct Django model table for a tenant/shop schema.

    POST /api/v1/saas-admin/import/execute/
    Body (multipart/form-data):
        file        : CSV file
        tenant_id   : int
        shop_id     : int
        mappings    : JSON string  {csv_header: model_field, ...}
        model_type  : one of VALID_MODEL_TYPES
        mode        : 'create_or_update' (default) | 'create_only' | 'update_only'
        year        : int — required for model_type=supexp (financial year, no DBF source)
    """
    file_obj = request.FILES.get("file")
    tenant_id = request.data.get("tenant_id")
    shop_id = request.data.get("shop_id")
    mappings_json = request.data.get("mappings", "{}")
    model_type = request.data.get("model_type", "debtor").lower()
    mode = request.data.get("mode", "create_or_update")
    import_year = request.data.get("year")

    if not file_obj:
        return Response(
            {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
        )

    if model_type not in VALID_MODEL_TYPES:
        return Response(
            {
                "error": f'Invalid model_type. Must be one of: {", ".join(sorted(VALID_MODEL_TYPES))}'
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not tenant_id or not shop_id:
        return Response(
            {"error": "tenant_id and shop_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        mappings = (
            json.loads(mappings_json)
            if isinstance(mappings_json, str)
            else mappings_json
        )
    except json.JSONDecodeError:
        return Response(
            {"error": "Invalid mappings JSON"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not mappings:
        return Response(
            {"error": "Column mappings are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    required_field = REQUIRED_FIELD_MAP[model_type]
    if required_field not in mappings.values():
        return Response(
            {"error": f'Mapping for required field "{required_field}" is missing'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # `mappings` values become dict keys that _uoc() later interpolates
    # directly into raw SQL column identifiers (only the values are
    # parameterized). Since `mappings` is caller-supplied JSON, an
    # unvalidated model_field would be a SQL injection vector — restrict
    # every mapped field to the model's real, known field names.
    allowed_fields = set(_get_available_fields(model_type))
    invalid_fields = sorted(set(mappings.values()) - allowed_fields)
    if invalid_fields:
        return Response(
            {"error": f"Invalid mapped field(s) for {model_type}: {invalid_fields}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if model_type == "supexp" and not import_year:
        return Response(
            {"error": '"year" parameter is required for supexp imports'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        shop = Shop.objects.select_related("tenant").get(id=shop_id, is_active=True)
    except Shop.DoesNotExist:
        return Response(
            {"error": f"Shop {shop_id} not found"}, status=status.HTTP_404_NOT_FOUND
        )

    tenant = shop.tenant
    if not tenant.is_active:
        return Response(
            {"error": "Tenant is not active"}, status=status.HTTP_400_BAD_REQUEST
        )

    db_alias = _set_schema_context(tenant, shop)
    _apply_search_path(db_alias, shop.schema_name)

    try:
        file_obj.seek(0)
        text = file_obj.read().decode("utf-8", errors="ignore")
    except Exception as e:
        clear_current()
        return Response(
            {"error": f"Cannot read file: {e}"}, status=status.HTTP_400_BAD_REQUEST
        )

    delimiter = _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    try:
        headers = [h.strip() for h in next(reader)]
    except StopIteration:
        clear_current()
        return Response(
            {"error": "CSV file is empty"}, status=status.HTTP_400_BAD_REQUEST
        )

    header_idx = {h: i for i, h in enumerate(headers)}
    for csv_col in mappings:
        if csv_col not in header_idx:
            clear_current()
            return Response(
                {"error": f"Mapped column '{csv_col}' not found in CSV headers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    dispatch = {
        "debtor": _import_debtor_record,
        "creditor": _import_creditor_record,
        "stock": _import_stock_record,
        "department": _import_department_record,
        "debtran": _import_debtran_record,
        "debtopen": _import_debtopen_record,
        "debtoaud": _import_debtoaud_record,
        "dpdc": _import_dpdc_record,
        "suptran": _import_suptran_record,
        "supopen": _import_supopen_record,
        "supoaud": _import_supoaud_record,
        "supcrmas": _import_supcrmas_record,
        "supcrtrn": _import_supcrtrn_record,
        "suppo": _import_suppo_record,
        "supexp": _import_supexp_record,
        "supexpt": _import_supexpt_record,
        "stran": _import_stran_record,
    }
    import_fn = dispatch[model_type]

    extra_kwargs = {"schema_name": shop.schema_name}
    if model_type == "supexp":
        extra_kwargs["year"] = int(import_year)

    created = updated = skipped = 0
    errors_list = []
    rows = list(reader)
    total = len(rows)

    # Progress report interval (every N rows)
    progress_interval = max(10, total // 20)  # ~20 progress updates

    def generate_progress():
        """Generator that yields progress updates as JSON lines."""
        nonlocal created, updated, skipped

        # Yield initial progress
        yield json.dumps(
            {
                "status": "started",
                "total": total,
                "processed": 0,
                "created": 0,
                "updated": 0,
                "skipped": 0,
            }
        ) + "\n"

        try:
            for row_num, row in enumerate(rows, start=2):
                # Parse record first (outside transaction)
                record = {}
                for csv_col, model_field in mappings.items():
                    idx = header_idx.get(csv_col)
                    if idx is not None and idx < len(row):
                        record[model_field] = _parse_value(row[idx], model_field)

                required_val = record.get(required_field)
                if required_val is None or required_val == "":
                    # DEBUG: Add info to errors list for frontend to show
                    errors_list.append(
                        f"DEBUG: Row {row_num} - record_keys={list(record.keys())}, required_field={required_field}, csv_headers={headers}, mappings={mappings}"
                    )
                    errors_list.append(
                        f"Row {row_num}: Missing {required_field} — skipped"
                    )
                    skipped += 1
                    continue

                # Process record in its own transaction
                try:
                    with transaction.atomic(using=db_alias):
                        result = import_fn(db_alias, record, mode, **extra_kwargs)

                        if result == "created":
                            created += 1
                        elif result == "updated":
                            updated += 1
                        else:
                            skipped += 1

                except Exception as e:
                    # The inner transaction.atomic() savepoint has already rolled back
                    # this row cleanly. Do NOT call set_rollback() here — that would
                    # poison the outer connection and cause the "atomic block" cascade
                    # error on every subsequent row.
                    import traceback

                    error_details = (
                        f"Row {row_num}: {e}\n{traceback.format_exc(limit=3)}"
                    )
                    errors_list.append(error_details)
                    skipped += 1
                    if len(errors_list) > 50:
                        errors_list.append("... too many errors, stopping")
                        break

                # Yield progress update every N rows
                if (row_num - 1) % progress_interval == 0:
                    yield json.dumps(
                        {
                            "status": "processing",
                            "total": total,
                            "processed": row_num - 1,
                            "created": created,
                            "updated": updated,
                            "skipped": skipped,
                        }
                    ) + "\n"

            # Yield completion status
            yield json.dumps(
                {
                    "status": "complete",
                    "total": total,
                    "processed": total,
                    "created": created,
                    "updated": updated,
                    "skipped": skipped,
                    "error_count": len(errors_list),
                    "errors": errors_list[:50],  # Include errors in response
                }
            ) + "\n"

        except Exception as e:
            yield json.dumps(
                {
                    "status": "error",
                    "message": f"Import failed: {e}",
                    "errors": errors_list[:50],  # Limit errors in response
                }
            ) + "\n"
        finally:
            _remove_schema_patch()
            clear_current()

    return StreamingHttpResponse(
        generate_progress(), content_type="application/x-ndjson"
    )


# ============================================================
# Record import functions
# Signature: (db_alias, record, mode, **kwargs) → 'created'|'updated'|'skipped'
# Each function resolves FKs, builds lookup + defaults dicts,
# then calls _uoc() which bypasses model.save() validation.
# ============================================================

# Map Django model field names → actual dmast column names
# (The model uses friendly names; the DB retains legacy DBF column names)
_DEBTOR_FIELD_TO_COL = {
    "address_line1": "dadd1",
    "address_line2": "dadd2",
    "address_line3": "dadd3",
    "postal_code": "dpcode",
    "delivery_address1": "delad1",
    "delivery_address2": "delad2",
    "delivery_address3": "delad3",
    "delivery_address4": "delad4",
    "discount_printable": "discprn",
}

# NOT NULL varchar/text columns in dmast that may be absent from CSV
_DMAST_NOT_NULL_TEXT_COLS = {
    "dname",
    "dsname",
    "dcontact",
    "dtel",
    "dtel2",
    "dfax",
    "email",
    "dadd1",
    "dadd2",
    "dadd3",
    "dpcode",
    "delad1",
    "delad2",
    "delad3",
    "delad4",
    "dtaxno",
    "vatref",
    "acctype",
    "discprn",
    "blockflag",
    "dintflag",
    "dposbal",
    "notes",
}


def _import_debtor_record(db_alias, record, mode, schema_name="public", **_):
    cust_num = record.get("dno")
    defaults = {k: v for k, v in record.items() if k != "dno" and v is not None}
    defaults.setdefault("is_active", True)

    # Translate Django model field names → actual DB column names
    translated = {}
    for field, val in defaults.items():
        col = _DEBTOR_FIELD_TO_COL.get(field, field)
        translated[col] = val

    # Ensure NOT NULL text columns are always present
    for col in _DMAST_NOT_NULL_TEXT_COLS:
        translated.setdefault(col, "")

    return _uoc(
        Debtor.objects.using(db_alias),
        {"dno": cust_num},
        translated,
        mode,
        schema_name=schema_name,
    )


def _import_creditor_record(db_alias, record, mode, schema_name=None, **_):
    sup_num = record.get("supplier_number")
    defaults = {
        k: v for k, v in record.items() if k != "supplier_number" and v is not None
    }
    defaults.setdefault("is_active", True)
    return _uoc(
        Creditor.objects.using(db_alias),
        {"supplier_number": sup_num},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_stock_record(db_alias, record, mode, schema_name=None, **_):
    stock_code = record.get("stock_code")
    defaults = {k: v for k, v in record.items() if k != "stock_code" and v is not None}
    defaults.setdefault("is_active", True)

    if "department" in defaults:
        dept_val = defaults.pop("department")
        try:
            defaults["department"] = SalesDepartment.objects.using(db_alias).get(
                number=int(dept_val)
            )
        except (SalesDepartment.DoesNotExist, ValueError, TypeError):
            # Department not found — leave field unset (NULL) rather than
            # failing the row. Import departments first to avoid this.
            pass

    if "supplier" in defaults:
        sup_val = defaults.pop("supplier")
        if sup_val:
            sup = (
                Creditor.objects.using(db_alias)
                .filter(supplier_number=str(sup_val))
                .first()
            )
            if sup:
                defaults["supplier"] = sup

    if "tax_code" in defaults:
        tc_val = defaults.pop("tax_code")
        if tc_val:
            try:
                defaults["tax_code"] = TaxCode.objects.using(db_alias).get(
                    code=int(tc_val)
                )
            except (TaxCode.DoesNotExist, ValueError, TypeError):
                pass  # Leave unset if not found

    return _uoc(
        StockItem.objects.using(db_alias),
        {"stock_code": stock_code},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_department_record(db_alias, record, mode, schema_name=None, **_):
    dept_number = record.get("number")
    # `number` is in INTEGER_FIELDS, so _parse_value() always hands back an
    # int (or None if the row had no value at all) - never a string. A
    # falsy check here also skips a legitimately-numbered "department 0"
    # (common in legacy DBF data as the default/uncategorized department),
    # silently leaving it out of SalesDepartment. Anything that references
    # it later (e.g. stock items) then can't resolve the FK.
    if dept_number is None:
        return "skipped"

    dept_name = record.get("name")
    defaults = {k: v for k, v in record.items() if k != "number" and v is not None}

    # SalesDepartment has BOTH number AND name as unique fields.
    # We need to check for existing department by name first to avoid
    # unique constraint violation on the name field.
    manager = SalesDepartment.objects.using(db_alias)

    if dept_name:
        # Check if a department with this name already exists
        existing_by_name = manager.filter(name=dept_name).first()
        if existing_by_name:
            # If found by name but different number, update or skip based on mode
            if existing_by_name.number != int(dept_number):
                if mode == "create_only":
                    return "skipped"
                # Update the existing department (by name)
                existing_by_name.number = int(dept_number)
                for key, value in defaults.items():
                    setattr(existing_by_name, key, value)
                existing_by_name.save(using=db_alias)
                return "updated"

    # Proceed with normal lookup by number
    return _uoc(
        manager, {"number": dept_number}, defaults, mode, schema_name=schema_name
    )


def _resolve_debtor(db_alias, dno_val):
    """Resolve a DNO integer value to a Debtor instance."""
    if not dno_val:
        raise ValueError("DNO (debtor) is required")
    try:
        return Debtor.objects.using(db_alias).get(dno=int(dno_val))
    except (Debtor.DoesNotExist, ValueError, TypeError) as e:
        raise ValueError(f"Debtor '{dno_val}' not found: {e}")


def _resolve_creditor(db_alias, sup_val):
    """Resolve a SUPNO value to a Creditor instance."""
    if not sup_val:
        raise ValueError("SUPNO (creditor) is required")
    try:
        return Creditor.objects.using(db_alias).get(supplier_number=str(sup_val))
    except (Creditor.DoesNotExist, ValueError, TypeError) as e:
        raise ValueError(f"Creditor '{sup_val}' not found: {e}")


def _import_debtran_record(db_alias, record, mode, schema_name=None, **_):
    """debtran.csv AND dtran.csv → DebtorTransaction."""
    tran_no = record.get("transaction_number")
    debtor = _resolve_debtor(db_alias, record.get("debtor"))
    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("transaction_number", "debtor") and v is not None
    }
    defaults.setdefault("source_type", "IMPORT")
    defaults.setdefault("status", "posted")
    return _uoc(
        DebtorOpenItem.objects.using(db_alias),
        {"debtor": debtor, "transaction_number": tran_no},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_debtopen_record(db_alias, record, mode, schema_name=None, **_):
    """debtopen.csv → DebtorOpenItem."""
    tran_no = record.get("transaction_number")
    debtor = _resolve_debtor(db_alias, record.get("debtor"))
    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("transaction_number", "debtor") and v is not None
    }
    return _uoc(
        DebtorOpenItem.objects.using(db_alias),
        {"debtor": debtor, "transaction_number": tran_no},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_debtoaud_record(db_alias, record, mode, schema_name=None, **_):
    """debtoaud.csv → DebtorAudit."""
    tran_no = record.get("transaction_number")
    audit_date = record.get("audit_date")
    debtor = _resolve_debtor(db_alias, record.get("debtor"))
    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("transaction_number", "audit_date", "debtor") and v is not None
    }
    return _uoc(
        DebtorAudit.objects.using(db_alias),
        {"debtor": debtor, "transaction_number": tran_no, "audit_date": audit_date},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_dpdc_record(db_alias, record, mode, schema_name=None, **_):
    """dpdc.csv → Dpdc. FK field on model is named 'dno'."""
    cheque_date = record.get("date")
    debtor = _resolve_debtor(db_alias, record.get("dno"))
    defaults = {
        k: v for k, v in record.items() if k not in ("dno", "date") and v is not None
    }
    return _uoc(
        Dpdc.objects.using(db_alias),
        {"dno": debtor, "date": cheque_date},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_suptran_record(db_alias, record, mode, schema_name=None, **_):
    """suptran.csv → SupplierLedgerEntry."""
    tran_no = record.get("transaction_number")
    creditor = _resolve_creditor(db_alias, record.get("creditor"))
    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("transaction_number", "creditor") and v is not None
    }
    return _uoc(
        SupplierLedgerEntry.objects.using(db_alias),
        {"creditor": creditor, "transaction_number": tran_no},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_supopen_record(db_alias, record, mode, schema_name=None, **_):
    """supopen.csv → CreditorOpenItem with is_legacy=True."""
    tran_no = record.get("transaction_number")
    tran_type = record.get("transaction_type", "")
    creditor = _resolve_creditor(db_alias, record.get("creditor"))
    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("transaction_number", "transaction_type", "creditor")
        and v is not None
    }
    defaults["is_legacy"] = True  # skip typed-FK validation in clean()
    return _uoc(
        CreditorOpenItem.objects.using(db_alias),
        {
            "creditor": creditor,
            "transaction_number": tran_no,
            "transaction_type": tran_type,
        },
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_supoaud_record(db_alias, record, mode, schema_name=None, **_):
    """supoaud.csv → OpenItemAudit."""
    tran_no = record.get("transaction_number")
    creditor = _resolve_creditor(db_alias, record.get("creditor"))
    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("transaction_number", "creditor") and v is not None
    }
    return _uoc(
        OpenItemAudit.objects.using(db_alias),
        {"creditor": creditor, "transaction_number": tran_no},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_supcrmas_record(db_alias, record, mode, schema_name=None, **_):
    """supcrmas.csv → RFC."""
    rfc_no = str(record.get("rfc_number", ""))
    creditor = _resolve_creditor(db_alias, record.get("creditor"))
    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("rfc_number", "creditor") and v is not None
    }
    # return_date has no DBF source — backfill from date_sent
    if "return_date" not in defaults and defaults.get("date_sent"):
        defaults["return_date"] = defaults["date_sent"]
    defaults["creditor"] = creditor
    return _uoc(
        RFC.objects.using(db_alias),
        {"rfc_number": rfc_no},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_supcrtrn_record(db_alias, record, mode, schema_name=None, **_):
    """supcrtrn.csv → RFCLineItem."""
    rfc_val = record.get("rfc")
    stock_val = record.get("stock_item")

    try:
        rfc = RFC.objects.using(db_alias).get(rfc_number=str(rfc_val))
    except RFC.DoesNotExist:
        return "skipped"

    try:
        stock_item = StockItem.objects.using(db_alias).get(stock_code=str(stock_val))
    except StockItem.DoesNotExist:
        return "skipped"

    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("rfc", "stock_item") and v is not None
    }
    defaults["rfc"] = rfc
    defaults["stock_item"] = stock_item

    # tax_code required by model — borrow from stock item if not in CSV
    if "tax_code" not in defaults and stock_item.tax_code_id:
        defaults["tax_code"] = stock_item.tax_code

    # auto-assign line_number if missing
    if "line_number" not in defaults:
        defaults["line_number"] = (
            RFCLineItem.objects.using(db_alias).filter(rfc=rfc).count() + 1
        )

    return _uoc(
        RFCLineItem.objects.using(db_alias),
        {"rfc": rfc, "stock_item": stock_item},
        {k: v for k, v in defaults.items() if k not in ("rfc", "stock_item")},
        mode,
        schema_name=schema_name,
    )


def _import_suppo_record(db_alias, record, mode, schema_name=None, **_):
    """
    suppo.csv → SupplierPaymentOrder.
    suppo.dbf has no SUPNO — creditor is always null on legacy records.
    No unique key in DBF; use payment_date + amount + detail_line1 as composite.
    """
    pay_date = record.get("payment_date")
    amount = record.get("amount")
    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("payment_date", "amount") and v is not None
    }
    detail1 = defaults.pop("detail_line1", "")
    return _uoc(
        SupplierPaymentOrder.objects.using(db_alias),
        {"payment_date": pay_date, "amount": amount, "detail_line1": detail1},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_supexp_record(db_alias, record, mode, year=None, schema_name=None, **_):
    """
    supexp.csv → ExpenseCategoryMonthlyBalance.
    'year' is a Django-only field (no DBF source) — passed as kwarg.
    All monthly balance fields are editable=False; _uoc bypasses that via QuerySet.update().
    """
    expcat_val = record.get("expense_category")
    try:
        expense_cat = ExpenseCategory.objects.using(db_alias).get(pk=int(expcat_val))
    except (ExpenseCategory.DoesNotExist, ValueError, TypeError) as e:
        raise ValueError(f"ExpenseCategory '{expcat_val}' not found: {e}")

    defaults = {
        k: v for k, v in record.items() if k != "expense_category" and v is not None
    }
    defaults["year"] = year
    return _uoc(
        ExpenseCategoryMonthlyBalance.objects.using(db_alias),
        {"expense_category": expense_cat, "year": year},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_supexpt_record(db_alias, record, mode, schema_name=None, **_):
    """
    supexpt.csv → ExpenseCategoryTransaction.
    INVAT and TOTAL (input_vat_amount / amount_inclusive) are editable=False —
    omitted from import; they will be recalculated on next application save.
    """
    tran_no = record.get("transaction_number")
    expcat_val = record.get("expense_category")
    sup_val = record.get("creditor")

    try:
        expense_cat = ExpenseCategory.objects.using(db_alias).get(pk=int(expcat_val))
    except (ExpenseCategory.DoesNotExist, ValueError, TypeError) as e:
        raise ValueError(f"ExpenseCategory '{expcat_val}' not found: {e}")

    creditor = _resolve_creditor(db_alias, sup_val)

    defaults = {
        k: v
        for k, v in record.items()
        if k not in ("transaction_number", "expense_category", "creditor")
        and v is not None
    }
    defaults["expense_category"] = expense_cat
    defaults["creditor"] = creditor
    return _uoc(
        ExpenseCategoryTransaction.objects.using(db_alias),
        {"transaction_number": tran_no},
        defaults,
        mode,
        schema_name=schema_name,
    )


def _import_stran_record(db_alias, record, mode, schema_name=None, **_):
    """
    stran.csv → StockTransaction.

    Key differences from a simple mapping:
    - CODE → stock_item FK (required)
    - QTY → split into quantity_in / quantity_out based on transaction_type
    - TYPE → mapped via STRAN_TYPE_MAP to TRANSACTION_TYPES choices
    - DEPT → department FK (SET_NULL, optional)
    - TAXIND → tax_code FK (SET_NULL, optional)
    - DNO → debtor FK (SET_NULL, optional)
    - SUPNO → supplier FK (SET_NULL, optional)
    - COST → unit_cost, STDPRICE → unit_price, SOURCE → station_number
    """
    tran_no = record.get("transaction_number")
    stock_val = record.get("stock_item")

    if not stock_val:
        return "skipped"  # blank CODE — nothing to import
    try:
        stock_item = StockItem.objects.using(db_alias).get(stock_code=str(stock_val))
    except StockItem.DoesNotExist:
        return "skipped"  # stock not imported yet or doesn't exist

    tran_type = record.get("transaction_type", "SALE")
    defaults = {"stock_item": stock_item, "transaction_type": tran_type}

    # Split QTY into quantity_in / quantity_out
    qty_raw = record.get("_qty")
    if qty_raw is not None:
        try:
            qty = Decimal(str(qty_raw).replace(",", ""))
        except InvalidOperation:
            qty = Decimal("0")
        outbound = {"SALE", "BUNDLE_USE", "BULK_ISSUE", "LAYBYE_IN", "JOB_IN", "RFC_IN"}
        if tran_type in outbound:
            defaults["quantity_out"] = abs(qty)
            defaults["quantity_in"] = Decimal("0")
        else:
            defaults["quantity_in"] = abs(qty)
            defaults["quantity_out"] = Decimal("0")

    # Optional FK: department (SET_NULL)
    dept_val = record.get("department")
    if dept_val:
        try:
            defaults["department"] = SalesDepartment.objects.using(db_alias).get(
                number=int(dept_val)
            )
        except (SalesDepartment.DoesNotExist, ValueError):
            pass

    # Optional FK: tax_code (SET_NULL)
    tc_val = record.get("tax_code")
    if tc_val:
        try:
            defaults["tax_code"] = TaxCode.objects.using(db_alias).get(code=int(tc_val))
        except (TaxCode.DoesNotExist, ValueError):
            pass

    # Optional FK: debtor (SET_NULL)
    dno_val = record.get("debtor")
    if dno_val:
        try:
            defaults["debtor"] = Debtor.objects.using(db_alias).get(dno=int(dno_val))
        except (Debtor.DoesNotExist, ValueError):
            pass

    # Optional FK: supplier (SET_NULL)
    sup_val = record.get("supplier")
    if sup_val:
        try:
            defaults["supplier"] = Creditor.objects.using(db_alias).get(
                supplier_number=str(sup_val)
            )
        except (Creditor.DoesNotExist, ValueError):
            pass

    # Simple scalar fields
    for field in (
        "transaction_date",
        "transaction_time",
        "discount",
        "value",
        "unit_cost",
        "unit_price",
        "station_number",
        "comments",
    ):
        val = record.get(field)
        if val is not None:
            defaults[field] = val

    return _uoc(
        StockTransaction.objects.using(db_alias),
        {"transaction_number": tran_no},
        defaults,
        mode,
        schema_name=schema_name,
    )
