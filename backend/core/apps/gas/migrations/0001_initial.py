from decimal import Decimal

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("debtors", "0009_dpdc_cheque_details"),
        ("stock_control", "0005_add_barcode_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="RentalSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "overdue_threshold_days",
                    models.PositiveIntegerField(
                        default=90,
                        help_text="Days after checkout a rental is flagged overdue if not returned",
                    ),
                ),
                (
                    "deposits_held_accno",
                    models.BigIntegerField(
                        blank=True,
                        help_text="Balance Sheet liability account for cylinder deposits held",
                        null=True,
                    ),
                ),
                (
                    "cash_accno",
                    models.BigIntegerField(
                        blank=True,
                        help_text="Cash/till account debited on refund, credited on checkout",
                        null=True,
                    ),
                ),
                (
                    "sales_revenue_accno",
                    models.BigIntegerField(
                        blank=True,
                        help_text="Income account credited for billed-for-replacement sales (ex-VAT)",
                        null=True,
                    ),
                ),
                (
                    "vat_output_accno",
                    models.BigIntegerField(
                        blank=True,
                        help_text="VAT output account credited on billed-for-replacement sales",
                        null=True,
                    ),
                ),
                (
                    "writeoff_income_accno",
                    models.BigIntegerField(
                        blank=True,
                        help_text="Income account credited when a deposit is written off (forfeited)",
                        null=True,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Rental Settings",
                "verbose_name_plural": "Rental Settings",
            },
        ),
        migrations.CreateModel(
            name="RentalTransaction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "is_reconciled",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this transaction has been reconciled",
                    ),
                ),
                (
                    "reconciled_at",
                    models.DateTimeField(
                        blank=True,
                        editable=False,
                        help_text="Timestamp when reconciled",
                        null=True,
                    ),
                ),
                (
                    "quantity",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Number of units checked out",
                        max_digits=10,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.01"))
                        ],
                    ),
                ),
                (
                    "deposit_amount",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Total deposit held for this checkout",
                        max_digits=12,
                        validators=[
                            django.core.validators.MinValueValidator(Decimal("0.00"))
                        ],
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("OPEN", "Open"), ("RETURNED", "Returned")],
                        default="OPEN",
                        max_length=25,
                    ),
                ),
                ("checkout_date", models.DateField(default=django.utils.timezone.now)),
                (
                    "due_date",
                    models.DateField(
                        help_text="Expected return date — checkout_date + tenant's overdue_threshold_days at creation time"
                    ),
                ),
                ("returned_date", models.DateField(blank=True, null=True)),
                (
                    "reconciliation_state",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("REFUNDED", "Refunded"),
                            ("WRITTEN_OFF", "Written Off"),
                            ("DISPUTED", "Disputed"),
                            ("BILLED_FOR_REPLACEMENT", "Billed For Replacement"),
                        ],
                        help_text="Set only when status=RETURNED",
                        max_length=25,
                        null=True,
                    ),
                ),
                ("gl_batchno_checkout", models.BigIntegerField(blank=True, null=True)),
                ("gl_batchno_return", models.BigIntegerField(blank=True, null=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_created",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_updated",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reconciled_by",
                    models.ForeignKey(
                        blank=True,
                        editable=False,
                        help_text="User who reconciled this transaction",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="%(class)s_reconciled",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "debtor",
                    models.ForeignKey(
                        help_text="Customer the cylinders are rented to",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="rental_transactions",
                        to="debtors.debtor",
                    ),
                ),
                (
                    "stock_item",
                    models.ForeignKey(
                        help_text="Stock item representing the rented product (e.g. LPG cylinder)",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="rental_transactions",
                        to="stock_control.stockitem",
                    ),
                ),
            ],
            options={
                "ordering": ["-checkout_date"],
            },
        ),
        migrations.AddIndex(
            model_name="rentaltransaction",
            index=models.Index(
                fields=["debtor", "status"], name="rentals_ren_debtor__1a6b4a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="rentaltransaction",
            index=models.Index(
                fields=["status", "due_date"], name="rentals_ren_status_9d5e21_idx"
            ),
        ),
    ]
