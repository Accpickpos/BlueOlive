"""Import day-of-week/time-window department discounts from smast_discounts.dbf."""

from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    open_dbf,
    parse_hhmm,
    to_decimal,
    to_int,
    to_str,
)
from apps.settings.models import SalesDepartment
from apps.stock_control.models import DepartmentTimeDiscount


class Command(TenantAwareLegacyImportCommand):
    help = (
        "Import day-of-week/time-window department discounts from smast_discounts.dbf"
    )

    def run(self, **options):
        path = self.pdf_dir / "smast_discounts.dbf"
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        departments = {
            d.number: d for d in SalesDepartment.objects.using(self.db_alias).all()
        }

        for record in open_dbf(path):
            dept_number = to_int(record.get("DEPT"))
            department = departments.get(dept_number)
            day_of_week = to_int(record.get("DAYOFWEEK"), default=None)
            start_time = parse_hhmm(record.get("START_TIME"))
            end_time = parse_hhmm(record.get("END_TIME"))
            if (
                department is None
                or day_of_week is None
                or not start_time
                or not end_time
            ):
                self.skipped += 1
                continue

            try:
                _, created = DepartmentTimeDiscount.objects.using(
                    self.db_alias
                ).update_or_create(
                    department=department,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    defaults={
                        "department_name_legacy": to_str(record.get("DEPTNAME"), 20),
                        "discount_percentage": to_decimal(record.get("DISCOUNT")),
                        "discount_type": to_str(record.get("TYPE"), 1),
                    },
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ dept {dept_number}: {e}"))
                self.errors += 1

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Department discounts imported from {path.name}")
        )
