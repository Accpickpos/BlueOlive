"""
Base class for the import_*_from_dbf management commands.

Handles tenant/shop resolution and Postgres connection registration
consistently (fixing the ordering bug present in the existing
import_debtors_csv.py-style commands, where register_tenant_connection()
was called before the shop was resolved, so the shop's schema was never
actually applied to the search_path). All legacy DBF importers should
subclass this instead of BaseCommand directly.
"""

import os
import re
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections
from tenancy.models import Tenant
from tenancy.tenant_context import clear_current, set_current_shop, set_current_tenant
from tenancy.utils import register_tenant_connection

DEFAULT_PDF_DIR = Path(settings.BASE_DIR).parent.parent / "pdf"


class TenantAwareLegacyImportCommand(BaseCommand):
    """
    Subclasses implement `run(self, **options)` and use `self.db_alias` on
    every `Model.objects.using(self.db_alias)` call. `self.pdf_dir` is a
    Path pointing at the folder of legacy .dbf files.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant", type=str, required=True, help="Tenant name or ID to import into"
        )
        parser.add_argument(
            "--shop", type=str, required=True, help="Shop name or code to import into"
        )
        parser.add_argument(
            "--dir",
            type=str,
            default=str(DEFAULT_PDF_DIR),
            help="Folder containing the legacy .dbf files",
        )
        parser.add_argument(
            "--migrate",
            action="store_true",
            help="Run migrations on the target schema before importing",
        )
        self.add_legacy_arguments(parser)

    def add_legacy_arguments(self, parser):
        """Hook for subclasses to add command-specific arguments."""

    def handle(self, *args, **options):
        tenant = self._get_tenant(options["tenant"])
        if not tenant:
            raise CommandError(f"Tenant '{options['tenant']}' not found")

        shop = self._get_shop(tenant, options["shop"])
        if not shop:
            raise CommandError(
                f"Shop '{options['shop']}' not found in tenant '{tenant.name}'"
            )

        # Resolve tenant AND shop first, then register the connection once —
        # this is the fix for the ordering bug described above.
        register_tenant_connection(tenant, shop=shop)

        # ALSO set the thread-local tenant/shop context that TenantDatabaseRouter
        # reads. This matters beyond routing plain .using(db_alias) queries:
        # several models (Creditor, Debtor, DebtorTransaction, RFC, ...) call
        # full_clean() in save(), and Django's validate_unique() queries via
        # `model._default_manager.filter(...)` with NO explicit .using() —
        # that goes through the router, which (with no thread-local context)
        # returns None for shop-app models and Django falls back to the
        # "default" DB, which doesn't have these tables. Without this, every
        # update_or_create() on such a model fails with
        # "relation ... does not exist" despite .using(db_alias) being correct.
        set_current_tenant(tenant)
        set_current_shop(shop.schema_name)

        self.tenant = tenant
        self.shop = shop
        self.db_alias = tenant.db_alias
        self.pdf_dir = Path(options["dir"])

        # Shop-app migrations are blocked by TenantDatabaseRouter unless
        # SHOP_SCHEMA is set (see tenancy/db_router.py _is_shop_schema_migration) —
        # required for --migrate, and harmless to set unconditionally.
        os.environ["SHOP_SCHEMA"] = shop.schema_name

        self.stdout.write(
            f"Tenant: {tenant.name}  Shop: {shop.name} (schema: {shop.schema_name})"
        )

        try:
            if options.get("migrate"):
                self.stdout.write(self.style.WARNING("Running migrations..."))
                call_command("migrate", database=self.db_alias, verbosity=1)

            self.created = 0
            self.updated = 0
            self.skipped = 0
            self.errors = 0

            self.run(**options)

            self.stdout.write(
                self.style.SUCCESS(
                    f"\n✓ Done — Created: {self.created}  Updated: {self.updated}  "
                    f"Skipped: {self.skipped}  Errors: {self.errors}"
                )
            )
        finally:
            clear_current()

    def run(self, **options):
        raise NotImplementedError("Subclasses must implement run()")

    def _get_tenant(self, identifier):
        try:
            return Tenant.objects.get(id=int(identifier))
        except (ValueError, Tenant.DoesNotExist):
            return (
                Tenant.objects.filter(slug__iexact=identifier).first()
                or Tenant.objects.filter(name__iexact=identifier).first()
            )

    def _get_shop(self, tenant, identifier):
        return (
            tenant.shops.filter(code__iexact=identifier).first()
            or tenant.shops.filter(name__iexact=identifier).first()
        )

    def _check_table_exists(self, table_name):
        # Defense-in-depth: this builds raw SQL by string interpolation, so
        # reject anything that isn't a plain identifier even though this
        # method currently has no callers.
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table_name):
            raise ValueError(f"Invalid table name: {table_name!r}")
        try:
            with connections[self.db_alias].cursor() as cursor:
                cursor.execute(f"SELECT 1 FROM {table_name} LIMIT 1")  # nosec B608
            return True
        except Exception:
            return False
