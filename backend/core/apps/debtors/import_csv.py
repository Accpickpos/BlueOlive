"""
Debtor CSV Import API
Imports debtor data from CSV files into a specific tenant/shop schema.
Supports auto-detection of column mappings for legacy DMAST CSV format.
"""
import csv
import io
from decimal import Decimal, InvalidOperation
from datetime import datetime

from django.db import connections, transaction
from django.conf import settings as django_settings
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection
from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current
from .models import Debtor


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


def _parse_value(value, field_name, skip_empty=True):
    """
    Convert a raw CSV string value to the correct Python type for the model field.
    If skip_empty is True and value is empty, returns None to signal it should be excluded.
    """
    if value is None:
        return None

    value = str(value).strip()

    # Empty string handling - return None if we want to skip empty fields
    if value == '' or value.upper() == 'N/A':
        if skip_empty:
            # Return None to signal this field should be excluded from the import
            return None
        
        # Legacy behavior when not skipping empty fields
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
            return 0 if not skip_empty else None

    # Decimal fields
    if field_name in DECIMAL_FIELDS:
        try:
            return Decimal(value.replace(',', ''))
        except (InvalidOperation, ValueError):
            return Decimal('0.00') if not skip_empty else None

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
        return '0' if not skip_empty else None

    # Account type - Valid values: 'O', 'C', 'N', 'B'
    if field_name == 'account_type':
        v = value.upper().strip()
        if v in ('O', 'C', 'N', 'B', ''):
            return v
        # Return None if invalid and we're skipping empty fields
        return None if skip_empty else ''

    # VAT Reference - Must be exactly 10 digits (South African format)
    if field_name == 'vat_reference':
        # Remove any non-digit characters
        digits_only = ''.join(c for c in value if c.isdigit())
        # Only accept if exactly 10 digits
        if len(digits_only) == 10:
            return digits_only
        # Skip invalid VAT numbers when skip_empty is True
        return None if skip_empty else ''

    # String fields — just return trimmed, or None if empty
    return value if value else (None if skip_empty else '')


def _set_schema_and_get_table_name(tenant, shop):
    """
    Register tenant DB connection, set search_path, and return the full table name.
    Returns: (db_alias, schema_qualified_table_name)
    """
    register_tenant_connection(tenant)
    db_alias = tenant.db_alias

    # Set thread-local context
    set_current_tenant(tenant)
    set_current_shop(shop.schema_name)

    # Get the database connection and set search_path
    connection = connections[db_alias]
    with connection.cursor() as cursor:
        # Set search_path
        cursor.execute(f'SET search_path TO "{shop.schema_name}", public')
        # Verify it was set correctly
        cursor.execute('SHOW search_path')
        current_path = cursor.fetchone()[0]
        print(f"DEBUG: search_path set to: {current_path}")
    
    # Get the base table name from the model's Meta
    base_table_name = Debtor._meta.db_table
    
    # If the table name already includes a schema, extract just the table part
    if '.' in base_table_name:
        base_table_name = base_table_name.split('.')[-1]
    
    # Create schema-qualified table name
    schema_table = f'"{shop.schema_name}"."{base_table_name}"'
    
    print(f"DEBUG: Using table: {schema_table}")
    
    return db_alias, schema_table


# ============================================================
# API Views
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tenants_and_shops(request):
    """
    Return all tenants with their shops for the import UI dropdown.
    GET /api/v1/debtors/import/tenants/
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
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def analyze_csv(request):
    """
    Upload and analyze a CSV file, return headers and sample data.
    POST /api/v1/debtors/import/analyze/
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
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def import_csv(request):
    """
    Import a CSV file into the debtors table of a specific tenant/shop schema.
    
    POST /api/v1/debtors/import/execute/
    Body (multipart/form-data):
        file                 : CSV file
        tenant_id            : int
        shop_id              : int
        mappings             : JSON string  {csv_header: model_field, ...}
        mode                 : 'create_or_update' (default) | 'create_only' | 'update_only'
        skip_empty_fields    : bool (default: True) - Skip empty fields to allow editing later
        default_account_type : str (default: 'O') - Default value for empty account_type fields
                               Valid values: 'O' = Open Item (default - most common)
                                           'C' = Cash Customer
                                           'N' = Normal Credit
                                           'B' = COD
    """
    # --- Validate inputs ---
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    tenant_id = request.data.get('tenant_id')
    shop_id = request.data.get('shop_id')
    mappings_json = request.data.get('mappings', '{}')
    mode = request.data.get('mode', 'create_or_update')
    
    # NEW: Option to skip empty fields (default: True)
    skip_empty_fields = request.data.get('skip_empty_fields', 'true')
    if isinstance(skip_empty_fields, str):
        skip_empty_fields = skip_empty_fields.lower() in ('true', '1', 'yes')
    else:
        skip_empty_fields = bool(skip_empty_fields)
    
    # NEW: Default account type for empty values (default: 'O' = Open Item)
    # Using 'O' as default since the model has blank=False and 'O' is most common
    default_account_type = request.data.get('default_account_type', 'O')
    if default_account_type:
        default_account_type = default_account_type.upper().strip()
    
    # Validate account_type - must be non-empty since model has blank=False
    if not default_account_type or default_account_type not in ('O', 'C', 'N', 'B'):
        return Response(
            {'error': f"Invalid default_account_type '{default_account_type}'. Must be O, C, N, or B (cannot be empty)."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not tenant_id or not shop_id:
        return Response(
            {'error': 'tenant_id and shop_id are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Parse mappings
    import json
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

    # --- CRITICAL FIX: Override the middleware's schema selection ---
    import logging
    logger = logging.getLogger(__name__)

    # Step 1: Update thread-local context to override middleware
    set_current_shop(shop.schema_name)
    logger.info(f"🔧 IMPORT: Overriding schema to '{shop.schema_name}' (shop_id={shop_id}, shop_name='{shop.name}')")

    # Step 2: Get DB connection and register it
    register_tenant_connection(tenant)
    db_alias = tenant.db_alias

    # Step 3: Force set search_path using raw SQL (this overrides middleware)
    connection = connections[db_alias]
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{shop.schema_name}", public')
        # Verify it was set
        cursor.execute('SHOW search_path')
        actual_path = cursor.fetchone()[0]
        logger.info(f"✅ IMPORT: search_path verified as: {actual_path}")

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
            # Re-set search_path inside transaction to ensure it's active
            connection = connections[db_alias]
            with connection.cursor() as cursor:
                cursor.execute(f'SET search_path TO "{shop.schema_name}", public')
            
            for row_num, row in enumerate(rows, start=2):  # row 1 is header
                try:
                    record = {}
                    for csv_col, model_field in mappings.items():
                        idx = header_idx.get(csv_col)
                        if idx is not None and idx < len(row):
                            raw_val = row[idx]
                            parsed_val = _parse_value(raw_val, model_field, skip_empty=skip_empty_fields)
                            # Only add to record if not None (None means empty and should be skipped)
                            if parsed_val is not None:
                                record[model_field] = parsed_val

                    # Must have customer_number
                    cust_num = record.get('customer_number')
                    if cust_num is None or cust_num == 0:
                        errors_list.append(f"Row {row_num}: Missing customer_number — skipped")
                        skipped += 1
                        continue

                    # Separate customer_number from other fields
                    defaults = {k: v for k, v in record.items() if k != 'customer_number'}

                    # CRITICAL: Always set account_type if not provided since model has blank=False
                    # Use the default_account_type to prevent validation errors
                    if 'account_type' not in defaults:
                        defaults['account_type'] = default_account_type

                    # Set is_active default only if not already set
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

    # Map account_type code to human-readable name for response
    account_type_names = {
        'O': 'Open Item',
        'C': 'Cash Customer',
        'N': 'Normal Credit',
        'B': 'COD',
    }
    
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
        'skip_empty_fields': skip_empty_fields,
        'default_account_type': f"{default_account_type} ({account_type_names.get(default_account_type, 'Unknown')})",
        'message': f'Import complete: {created} created, {updated} updated, {skipped} skipped. Data imported to schema: {shop.schema_name}',
    })