"""
Gas app models — LPG cylinder rental/deposit tracking.

No COBOL equivalent exists for this concept (per the /office-hours design doc);
built greenfield. Cylinders are tracked as per-customer aggregate counts, not
individually serialized (see /plan-eng-review Performance Issue 1) — a
RentalTransaction represents "N units of this stock item checked out to this
customer," not a specific physical unit.
"""
from datetime import timedelta
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

from apps.settings.models import TimeStampedModel, ReconciliationMixin
from apps.debtors.models import Debtor
from apps.stock_control.models import StockItem

DEFAULT_OVERDUE_THRESHOLD_DAYS = 90


class RentalSettings(TimeStampedModel):
    """
    Per-tenant rental configuration. Singleton per tenant schema — mirrors
    general_ledger.GLParam's one-row-per-tenant pattern.

    GL account numbers are configurable rather than hardcoded: this tenant's
    real chart-of-accounts (accno values) is unknown ahead of time — set these
    to real GLMast.accno values during onboarding (see the
    setup_rental_gl_accounts management command for the Deposits Held account).
    """
    overdue_threshold_days = models.PositiveIntegerField(
        default=DEFAULT_OVERDUE_THRESHOLD_DAYS,
        help_text="Days after checkout a rental is flagged overdue if not returned",
    )

    # GL account mapping — must point at real GLMast.accno rows before go-live.
    deposits_held_accno = models.BigIntegerField(
        null=True, blank=True,
        help_text="Balance Sheet liability account for cylinder deposits held",
    )
    cash_accno = models.BigIntegerField(
        null=True, blank=True,
        help_text="Cash/till account debited on refund, credited on checkout",
    )
    sales_revenue_accno = models.BigIntegerField(
        null=True, blank=True,
        help_text="Income account credited for billed-for-replacement sales (ex-VAT)",
    )
    vat_output_accno = models.BigIntegerField(
        null=True, blank=True,
        help_text="VAT output account credited on billed-for-replacement sales",
    )
    writeoff_income_accno = models.BigIntegerField(
        null=True, blank=True,
        help_text="Income account credited when a deposit is written off (forfeited)",
    )

    class Meta:
        verbose_name = "Rental Settings"
        verbose_name_plural = "Rental Settings"

    def __str__(self):
        return f"Rental Settings (overdue threshold: {self.overdue_threshold_days}d)"

    @classmethod
    def get_solo(cls):
        """Return the tenant's single settings row, creating it with defaults if missing."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class RentalTransaction(TimeStampedModel, ReconciliationMixin):
    """
    One rental checkout: N units of a stock item (e.g. LPG cylinders) go out
    to a debtor against a held deposit. Reconciled on return into one of four
    states — see RECONCILIATION_STATE_CHOICES.
    """

    STATUS_OPEN = 'OPEN'
    STATUS_RETURNED = 'RETURNED'
    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_RETURNED, 'Returned'),
    ]

    RECON_REFUNDED = 'REFUNDED'
    RECON_WRITTEN_OFF = 'WRITTEN_OFF'
    RECON_DISPUTED = 'DISPUTED'
    RECON_BILLED_FOR_REPLACEMENT = 'BILLED_FOR_REPLACEMENT'
    RECONCILIATION_STATE_CHOICES = [
        (RECON_REFUNDED, 'Refunded'),
        (RECON_WRITTEN_OFF, 'Written Off'),
        (RECON_DISPUTED, 'Disputed'),
        (RECON_BILLED_FOR_REPLACEMENT, 'Billed For Replacement'),
    ]

    # Who and what
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.PROTECT,
        related_name='rental_transactions',
        help_text="Customer the cylinders are rented to",
    )
    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.PROTECT,
        related_name='rental_transactions',
        help_text="Stock item representing the rented product (e.g. LPG cylinder)",
    )
    quantity = models.DecimalField(
        max_digits=10, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Number of units checked out",
    )
    deposit_amount = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Total deposit held for this checkout",
    )

    # Lifecycle
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default=STATUS_OPEN)
    checkout_date = models.DateField(default=timezone.now)
    due_date = models.DateField(
        help_text="Expected return date — checkout_date + tenant's overdue_threshold_days at creation time",
    )
    returned_date = models.DateField(null=True, blank=True)
    reconciliation_state = models.CharField(
        max_length=25, choices=RECONCILIATION_STATE_CHOICES, null=True, blank=True,
        help_text="Set only when status=RETURNED",
    )

    # GL audit trail — links back to the GLTran batch(es) this transaction posted
    gl_batchno_checkout = models.BigIntegerField(null=True, blank=True)
    gl_batchno_return = models.BigIntegerField(null=True, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-checkout_date']
        indexes = [
            models.Index(fields=['debtor', 'status']),
            models.Index(fields=['status', 'due_date']),
        ]

    def __str__(self):
        return f"Rental #{self.pk} — {self.debtor.dname} — {self.stock_item.description} x{self.quantity}"

    @property
    def is_overdue(self):
        """Computed on read — no scheduled job (see /plan-eng-review Performance discussion)."""
        if self.status != self.STATUS_OPEN:
            return False
        return timezone.now().date() > self.due_date

    def save(self, *args, **kwargs):
        if self._state.adding and not self.due_date:
            threshold = RentalSettings.get_solo().overdue_threshold_days
            self.due_date = self.checkout_date + timedelta(days=threshold)
        super().save(*args, **kwargs)
