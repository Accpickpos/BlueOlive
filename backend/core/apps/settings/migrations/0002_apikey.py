# Generated migration for APIKey model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0001_initial'),
        ('tenancy', '0010_shop_setup_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='APIKey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(help_text="Descriptive name for this API key (e.g., 'Stockfinder Integration')", max_length=255)),
                ('key', models.CharField(db_index=True, help_text='Secret API key', max_length=40, unique=True)),
                ('external_service', models.CharField(help_text="Name of external service using this key (e.g., 'Stockfinder')", max_length=100)),
                ('description', models.TextField(blank=True, help_text='Description of the API key usage')),
                ('allowed_endpoints', models.JSONField(blank=True, default=list, help_text='List of allowed endpoints (empty = all endpoints)')),
                ('allowed_methods', models.JSONField(blank=True, default=list, help_text="Allowed HTTP methods (e.g., ['GET', 'POST'])")),
                ('rate_limit_requests', models.PositiveIntegerField(default=1000, help_text='Number of requests allowed per hour')),
                ('rate_limit_window', models.PositiveIntegerField(default=3600, help_text='Time window in seconds for rate limiting')),
                ('status', models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive'), ('REVOKED', 'Revoked')], default='ACTIVE', max_length=20)),
                ('last_used', models.DateTimeField(blank=True, help_text='Last time this API key was used', null=True)),
                ('last_ip', models.GenericIPAddressField(blank=True, help_text='Last IP address that used this key', null=True)),
                ('expires_at', models.DateTimeField(blank=True, help_text='API key expiration date (null = no expiration)', null=True)),
                ('tenant', models.ForeignKey(blank=True, help_text='Tenant this API key belongs to', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='api_keys', to='tenancy.tenant')),
                ('created_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_created', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='%(class)s_updated', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'API Key',
                'verbose_name_plural': 'API Keys',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['key', 'status'], name='settings_ap_key_85f09f_idx'),
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['external_service'], name='settings_ap_externa_1c5236_idx'),
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['created_at'], name='settings_ap_created_4c2ec4_idx'),
        ),
        migrations.AddIndex(
            model_name='apikey',
            index=models.Index(fields=['tenant', 'status'], name='settings_ap_tenant__9ba903_idx'),
        ),
    ]
