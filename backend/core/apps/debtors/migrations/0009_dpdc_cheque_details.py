from django.db import migrations, models

OLD_TO_NEW_STATUS = {
    "A": "OUTSTANDING",
    "I": "OUTSTANDING",
    "P": "CLEARED",
    "C": "DISHONOURED",
}


def migrate_status_forward(apps, schema_editor):
    Dpdc = apps.get_model("debtors", "Dpdc")
    for old, new in OLD_TO_NEW_STATUS.items():
        Dpdc.objects.filter(status=old).update(status=new)


def migrate_status_backward(apps, schema_editor):
    Dpdc = apps.get_model("debtors", "Dpdc")
    new_to_old = {
        "OUTSTANDING": "A",
        "RECEIVED": "A",
        "CLEARED": "P",
        "DISHONOURED": "C",
    }
    for new, old in new_to_old.items():
        Dpdc.objects.filter(status=new).update(status=old)


class Migration(migrations.Migration):

    dependencies = [
        ("debtors", "0008_debtor_tel2"),
    ]

    operations = [
        migrations.AddField(
            model_name="dpdc",
            name="cheque_number",
            field=models.CharField(
                blank=True, help_text="Cheque number", max_length=30
            ),
        ),
        migrations.AddField(
            model_name="dpdc",
            name="bank",
            field=models.CharField(blank=True, help_text="Issuing bank", max_length=50),
        ),
        migrations.AddField(
            model_name="dpdc",
            name="received_date",
            field=models.DateField(
                blank=True, help_text="Date the cheque was received/banked", null=True
            ),
        ),
        migrations.AddField(
            model_name="dpdc",
            name="cleared_date",
            field=models.DateField(
                blank=True, help_text="Date the cheque cleared", null=True
            ),
        ),
        migrations.AddField(
            model_name="dpdc",
            name="notes",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="dpdc",
            name="date",
            field=models.DateField(db_index=True, help_text="Expected/cheque date"),
        ),
        migrations.AlterField(
            model_name="dpdc",
            name="status",
            field=models.CharField(
                choices=[
                    ("OUTSTANDING", "Outstanding"),
                    ("RECEIVED", "Received"),
                    ("CLEARED", "Cleared"),
                    ("DISHONOURED", "Dishonoured"),
                ],
                default="OUTSTANDING",
                max_length=20,
            ),
        ),
        # Column is now wide enough (varchar(20)) to hold the new status
        # values, so translate any existing rows' old single-letter codes.
        migrations.RunPython(migrate_status_forward, migrate_status_backward),
    ]
