"""
Migration to add performance indexes to stock_control models.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stock_control", "0002_stockmovementledger_and_more"),
    ]

    operations = [
        # StockItem indexes
        migrations.AddIndex(
            model_name="stockitem",
            index=models.Index(fields=["is_active"], name="idx_stockitem_is_active"),
        ),
        migrations.AddIndex(
            model_name="stockitem",
            index=models.Index(fields=["bin_number"], name="idx_stockitem_bin"),
        ),
        migrations.AddIndex(
            model_name="stockitem",
            index=models.Index(
                fields=["is_active", "department"], name="idx_stock_active_dept"
            ),
        ),
        # StockTransaction indexes
        migrations.AddIndex(
            model_name="stocktransaction",
            index=models.Index(
                fields=["debtor", "transaction_date"], name="idx_stock_debtor_date"
            ),
        ),
        migrations.AddIndex(
            model_name="stocktransaction",
            index=models.Index(
                fields=["supplier", "transaction_date"], name="idx_stock_supplier_date"
            ),
        ),
    ]
