import django.db.models.deletion
import tenancy.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stock_control', '0004_rename_idx_stockitem_is_active_stock_items_is_acti_025493_idx_and_more'),
        ('stockfinder', '0002_remove_stockfindersynclog_config_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='StockFinderConfig',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text='Label for this configuration', max_length=100)),
                ('base_url', models.URLField(help_text='Stockfinder API base URL')),
                ('api_key', tenancy.models.EncryptedCharField(blank=True, max_length=255)),
                ('api_secret', tenancy.models.EncryptedCharField(blank=True, max_length=255)),
                ('fitment_center_code', models.CharField(blank=True, help_text="This shop's Stockfinder fitment-center code", max_length=100)),
                ('auto_sync_stock', models.BooleanField(default=False, help_text="Periodically push this shop's stock catalog to Stockfinder")),
                ('sync_interval_minutes', models.PositiveIntegerField(default=60)),
                ('last_sync', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('enable_custom_pricing', models.BooleanField(default=False)),
                ('custom_price_field_1', models.CharField(blank=True, max_length=50)),
                ('custom_price_field_2', models.CharField(blank=True, max_length=50)),
                ('custom_price_field_3', models.CharField(blank=True, max_length=50)),
                ('webhook_enabled', models.BooleanField(default=True)),
                ('webhook_secret', tenancy.models.EncryptedCharField(blank=True, help_text='Per-shop HMAC secret Stockfinder signs webhook payloads with', max_length=255)),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Stockfinder Configuration',
                'verbose_name_plural': 'Stockfinder Configurations',
            },
        ),
        migrations.AddField(
            model_name='stockfindersalesorderline',
            name='unmatched',
            field=models.BooleanField(default=False, help_text='True if stock_code (or barcode fallback) matched no local StockItem'),
        ),
        migrations.AddField(
            model_name='stockfinderpurchaseorderline',
            name='unmatched',
            field=models.BooleanField(default=False, help_text='True if stock_code (or barcode fallback) matched no local StockItem'),
        ),
        migrations.AddField(
            model_name='stockfinderpurchaseorderline',
            name='local_stock_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='stock_control.stockitem'),
        ),
    ]
