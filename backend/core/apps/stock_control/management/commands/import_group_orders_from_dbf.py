"""
Import consolidated group order worksheets from grp_order_<n>_<date>.dbf.

KNOWN LIMITATION: these files carry ~30 per-branch columns (QSOLD_<branch>,
ON_H_<branch>, Q_ORD_<branch> for each of 171/SQP/MKO/HIQ/HOW/NOR/109/ECO/
GAT/BES) that the current GroupOrder/GroupOrderItem schema has no home for
(it tracks per-branch quantity via separate BranchStock rows, not wide
columns). Only CODE/ORDER_QTY/COST_PRICE are imported; the per-branch
breakdown is dropped. The file has no branch identifier of its own, so the
target branch must be supplied via --branch-code (a Branch is
get_or_create'd if it doesn't exist yet).
"""
import re

from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_str
from apps.stock_control.models import Branch, GroupOrder, GroupOrderItem, StockItem

_FILENAME_RE = re.compile(r'grp_order_(\d+)_(\d{8})', re.IGNORECASE)


class Command(TenantAwareLegacyImportCommand):
    help = 'Import consolidated group order worksheets from grp_order_<n>_<date>.dbf'

    def add_legacy_arguments(self, parser):
        parser.add_argument('--branch-code', type=str, default='MAIN', help='Branch code to attach these group orders to')

    def run(self, **options):
        paths = sorted(self.pdf_dir.glob('grp_order_*.dbf'))
        if not paths:
            self.stdout.write(self.style.WARNING('  ⚠ No grp_order_*.dbf files found'))
            return

        branch, _ = Branch.objects.using(self.db_alias).get_or_create(
            branch_code=options['branch_code'],
            defaults={'branch_name': options['branch_code'], 'branch_type': 'RETAIL'},
        )
        stock_items = {s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()}

        for path in paths:
            match = _FILENAME_RE.match(path.stem)
            if not match:
                self.stdout.write(self.style.WARNING(f'  ⚠ {path.name}: unrecognised filename pattern, skipping'))
                self.skipped += 1
                continue
            order_number, date_str = match.groups()
            order_date = f'{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}'
            group_order_number = f'{order_number}-{date_str}'

            group_order, _ = GroupOrder.objects.using(self.db_alias).update_or_create(
                group_order_number=group_order_number,
                defaults={'order_date': order_date, 'branch': branch},
            )

            total = 0
            for record in open_dbf(path):
                stock_code = to_str(record.get('CODE'), 13)
                stock_item = stock_items.get(stock_code)
                if not stock_item:
                    self.skipped += 1
                    continue

                quantity = to_decimal(record.get('ORDER_QTY'))
                unit_price = to_decimal(record.get('COST_PRICE'))
                line_total = quantity * unit_price
                total += line_total

                try:
                    _, created = GroupOrderItem.objects.using(self.db_alias).update_or_create(
                        group_order=group_order, stock_item=stock_item,
                        defaults={'quantity': quantity, 'unit_price': unit_price, 'line_total': line_total},
                    )
                    self.created += created
                    self.updated += not created
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  ⚠ {path.name} {stock_code}: {e}'))
                    self.errors += 1

            GroupOrder.objects.using(self.db_alias).filter(pk=group_order.pk).update(total_amount=total)

        self.stdout.write(self.style.SUCCESS(f'  ✓ Group orders imported from {len(paths)} file(s)'))
