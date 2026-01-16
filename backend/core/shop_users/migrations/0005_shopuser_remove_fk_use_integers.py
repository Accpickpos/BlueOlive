# Generated migration to convert ForeignKeys to integers
# This allows shop_users to live in tenant schemas without cross-schema FK constraints

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop_users', '0004_alter_shopuser_username'),
    ]

    operations = [
        # Fields already converted to integers in 0001_initial
    ]
