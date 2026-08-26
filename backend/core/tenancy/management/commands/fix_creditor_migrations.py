"""
Management command to fix creditors migrations on all tenant databases.

This fixes the issue where migration 0002_creditor_align_to_current_model
was not applied correctly due to:
1. Wrong SHOP_APP_LABELS order (settings not first)
2. preserve_default=False in migration

Usage:
    python manage.py fix_creditor_migrations [--fake-to-0001] [--re-run]
"""
import logging

from django.core.management.base import BaseCommand
from django.db import connections
from tenancy.models import Shop, Tenant
from tenancy.shop_manager import migrate_shop_apps
from tenancy.utils import register_tenant_connection

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix creditors migrations on all tenant databases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fake-to-0001',
            action='store_true',
            help='Fake creditors migration back to 0001 before re-running',
        )
        parser.add_argument(
            '--re-run',
            action='store_true',
            help='Re-run creditors migrations after faking',
        )

    def handle(self, *args, **options):
        fake_to_0001 = options.get('fake_to_0001', False)
        re_run = options.get('re_run', False)

        tenants = Tenant.objects.filter(is_active=True)
        total = tenants.count()

        self.stdout.write(f'Found {total} active tenants')

        for tenant in tenants:
            self.stdout.write(f'\nProcessing tenant: {tenant.name} ({tenant.db_alias})')

            # Register the tenant connection first
            try:
                register_tenant_connection(tenant)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Failed to register connection: {e}'))
                continue

            try:
                shops = Shop.objects.using('default').filter(tenant=tenant, is_active=True)
                for shop in shops:
                    self.stdout.write(f'  Processing shop: {shop.name} ({shop.schema_name})')

                    alias = tenant.db_alias
                    schema_name = shop.schema_name

                    # Connect to the tenant database
                    conn = connections[alias]

                    if fake_to_0001:
                        # Check current migration state
                        with conn.cursor() as cur:
                            cur.execute(f'SET search_path TO "{schema_name}"')
                            cur.execute("""
                                SELECT name FROM django_migrations
                                WHERE app = 'creditors'
                                ORDER BY id
                            """)
                            current_migrations = [r[0] for r in cur.fetchall()]

                            self.stdout.write(f'    Current creditors migrations: {current_migrations}')

                            if '0002_creditor_align_to_current_model' in current_migrations:
                                # Fake back to 0001
                                cur.execute("""
                                    DELETE FROM django_migrations
                                    WHERE app = 'creditors' AND name > '0001_initial'
                                """)
                                conn.commit()
                                self.stdout.write(self.style.SUCCESS('    [OK] Faked creditors back to 0001'))

                    if re_run:
                        # Re-run migrations - this will apply 0002 and beyond
                        try:
                            migrate_shop_apps(tenant, schema_name)
                            self.stdout.write(self.style.SUCCESS('    [OK] Re-ran migrations'))
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'    [X] Migration failed: {e}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [X] Failed: {e}'))
                logger.exception(f'Failed to fix migrations for tenant {tenant.name}')

        self.stdout.write(self.style.SUCCESS('\n[OK] Done!'))
