"""
Migration to add performance indexes to POS models.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pos", "0002_initial"),
    ]

    operations = [
        # InvoiceLine indexes
        migrations.AddIndex(
            model_name="invoiceline",
            index=models.Index(fields=["stock_code"], name="idx_invline_stock"),
        ),
        migrations.AddIndex(
            model_name="invoiceline",
            index=models.Index(
                fields=["invoice", "stock_code"], name="idx_invline_inv_stock"
            ),
        ),
    ]
