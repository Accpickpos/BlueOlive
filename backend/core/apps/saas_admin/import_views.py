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
from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.db import connections, transaction
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection
from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current

# Master data models
from apps.debtors.models import Debtor
from apps.creditors.models import Creditor
from apps.stock_control.models import StockItem, StockTransaction
from apps.settings.models import SalesDepartment, TaxCode, ExpenseCategory

# Debtor transaction models
from apps.debtors.models import (
    DebtorTransaction,
    DebtorOpenItem,
    DebtorAudit,
    Dpdc,
)

# Creditor/supplier transaction models
from apps.creditors.models import (
    SupplierLedgerEntry,
    CreditorOpenItem,
    OpenItemAudit,
    RFC,
    RFCLineItem,
    SupplierPaymentOrder,
    ExpenseCategoryMonthlyBalance,
    ExpenseCategoryTransaction,
)


# ============================================================
# CSV → model field maps
# Only columns that map to writable fields are listed here.
# FK columns are resolved inside each _import_*_record().
# ============================================================

DEBTOR_CSV_TO_MODEL_FIELD_MAP = {
    'DNO':        'customer_number',
    'DNAME':      'name',
    'DSNAME':     'short_name',
    'DCONTACT':   'contact_person',
    'DTEL':       'phone',
    'TEL2':       'phone2',
    'DFAX':       'fax',
    'EMAIL':      'email',
    'DADD1':      'address_line1',
    'DADD2':      'address_line2',
    'DADD3':      'address_line3',
    'DPCODE':     'postal_code',
    'DELAD1':     'delivery_address1',
    'DELAD2':     'delivery_address2',
    'DELAD3':     'delivery_address3',
    'DELAD4':     'delivery_address4',
    'DTAXNO':     'tax_number',
    'VATREF':     'vat_reference',
    'DAREA':      'area_code',
    'DBALBFWD':   'balance_brought_forward',
    'DCRNT':      'balance_current',
    'D30':        'balance_30_days',
    'D60':        'balance_60_days',
    'D90':        'balance_90_days',
    'D120':       'balance_120_days',
    'D150':       'balance_150_days',
    'D180':       'balance_180_days',
    'DSALESM':    'sales_month',
    'DSALESY':    'sales_year',
    'DPROFITM':   'profit_month',
    'DPROFITY':   'profit_year',
    'DAMTLPD':    'last_payment_amount',
    'DDATLPD':    'last_payment_date',
    'DATEOPENED': 'date_opened',
    'DDISCPER':   'discount_percentage',
    'DCLIMIT':    'credit_limit',
    'DINTFLAG':   'interest_flag',
    'PRICE':      'price_level',
    'ACCTYPE':    'account_type',
    'TERMS':      'payment_terms',
    'PDISC':      'prompt_payment_discount',
    'DISCPRN':    'discount_printable',
    'DPOSBAL':    'positive_balance_only',
    'BLOCKFLAG':  'block_flag',
    'NOTES':      'notes',
}

CREDITOR_CSV_TO_MODEL_FIELD_MAP = {
    'SUPNO':      'supplier_number',
    'SUPNAME':    'name',
    'SUPCONT':    'contact_person',
    'SUPTEL':     'telephone',
    'SUPFAX':     'fax',
    'EMAIL':      'email',
    'SUPADD1':    'physical_address_line1',
    'SUPADD2':    'physical_address_line2',
    'SUPADD3':    'physical_address_line3',
    'SUPPADD1':   'postal_address_line1',
    'SUPPADD2':   'postal_address_line2',
    'SUPPADD3':   'postal_address_line3',
    'SUPOURACC':  'our_account_number',
    'SUPTERMS':   'payment_terms_days',
    'ACCTYPE':    'account_category',
    'SUPDISC':    'prompt_payment_discount_percent',
    'BANK':       'bank_name',
    'BANKCODE':   'branch_code',
    'BANKACC':    'account_number',
    'SUPBALBFWD': 'balance_brought_forward',
    'SUPCRNT':    'balance_current',
    'SUP30':      'balance_30_days',
    'SUP60':      'balance_60_days',
    'SUP90':      'balance_90_days',
    'SUP120':     'balance_120_days',
    'SUP150':     'balance_150_days',
    'SUPPMT':     'last_paid_amount',
    'SUPPMTDATE': 'last_paid_date',
    'SUPURCHMTD': 'purchases_mtd',
    'SUPURCHYTD': 'purchases_ytd',
    'UPDSTKSP':   'update_selling_price_on_receipt',
}

STOCK_CSV_TO_MODEL_FIELD_MAP = {
    'CODE':        'stock_code',
    'DESCRIP':     'description',
    'DEPT':        'department',       # FK resolved in _import_stock_record
    'SUPNO':       'supplier',         # FK resolved in _import_stock_record
    'SUPCODE':     'supplier_code',
    'TAXCODE':     'tax_code',         # FK resolved in _import_stock_record
    'CPRICE':      'cost_price',
    'AVGCOST':     'average_cost',
    'SPRICE':      'selling_price_1',
    'SPRICE1':     'selling_price_2',
    'SPRICE2':     'selling_price_3',
    'MARKUP':      'markup_1',
    'MARKUP1':     'markup_2',
    'MARKUP2':     'markup_3',
    'QOH':         'quantity_on_hand',
    'QTYBYSTOCK':  'quantity_allocated',
    'QTYSORD':     'quantity_sale_order',
    'REORDERQTY':  'reorder_quantity',
    'QTYONORDER':  'quantity_on_order',
    'DEFAULTQTY':  'default_selling_quantity',
    'ALLOWNEG':    'allow_negative_quantities',
    'MAXDISC':     'maximum_discount_percent',
    'SALESMTDQ':   'sales_mtd_quantity',
    'SALESMTDV':   'sales_mtd_value',
    'SALESYTDQ':   'sales_ytd_quantity',
    'SALESYTDV':   'sales_ytd_value',
    'GPMTD':       'gross_profit_mtd',
    'GPYTD':       'gross_profit_ytd',
    'PURMTDQ':     'purchased_mtd_quantity',
    'PURYTDQ':     'purchased_ytd_quantity',
    'BALBFWDQ':    'balance_bfwd_quantity',
    'BALBFWDV':    'balance_bfwd_value',
    'CLOSING':     'closing_stock_balance',
    'LASTPUDATE':  'date_last_purchased',
    'LASTSOLDATE': 'date_last_sold',
    'BIN':         'bin_number',
    'WEIGHT':      'weight',
    'STKCNTFLAG':  'stock_count_flag',
    'ACTIVE':      'is_active',
}

DEPARTMENT_CSV_TO_MODEL_FIELD_MAP = {
    'DEPT':       'number',
    'DEPTNAME':   'name',
    'SLSMTD':     'sales_mtd',
    'SLSYTD':     'sales_ytd',
}

# debtran.csv AND dtran.csv both map to DebtorTransaction.
# dtran has fewer columns (no STATION/VATREF) but the same model.
# DNO resolves to debtor FK in _import_debtran_record.
# DEL1-4 map to description_line1-4 (NOT delivery_address).
# SOURCE maps to source_station (NOT source).
# DTAXSTAT maps to vat_status (NOT tax_status).
DEBTRAN_CSV_TO_MODEL_FIELD_MAP = {
    'DNO':      'debtor',              # FK — customer_number lookup
    'DTRANO':   'transaction_number',
    'DTDATE':   'transaction_date',
    'TIME':     'transaction_time',
    'DTYPE':    'transaction_type',
    'DTSUB':    'subtotal',
    'DTGST':    'vat_amount',
    'DTTOT':    'total_amount',
    'DTAXSTAT': 'vat_status',
    'SOURCE':   'source_station',
    'ORDNO':    'order_number',
    'CUSTREF':  'customer_reference',
    'DEL1':     'description_line1',
    'DEL2':     'description_line2',
    'DEL3':     'description_line3',
    'DEL4':     'description_line4',
    'STATION':  'station',
    'VATREF':   'vat_reference',
}

# debtopen.csv → DebtorOpenItem
# TOTAL maps to original_amount (the model field name), NOT total_amount.
# AGEFLAG is CharField '0'-'4', not integer.
DEBTOPEN_CSV_TO_MODEL_FIELD_MAP = {
    'DNO':        'debtor',            # FK — customer_number lookup
    'DTRANO':     'transaction_number',
    'TYPE':       'transaction_type',
    'DATE':       'transaction_date',
    'TOTAL':      'original_amount',
    'BALANCEDUE': 'balance_due',
    'AGEFLAG':    'age_flag',
    'POSTED':     'posted',
}

# debtoaud.csv → DebtorAudit
# THISTYPE → current_type. THISTRAN → current_transaction.
DEBTOAUD_CSV_TO_MODEL_FIELD_MAP = {
    'DNO':      'debtor',              # FK — customer_number lookup
    'DTRANO':   'transaction_number',
    'TYPE':     'transaction_type',
    'THISTYPE': 'current_type',
    'THISTRAN': 'current_transaction',
    'DATE':     'audit_date',
    'AMOUNT':   'amount',
}

# dpdc.csv → Dpdc
# The FK field on Dpdc is named 'dno', not 'debtor'.
DPDC_CSV_TO_MODEL_FIELD_MAP = {
    'DNO':    'dno',                   # FK — customer_number lookup
    'DATE':   'date',
    'AMOUNT': 'amount',
    'STATUS': 'status',
}

# suptran.csv → SupplierLedgerEntry (direct 1:1 DBF mapping, no validation on save)
SUPTRAN_CSV_TO_MODEL_FIELD_MAP = {
    'SUPNO':    'creditor',            # FK — supplier_number lookup
    'STRANO':   'transaction_number',
    'STDATE':   'transaction_date',
    'SDUEDATE': 'due_date',
    'STYPE':    'transaction_type',
    'STSUB':    'subtotal',
    'STGST':    'vat_amount',
    'STTOT':    'total_amount',
    'STREF':    'reference',
    'GRNNO':    'grn_number',
    'STATION':  'station',
    'USER':     'created_by_user',
}

# supopen.csv → CreditorOpenItem (is_legacy=True skips FK link validation)
# TOTAL → original_amount. AGEFLAG → ageing_flag (CharField).
SUPOPEN_CSV_TO_MODEL_FIELD_MAP = {
    'SUPNO':      'creditor',          # FK — supplier_number lookup
    'TRANO':      'transaction_number',
    'TYPE':       'transaction_type',
    'DATE':       'transaction_date',
    'TOTAL':      'original_amount',
    'BALANCEDUE': 'balance_due',
    'AGEFLAG':    'ageing_flag',
}

# supoaud.csv → OpenItemAudit
# THISTYPE → this_transaction_type. THISTRAN → this_transaction_number (IntegerField).
SUPOAUD_CSV_TO_MODEL_FIELD_MAP = {
    'SUPNO':    'creditor',            # FK — supplier_number lookup
    'TRANO':    'transaction_number',
    'TYPE':     'transaction_type',
    'THISTYPE': 'this_transaction_type',
    'THISTRAN': 'this_transaction_number',
    'DATE':     'transaction_date',
    'AMOUNT':   'amount',
}

# supcrmas.csv → RFC
# STATUS: DBF A/C/R/X → Django PE/CR/RE/CA (mapped in RFC_STATUS_MAP).
# return_date is not in DBF — set from date_sent in record fn.
SUPCRMAS_CSV_TO_MODEL_FIELD_MAP = {
    'RFCNO':    'rfc_number',
    'SUPNO':    'creditor',            # FK — supplier_number lookup
    'DATESENT': 'date_sent',
    'DATERETN': 'date_returned',
    'STATUS':   'status',              # mapped via RFC_STATUS_MAP
}

# supcrtrn.csv → RFCLineItem
# RFCNO → rfc FK. CODE → stock_item FK.
# QTY → quantity_stock. VAL → line_value. COMMENT → reason.
SUPCRTRN_CSV_TO_MODEL_FIELD_MAP = {
    'RFCNO':     'rfc',                # FK — rfc_number lookup
    'TYPE':      'original_transaction_type',
    'CODE':      'stock_item',         # FK — stock_code lookup
    'DATE':      'rfc_line_date',
    'TIME':      'rfc_line_time',
    'QTY':       'quantity_stock',
    'VAL':       'line_value',
    'QTYRFC':    'quantity_returned',
    'QTYCRED':   'quantity_credited',
    'COMMENT':   'reason',
    'PURCHDATE': 'original_transaction_date',
    'SUPREFNO':  'supplier_reference_number',
}

# suppo.csv → SupplierPaymentOrder
# No SUPNO in DBF — creditor is always null on legacy records.
SUPPO_CSV_TO_MODEL_FIELD_MAP = {
    'DATE':    'payment_date',
    'AMOUNT':  'amount',
    'DETAIL1': 'detail_line1',
    'DETAIL2': 'detail_line2',
    'DETAIL3': 'detail_line3',
}

# supexp.csv → ExpenseCategoryMonthlyBalance
# EXPCAT → expense_category FK. All EXP1-12 / EXPMTD fields are editable=False
# on the model but we write them anyway via _uoc (QuerySet.update bypass).
# 'year' is Django-only — passed as extra kwarg to import fn.
SUPEXP_CSV_TO_MODEL_FIELD_MAP = {
    'EXPCAT':     'expense_category',  # FK — pk lookup
    'EXPCATNAME': 'expense_category_name',
    'EXPMTD':     'expense_mtd',
    'EXPINVAT':   'input_vat_mtd',
    'EXP1':       'exp_month_1',
    'EXP2':       'exp_month_2',
    'EXP3':       'exp_month_3',
    'EXP4':       'exp_month_4',
    'EXP5':       'exp_month_5',
    'EXP6':       'exp_month_6',
    'EXP7':       'exp_month_7',
    'EXP8':       'exp_month_8',
    'EXP9':       'exp_month_9',
    'EXP10':      'exp_month_10',
    'EXP11':      'exp_month_11',
    'EXP12':      'exp_month_12',
}

# supexpt.csv → ExpenseCategoryTransaction
# EXPCAT → expense_category FK. SUPNO → creditor FK.
# INVAT and TOTAL are editable=False (system-calculated) — excluded from import.
SUPEXPT_CSV_TO_MODEL_FIELD_MAP = {
    'EXPCAT': 'expense_category',      # FK — pk lookup
    'DATE':   'transaction_date',
    'TRANO':  'transaction_number',
    'SUPNO':  'creditor',              # FK — supplier_number lookup
    'VALUE':  'amount_exclusive',
    'SOURCE': 'source_type',
    'GRNNO':  'grn_number',
    'TAXIND': 'tax_indicator',
}

# stran.csv → StockTransaction
# CODE → stock_item FK. DEPT → department FK. TAXIND → tax_code FK.
# DNO → debtor FK (optional). SUPNO → supplier FK (optional).
# QTY → split into quantity_in/quantity_out based on transaction_type.
# TYPE legacy codes mapped via STRAN_TYPE_MAP.
# COST → unit_cost. STDPRICE → unit_price. SOURCE → station_number.
STRAN_CSV_TO_MODEL_FIELD_MAP = {
    'TRANO':    'transaction_number',
    'CODE':     'stock_item',          # FK — stock_code lookup
    'QTY':      '_qty',                # special — split in _import_stran_record
    'DISCOUNT': 'discount',
    'VAL':      'value',
    'TYPE':     'transaction_type',   # mapped via STRAN_TYPE_MAP
    'DATE':     'transaction_date',
    'TIME':     'transaction_time',
    'DEPT':     'department',          # FK — SalesDepartment number lookup
    'COST':     'unit_cost',
    'TAXIND':   'tax_code',           # FK — TaxCode code lookup
    'SOURCE':   'station_number',
    'DNO':      'debtor',             # FK — customer_number lookup (optional)
    'SUPNO':    'supplier',           # FK — supplier_number lookup (optional)
    'COMMENTS': 'comments',
    'STDPRICE': 'unit_price',
}

# Legacy STRAN TYPE codes → StockTransaction.TRANSACTION_TYPES choices
STRAN_TYPE_MAP = {
    'SI': 'INCOMING',    'IN': 'INCOMING',
    'SO': 'SALE',        'SA': 'SALE',
    'SR': 'SALE_RETURN', 'RT': 'RETURN',
    'AD': 'ADJUSTMENT',  'ST': 'STOCK_TAKE',
    'MN': 'MANUFACTURE', 'BU': 'BUNDLE_USE',
    'BI': 'BULK_ISSUE',  'LI': 'LAYBYE_IN',
    'LO': 'LAYBYE_OUT',  'JI': 'JOB_IN',
    'JO': 'JOB_OUT',     'RI': 'RFC_IN',
    'RO': 'RFC_OUT',
}

# RFC STATUS: DBF single-char → Django choices
RFC_STATUS_MAP = {
    'A': 'PE', 'C': 'CR', 'R': 'RE', 'X': 'CA',
    # Pass-through if already mapped
    'PE': 'PE', 'CR': 'CR', 'RE': 'RE', 'CA': 'CA',
}


# ============================================================
# Field type sets — drive _parse_value() type conversions
# ============================================================

DECIMAL_FIELDS = {
    # Debtor
    'balance_brought_forward', 'balance_current', 'balance_30_days',
    'balance_60_days', 'balance_90_days', 'balance_120_days',
    'balance_150_days', 'balance_180_days', 'sales_month', 'sales_year',
    'profit_month', 'profit_year', 'last_payment_amount',
    'discount_percentage', 'credit_limit', 'prompt_payment_discount',
    # Creditor
    'total_outstanding_balance', 'last_paid_amount', 'purchases_mtd',
    'purchases_ytd', 'prompt_payment_discount_percent',
    # Stock
    'cost_price', 'average_cost', 'selling_price_1', 'selling_price_2',
    'selling_price_3', 'markup_1', 'markup_2', 'markup_3',
    'quantity_on_hand', 'quantity_allocated', 'quantity_sale_order',
    'quantity_counted', 'reorder_quantity', 'quantity_on_order',
    'default_selling_quantity', 'maximum_discount_percent',
    'sales_mtd_quantity', 'sales_mtd_value', 'sales_ytd_quantity',
    'sales_ytd_value', 'gross_profit_mtd', 'gross_profit_ytd',
    'purchased_mtd_quantity', 'purchased_ytd_quantity',
    'balance_bfwd_quantity', 'balance_bfwd_value', 'closing_stock_balance',
    'weight',
    # Department
    'sales_mtd',
    'sales_month_1', 'sales_month_2', 'sales_month_3', 'sales_month_4',
    'sales_month_5', 'sales_month_6', 'sales_month_7', 'sales_month_8',
    'sales_month_9', 'sales_month_10', 'sales_month_11', 'sales_month_12',
    # DebtorTransaction
    'subtotal', 'vat_amount', 'total_amount',
    # DebtorOpenItem / CreditorOpenItem
    'original_amount', 'balance_due',
    # DebtorAudit / OpenItemAudit / Dpdc / SupplierPaymentOrder
    'amount',
    # RFC / RFCLineItem
    'line_value', 'quantity_returned', 'quantity_credited', 'quantity_stock',
    # ExpenseCategoryMonthlyBalance
    'expense_mtd', 'input_vat_mtd',
    'exp_month_1', 'exp_month_2', 'exp_month_3', 'exp_month_4',
    'exp_month_5', 'exp_month_6', 'exp_month_7', 'exp_month_8',
    'exp_month_9', 'exp_month_10', 'exp_month_11', 'exp_month_12',
    # ExpenseCategoryTransaction
    'amount_exclusive',
    # StockTransaction / SupplierLedgerEntry
    'discount', 'value', 'unit_cost', 'unit_price',
}

INTEGER_FIELDS = {
    'customer_number', 'area_code', 'price_level', 'payment_terms',
    'payment_terms_days',
    # Department
    'number',
    # StockTransaction
    'transaction_number', 'station_number',
    # SupplierLedgerEntry / ExpenseCategoryTransaction
    'grn_number',
    # OpenItemAudit (THISTRAN N(6))
    'this_transaction_number',
    # ExpenseCategoryTransaction
    'tax_indicator',
    # StockItem
    'bin_number', 'station_number',
}

DATE_FIELDS = {
    'last_payment_date', 'last_paid_date', 'date_opened',
    'date_last_purchased', 'date_last_sold',
    'transaction_date', 'audit_date',
    'date', 'due_date',
    'date_sent', 'date_returned',
    'rfc_line_date', 'original_transaction_date',
    'payment_date',
}

# CharField Y/N fields
YN_FIELDS = {
    'interest_flag', 'discount_printable', 'positive_balance_only',
    'serial_tracking', 'charge_scrap', 'posted',
}

# Python bool fields
BOOL_FIELDS = {
    'update_selling_price_on_receipt', 'allow_negative_quantities', 'is_active',
}

EMAIL_FIELDS = {'email'}


# ============================================================
# Master lookup table and constants
# ============================================================

_ALL_MAPS = {
    'debtor':     DEBTOR_CSV_TO_MODEL_FIELD_MAP,
    'creditor':   CREDITOR_CSV_TO_MODEL_FIELD_MAP,
    'stock':      STOCK_CSV_TO_MODEL_FIELD_MAP,
    'department': DEPARTMENT_CSV_TO_MODEL_FIELD_MAP,
    'debtran':    DEBTRAN_CSV_TO_MODEL_FIELD_MAP,
    'debtopen':   DEBTOPEN_CSV_TO_MODEL_FIELD_MAP,
    'debtoaud':   DEBTOAUD_CSV_TO_MODEL_FIELD_MAP,
    'dpdc':       DPDC_CSV_TO_MODEL_FIELD_MAP,
    'suptran':    SUPTRAN_CSV_TO_MODEL_FIELD_MAP,
    'supopen':    SUPOPEN_CSV_TO_MODEL_FIELD_MAP,
    'supoaud':    SUPOAUD_CSV_TO_MODEL_FIELD_MAP,
    'supcrmas':   SUPCRMAS_CSV_TO_MODEL_FIELD_MAP,
    'supcrtrn':   SUPCRTRN_CSV_TO_MODEL_FIELD_MAP,
    'suppo':      SUPPO_CSV_TO_MODEL_FIELD_MAP,
    'supexp':     SUPEXP_CSV_TO_MODEL_FIELD_MAP,
    'supexpt':    SUPEXPT_CSV_TO_MODEL_FIELD_MAP,
    'stran':      STRAN_CSV_TO_MODEL_FIELD_MAP,
}

VALID_MODEL_TYPES = set(_ALL_MAPS.keys())

# The field that uniquely identifies each record, used to validate mappings
REQUIRED_FIELD_MAP = {
    'debtor':     'customer_number',
    'creditor':   'supplier_number',
    'stock':      'stock_code',
    'department': 'number',
    'debtran':    'transaction_number',
    'debtopen':   'transaction_number',
    'debtoaud':   'transaction_number',
    'dpdc':       'dno',
    'suptran':    'transaction_number',
    'supopen':    'transaction_number',
    'supoaud':    'transaction_number',
    'supcrmas':   'rfc_number',
    'supcrtrn':   'rfc',
    'suppo':      'payment_date',
    'supexp':     'expense_category',
    'supexpt':    'transaction_number',
    'stran':      'transaction_number',
}


# ============================================================
# Helpers
# ============================================================

def _detect_delimiter(text):
    first_line = text.split('\n')[0]
    if ';' in first_line and first_line.count(';') > first_line.count(','):
        return ';'
    return ','


def _parse_value(value, field_name):
    """Convert a raw CSV string to the correct Python type for the given model field."""
    if value is None:
        return None
    value = str(value).strip()

    if value == '' or value.upper() == 'N/A':
        if field_name in DECIMAL_FIELDS: return Decimal('0.00')
        if field_name in INTEGER_FIELDS: return 0
        if field_name in DATE_FIELDS:    return None
        if field_name in YN_FIELDS:      return 'N'
        if field_name in BOOL_FIELDS:    return False
        if field_name in EMAIL_FIELDS:   return ''
        if field_name == 'block_flag':   return '0'
        return ''

    if field_name in INTEGER_FIELDS:
        try:    return int(float(value))
        except: return 0

    if field_name in DECIMAL_FIELDS:
        try:    return Decimal(value.replace(',', ''))
        except: return Decimal('0.00')

    if field_name in DATE_FIELDS:
        for fmt in ('%Y/%m/%d', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:    return datetime.strptime(value, fmt).date()
            except: continue
        return None

    if field_name in YN_FIELDS:
        return 'Y' if value.upper() in ('Y', 'YES', 'TRUE', '1') else 'N'

    if field_name in BOOL_FIELDS:
        return value.upper() in ('Y', 'YES', 'TRUE', '1')

    if field_name in EMAIL_FIELDS:
        return value.lower() if '@' in value and '.' in value.split('@')[-1] else ''

    if field_name == 'block_flag':
        if value in ('0', '1', '2', '3', 'Y', 'N'): return value
        if value.upper() in ('YES', 'TRUE'):          return 'Y'
        return '0'

    if field_name == 'account_type':
        v = value.upper().strip()
        return v if v in ('', 'O', 'C', 'N', 'B') else ''

    if field_name == 'account_category':
        v = value.upper().strip()
        return v if v in ('BBF', 'OI', '') else 'BBF'

    if field_name == 'vat_status':
        v = value.upper().strip()
        return v if v in ('S', 'E', 'Z') else 'S'

    if field_name == 'age_flag':
        v = str(value).strip()
        return v if v in ('0', '1', '2', '3', '4') else '0'

    if field_name == 'transaction_type':
        upper = value.upper()
        return STRAN_TYPE_MAP.get(upper, value)

    if field_name == 'status':
        return RFC_STATUS_MAP.get(value.upper(), value)

    if field_name == 'rfc_line_time':
        return value[:5] if value else ''

    return value


def _set_schema_context(tenant, shop):
    register_tenant_connection(tenant, shop=shop)
    db_alias = tenant.db_alias
    set_current_tenant(tenant)
    set_current_shop(shop.schema_name)
    return db_alias


def _apply_search_path(db_alias, schema_name):
    conn = connections[db_alias]
    with conn.cursor() as cursor:
        cursor.execute(f"SET search_path TO {schema_name}, public")


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

def _uoc(manager, lookup, defaults, mode):
    """
    Safe update_or_create that bypasses model.save() validation.
    - create path: Model(**lookup, **defaults).save() — skips full_clean
      by NOT calling the model's save() override; uses super().save() directly
      via bulk_create of a single object (which skips all save() overrides).
    - update path: QuerySet.update(**defaults) — pure SQL, no Python hooks.
    """
    from django.db import IntegrityError
    
    if mode == 'create_only':
        if manager.filter(**lookup).exists():
            return 'skipped'
        # bulk_create bypasses all save() overrides including full_clean()
        try:
            obj = manager.model(**lookup, **defaults)
            manager.bulk_create([obj])
            return 'created'
        except IntegrityError:
            # Record was created by another process between check and create
            return 'skipped'

    elif mode == 'update_only':
        rows = manager.filter(**lookup).update(**defaults)
        return 'updated' if rows else 'skipped'

    else:  # create_or_update
        qs = manager.filter(**lookup)
        if qs.exists():
            qs.update(**defaults)
            return 'updated'
        else:
            try:
                obj = manager.model(**lookup, **defaults)
                manager.bulk_create([obj])
                return 'created'
            except IntegrityError:
                # Record was created by another process between check and create
                # Try to update instead
                rows = manager.filter(**lookup).update(**defaults)
                return 'updated' if rows else 'skipped'


# ============================================================
# API Views — SaaS Admin only (superuser)
# ============================================================

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_tenants_and_shops(request):
    """
    Return all tenants with their shops for the import UI dropdown.
    GET /api/v1/saas-admin/import/tenants/
    """
    tenants = Tenant.objects.filter(is_active=True).order_by('name')
    data = []
    for t in tenants:
        shops = Shop.objects.filter(tenant=t, is_active=True).order_by('name')
        data.append({
            'id': t.id,
            'name': t.name,
            'slug': t.slug,
            'shops': [
                {'id': s.id, 'name': s.name, 'code': s.code, 'schema_name': s.schema_name}
                for s in shops
            ],
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def analyze_csv(request):
    """
    Upload and analyze a CSV file — return headers, sample rows, and suggested mappings.
    POST /api/v1/saas-admin/import/analyze/
    Body: multipart/form-data  'file' + optional 'model_type'
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    file_obj = request.FILES['file']
    if not file_obj.name.lower().endswith('.csv'):
        return Response({'error': 'Only CSV files are supported'}, status=status.HTTP_400_BAD_REQUEST)

    model_type = request.data.get('model_type', 'debtor').lower()
    if model_type not in VALID_MODEL_TYPES:
        return Response(
            {'error': f'Invalid model_type. Must be one of: {", ".join(sorted(VALID_MODEL_TYPES))}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        file_obj.seek(0)
        text = file_obj.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return Response({'error': f'Cannot read file: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    delimiter = _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    try:
        headers = [h.strip() for h in next(reader)]
    except StopIteration:
        return Response({'error': 'File is empty'}, status=status.HTTP_400_BAD_REQUEST)

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

    return Response({
        'headers': headers,
        'total_rows': total_rows,
        'sample_rows': sample_rows,
        'suggested_mappings': suggested,
        'available_model_fields': _get_available_fields(model_type),
        'delimiter': delimiter,
        'model_type': model_type,
    })


@api_view(['POST'])
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
    file_obj     = request.FILES.get('file')
    tenant_id    = request.data.get('tenant_id')
    shop_id      = request.data.get('shop_id')
    mappings_json = request.data.get('mappings', '{}')
    model_type   = request.data.get('model_type', 'debtor').lower()
    mode         = request.data.get('mode', 'create_or_update')
    import_year  = request.data.get('year')

    if not file_obj:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    if model_type not in VALID_MODEL_TYPES:
        return Response(
            {'error': f'Invalid model_type. Must be one of: {", ".join(sorted(VALID_MODEL_TYPES))}'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not tenant_id or not shop_id:
        return Response({'error': 'tenant_id and shop_id are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        mappings = json.loads(mappings_json) if isinstance(mappings_json, str) else mappings_json
    except json.JSONDecodeError:
        return Response({'error': 'Invalid mappings JSON'}, status=status.HTTP_400_BAD_REQUEST)

    if not mappings:
        return Response({'error': 'Column mappings are required'}, status=status.HTTP_400_BAD_REQUEST)

    required_field = REQUIRED_FIELD_MAP[model_type]
    if required_field not in mappings.values():
        return Response(
            {'error': f'Mapping for required field "{required_field}" is missing'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if model_type == 'supexp' and not import_year:
        return Response(
            {'error': '"year" parameter is required for supexp imports'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        shop = Shop.objects.select_related('tenant').get(id=shop_id, is_active=True)
    except Shop.DoesNotExist:
        return Response({'error': f'Shop {shop_id} not found'}, status=status.HTTP_404_NOT_FOUND)

    tenant = shop.tenant
    if not tenant.is_active:
        return Response({'error': 'Tenant is not active'}, status=status.HTTP_400_BAD_REQUEST)

    db_alias = _set_schema_context(tenant, shop)
    _apply_search_path(db_alias, shop.schema_name)

    try:
        file_obj.seek(0)
        text = file_obj.read().decode('utf-8', errors='ignore')
    except Exception as e:
        clear_current()
        return Response({'error': f'Cannot read file: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    delimiter = _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    try:
        headers = [h.strip() for h in next(reader)]
    except StopIteration:
        clear_current()
        return Response({'error': 'CSV file is empty'}, status=status.HTTP_400_BAD_REQUEST)

    header_idx = {h: i for i, h in enumerate(headers)}
    for csv_col in mappings:
        if csv_col not in header_idx:
            clear_current()
            return Response(
                {'error': f"Mapped column '{csv_col}' not found in CSV headers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    dispatch = {
        'debtor':     _import_debtor_record,
        'creditor':   _import_creditor_record,
        'stock':      _import_stock_record,
        'department': _import_department_record,
        'debtran':    _import_debtran_record,
        'debtopen':   _import_debtopen_record,
        'debtoaud':   _import_debtoaud_record,
        'dpdc':       _import_dpdc_record,
        'suptran':    _import_suptran_record,
        'supopen':    _import_supopen_record,
        'supoaud':    _import_supoaud_record,
        'supcrmas':   _import_supcrmas_record,
        'supcrtrn':   _import_supcrtrn_record,
        'suppo':      _import_suppo_record,
        'supexp':     _import_supexp_record,
        'supexpt':    _import_supexpt_record,
        'stran':      _import_stran_record,
    }
    import_fn = dispatch[model_type]

    extra_kwargs = {}
    if model_type == 'supexp':
        extra_kwargs['year'] = int(import_year)

    created = updated = skipped = 0
    errors_list = []
    rows = list(reader)
    total = len(rows)

    # Progress report interval (every N rows)
    progress_interval = max(10, total // 20)  # ~20 progress updates

    def generate_progress():
        """Generator that yields progress updates as JSON lines."""
        nonlocal created, updated, skipped, errors_list
        
        # Yield initial progress
        yield json.dumps({
            'status': 'started',
            'total': total,
            'processed': 0,
            'created': 0,
            'updated': 0,
            'skipped': 0,
        }) + '\n'

        try:
            with transaction.atomic(using=db_alias):
                for row_num, row in enumerate(rows, start=2):
                    try:
                        record = {}
                        for csv_col, model_field in mappings.items():
                            idx = header_idx.get(csv_col)
                            if idx is not None and idx < len(row):
                                record[model_field] = _parse_value(row[idx], model_field)

                        required_val = record.get(required_field)
                        if required_val is None or required_val == '':
                            errors_list.append(f"Row {row_num}: Missing {required_field} — skipped")
                            skipped += 1
                            continue

                        result = import_fn(db_alias, record, mode, **extra_kwargs)

                        if result == 'created':
                            created += 1
                        elif result == 'updated':
                            updated += 1
                        else:
                            skipped += 1

                    except Exception as e:
                        errors_list.append(f"Row {row_num}: {e}")
                        if len(errors_list) > 50:
                            errors_list.append("... too many errors, stopping")
                            break

                    # Yield progress update every N rows
                    if (row_num - 1) % progress_interval == 0:
                        yield json.dumps({
                            'status': 'processing',
                            'total': total,
                            'processed': row_num - 1,
                            'created': created,
                            'updated': updated,
                            'skipped': skipped,
                        }) + '\n'

                # Yield completion status
                yield json.dumps({
                    'status': 'complete',
                    'total': total,
                    'processed': total,
                    'created': created,
                    'updated': updated,
                    'skipped': skipped,
                    'error_count': len(errors_list),
                }) + '\n'

        except Exception as e:
            yield json.dumps({
                'status': 'error',
                'message': f'Import failed: {e}',
                'errors': errors_list[:50],  # Limit errors in response
            }) + '\n'
        finally:
            clear_current()

    return StreamingHttpResponse(
        generate_progress(),
        content_type='application/x-ndjson'
    )


# ============================================================
# Record import functions
# Signature: (db_alias, record, mode, **kwargs) → 'created'|'updated'|'skipped'
# Each function resolves FKs, builds lookup + defaults dicts,
# then calls _uoc() which bypasses model.save() validation.
# ============================================================

def _import_debtor_record(db_alias, record, mode, **_):
    cust_num = record.get('customer_number')
    defaults = {k: v for k, v in record.items() if k != 'customer_number' and v is not None}
    defaults.setdefault('is_active', True)
    return _uoc(Debtor.objects.using(db_alias), {'customer_number': cust_num}, defaults, mode)


def _import_creditor_record(db_alias, record, mode, **_):
    sup_num = record.get('supplier_number')
    defaults = {k: v for k, v in record.items() if k != 'supplier_number' and v is not None}
    defaults.setdefault('is_active', True)
    return _uoc(Creditor.objects.using(db_alias), {'supplier_number': sup_num}, defaults, mode)


def _import_stock_record(db_alias, record, mode, **_):
    stock_code = record.get('stock_code')
    defaults = {k: v for k, v in record.items() if k != 'stock_code' and v is not None}
    defaults.setdefault('is_active', True)

    if 'department' in defaults:
        dept_val = defaults.pop('department')
        try:
            defaults['department'] = SalesDepartment.objects.using(db_alias).get(number=int(dept_val))
        except (SalesDepartment.DoesNotExist, ValueError, TypeError) as e:
            raise ValueError(f"Department '{dept_val}' not found: {e}")

    if 'supplier' in defaults:
        sup_val = defaults.pop('supplier')
        if sup_val:
            sup = Creditor.objects.using(db_alias).filter(supplier_number=str(sup_val)).first()
            if sup:
                defaults['supplier'] = sup

    if 'tax_code' in defaults:
        tc_val = defaults.pop('tax_code')
        if tc_val:
            try:
                defaults['tax_code'] = TaxCode.objects.using(db_alias).get(code=int(tc_val))
            except (TaxCode.DoesNotExist, ValueError, TypeError) as e:
                raise ValueError(f"TaxCode '{tc_val}' not found: {e}")

    return _uoc(StockItem.objects.using(db_alias), {'stock_code': stock_code}, defaults, mode)


def _import_department_record(db_alias, record, mode, **_):
    dept_number = record.get('number')
    if not dept_number:
        return 'skipped'
    
    dept_name = record.get('name')
    defaults = {k: v for k, v in record.items() if k != 'number' and v is not None}
    
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
                if mode == 'create_only':
                    return 'skipped'
                # Update the existing department (by name)
                existing_by_name.number = int(dept_number)
                for key, value in defaults.items():
                    setattr(existing_by_name, key, value)
                existing_by_name.save(using=db_alias)
                return 'updated'
    
    # Proceed with normal lookup by number
    return _uoc(manager, {'number': dept_number}, defaults, mode)


def _resolve_debtor(db_alias, dno_val):
    """Resolve a DNO integer value to a Debtor instance."""
    if not dno_val:
        raise ValueError("DNO (debtor) is required")
    try:
        return Debtor.objects.using(db_alias).get(customer_number=int(dno_val))
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


def _import_debtran_record(db_alias, record, mode, **_):
    """debtran.csv AND dtran.csv → DebtorTransaction."""
    tran_no = record.get('transaction_number')
    debtor  = _resolve_debtor(db_alias, record.get('debtor'))
    defaults = {
        k: v for k, v in record.items()
        if k not in ('transaction_number', 'debtor') and v is not None
    }
    defaults.setdefault('source_type', 'IMPORT')
    defaults.setdefault('status', 'posted')
    return _uoc(
        DebtorTransaction.objects.using(db_alias),
        {'debtor': debtor, 'transaction_number': tran_no},
        defaults, mode,
    )


def _import_debtopen_record(db_alias, record, mode, **_):
    """debtopen.csv → DebtorOpenItem."""
    tran_no = record.get('transaction_number')
    debtor  = _resolve_debtor(db_alias, record.get('debtor'))
    defaults = {
        k: v for k, v in record.items()
        if k not in ('transaction_number', 'debtor') and v is not None
    }
    return _uoc(
        DebtorOpenItem.objects.using(db_alias),
        {'debtor': debtor, 'transaction_number': tran_no},
        defaults, mode,
    )


def _import_debtoaud_record(db_alias, record, mode, **_):
    """debtoaud.csv → DebtorAudit."""
    tran_no    = record.get('transaction_number')
    audit_date = record.get('audit_date')
    debtor     = _resolve_debtor(db_alias, record.get('debtor'))
    defaults = {
        k: v for k, v in record.items()
        if k not in ('transaction_number', 'audit_date', 'debtor') and v is not None
    }
    return _uoc(
        DebtorAudit.objects.using(db_alias),
        {'debtor': debtor, 'transaction_number': tran_no, 'audit_date': audit_date},
        defaults, mode,
    )


def _import_dpdc_record(db_alias, record, mode, **_):
    """dpdc.csv → Dpdc. FK field on model is named 'dno'."""
    cheque_date = record.get('date')
    debtor      = _resolve_debtor(db_alias, record.get('dno'))
    defaults = {
        k: v for k, v in record.items()
        if k not in ('dno', 'date') and v is not None
    }
    return _uoc(
        Dpdc.objects.using(db_alias),
        {'dno': debtor, 'date': cheque_date},
        defaults, mode,
    )


def _import_suptran_record(db_alias, record, mode, **_):
    """suptran.csv → SupplierLedgerEntry."""
    tran_no  = record.get('transaction_number')
    creditor = _resolve_creditor(db_alias, record.get('creditor'))
    defaults = {
        k: v for k, v in record.items()
        if k not in ('transaction_number', 'creditor') and v is not None
    }
    return _uoc(
        SupplierLedgerEntry.objects.using(db_alias),
        {'creditor': creditor, 'transaction_number': tran_no},
        defaults, mode,
    )


def _import_supopen_record(db_alias, record, mode, **_):
    """supopen.csv → CreditorOpenItem with is_legacy=True."""
    tran_no   = record.get('transaction_number')
    tran_type = record.get('transaction_type', '')
    creditor  = _resolve_creditor(db_alias, record.get('creditor'))
    defaults = {
        k: v for k, v in record.items()
        if k not in ('transaction_number', 'transaction_type', 'creditor') and v is not None
    }
    defaults['is_legacy'] = True   # skip typed-FK validation in clean()
    return _uoc(
        CreditorOpenItem.objects.using(db_alias),
        {'creditor': creditor, 'transaction_number': tran_no, 'transaction_type': tran_type},
        defaults, mode,
    )


def _import_supoaud_record(db_alias, record, mode, **_):
    """supoaud.csv → OpenItemAudit."""
    tran_no  = record.get('transaction_number')
    creditor = _resolve_creditor(db_alias, record.get('creditor'))
    defaults = {
        k: v for k, v in record.items()
        if k not in ('transaction_number', 'creditor') and v is not None
    }
    return _uoc(
        OpenItemAudit.objects.using(db_alias),
        {'creditor': creditor, 'transaction_number': tran_no},
        defaults, mode,
    )


def _import_supcrmas_record(db_alias, record, mode, **_):
    """supcrmas.csv → RFC."""
    rfc_no   = str(record.get('rfc_number', ''))
    creditor = _resolve_creditor(db_alias, record.get('creditor'))
    defaults = {
        k: v for k, v in record.items()
        if k not in ('rfc_number', 'creditor') and v is not None
    }
    # return_date has no DBF source — backfill from date_sent
    if 'return_date' not in defaults and defaults.get('date_sent'):
        defaults['return_date'] = defaults['date_sent']
    defaults['creditor'] = creditor
    return _uoc(RFC.objects.using(db_alias), {'rfc_number': rfc_no}, defaults, mode)


def _import_supcrtrn_record(db_alias, record, mode, **_):
    """supcrtrn.csv → RFCLineItem."""
    rfc_val   = record.get('rfc')
    stock_val = record.get('stock_item')

    try:
        rfc = RFC.objects.using(db_alias).get(rfc_number=str(rfc_val))
    except RFC.DoesNotExist as e:
        raise ValueError(f"RFC '{rfc_val}' not found: {e}")

    try:
        stock_item = StockItem.objects.using(db_alias).get(stock_code=str(stock_val))
    except StockItem.DoesNotExist as e:
        raise ValueError(f"StockItem '{stock_val}' not found: {e}")

    defaults = {
        k: v for k, v in record.items()
        if k not in ('rfc', 'stock_item') and v is not None
    }
    defaults['rfc']        = rfc
    defaults['stock_item'] = stock_item

    # tax_code required by model — borrow from stock item if not in CSV
    if 'tax_code' not in defaults and stock_item.tax_code_id:
        defaults['tax_code'] = stock_item.tax_code

    # auto-assign line_number if missing
    if 'line_number' not in defaults:
        defaults['line_number'] = (
            RFCLineItem.objects.using(db_alias).filter(rfc=rfc).count() + 1
        )

    return _uoc(
        RFCLineItem.objects.using(db_alias),
        {'rfc': rfc, 'stock_item': stock_item},
        {k: v for k, v in defaults.items() if k not in ('rfc', 'stock_item')},
        mode,
    )


def _import_suppo_record(db_alias, record, mode, **_):
    """
    suppo.csv → SupplierPaymentOrder.
    suppo.dbf has no SUPNO — creditor is always null on legacy records.
    No unique key in DBF; use payment_date + amount + detail_line1 as composite.
    """
    pay_date = record.get('payment_date')
    amount   = record.get('amount')
    defaults = {k: v for k, v in record.items() if k not in ('payment_date', 'amount') and v is not None}
    detail1  = defaults.pop('detail_line1', '')
    return _uoc(
        SupplierPaymentOrder.objects.using(db_alias),
        {'payment_date': pay_date, 'amount': amount, 'detail_line1': detail1},
        defaults, mode,
    )


def _import_supexp_record(db_alias, record, mode, year, **_):
    """
    supexp.csv → ExpenseCategoryMonthlyBalance.
    'year' is a Django-only field (no DBF source) — passed as kwarg.
    All monthly balance fields are editable=False; _uoc bypasses that via QuerySet.update().
    """
    expcat_val = record.get('expense_category')
    try:
        expense_cat = ExpenseCategory.objects.using(db_alias).get(pk=int(expcat_val))
    except (ExpenseCategory.DoesNotExist, ValueError, TypeError) as e:
        raise ValueError(f"ExpenseCategory '{expcat_val}' not found: {e}")

    defaults = {k: v for k, v in record.items() if k != 'expense_category' and v is not None}
    defaults['year'] = year
    return _uoc(
        ExpenseCategoryMonthlyBalance.objects.using(db_alias),
        {'expense_category': expense_cat, 'year': year},
        defaults, mode,
    )


def _import_supexpt_record(db_alias, record, mode, **_):
    """
    supexpt.csv → ExpenseCategoryTransaction.
    INVAT and TOTAL (input_vat_amount / amount_inclusive) are editable=False —
    omitted from import; they will be recalculated on next application save.
    """
    tran_no    = record.get('transaction_number')
    expcat_val = record.get('expense_category')
    sup_val    = record.get('creditor')

    try:
        expense_cat = ExpenseCategory.objects.using(db_alias).get(pk=int(expcat_val))
    except (ExpenseCategory.DoesNotExist, ValueError, TypeError) as e:
        raise ValueError(f"ExpenseCategory '{expcat_val}' not found: {e}")

    creditor = _resolve_creditor(db_alias, sup_val)

    defaults = {
        k: v for k, v in record.items()
        if k not in ('transaction_number', 'expense_category', 'creditor') and v is not None
    }
    defaults['expense_category'] = expense_cat
    defaults['creditor']         = creditor
    return _uoc(
        ExpenseCategoryTransaction.objects.using(db_alias),
        {'transaction_number': tran_no},
        defaults, mode,
    )


def _import_stran_record(db_alias, record, mode, **_):
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
    tran_no   = record.get('transaction_number')
    stock_val = record.get('stock_item')

    if not stock_val:
        raise ValueError("CODE (stock_item) is required for stran import")
    try:
        stock_item = StockItem.objects.using(db_alias).get(stock_code=str(stock_val))
    except StockItem.DoesNotExist as e:
        raise ValueError(f"StockItem '{stock_val}' not found: {e}")

    tran_type = record.get('transaction_type', 'SALE')
    defaults  = {'stock_item': stock_item, 'transaction_type': tran_type}

    # Split QTY into quantity_in / quantity_out
    qty_raw = record.get('_qty')
    if qty_raw is not None:
        try:
            qty = Decimal(str(qty_raw).replace(',', ''))
        except InvalidOperation:
            qty = Decimal('0')
        outbound = {'SALE', 'BUNDLE_USE', 'BULK_ISSUE', 'LAYBYE_IN', 'JOB_IN', 'RFC_IN'}
        if tran_type in outbound:
            defaults['quantity_out'] = abs(qty)
            defaults['quantity_in']  = Decimal('0')
        else:
            defaults['quantity_in']  = abs(qty)
            defaults['quantity_out'] = Decimal('0')

    # Optional FK: department (SET_NULL)
    dept_val = record.get('department')
    if dept_val:
        try:
            defaults['department'] = SalesDepartment.objects.using(db_alias).get(number=int(dept_val))
        except (SalesDepartment.DoesNotExist, ValueError):
            pass

    # Optional FK: tax_code (SET_NULL)
    tc_val = record.get('tax_code')
    if tc_val:
        try:
            defaults['tax_code'] = TaxCode.objects.using(db_alias).get(code=int(tc_val))
        except (TaxCode.DoesNotExist, ValueError):
            pass

    # Optional FK: debtor (SET_NULL)
    dno_val = record.get('debtor')
    if dno_val:
        try:
            defaults['debtor'] = Debtor.objects.using(db_alias).get(customer_number=int(dno_val))
        except (Debtor.DoesNotExist, ValueError):
            pass

    # Optional FK: supplier (SET_NULL)
    sup_val = record.get('supplier')
    if sup_val:
        try:
            defaults['supplier'] = Creditor.objects.using(db_alias).get(supplier_number=str(sup_val))
        except (Creditor.DoesNotExist, ValueError):
            pass

    # Simple scalar fields
    for field in ('transaction_date', 'transaction_time', 'discount',
                  'value', 'unit_cost', 'unit_price', 'station_number', 'comments'):
        val = record.get(field)
        if val is not None:
            defaults[field] = val

    return _uoc(
        StockTransaction.objects.using(db_alias),
        {'transaction_number': tran_no},
        defaults, mode,
    )