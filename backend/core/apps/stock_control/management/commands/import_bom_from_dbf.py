"""
Import bill-of-materials (pack/bundle ingredients) from bom.dbf/bom5.dbf.
Requires a PackBundle to already exist for MASTCODE — rows with no matching
PackBundle are skipped with a warning (creating one implicitly would guess
at bundle-level fields this file doesn't provide).
"""

from apps.settings.legacy_import_command import TenantAwareLegacyImportCommand
from apps.settings.legacy_import_utils import open_dbf, to_decimal, to_str
from apps.stock_control.models import PackBundle, PackBundleIngredient, StockItem


class Command(TenantAwareLegacyImportCommand):
    help = "Import bill-of-materials ingredients from bom.dbf/bom5.dbf"

    def run(self, **options):
        stock_items = {
            s.stock_code: s for s in StockItem.objects.using(self.db_alias).all()
        }
        pack_bundles = {
            pb.stock_item_id: pb for pb in PackBundle.objects.using(self.db_alias).all()
        }

        for filename in ("bom.dbf", "bom5.dbf"):
            path = self.pdf_dir / filename
            if not path.exists():
                self.stdout.write(self.style.WARNING(f"  ⚠ {path} not found"))
                continue

            for record in open_dbf(path):
                mast_code = to_str(record.get("MASTCODE"), 13)
                icode = to_str(record.get("ICODE"), 13)
                if not mast_code or not icode:
                    self.skipped += 1
                    continue

                pack_bundle = pack_bundles.get(mast_code)
                ingredient = stock_items.get(icode)
                if pack_bundle is None or ingredient is None:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠ {filename}: no PackBundle/StockItem for {mast_code!r}->{icode!r}, skipping"
                        )
                    )
                    self.skipped += 1
                    continue

                try:
                    _, created = PackBundleIngredient.objects.using(
                        self.db_alias
                    ).update_or_create(
                        pack_bundle=pack_bundle,
                        ingredient_stock=ingredient,
                        defaults={"quantity": to_decimal(record.get("IQTY")) or 1},
                    )
                    self.created += created
                    self.updated += not created
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠ {mast_code}->{icode}: {e}")
                    )
                    self.errors += 1

            self.stdout.write(self.style.SUCCESS(f"  ✓ BOM imported from {filename}"))
