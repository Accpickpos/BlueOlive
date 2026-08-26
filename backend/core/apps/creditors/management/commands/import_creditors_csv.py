import csv
import re

from apps.creditors.models import Creditor
from apps.settings.models import CreditTerms
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from tenancy.models import Shop, Tenant
from tenancy.utils import register_tenant_connection


class Command(BaseCommand):
    help = "Import creditors/suppliers from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)
        parser.add_argument(
            "--credit-terms-id", type=int, default=1, help="Default credit terms ID"
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
                if not self._check_table_exists(db_alias, "creditors_creditor"):
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
                            f'Creditors table does not exist in schema "{schema_name}". '
                            f"Run migrations first:\n"
                            f"  python manage.py migrate --database={db_alias}\n"
                            f"Or use --migrate flag to run automatically:\n"
                            f'  python manage.py import_creditors_csv creditors.csv --migrate --tenant "McM"'
                        )

            with open(options["file_path"], "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=options["delimiter"])

                if not reader.fieldnames:
                    raise CommandError("CSV file is empty")

                # Get default credit terms
                try:
                    credit_terms = CreditTerms.objects.get(
                        id=options["credit_terms_id"]
                    )
                except CreditTerms.DoesNotExist:
                    raise CommandError(
                        f'Credit terms with ID {options["credit_terms_id"]} not found'
                    )

                created = 0
                updated = 0
                errors = 0

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Required field
                        supplier_number = row.get("supplier_number", "").strip()
                        if not supplier_number:
                            self.stdout.write(
                                f"Row {row_num}: Missing supplier_number, skipping"
                            )
                            errors += 1
                            continue

                        # Perform update_or_create
                        creditor, created_flag = Creditor.objects.using(
                            db_alias
                        ).update_or_create(
                            supplier_number=supplier_number,
                            defaults={
                                "name": row.get("name", "")[:200],
                                "contact_person": row.get("contact_person", "")[:100],
                                "telephone": row.get("telephone", "")[:20],
                                "fax": row.get("fax", "")[:20],
                                "email": row.get("email", "") or "",
                                "physical_address_line1": row.get(
                                    "physical_address_line1", ""
                                )[:100],
                                "physical_address_line2": row.get(
                                    "physical_address_line2", ""
                                )[:100],
                                "physical_city": row.get("physical_city", "")[:50],
                                "physical_province": row.get("physical_province", "")[
                                    :50
                                ],
                                "physical_code": row.get("physical_code", "")[:10],
                                "postal_address_line1": row.get(
                                    "postal_address_line1", ""
                                )[:100],
                                "postal_address_line2": row.get(
                                    "postal_address_line2", ""
                                )[:100],
                                "postal_city": row.get("postal_city", "")[:50],
                                "postal_province": row.get("postal_province", "")[:50],
                                "postal_code": row.get("postal_code", "")[:10],
                                "our_account_number": row.get("our_account_number", "")[
                                    :50
                                ],
                                "credit_terms": credit_terms,
                                "bank_name": row.get("bank_name", "")[:100],
                                "branch_code": row.get("branch_code", "")[:20],
                                "account_number": row.get("account_number", "")[:50],
                                "account_category": row.get("account_category", "BBF"),
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
