"""
Add barcode field to StockItem — no legacy DBF equivalent, sector-agnostic
(helps LPG/tyre/hardware scanning too, not just grocery). See
~/.gstack/projects/BootCodex-BlueOlive/accpi-main-design-20260729-001256.md
for the scoping decision.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stock_control', '0004_rename_idx_stockitem_is_active_stock_items_is_acti_025493_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockitem',
            name='barcode',
            field=models.CharField(blank=True, help_text='Barcode/EAN for scanner lookup', max_length=20, null=True),
        ),
        migrations.AddIndex(
            model_name='stockitem',
            index=models.Index(fields=['barcode'], name='idx_stockitem_barcode'),
        ),
    ]
