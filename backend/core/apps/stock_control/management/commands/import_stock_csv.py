import csv
import re
from decimal import Decimal

from apps.settings.models import SalesDepartment
from apps.stock_control.models import StockItem
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from tenancy.models import Shop, Tenant
from tenancy.utils import register_tenant_connection


class Command(BaseCommand):
    help = "Import stock items from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)
        parser.add_argument(
            "--department-id", type=int, default=1, help="Default department ID"
        )
        parser.add_argument(
            "--delimiter", type=str, default=",", help="CSV delimiter (default: comma)"
        )
        parser.add_argument(
            "--tenant", type=str, help="Tenant name or ID to import into"
        )
        parser.add_argument("--shop", type=str, help="Shop name or code to import into")
        parser.add_argument(
            "--migrate", action="store_true", help="Run migrations before importing"
        )

    def handle(self, *args, **options):
        try:
            # Get tenant if specified
            tenant = None
            db_alias = DEFAULT_DB_ALIAS
            schema_name = None

            if options.get("tenant"):
                tenant = self._get_tenant(options["tenant"])
                if not tenant:
                    raise CommandError(f"Tenant '{options['tenant']}' not found")
                register_tenant_connection(tenant)
                db_alias = tenant.db_alias
                self.stdout.write(f"Using tenant: {tenant.name}")

            # Get shop if specified
            if options.get("shop"):
                if not tenant:
                    raise CommandError("--shop requires --tenant to be specified")
                shop = self._get_shop(tenant, options["shop"])
                if not shop:
                    raise CommandError(
                        f"Shop '{options['shop']}' not found in tenant '{tenant.name}'"
                    )
                schema_name = shop.schema_name
                self.stdout.write(f"Using shop: {shop.name} (schema: {schema_name})")
            elif tenant:
                # Use first shop if tenant is specified but shop is not
                shop = tenant.shops.first()
                if shop:
                    schema_name = shop.schema_name
                    self.stdout.write(
                        f"Using default shop: {shop.name} (schema: {schema_name})"
                    )

            # Check if migrations have been run
            if db_alias != DEFAULT_DB_ALIAS:
                if not self._check_table_exists(db_alias, "stock_control_stockitem"):
                    if options.get("migrate"):
                        self.stdout.write(self.style.WARNING("Running migrations..."))
                        try:
                            call_command("migrate", database=db_alias, verbosity=1)
                            self.stdout.write(
                                self.style.SUCCESS("Migrations completed")
                            )
                        except Exception as e:
                            raise CommandError(f"Migration failed: {str(e)}")
                    else:
                        raise CommandError(
                            f'Stock items table does not exist in schema "{schema_name}". '
                            f"Run migrations first:\n"
                            f"  python manage.py migrate --database={db_alias}\n"
                            f"Or use --migrate flag to run automatically:\n"
                            f'  python manage.py import_stock_csv stock_items.csv --migrate --tenant "McM"'
                        )

            with open(options["file_path"], "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=options["delimiter"])

                if not reader.fieldnames:
                    raise CommandError("CSV file is empty")

                # Get default department
                try:
                    department = SalesDepartment.objects.get(
                        id=options["department_id"]
                    )
                except SalesDepartment.DoesNotExist:
                    raise CommandError(
                        f'Department with ID {options["department_id"]} not found'
                    )

                created = 0
                updated = 0
                errors = 0

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Required field
                        stock_code = row.get("stock_code", "").strip()
                        if not stock_code:
                            self.stdout.write(
                                f"Row {row_num}: Missing stock_code, skipping"
                            )
                            errors += 1
                            continue

                        # Perform update_or_create
                        item, created_flag = StockItem.objects.using(
                            db_alias
                        ).update_or_create(
                            stock_code=stock_code,
                            defaults={
                                "description": row.get("description", "")[:255],
                                "department": department,
                                "cost_price": (
                                    Decimal(row.get("cost_price", 0))
                                    if row.get("cost_price")
                                    else Decimal(0)
                                ),
                                "average_cost": (
                                    Decimal(row.get("average_cost", 0))
                                    if row.get("average_cost")
                                    else Decimal(0)
                                ),
                                "selling_price_1": (
                                    Decimal(row.get("selling_price_1", 0))
                                    if row.get("selling_price_1")
                                    else Decimal(0)
                                ),
                                "selling_price_2": (
                                    Decimal(row.get("selling_price_2", 0))
                                    if row.get("selling_price_2")
                                    else Decimal(0)
                                ),
                                "selling_price_3": (
                                    Decimal(row.get("selling_price_3", 0))
                                    if row.get("selling_price_3")
                                    else Decimal(0)
                                ),
                                "quantity_on_hand": (
                                    Decimal(row.get("quantity_on_hand", 0))
                                    if row.get("quantity_on_hand")
                                    else Decimal(0)
                                ),
                                "reorder_quantity": (
                                    Decimal(row.get("reorder_quantity", 0))
                                    if row.get("reorder_quantity")
                                    else Decimal(0)
                                ),
                                "bin_number": row.get("bin_number", ""),
                                "maximum_discount_percent": (
                                    Decimal(row.get("maximum_discount_percent", 0))
                                    if row.get("maximum_discount_percent")
                                    else Decimal(0)
                                ),
                                "is_active": row.get("is_active", "True").lower()
                                in ["true", "yes", "1", "y"],
                            },
                        )

                        if created_flag:
                            created += 1
                        else:
                            updated += 1

                    except Exception as e:
                        self.stdout.write(f"Row {row_num}: Error - {str(e)}")
                        errors += 1

                # Summary output
                self.stdout.write(self.style.SUCCESS("\n✓ Import completed:"))
                self.stdout.write(f"  Created: {created}")
                self.stdout.write(f"  Updated: {updated}")
                if errors:
                    self.stdout.write(self.style.WARNING(f"  Errors: {errors}"))

        except FileNotFoundError:
            raise CommandError(f'File not found: {options["file_path"]}')
        except Exception as e:
            raise CommandError(f"Import failed: {str(e)}")

    def _get_tenant(self, identifier):
        """Get tenant by ID or name"""
        try:
            # Try by ID first
            return Tenant.objects.get(id=int(identifier))
        except (ValueError, Tenant.DoesNotExist):
            # Try by name
            return Tenant.objects.filter(name=identifier).first()

    def _get_shop(self, tenant, identifier):
        """Get shop from tenant by code or name"""
        return (
            tenant.shops.filter(code=identifier).first()
            or tenant.shops.filter(name=identifier).first()
        )

    def _check_table_exists(self, db_alias, table_name):
        """Check if a table exists in the database"""
        # table_name is always a hardcoded literal from call sites in this
        # file, but validate the identifier shape anyway since this builds
        # raw SQL by string interpolation.
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
            raise ValueError(f"Invalid table name: {table_name!r}")
        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")  # nosec B608
            return True
        except Exception:
            return False
