"""
Import API - User-friendly file upload and import system
Supports CSV and DBF files with auto-detection and validation
"""

import csv
import io
import tempfile
from datetime import datetime
from decimal import Decimal

from apps.creditors.models import Creditor
from apps.debtors.models import Debtor
from apps.settings.models import SalesArea, SalesDepartment, TaxCode
from apps.stock_control.models import StockItem
from dbfread import DBF
from django.core.files.storage import default_storage
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response


class FileAnalyzer:
    """Analyze uploaded files to detect structure and column names."""

    @staticmethod
    def analyze_csv(file_obj):
        """Analyze CSV file structure."""
        try:
            file_obj.seek(0)
            # Read as text
            if isinstance(file_obj.read(1), bytes):
                file_obj.seek(0)
                text_content = file_obj.read().decode("utf-8", errors="ignore")
            else:
                file_obj.seek(0)
                text_content = file_obj.read()

            # Parse CSV
            f = io.StringIO(text_content)
            reader = csv.reader(f)
            headers = next(reader)

            # Get sample rows
            sample_rows = []
            for i, row in enumerate(reader):
                if i < 5:  # Get first 5 rows
                    sample_rows.append(row)
                else:
                    break

            return {
                "format": "CSV",
                "headers": headers,
                "sample_data": sample_rows,
                "row_count": len(sample_rows),
                "total_rows": sum(1 for line in text_content.splitlines())
                - 1,  # Subtract header
            }
        except Exception as e:
            return {"error": f"CSV analysis failed: {str(e)}"}

    @staticmethod
    def analyze_dbf(file_obj):
        """Analyze DBF file structure."""
        try:
            # Save to temp file (dbfread works with file paths)
            with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as tmp:
                tmp.write(file_obj.read())
                tmp_path = tmp.name

            # Open DBF
            table = DBF(tmp_path)

            # Get headers
            headers = [field.name for field in table.fields]

            # Get sample rows
            sample_rows = []
            table = DBF(tmp_path)  # Reopen to reset
            for i, record in enumerate(table):
                if i < 5:
                    sample_rows.append([record.get(h) for h in headers])
                else:
                    break

            # Count total rows
            table = DBF(tmp_path)
            total_rows = len(list(table))

            return {
                "format": "DBF",
                "headers": headers,
                "sample_data": sample_rows,
                "row_count": len(sample_rows),
                "total_rows": total_rows,
            }
        except Exception as e:
            return {"error": f"DBF analysis failed: {str(e)}"}

    @staticmethod
    def detect_file_type(file_obj):
        """Detect if file is CSV or DBF."""
        name = file_obj.name.lower()
        if name.endswith(".csv"):
            return "CSV"
        elif name.endswith(".dbf"):
            return "DBF"
        else:
            return "UNKNOWN"


class ColumnMapper:
    """Map source columns to Django model fields."""

    # Debtor field mappings
    DEBTOR_MAPPINGS = {
        "account_number": ["DNO", "ACCTNO", "ACCOUNT", "ACCT_NO", "ACCOUNT_NUMBER"],
        "name": ["DNAME", "NAME", "ACCTNAME", "CUSTOMER_NAME", "DEBTOR_NAME"],
        "search_name": ["DSNAME", "SHORT_NAME", "SEARCH_NAME"],
        "contact_person": ["DCONTACT", "CONTACT", "CONTACT_PERSON"],
        "telephone1": ["DTEL", "PHONE", "TEL", "TEL1", "TELEPHONE"],
        "telephone2": ["TEL2", "TELEPHONE2"],
        "fax": ["DFAX", "FAX"],
        "postal_address_line1": ["DADD1", "ADDR1", "ADDRESS1", "POSTAL_ADDRESS"],
        "postal_address_line2": ["DADD2", "ADDR2", "ADDRESS2"],
        "postal_address_line3": ["DADD3", "ADDR3", "ADDRESS3"],
        "postal_code": ["DPCODE", "ZIP", "POSTAL", "POSTAL_CODE", "ZIPCODE"],
        "delivery_address_line1": ["DELAD1", "DADDR1", "DELIVERY_ADDR1"],
        "delivery_address_line2": ["DELAD2", "DADDR2", "DELIVERY_ADDR2"],
        "delivery_address_line3": ["DELAD3", "DADDR3", "DELIVERY_ADDR3"],
        "delivery_code": ["DELAD4", "DZIP", "DELIVERY_CODE"],
        "vat_number": ["DTAXNO", "TAX_NO", "VATNUMBER", "VAT_NUMBER"],
        "credit_limit": ["DCLIMIT", "CREDLIMIT", "CREDIT_LIMIT"],
        "trade_discount": ["DDISCPER", "DISCOUNT_PERCENT", "TRADE_DISCOUNT"],
        "price_level": ["PRICE", "PRICE_LEVEL"],
        "terms": ["TERMS", "PAYMENT_TERMS"],
        "prompt_discount_percentage": ["PDISC", "PROMPT_DISCOUNT"],
        "account_category": ["ACCTYPE", "ACCOUNT_TYPE", "CATEGORY"],
        "current_balance": ["DCRNT", "CURRENT_BALANCE", "BALANCE"],
        "balance_30_days": ["D30", "BALANCE_30"],
        "balance_60_days": ["D60", "BALANCE_60"],
        "balance_90_days": ["D90", "BALANCE_90"],
        "is_blocked": ["BLOCKFLAG", "BLOCKED", "IS_BLOCKED"],
    }

    @staticmethod
    def suggest_mappings(headers):
        """Suggest field mappings based on headers."""
        mappings = {}
        used_columns = set()

        for django_field, possible_names in ColumnMapper.DEBTOR_MAPPINGS.items():
            for source_col in headers:
                if source_col.upper() in [p.upper() for p in possible_names]:
                    if source_col not in used_columns:
                        mappings[django_field] = source_col
                        used_columns.add(source_col)
                        break

        return mappings

    @staticmethod
    def validate_mapping(mapping, headers):
        """Validate that all mapped columns exist."""
        errors = []
        for field, column in mapping.items():
            if column not in headers and column is not None:
                errors.append(f"Column '{column}' not found in file")
        return errors


class ImportProgress:
    """Track import progress in session."""

    def __init__(self, session, import_id):
        self.session = session
        self.import_id = import_id
        self.key = f"import_{import_id}"

    def update(self, processed, total, current_record, status="processing"):
        """Update progress in session."""
        self.session[self.key] = {
            "processed": processed,
            "total": total,
            "percentage": (processed / total * 100) if total > 0 else 0,
            "current_record": current_record,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        self.session.modified = True

    def get(self):
        """Get current progress."""
        return self.session.get(
            self.key,
            {"processed": 0, "total": 0, "percentage": 0, "status": "not_started"},
        )


class ImportViewSet(viewsets.ViewSet):
    """API for uploading and importing data files."""

    parser_classes = (MultiPartParser,)

    @action(detail=False, methods=["post"])
    def upload_and_analyze(self, request):
        """Upload file and analyze structure."""
        if "file" not in request.FILES:
            return Response(
                {"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        file_obj = request.FILES["file"]

        # Detect file type
        file_type = FileAnalyzer.detect_file_type(file_obj)
        if file_type == "UNKNOWN":
            return Response(
                {"error": "Unsupported file type. Use .csv or .dbf"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Analyze file
        if file_type == "CSV":
            analysis = FileAnalyzer.analyze_csv(file_obj)
        else:
            analysis = FileAnalyzer.analyze_dbf(file_obj)

        if "error" in analysis:
            return Response(analysis, status=status.HTTP_400_BAD_REQUEST)

        # Suggest column mappings
        mappings = ColumnMapper.suggest_mappings(analysis["headers"])

        # Store file in session for later import
        import_id = f"import_{datetime.now().timestamp()}"
        request.session[import_id] = {
            "filename": file_obj.name,
            "file_type": file_type,
            "headers": analysis["headers"],
            "mappings": mappings,
            "sample_data": [
                [str(v) if v is not None else "" for v in row]
                for row in analysis["sample_data"]
            ],
        }
        request.session.modified = True

        return Response(
            {
                "import_id": import_id,
                "file_type": file_type,
                "headers": analysis["headers"],
                "total_rows": analysis["total_rows"],
                "sample_data": analysis["sample_data"],
                "suggested_mappings": mappings,
                "message": f'File analyzed. {analysis["total_rows"]} rows found.',
            }
        )

    @action(detail=False, methods=["post"])
    def preview(self, request):
        """Preview data with current mappings."""
        import_id = request.data.get("import_id")
        mappings = request.data.get("mappings", {})
        request.data.get("model_type", "debtor")

        if import_id not in request.session:
            return Response(
                {"error": "Import session not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import_data = request.session[import_id]

        # Validate mappings
        errors = ColumnMapper.validate_mapping(mappings, import_data["headers"])
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare preview data
        preview = {"file": import_data["filename"], "rows": [], "warnings": []}

        for i, row in enumerate(import_data["sample_data"]):
            record = {}
            for django_field, source_col in mappings.items():
                if source_col:
                    col_idx = import_data["headers"].index(source_col)
                    if col_idx < len(row):
                        record[django_field] = row[col_idx]
            preview["rows"].append(record)

        return Response(preview)

    @action(detail=False, methods=["post"])
    def import_data(self, request):
        """Execute the import with mapped columns."""
        import_id = request.data.get("import_id")
        mappings = request.data.get("mappings", {})
        model_type = request.data.get("model_type", "debtor").lower()

        if import_id not in request.session:
            return Response(
                {"error": "Import session not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        import_data = request.session[import_id]
        import_data["file_type"]

        # Validate mappings
        errors = ColumnMapper.validate_mapping(mappings, import_data["headers"])
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        # Import based on model type
        if model_type == "debtor":
            result = self._import_debtors(
                import_data, mappings, request.session, import_id
            )
        elif model_type == "creditor":
            result = self._import_creditors(
                import_data, mappings, request.session, import_id
            )
        elif model_type == "stock":
            result = self._import_stock(
                import_data, mappings, request.session, import_id
            )
        else:
            return Response(
                {"error": f"Unknown model type: {model_type}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Clean up session
        del request.session[import_id]
        request.session.modified = True

        return Response(result)

    def _import_debtors(self, import_data, mappings, session, import_id):
        """Import debtors from file."""
        progress = ImportProgress(session, import_id)
        created = 0
        updated = 0
        errors_list = []

        headers = import_data["headers"]
        rows = import_data["sample_data"]
        total = len(rows)

        for i, row in enumerate(rows):
            try:
                # Extract values using mappings
                data = {}
                for django_field, source_col in mappings.items():
                    if source_col and source_col in headers:
                        col_idx = headers.index(source_col)
                        if col_idx < len(row):
                            value = row[col_idx]
                            # Convert value
                            data[django_field] = self._convert_value(
                                value, django_field
                            )

                # Get or create debtor
                if "account_number" not in data or not data["account_number"]:
                    errors_list.append(f"Row {i+1}: Missing account number")
                    continue

                debtor, created_new = Debtor.objects.update_or_create(
                    account_number=str(data.get("account_number", "")),
                    defaults={
                        k: v
                        for k, v in data.items()
                        if k != "account_number" and v is not None
                    },
                )

                if created_new:
                    created += 1
                else:
                    updated += 1

                progress.update(
                    i + 1, total, f"Account: {data.get('account_number', 'Unknown')}"
                )

            except Exception as e:
                errors_list.append(f"Row {i+1}: {str(e)}")

        return {
            "model_type": "debtor",
            "created": created,
            "updated": updated,
            "errors": errors_list,
            "total_processed": created + updated,
            "message": f"✓ Import complete: {created} created, {updated} updated",
        }

    def _import_creditors(self, import_data, mappings, session, import_id):
        """Import creditors from file."""
        # Similar to debtors - simplified for this example
        return {
            "model_type": "creditor",
            "created": 0,
            "updated": 0,
            "message": "Creditor import not yet implemented in UI",
        }

    def _import_stock(self, import_data, mappings, session, import_id):
        """Import stock items from file."""
        # Similar to debtors - simplified for this example
        return {
            "model_type": "stock",
            "created": 0,
            "updated": 0,
            "message": "Stock import not yet implemented in UI",
        }

    @staticmethod
    def _convert_value(value, field_name):
        """Convert value to appropriate type for model field."""
        if value is None or value == "":
            return None

        try:
            # Boolean fields
            if (
                "blocked" in field_name
                or "discount" in field_name.lower()
                and isinstance(value, str)
            ):
                if value.upper() in ("Y", "YES", "TRUE", "1"):
                    return True
                return False

            # Decimal fields
            if any(
                x in field_name
                for x in [
                    "limit",
                    "balance",
                    "price",
                    "cost",
                    "amount",
                    "discount",
                    "markdown",
                ]
            ):
                return Decimal(str(value).replace(",", ""))

            # Integer fields
            if field_name in ("price_level", "terms"):
                return int(float(str(value)))

            # Date fields
            if "date" in field_name:
                if isinstance(value, str):
                    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
                        try:
                            return datetime.strptime(value, fmt).date()
                        except Exception:  # nosec - trying next date format is expected
                            continue
                return value

            return str(value)

        except Exception:
            return str(value)

    @action(detail=False, methods=["get"])
    def progress(self, request):
        """Get import progress."""
        import_id = request.query_params.get("import_id")
        if not import_id:
            return Response(
                {"error": "import_id required"}, status=status.HTTP_400_BAD_REQUEST
            )

        progress = ImportProgress(request.session, import_id).get()
        return Response(progress)
