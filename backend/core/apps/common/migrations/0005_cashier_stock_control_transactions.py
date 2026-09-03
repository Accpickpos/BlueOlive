# 0002's CASHIER_ALLOW_MODULES = {"pos", "cash_book"} didn't account for
# apps/stock_control/permissions.py's IsStockMover, which has always
# explicitly allowed CASHIER to move stock (receive GRNs, take stock,
# create special deals in bulk, etc) — every stock_control ViewSet layers
# HasModuleFunctionAccess on top of that via ModuleFunctionPermissionMixin,
# so the seed matrix silently 403's cashiers out of stock movement
# entirely despite IsStockMover intending to allow it. Bring the two back
# in sync: grant CASHIER TRANSACTIONS access on stock_control (ENQUIRY is
# already open to everyone since 0003).

from django.db import migrations


def grant_cashier_stock_control_transactions(apps, schema_editor):
    AccessGrant = apps.get_model("common", "AccessGrant")
    db_alias = schema_editor.connection.alias
    AccessGrant.objects.using(db_alias).filter(
        role="CASHIER", module="stock_control", function_type="TRANSACTIONS"
    ).update(is_allowed=True)


def revert(apps, schema_editor):
    AccessGrant = apps.get_model("common", "AccessGrant")
    db_alias = schema_editor.connection.alias
    AccessGrant.objects.using(db_alias).filter(
        role="CASHIER", module="stock_control", function_type="TRANSACTIONS"
    ).update(is_allowed=False)


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0004_open_report_to_all_roles"),
    ]

    operations = [
        migrations.RunPython(grant_cashier_stock_control_transactions, revert),
    ]
