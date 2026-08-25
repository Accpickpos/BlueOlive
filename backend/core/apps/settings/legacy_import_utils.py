"""
Shared helpers for importing legacy DBF data (pdf/ folder) into the current
Django models. Used by the import_*_from_dbf management commands across the
debtors, creditors, stock_control, cash_book and pos apps.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from dbfread import DBF


def open_dbf(path):
    """Open a legacy DBF file, tolerating missing memo files and odd encodings."""
    return DBF(str(path), load=True, ignore_missing_memofile=True, encoding='latin-1')


def to_decimal(value, default=Decimal('0')):
    if value is None or value == '':
        return default
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return default


def clamp_decimal(value, max_digits, decimal_places, default=Decimal('0')):
    """
    Some legacy numeric fields (e.g. markup %) occasionally contain garbage
    values that overflow the target DecimalField's precision. Clamp to the
    field's representable range rather than letting the whole record fail.
    """
    value = to_decimal(value, default)
    limit = Decimal(10) ** (max_digits - decimal_places) - Decimal(10) ** -decimal_places
    if value > limit:
        return limit
    if value < -limit:
        return -limit
    return value


def to_int(value, default=0):
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default


def to_date(value):
    """dbfread already returns datetime.date for 'D' fields, or None if blank."""
    return value or None


def parse_yyyymmdd(value):
    """Some files (e.g. stmove<code>.dbf) store DATE as a raw 'YYYYMMDD' string, not a D field."""
    value = to_str(value)
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y%m%d').date()
    except ValueError:
        return None


def parse_ddmmyy(value):
    """Some files (e.g. prupdate.dbf EFFECTDATE) store dates as 'DD/MM/YY' strings."""
    value = to_str(value)
    if not value:
        return None
    try:
        return datetime.strptime(value, '%d/%m/%y').date()
    except ValueError:
        return None


def parse_hhmm(value):
    """TIME stored as 'HH:MM' string."""
    value = to_str(value)
    if not value:
        return None
    try:
        return datetime.strptime(value, '%H:%M').time()
    except ValueError:
        return None


def clean_email(value, maxlen=None):
    """Return value if it's a valid email (per Django's own validator), else ''."""
    value = to_str(value, maxlen)
    try:
        validate_email(value)
        return value
    except ValidationError:
        return ''


def to_str(value, maxlen=None):
    if value is None:
        return ''
    text = str(value).strip()
    return text[:maxlen] if maxlen else text


def translate_code(command, value, mapping, fallback, *, context):
    """
    Look up `value` in `mapping`; if not found, log a warning identifying
    `context` (e.g. "repmast.dbf STATUS") and the unmapped raw code, then
    return `fallback`. Standard pattern for every legacy status/type code
    field so nothing crashes and nothing is silently miscategorized without
    a trace.
    """
    key = to_str(value)
    if key in mapping:
        return mapping[key]
    command.stdout.write(command.style.WARNING(
        f'  ⚠ Unmapped {context} code {key!r} — using fallback {fallback!r}'
    ))
    return fallback


def dedupe_name(queryset, name, key_field, key_value, maxlen=None):
    """
    Legacy exports sometimes reuse the same name under two different natural
    keys (e.g. deptfile.dbf has 'TYRESURANCE' under both DEPT 601 and 890),
    but the target model enforces a unique name. If `name` is already used
    by a *different* row, disambiguate by appending the key value.
    """
    if queryset.filter(name=name).exclude(**{key_field: key_value}).exists():
        name = f'{name} ({key_value})'
        if maxlen:
            name = name[:maxlen]
    return name


_CODE_FROM_FILENAME_RE = re.compile(r'(\d+)')


def code_from_filename(path):
    """Extract the numeric stock code embedded in files like stmove41200.dbf."""
    stem = path.stem if hasattr(path, 'stem') else path
    match = _CODE_FROM_FILENAME_RE.search(stem)
    return match.group(1) if match else None
