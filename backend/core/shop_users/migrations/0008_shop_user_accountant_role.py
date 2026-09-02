from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("shop_users", "0007_add_created_by_field"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shopuser",
            name="role",
            field=models.CharField(
                choices=[
                    ("ADMIN", "Admin - Full tenant access"),
                    ("MANAGER", "Manager - Manages a single shop"),
                    ("ACCOUNTANT", "Accountant - Cross-shop financial access"),
                    ("STAFF", "Staff - Staff member with limited access"),
                    ("CASHIER", "Cashier - Till operator, single shop"),
                ],
                default="CASHIER",
                max_length=20,
            ),
        ),
    ]
