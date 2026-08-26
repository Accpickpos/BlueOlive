# Generated migration for APIKey model
#
# NOTE: This used to CreateModel(APIKey) + AddIndex all over again, but
# 0001_initial already creates APIKey in full (same fields, indexes inline
# via options, db_constraint=False on the tenant FK) - applying both on a
# fresh database fails with "relation settings_apikey already exists".
# This is now a no-op that only preserves the dependency chain for anyone
# who already has it recorded as applied.

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0001_initial'),
        ('tenancy', '0010_shop_setup_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = []
