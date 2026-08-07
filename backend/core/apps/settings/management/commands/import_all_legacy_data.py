"""
Run every import_*_from_dbf command in the correct dependency order:
settings reference data -> creditors master -> stock master -> everything
else. Stops on the first hard failure rather than continuing with missing
prerequisite data.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from apps.settings.legacy_import_command import DEFAULT_PDF_DIR

COMMAND_SEQUENCE = [
    'import_settings_from_dbf',
    'import_creditors_from_dbf',
    'import_stock_from_dbf',
    'import_bom_from_dbf',
    'import_shrinkwrap_from_dbf',
    'import_stock_movements_from_dbf',
    'import_serial_numbers_from_dbf',
    'import_staged_price_updates_from_dbf',
    'import_stock_promotions_from_dbf',
    'import_department_discounts_from_dbf',
    'import_group_orders_from_dbf',
    'import_supplier_ledger_from_dbf',
    'import_creditor_open_items_from_dbf',
    'import_creditor_audit_from_dbf',
    'import_rfc_from_dbf',
    'import_expense_categories_from_dbf',
    'import_expense_transactions_from_dbf',
    'import_payment_orders_from_dbf',
    'import_debtors_from_dbf',
    'import_debtor_pdcs_from_dbf',
    'import_debtor_open_items_from_dbf',
    'import_debtor_audit_from_dbf',
    'import_debtor_transactions_from_dbf',
    'import_job_costings_from_dbf',
    'import_job_persons_from_dbf',
    'import_job_printing_from_dbf',
    'import_cashbook_transactions_from_dbf',
    'import_expense_income_balances_from_dbf',
    'import_daily_till_from_dbf',
    'import_laybyes_from_dbf',
    'import_quotations_from_dbf',
    'import_repairs_from_dbf',
]

# Extra per-command kwargs beyond --tenant/--shop/--dir
EXTRA_KWARGS = {
    'import_expense_categories_from_dbf': lambda opts: {'year': opts['year']},
    'import_group_orders_from_dbf': lambda opts: {'branch_code': opts['branch_code']},
}


class Command(BaseCommand):
    help = 'Run every legacy DBF importer in dependency order'

    def add_arguments(self, parser):
        parser.add_argument('--tenant', type=str, required=True)
        parser.add_argument('--shop', type=str, required=True)
        parser.add_argument('--dir', type=str, default=str(DEFAULT_PDF_DIR))
        parser.add_argument('--migrate', action='store_true')
        parser.add_argument('--year', type=int, default=None, help='Financial year for expense category balances')
        parser.add_argument('--branch-code', type=str, default='MAIN', help='Branch code for group orders')

    def handle(self, *args, **options):
        if options.get('year') is None:
            raise CommandError('--year is required (used by import_expense_categories_from_dbf)')

        base_kwargs = {
            'tenant': options['tenant'], 'shop': options['shop'],
            'dir': options['dir'], 'migrate': options['migrate'],
        }

        for name in COMMAND_SEQUENCE:
            self.stdout.write(self.style.HTTP_INFO(f'\n=== {name} ==='))
            kwargs = dict(base_kwargs)
            if name in EXTRA_KWARGS:
                kwargs.update(EXTRA_KWARGS[name](options))
            try:
                call_command(name, **kwargs)
            except CommandError as e:
                raise CommandError(f'{name} failed: {e}') from e

        self.stdout.write(self.style.SUCCESS('\n✓ All legacy data imported'))
