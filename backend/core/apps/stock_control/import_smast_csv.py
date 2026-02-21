"""
Stock Master (SMAST) CSV Import API
Imports stock item data from CSV files into a specific tenant/shop schema.
Supports auto-detection of column mappings for legacy SMAST CSV format.
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
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tenancy.models import Tenant, Shop
from tenancy.utils import register_tenant_connection
from tenancy.tenant_context import set_current_tenant, set_current_shop, clear_current
from .models import StockItem


# ============================================================
# CSV column → Django model field mapping
# Maps legacy SMAST CSV headers to StockItem model field names
# ============================================================
CSV_TO_MODEL_FIELD_MAP = {
    'CODE':         'stock_code',
    'DESCRIP':      'description',
    'SUPNO':        'supplier',
    'DEPT':         'department',
    'TAXIND':       'tax_code',
    'CPRICE':       'cost_price',
    'AVECOST':      'average_cost',
    'SPRICE':       'selling_price_1',
    'SPRICE1':      'selling_price_2',
    'SPRICE2':      'selling_price_3',
    'MUP':          'markup_1',
    'MUP1':         'markup_2',
    'MUP2':         'markup_3',
    'REORD':        'reorder_quantity',
    'QOH':          'quantity_on_hand',
    'QSOLDM':       'sales_mtd_quantity',
    'QSOLDY':       'sales_ytd_quantity',
    'VSOLDM':       'sales_mtd_value',
    'VSOLDY':       'sales_ytd_value',
    'GPM':          'gross_profit_mtd',
    'GPY':          'gross_profit_ytd',
    'QTYBYSTOCK':   'quantity_allocated',
    'SCOUNTFLAG':   'stock_count_flag',
    'CLOSTOCK':     'closing_stock_balance',
    'DATELSOLD':    'date_last_sold',
    'DATELPURCH':   'date_last_purchased',
    'LASTSUP':      'last_supplier',
    'BFWDQTY':      'balance_bfwd_quantity',
    'BFWDVAL':      'balance_bfwd_value',
    'QTYSORD':      'quantity_sale_order',
    'QTYPORD':      'quantity_on_order',
    'QTYPURCHM':    'purchased_mtd_quantity',
    'QTYPURCHY':    'purchased_ytd_quantity',
    'SELLQTY':      'default_selling_quantity',
    'SUPCODE':      'supplier_code',
    'MAXDISC':      'maximum_discount_percent',
    'WEIGHT':       'weight',
    'ALLOWNEGSL':   'allow_negative_quantities',
    'BIN':          'bin_number',
}

# Fields that store Decimal values
DECIMAL_FIELDS = {
    'cost_price', 'average_cost',
    'selling_price_1', 'selling_price_2', 'selling_price_3',
    'markup_1', 'markup_2', 'markup_3',
    'reorder_quantity', 'quantity_on_hand', 'quantity_allocated',
    'quantity_sale_order', 'quantity_on_order', 'quantity_counted',
    'default_selling_quantity', 'maximum_discount_percent', 'weight',
    'sales_mtd_quantity', 'sales_mtd_value',
    'sales_ytd_quantity', 'sales_ytd_value',
    'gross_profit_mtd', 'gross_profit_ytd',
    'purchased_mtd_quantity', 'purchased_ytd_quantity',
    'balance_bfwd_quantity', 'balance_bfwd_value', 'closing_stock_balance',
}

# Fields that store dates
DATE_FIELDS = {'date_last_sold', 'date_last_purchased'}

# Boolean fields (Y/N in CSV)
BOOLEAN_FIELDS = {'allow_negative_quantities'}

# FK fields — stored as raw integer IDs in the CSV; we resolve them as _id
FK_INT_FIELDS = {'supplier', 'department', 'tax_code', 'last_supplier'}


def _detect_delimiter(text):
    """Auto-detect CSV delimiter (semicolon or comma)."""
    first_line = text.split('\n')[0]
    if ';' in first_line and first_line.count(';') > first_line.count(','):
        return ';'
    return ','


def _parse_value(value, field_name, skip_empty=True):
    """
    Convert a raw CSV string value to the correct Python type for the model field.
    If skip_empty is True and value is empty/invalid, returns None to signal exclusion.
    """
    if value is None:
        return None

    value = str(value).strip()

    # Empty / N/A handling
    if value == '' or value.upper() == 'N/A':
        if skip_empty:
            return None
        if field_name in DECIMAL_FIELDS:
            return Decimal('0.00')
        if field_name in DATE_FIELDS:
            return None
        if field_name in BOOLEAN_FIELDS:
            return True
        if field_name in FK_INT_FIELDS:
            return None
        return ''

    # FK integer fields (supplier id, department id, etc.)
    if field_name in FK_INT_FIELDS:
        try:
            int_val = int(float(value))
            return int_val if int_val > 0 else None
        except (ValueError, TypeError):
            return None

    # Decimal fields
    if field_name in DECIMAL_FIELDS:
        try:
            return Decimal(value.replace(',', ''))
        except (InvalidOperation, ValueError):
            return Decimal('0.00') if not skip_empty else None

    # Date fields (handles YYYY/MM/DD, YYYY-MM-DD, DD/MM/YYYY, MM/DD/YYYY)
    if field_name in DATE_FIELDS:
        for fmt in ('%Y/%m/%d', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
            try:
                parsed = datetime.strptime(value, fmt).date()
                # Reject obviously invalid sentinel dates (e.g. 1960-01-01)
                if parsed.year < 1970:
                    return None
                return parsed
            except (ValueError, TypeError):
                continue
        return None

    # Boolean fields (Y/N, YES/NO, TRUE/FALSE, 1/0)
    if field_name in BOOLEAN_FIELDS:
        return value.upper() in ('Y', 'YES', 'TRUE', '1')

    # String / char fields — return trimmed value, or None if empty
    return value if value else (None if skip_empty else '')


def _resolve_fk_fields(record, db_alias, shop_schema):
    """
    Convert raw FK integer IDs (supplier, department, tax_code, last_supplier)
    into Django ORM-compatible _id fields so that update_or_create works correctly
    without fetching full related objects.
    """
    fk_map = {
        'supplier':     'supplier_id',
        'department':   'department_id',
        'tax_code':     'tax_code_id',
        'last_supplier': 'last_supplier_id',
    }
    for src_field, dest_field in fk_map.items():
        if src_field in record:
            record[dest_field] = record.pop(src_field)
    return record


# ============================================================
# API Views
# ============================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_tenants_and_shops(request):
    """
    Return all tenants with their shops for the import UI dropdown.
    GET /api/v1/stock/import/tenants/
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
    Upload and analyze a SMAST CSV file, return headers and sample data.
    POST /api/v1/stock/import/analyze/
    Body: multipart/form-data with 'file' field
    """
    if 'file' not in request.FILES:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    file_obj = request.FILES['file']
    if not file_obj.name.lower().endswith('.csv'):
        return Response({'error': 'Only CSV files are supported'}, status=status.HTTP_400_BAD_REQUEST)

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

    # Build sample rows & count total
    sample_rows = []
    total_rows = 0
    for row in reader:
        total_rows += 1
        if len(sample_rows) < 5:
            sample_rows.append(row)

    # Auto-suggest mappings based on known SMAST headers
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
    Import a SMAST CSV file into the stock_items table of a specific tenant/shop schema.

    POST /api/v1/stock/import/execute/
    Body (multipart/form-data):
        file              : CSV file
        tenant_id         : int
        shop_id           : int
        mappings          : JSON string  {csv_header: model_field, ...}
        mode              : 'create_or_update' (default) | 'create_only' | 'update_only'
        skip_empty_fields : bool (default: True) — skip empty fields so existing values are preserved
    """
    import json
    import logging
    logger = logging.getLogger(__name__)

    # --- Validate inputs ---
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)

    tenant_id = request.data.get('tenant_id')
    shop_id = request.data.get('shop_id')
    mappings_json = request.data.get('mappings', '{}')
    mode = request.data.get('mode', 'create_or_update')

    skip_empty_fields = request.data.get('skip_empty_fields', 'true')
    if isinstance(skip_empty_fields, str):
        skip_empty_fields = skip_empty_fields.lower() in ('true', '1', 'yes')
    else:
        skip_empty_fields = bool(skip_empty_fields)

    if not tenant_id or not shop_id:
        return Response(
            {'error': 'tenant_id and shop_id are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Parse mappings JSON
    try:
        mappings = json.loads(mappings_json) if isinstance(mappings_json, str) else mappings_json
    except json.JSONDecodeError:
        return Response({'error': 'Invalid mappings JSON'}, status=status.HTTP_400_BAD_REQUEST)

    if not mappings:
        return Response({'error': 'Column mappings are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Ensure stock_code is mapped (primary key)
    if 'stock_code' not in mappings.values():
        return Response(
            {'error': 'stock_code mapping is required (maps to CODE / stock code)'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # --- Resolve tenant & shop ---
    # First, get the shop to find its tenant (allows importing to any shop regardless of tenant_id param)
    try:
        shop = Shop.objects.select_related('tenant').get(id=shop_id, is_active=True)
    except Shop.DoesNotExist:
        return Response({'error': f'Shop {shop_id} not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Use the shop's actual tenant - this ensures we import to the correct tenant
    # regardless of what tenant_id was sent in the request
    tenant = shop.tenant
    
    # Verify the tenant is active
    if not tenant.is_active:
        return Response({'error': f'Tenant for shop {shop_id} is not active'}, status=status.HTTP_400_BAD_REQUEST)

    # --- Set schema context ---
    set_current_shop(shop.schema_name)
    logger.info(f"🔧 SMAST IMPORT: Overriding schema to '{shop.schema_name}' (shop_id={shop_id}, shop_name='{shop.name}')")

    register_tenant_connection(tenant)
    db_alias = tenant.db_alias
    set_current_tenant(tenant)

    connection = connections[db_alias]
    with connection.cursor() as cursor:
        cursor.execute(f'SET search_path TO "{shop.schema_name}", public')
        cursor.execute('SHOW search_path')
        actual_path = cursor.fetchone()[0]
        logger.info(f"✅ SMAST IMPORT: search_path verified as: {actual_path}")

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

    # Validate mapped columns exist in CSV
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
            # Re-set search_path inside the transaction
            with connections[db_alias].cursor() as cursor:
                cursor.execute(f'SET search_path TO "{shop.schema_name}", public')

            for row_num, row in enumerate(rows, start=2):  # row 1 is header
                try:
                    record = {}
                    for csv_col, model_field in mappings.items():
                        idx = header_idx.get(csv_col)
                        if idx is not None and idx < len(row):
                            raw_val = row[idx]
                            parsed_val = _parse_value(raw_val, model_field, skip_empty=skip_empty_fields)
                            if parsed_val is not None:
                                record[model_field] = parsed_val

                    # Must have stock_code
                    stock_code = record.get('stock_code')
                    if not stock_code:
                        errors_list.append(f"Row {row_num}: Missing stock_code — skipped")
                        skipped += 1
                        continue

                    # Resolve FK integer IDs to _id fields
                    record = _resolve_fk_fields(record, db_alias, shop.schema_name)

                    # Separate PK from defaults
                    defaults = {k: v for k, v in record.items() if k != 'stock_code'}

                    # Set is_active default if not provided
                    if 'is_active' not in defaults:
                        defaults['is_active'] = True

                    if mode == 'create_only':
                        if StockItem.objects.using(db_alias).filter(stock_code=stock_code).exists():
                            skipped += 1
                            continue
                        StockItem.objects.using(db_alias).create(stock_code=stock_code, **defaults)
                        created += 1

                    elif mode == 'update_only':
                        rows_updated = StockItem.objects.using(db_alias).filter(
                            stock_code=stock_code
                        ).update(**defaults)
                        if rows_updated:
                            updated += 1
                        else:
                            skipped += 1

                    else:  # create_or_update (default)
                        obj, was_created = StockItem.objects.using(db_alias).update_or_create(
                            stock_code=stock_code,
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
        'skip_empty_fields': skip_empty_fields,
        'message': (
            f'Import complete: {created} created, {updated} updated, {skipped} skipped. '
            f'Data imported to schema: {shop.schema_name}'
        ),
    })