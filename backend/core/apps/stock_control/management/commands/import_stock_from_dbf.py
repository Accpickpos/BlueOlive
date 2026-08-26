"""
Import the stock item master from the legacy smast.dbf (the current live
master; newmast.dbf/helen.dbf are near-duplicate snapshots and are treated
as alternate --source files, not auto-merged, since all three claim to be
"the" master).

Must run after import_settings_from_dbf (needs SalesDepartment) and
import_creditors_from_dbf (needs Creditor for supplier/last_supplier FKs).
"""

from apps.creditors.models import Creditor
from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import (
    clamp_decimal,
    open_dbf,
    to_date,
    to_decimal,
    to_int,
    to_str,
)
from apps.settings.models import SalesDepartment, TaxCode
from apps.stock_control.models import FuturePricing, SpecialDeal, StockItem


def to_bool_flag(value):
    return to_str(value).upper() in ("Y", "YES", "T", "TRUE", "1")


class Command(TenantAwareLegacyImportCommand):
    help = "Import the stock item master from smast.dbf (or --source for newmast.dbf/helen.dbf)"

    def add_legacy_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            default="smast.dbf",
            help="Which DBF file to import as the stock master",
        )

    def run(self, **options):
        path = self.pdf_dir / options["source"]
        if not path.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
            return

        departments = {
            d.number: d for d in SalesDepartment.objects.using(self.db_alias).all()
        }
        tax_codes = {t.code: t for t in TaxCode.objects.using(self.db_alias).all()}
        creditors = {
            c.supplier_number: c for c in Creditor.objects.using(self.db_alias).all()
        }

        for record in open_dbf(path):
            stock_code = to_str(record.get("CODE"), 13)
            description = to_str(record.get("DESCRIP"), 30)
            if not stock_code:
                self.skipped += 1
                continue

            dept_number = to_int(record.get("DEPT"))
            department = departments.get(dept_number)
            if department is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠ Stock {stock_code}: unknown department {dept_number!r}, skipping"
                    )
                )
                self.skipped += 1
                continue

            supplier = creditors.get(to_str(record.get("SUPNO")))
            last_supplier = creditors.get(to_str(record.get("LASTSUP")))
            tax_code = tax_codes.get(to_int(record.get("TAXIND")))

            defaults = {
                "description": description or stock_code,
                "department": department,
                "supplier": supplier,
                "supplier_code": to_str(record.get("SUPCODE"), 20) or None,
                "tax_code": tax_code,
                "cost_price": to_decimal(record.get("CPRICE")),
                "average_cost": to_decimal(record.get("AVECOST")),
                "selling_price_1": to_decimal(record.get("SPRICE")),
                "selling_price_2": to_decimal(record.get("SPRICE1")),
                "selling_price_3": to_decimal(record.get("SPRICE2")),
                "markup_1": clamp_decimal(record.get("MUP"), 6, 2),
                "markup_2": clamp_decimal(record.get("MUP1"), 6, 2),
                "markup_3": clamp_decimal(record.get("MUP2"), 6, 2),
                "quantity_on_hand": to_decimal(record.get("QOH")),
                "quantity_allocated": to_decimal(record.get("QTYBYSTOCK")),
                "quantity_sale_order": to_decimal(record.get("QTYSORD")),
                "quantity_on_order": to_decimal(record.get("QTYPORD")),
                "reorder_quantity": to_decimal(record.get("REORD")),
                "default_selling_quantity": to_decimal(record.get("SELLQTY")) or 1,
                "allow_negative_quantities": to_bool_flag(record.get("ALLOWNEGSL")),
                "maximum_discount_percent": clamp_decimal(record.get("MAXDISC"), 6, 2),
                "sales_mtd_quantity": to_decimal(record.get("QSOLDM")),
                "sales_mtd_value": to_decimal(record.get("VSOLDM")),
                "sales_ytd_quantity": to_decimal(record.get("QSOLDY")),
                "sales_ytd_value": to_decimal(record.get("VSOLDY")),
                "gross_profit_mtd": to_decimal(record.get("GPM")),
                "gross_profit_ytd": to_decimal(record.get("GPY")),
                "purchased_mtd_quantity": to_decimal(record.get("QTYPURCHM")),
                "purchased_ytd_quantity": to_decimal(record.get("QTYPURCHY")),
                "balance_bfwd_quantity": to_decimal(record.get("BFWDQTY")),
                "balance_bfwd_value": to_decimal(record.get("BFWDVAL")),
                "closing_stock_balance": to_decimal(record.get("CLOSTOCK")),
                "job_card_bfwd_value": to_decimal(record.get("JCBFWDVAL")),
                "laybye_bfwd_value": to_decimal(record.get("LBBFWDVAL")),
                "rfc_bfwd_value": to_decimal(record.get("RFBFWDVAL")),
                "date_last_purchased": to_date(record.get("DATELPURCH")),
                "date_last_sold": to_date(record.get("DATELSOLD")),
                "last_supplier": last_supplier,
                "bin_number": to_int(record.get("BIN")) or None,
                "weight": to_decimal(record.get("WEIGHT")),
                "stock_count_flag": to_str(record.get("SCOUNTFLAG"), 1) or None,
                "pack_code": to_str(record.get("PACK"), 10) or None,
                "kvi_flag": to_str(record.get("KVI"), 1) or None,
            }

            try:
                item, created = StockItem.objects.using(self.db_alias).update_or_create(
                    stock_code=stock_code, defaults=defaults
                )
                self.created += created
                self.updated += not created
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠ Stock {stock_code}: {e}"))
                self.errors += 1
                continue

            self._import_special_deal(item, record)
            self._import_future_pricing(item, record)

        self.stdout.write(
            self.style.SUCCESS(f"  ✓ Stock items imported from {path.name}")
        )

    def _import_special_deal(self, item, record):
        start_date = to_date(record.get("SPECSTDATE"))
        end_date = to_date(record.get("SPECENDATE"))
        if not start_date or not end_date:
            return
        SpecialDeal.objects.using(self.db_alias).update_or_create(
            stock_item=item,
            start_date=start_date,
            end_date=end_date,
            defaults={
                "special_selling_price_1": to_decimal(record.get("SPPRICE1")),
                "special_selling_price_2": to_decimal(record.get("SPPRICE2")),
                "special_selling_price_3": to_decimal(record.get("SPPRICE3")),
            },
        )

    def _import_future_pricing(self, item, record):
        effective_date = to_date(record.get("NEWPRDATE"))
        if not effective_date:
            return
        FuturePricing.objects.using(self.db_alias).update_or_create(
            stock_item=item,
            effective_date=effective_date,
            defaults={
                "future_selling_price_1": to_decimal(record.get("NEWPR")),
                "future_selling_price_2": to_decimal(record.get("NEWPR1")),
                "future_selling_price_3": to_decimal(record.get("NEWPR2")),
            },
        )
