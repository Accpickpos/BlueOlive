"""
Add the tel2 column for all shop schemas.
This ensures new shops work correctly and fixes existing schemas.

NOTE: This used to run ALTER COLUMN statements against tel2 before that
column existed (it was only added in the migration that used to be
0008_debtor_tel2) - always failing on a fresh apply with "column tel2
does not exist". The AddField was moved here (ahead of the ALTER COLUMN
statements, which now live in 0008) so the column exists before it's
altered.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("debtors", "0006_alter_debtor_dtel2"),
    ]

    operations = [
        migrations.AddField(
            model_name="debtor",
            name="tel2",
            field=models.CharField(
                blank=True,
                db_column="tel2",
                default="",
                help_text="Legacy duplicate of dtel2 (TEL2)",
                max_length=20,
            ),
        ),
    ]
