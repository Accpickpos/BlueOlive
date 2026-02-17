"""
SaaS Admin — Debtor CSV Import API
Imports debtor data from CSV files into a specific tenant/shop schema.
Restricted to superusers (SaaS administrators).
Supports auto-detection of column mappings for legacy DMAST CSV format.
"""
import csv
import io
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.db import connections, transaction
from django.conf import settings as django_settings
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection
from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current
from apps.debtors.models import Debtor


# ============================================================
# CSV column → Django model field mapping
# Maps legacy DMAST CSV headers to Debtor model field names
# ============================================================
CSV_TO_MODEL_FIELD_MAP = {
    'DNO': 'customer_number',
    'DNAME': 'name',
    'DSNAME': 'short_name',
    'DCONTACT': 'contact_person',
    'DTEL': 'phone',
    'TEL2': 'phone2',
    'DFAX': 'fax',
    'EMAIL': 'email',
    'DADD1': 'address_line1',
    'DADD2': 'address_line2',
    'DADD3': 'address_line3',
    'DPCODE': 'postal_code',
    'DELAD1': 'delivery_address1',
    'DELAD2': 'delivery_address2',
    'DELAD3': 'delivery_address3',
    'DELAD4': 'delivery_address4',
    'DTAXNO': 'tax_number',
    'VATREF': 'vat_reference',
    'DAREA': 'area_code',
    'DBALBFWD': 'balance_brought_forward',
    'DCRNT': 'balance_current',
    'D30': 'balance_30_days',
    'D60': 'balance_60_days',
    'D90': 'balance_90_days',
    'D120': 'balance_120_days',
    'D150': 'balance_150_days',
    'D180': 'balance_180_days',
    'DSALESM': 'sales_month',
    'DSALESY': 'sales_year',
    'DPROFITM': 'profit_month',
    'DPROFITY': 'profit_year',
    'DAMTLPD': 'last_payment_amount',
    'DDATLPD': 'last_payment_date',
    'DDISCPER': 'discount_percentage',
    'DCLIMIT': 'credit_limit',
    'DINTFLAG': 'interest_flag',
    'PRICE': 'price_level',
    'ACCTYPE': 'account_type',
    'TERMS': 'payment_terms',
    'PDISC': 'prompt_payment_discount',
    'DISCPRN': 'discount_printable',
    'DPOSBAL': 'positive_balance_only',
    'BLOCKFLAG': 'block_flag',
    'DATEOPENED': 'date_opened',
    'NOTES': 'notes',
}

# Fields that store Decimal values
DECIMAL_FIELDS = {
    'balance_brought_forward', 'balance_current', 'balance_30_days',
    'balance_60_days', 'balance_90_days', 'balance_120_days',
    'balance_150_days', 'balance_180_days', 'sales_month', 'sales_year',
    'profit_month', 'profit_year', 'last_payment_amount',
    'discount_percentage', 'credit_limit', 'prompt_payment_discount',
}

# Fields that store integers
INTEGER_FIELDS = {'customer_number', 'area_code', 'price_level', 'payment_terms'}

# Fields that store dates
DATE_FIELDS = {'last_payment_date', 'date_opened'}

# Y/N flag fields
FLAG_FIELDS = {
    'interest_flag', 'discount_printable', 'positive_balance_only',
}

# Block flag field (special handling: 0-3,Y,N)
BLOCK_FLAG_FIELD = 'block_flag'


def _detect_delimiter(text):
    """Auto-detect CSV delimiter (semicolon or comma)."""
    first_line = text.split('\n')[0]
    if ';' in first_line and first_line.count(';') > first_line.count(','):
        return ';'
    return ','


def _parse_value(value, field_name):
    """Convert a raw CSV string value to the correct Python type for the model field."""
    if value is None:
        return None

    value = str(value).strip()

    # Empty string handling
    if value == '' or value.upper() == 'N/A':
        if field_name in DECIMAL_FIELDS:
            return Decimal('0.00')
        if field_name in INTEGER_FIELDS:
            return 0 if field_name != 'customer_number' else None
        if field_name in DATE_FIELDS:
            return None
        if field_name in FLAG_FIELDS:
            return 'N'
        if field_name == BLOCK_FLAG_FIELD:
            return '0'
        return ''

    # Integer fields
    if field_name in INTEGER_FIELDS:
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0

    # Decimal fields
    if field_name in DECIMAL_FIELDS:
        try:
            return Decimal(value.replace(',', ''))
        except (InvalidOperation, ValueError):
            return Decimal('0.00')

    # Date fields  (handles YYYY/MM/DD, YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)
    if field_name in DATE_FIELDS:
        for fmt in ('%Y/%m/%d', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                return datetime.strptime(value, fmt).date()
            except (ValueError, TypeError):
                continue
        return None

    # Y/N flag fields
    if field_name in FLAG_FIELDS:
        return 'Y' if value.upper() in ('Y', 'YES', 'TRUE', '1') else 'N'

    # Block flag
    if field_name == BLOCK_FLAG_FIELD:
        if value in ('0', '1', '2', '3', 'Y', 'N'):
            return value
        if value.upper() in ('YES', 'TRUE'):
            return 'Y'
        return '0'

    # Account type
    if field_name == 'account_type':
        v = value.upper().strip()
        if v in ('', 'O', 'C', 'N', 'B'):
            return v
        return ''

    # String fields — just return trimmed
    return value


def _set_schema_context(tenant, shop):
    """
    Register tenant DB connection and set search_path to shop schema.
    Returns the db_alias to use for queries.
    """
    register_tenant_connection(tenant)
    db_alias = tenant.db_alias

    # Override search_path for the specific shop schema
    db_config = django_settings.DATABASES[db_alias]
    db_config['OPTIONS'] = {
        **db_config.get('OPTIONS', {}),
        'options': f'-c search_path="{shop.schema_name}",public -c statement_timeout=0',
    }
    connections.databases[db_alias] = db_config

    # Close existing connection so the new search_path takes effect
    if db_alias in connections:
        connections[db_alias].close()

    # Set thread-local context
    set_current_tenant(tenant)
    set_current_shop(shop.schema_name)

    return db_alias


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
                {
                    'id': s.id,
                    'name': s.name,
                    'code': s.code,
                    'schema_name': s.schema_name,
                }
                for s in shops
            ],
        })
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def analyze_csv(request):
    """
    Upload and analyze a CSV file, return headers and sample data.
    POST /api/v1/saas-admin/import/analyze/
    Body: multipart/form-data with 'file' field
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    file_obj = request.FILES['file']
    if not file_obj.name.lower().endswith('.csv'):
        return Response({'error': 'Only CSV files are supported'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        file_obj.seek(0)
        raw = file_obj.read()
        text = raw.decode('utf-8', errors='ignore')
    except Exception as e:
        return Response({'error': f'Cannot read file: {e}'}, status=status.HTTP_400_BAD_REQUEST)

    delimiter = _detect_delimiter(text)
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)

    try:
        headers = [h.strip() for h in next(reader)]
    except StopIteration:
        return Response({'error': 'File is empty'}, status=status.HTTP_400_BAD_REQUEST)

    # Build sample rows & count total
    sample_rows = []
    total_rows = 0
    for row in reader:
        total_rows += 1
        if len(sample_rows) < 5:
            sample_rows.append(row)

    # Auto-suggest mappings
    suggested = {}
    for csv_col in headers:
        upper = csv_col.upper().strip()
        if upper in CSV_TO_MODEL_FIELD_MAP:
            suggested[csv_col] = CSV_TO_MODEL_FIELD_MAP[upper]

    # All available model fields for the dropdown
    available_fields = sorted(set(CSV_TO_MODEL_FIELD_MAP.values()))

    return Response({
        'headers': headers,
        'total_rows': total_rows,
        'sample_rows': sample_rows[:5],
        'suggested_mappings': suggested,
        'available_model_fields': available_fields,
        'delimiter': delimiter,
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def import_csv(request):
    """
    Import a CSV file into the debtors table of a specific tenant/shop schema.
    SaaS admin selects tenant + shop.

    POST /api/v1/saas-admin/import/execute/
    Body (multipart/form-data):
        file        : CSV file
        tenant_id   : int
        shop_id     : int
        mappings    : JSON string  {csv_header: model_field, ...}
        mode        : 'create_or_update' (default) | 'create_only' | 'update_only'
    """
    # --- Validate inputs ---
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    tenant_id = request.data.get('tenant_id')
    shop_id = request.data.get('shop_id')
    mappings_json = request.data.get('mappings', '{}')
    mode = request.data.get('mode', 'create_or_update')

    if not tenant_id or not shop_id:
        return Response(
            {'error': 'tenant_id and shop_id are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Parse mappings
    try:
        mappings = json.loads(mappings_json) if isinstance(mappings_json, str) else mappings_json
    except json.JSONDecodeError:
        return Response({'error': 'Invalid mappings JSON'}, status=status.HTTP_400_BAD_REQUEST)

    if not mappings:
        return Response({'error': 'Column mappings are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure customer_number is mapped
    if 'customer_number' not in mappings.values():
        return Response(
            {'error': 'customer_number mapping is required (maps to DNO / account number)'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --- Resolve tenant & shop ---
    try:
        tenant = Tenant.objects.get(id=tenant_id, is_active=True)
    except Tenant.DoesNotExist:
        return Response({'error': f'Tenant {tenant_id} not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        shop = Shop.objects.get(id=shop_id, tenant=tenant, is_active=True)
    except Shop.DoesNotExist:
        return Response({'error': f'Shop {shop_id} not found for tenant'}, status=status.HTTP_404_NOT_FOUND)

    # --- Set schema context ---
    db_alias = _set_schema_context(tenant, shop)

    # --- Read CSV ---
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

    # Build header-index lookup
    header_idx = {h: i for i, h in enumerate(headers)}

    # Validate mapped columns exist
    for csv_col in mappings:
        if csv_col not in header_idx:
            clear_current()
            return Response(
                {'error': f"Mapped column '{csv_col}' not found in CSV headers"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # --- Process rows ---
    created = 0
    updated = 0
    skipped = 0
    errors_list = []

    rows = list(reader)
    total = len(rows)

    try:
        with transaction.atomic(using=db_alias):
            for row_num, row in enumerate(rows, start=2):  # row 1 is header
                try:
                    record = {}
                    for csv_col, model_field in mappings.items():
                        idx = header_idx.get(csv_col)
                        if idx is not None and idx < len(row):
                            raw_val = row[idx]
                            record[model_field] = _parse_value(raw_val, model_field)

                    # Must have customer_number
                    cust_num = record.get('customer_number')
                    if cust_num is None:
                        errors_list.append(f"Row {row_num}: Missing customer_number — skipped")
                        skipped += 1
                        continue

                    defaults = {k: v for k, v in record.items() if k != 'customer_number' and v is not None}

                    # Set is_active default
                    if 'is_active' not in defaults:
                        defaults['is_active'] = True

                    if mode == 'create_only':
                        if Debtor.objects.using(db_alias).filter(customer_number=cust_num).exists():
                            skipped += 1
                            continue
                        Debtor.objects.using(db_alias).create(customer_number=cust_num, **defaults)
                        created += 1

                    elif mode == 'update_only':
                        rows_updated = Debtor.objects.using(db_alias).filter(
                            customer_number=cust_num
                        ).update(**defaults)
                        if rows_updated:
                            updated += 1
                        else:
                            skipped += 1

                    else:  # create_or_update
                        obj, was_created = Debtor.objects.using(db_alias).update_or_create(
                            customer_number=cust_num,
                            defaults=defaults,
                        )
                        if was_created:
                            created += 1
                        else:
                            updated += 1

                except Exception as e:
                    errors_list.append(f"Row {row_num}: {str(e)}")
                    if len(errors_list) > 50:
                        errors_list.append("... too many errors, stopping")
                        break

    except Exception as e:
        clear_current()
        return Response(
            {'error': f'Import failed (transaction rolled back): {str(e)}', 'errors': errors_list},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    finally:
        clear_current()

    return Response({
        'success': True,
        'tenant': tenant.name,
        'shop': shop.name,
        'schema': shop.schema_name,
        'total_rows': total,
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'errors': errors_list,
        'message': f'Import complete: {created} created, {updated} updated, {skipped} skipped',
    })
