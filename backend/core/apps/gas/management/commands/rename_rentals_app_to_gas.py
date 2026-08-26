"""
One-time data migration for shops that were already migrated under the old
'rentals' app label before this app was renamed to 'gas'.

Renaming a Django app label doesn't rename anything in an already-migrated
database — Django only ever tracks *new* migrations going forward. Any shop
schema that already ran the old `rentals.0001_initial` migration has real
tables named `rentals_rentalsettings` / `rentals_rentaltransaction`, indexes
named `rentals_ren_*`, and `django_migrations` rows recorded under
app='rentals'. Left alone, that shop's next `manage.py migrate` would see no
migration history for the new 'gas' app label and try to create brand-new,
empty `gas_rentalsettings` / `gas_rentaltransaction` tables — silently
orphaning any existing rental/deposit data in the old `rentals_*` tables.

This command renames the physical tables (and their PK constraints, FK
constraints, and owned sequences — none of which Django migrations track by
exact name) in place, and retags the shop's `django_migrations` rows from
app='rentals' to app='gas' up through `0001_initial`. It deliberately does
NOT touch indexes declared via the model's `Meta.indexes` (currently the
two indexes on RentalTransaction) — those get a Django-computed name that
depends on the table name (a hash suffix, e.g.
`rentals_ren_debtor__1a6b4a_idx` becomes `gas_rentalt_debtor__0939ac_idx`,
not a literal 'rentals'->'gas' substring swap), and reproducing that
algorithm correctly in raw SQL is exactly the kind of thing that silently
drifts from whatever Django version generated it. Instead, after this
command retags `0001_initial`, a normal `manage.py migrate` naturally picks
up and correctly applies `gas.0002_rename_...` — Django's own
`RenameIndex` operation already knows the exact old/new names, because it's
the same tool that computed them in the first place. Indexes NOT declared
in `Meta.indexes` (e.g. the implicit ones Postgres creates for the
`debtor`/`stock_item` foreign keys) aren't referenced by name in any
migration either way, so they're simply left with their original,
now-cosmetically-stale names — harmless, since Django only ever looks them
up by table+column, never by name, for anything outside `Meta.indexes`.

Safe to run against a shop that was never migrated with the old 'rentals'
app at all (e.g. a brand new shop) — it detects that the old tables don't
exist and does nothing; a normal `manage.py migrate` will then create the
`gas_*` tables fresh, correctly, on its own.

Usage — run once per already-migrated shop, THEN run `manage.py migrate`
normally to pick up the index rename migration:

    python manage.py rename_rentals_app_to_gas --tenant acme --shop main
    python manage.py rename_rentals_app_to_gas --tenant acme --all-shops
    python manage.py migrate  # finishes the index rename via 0002
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connections, transaction
from tenancy.models import Tenant
from tenancy.tenant_context import clear_current, set_current_shop, set_current_tenant
from tenancy.utils import register_tenant_connection

OLD_APP = "rentals"
NEW_APP = "gas"
OLD_TABLES = ["rentals_rentalsettings", "rentals_rentaltransaction"]


class Command(BaseCommand):
    help = (
        "Renames the physical rentals_* tables/constraints/sequences to gas_* "
        "for a shop that was already migrated under the old 'rentals' app "
        "label, and updates django_migrations bookkeeping to match. Follow "
        "with a normal 'manage.py migrate' to rename Meta.indexes-tracked "
        "indexes via the real migration."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--tenant", type=str, required=True, help="Tenant name, slug, or ID"
        )
        parser.add_argument(
            "--shop", type=str, help="Shop name or code (omit if using --all-shops)"
        )
        parser.add_argument(
            "--all-shops",
            action="store_true",
            help="Run for every shop belonging to the tenant",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would change without changing it",
        )

    def handle(self, *args, **options):
        tenant = self._get_tenant(options["tenant"])
        if not tenant:
            raise CommandError(f"Tenant '{options['tenant']}' not found")

        if options["all_shops"]:
            shops = list(tenant.shops.all())
            if not shops:
                raise CommandError(f"Tenant '{tenant.name}' has no shops")
        elif options["shop"]:
            shop = self._get_shop(tenant, options["shop"])
            if not shop:
                raise CommandError(
                    f"Shop '{options['shop']}' not found in tenant '{tenant.name}'"
                )
            shops = [shop]
        else:
            raise CommandError("Pass --shop <name> or --all-shops")

        for shop in shops:
            self._migrate_shop(tenant, shop, dry_run=options["dry_run"])

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

    def _migrate_shop(self, tenant, shop, *, dry_run):
        register_tenant_connection(tenant, shop=shop)
        set_current_tenant(tenant)
        set_current_shop(shop.schema_name)
        db_alias = tenant.db_alias

        try:
            with connections[db_alias].cursor() as cursor:
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = current_schema() AND table_name = ANY(%s)",
                    [OLD_TABLES],
                )
                existing_old_tables = {row[0] for row in cursor.fetchall()}

                if not existing_old_tables:
                    self.stdout.write(
                        f"[{shop.name}] No old '{OLD_APP}_*' tables found — nothing to rename "
                        f"(either never migrated, or already renamed)."
                    )
                    return

                self.stdout.write(
                    f"[{shop.name}] Found old tables: {sorted(existing_old_tables)}"
                )

                if dry_run:
                    self.stdout.write(f"[{shop.name}] --dry-run: no changes made.")
                    return

                # PostgreSQL supports transactional DDL — wrap the whole
                # multi-table/index/constraint/sequence rename plus the
                # django_migrations rewrite in one transaction, so a failure
                # partway through (permissions error, dropped connection,
                # unexpected name collision) leaves the schema exactly as it
                # was rather than half-renamed with no easy way back.
                with transaction.atomic(using=db_alias):
                    for old_table in sorted(existing_old_tables):
                        new_table = old_table.replace(OLD_APP, NEW_APP, 1)
                        self._rename_table_and_dependents(cursor, old_table, new_table)

                    self._rewrite_migration_history(cursor)

            self.stdout.write(
                self.style.SUCCESS(f"[{shop.name}] Renamed '{OLD_APP}' -> '{NEW_APP}'.")
            )
        finally:
            clear_current()

    def _rename_table_and_dependents(self, cursor, old_table, new_table):
        # Deliberately NOT renaming indexes here — see the module docstring.
        # Meta.indexes-tracked indexes (name depends on a table-name hash,
        # not a literal substring) are renamed correctly by Django's own
        # `0002_rename_...` migration after this command retags 0001 below;
        # untracked implicit indexes are never referenced by name by Django
        # and are safe to leave with stale-looking names.

        # Primary key constraint (implicit *_pkey, and its backing index of the same name)
        old_pkey = f"{old_table}_pkey"
        new_pkey = f"{new_table}_pkey"
        cursor.execute(
            "SELECT 1 FROM pg_constraint WHERE conname = %s",
            [old_pkey],
        )
        if cursor.fetchone():
            cursor.execute(
                f'ALTER TABLE "{old_table}" RENAME CONSTRAINT "{old_pkey}" TO "{new_pkey}"'
            )

        # Foreign key / other named constraints referencing this table
        cursor.execute(
            "SELECT conname FROM pg_constraint c "
            "JOIN pg_class t ON t.oid = c.conrelid "
            "WHERE t.relname = %s AND c.contype != 'p'",
            [old_table],
        )
        for (conname,) in cursor.fetchall():
            new_conname = (
                conname.replace(OLD_APP, NEW_APP, 1) if OLD_APP in conname else conname
            )
            if new_conname != conname:
                cursor.execute(
                    f'ALTER TABLE "{old_table}" RENAME CONSTRAINT "{conname}" TO "{new_conname}"'
                )

        # Owned sequences (id BigAutoField columns)
        cursor.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = %s",
            [old_table],
        )
        for (column_name,) in cursor.fetchall():
            cursor.execute(
                "SELECT pg_get_serial_sequence(%s, %s)", [old_table, column_name]
            )
            seq = cursor.fetchone()[0]
            if seq:
                seq_name = seq.split(".")[-1].strip('"')
                if OLD_APP in seq_name:
                    new_seq_name = seq_name.replace(OLD_APP, NEW_APP, 1)
                    cursor.execute(
                        f'ALTER SEQUENCE "{seq_name}" RENAME TO "{new_seq_name}"'
                    )

        # The table itself, last (indexes/constraints/sequences above still resolve
        # to it by OID, not name, so order doesn't matter functionally — renaming
        # it last just keeps the log output easier to follow).
        cursor.execute(f'ALTER TABLE "{old_table}" RENAME TO "{new_table}"')
        self.stdout.write(f"  {old_table} -> {new_table}")

    def _rewrite_migration_history(self, cursor):
        # Only retag 0001_initial — a shop that was migrated under the old
        # 'rentals' label only ever ran that one migration (0002 didn't
        # exist yet under either label). Leaving migration state at "0001
        # applied, 0002 not yet applied" is exactly right: the tables are
        # now named gas_*, but their Meta.indexes-tracked indexes are still
        # under their original rentals_* names, which is precisely the
        # starting state `0002_rename_...` expects to run against.
        cursor.execute(
            "SELECT id FROM django_migrations WHERE app = %s AND name = %s",
            [OLD_APP, "0001_initial"],
        )
        if not cursor.fetchone():
            self.stdout.write(
                self.style.WARNING(
                    f"  No '{OLD_APP}.0001_initial' row in django_migrations — "
                    f"tables were renamed, but migration history is unchanged. "
                    f"Investigate before running migrate."
                )
            )
            return

        cursor.execute(
            "UPDATE django_migrations SET app = %s WHERE app = %s AND name = %s",
            [NEW_APP, OLD_APP, "0001_initial"],
        )
        self.stdout.write(
            f"  django_migrations: re-tagged '{OLD_APP}.0001_initial' -> "
            f"'{NEW_APP}.0001_initial'. Run 'manage.py migrate' next to apply "
            f"'{NEW_APP}.0002_rename_...' and correctly rename the tracked indexes."
        )
