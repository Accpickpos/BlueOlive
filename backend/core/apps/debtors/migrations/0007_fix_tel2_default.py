"""
Add DEFAULT to tel2 column for all shop schemas.
This ensures new shops work correctly and fixes existing schemas.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('debtors', '0006_alter_debtor_dtel2'),
    ]

    operations = [
        # Drop NOT NULL, set DEFAULT, then re-add NOT NULL
        migrations.RunSQL(
            sql="ALTER TABLE dmast ALTER COLUMN tel2 DROP NOT NULL;",
            reverse_sql="ALTER TABLE dmast ALTER COLUMN tel2 SET NOT NULL;"
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dmast ALTER COLUMN tel2 SET DEFAULT '';",
            reverse_sql="ALTER TABLE dmast ALTER COLUMN tel2 DROP DEFAULT;"
        ),
        migrations.RunSQL(
            sql="ALTER TABLE dmast ALTER COLUMN tel2 SET NOT NULL;",
            reverse_sql="ALTER TABLE dmast ALTER COLUMN tel2 DROP NOT NULL;"
        ),
    ]