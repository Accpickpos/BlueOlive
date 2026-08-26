"""
Debtors (Customers) models.
Based on the Debtors.pdf documentation.
"""

from datetime import date
from decimal import Decimal

from apps.settings.models import PostingStatusMixin, SalesArea, TimeStampedModel
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Debtor(TimeStampedModel):
    """
    Debtor/Customer Master Record (DMAST table)
    """

    ACCOUNT_TYPE_CHOICES = [
        ("", "Balance Brought Forward"),
        ("O", "Open Item"),
        ("C", "Cash Customer"),
        ("N", "Normal Credit"),
        ("B", "COD"),
    ]

    BLOCK_FLAG_CHOICES = [
        ("0", "Active"),
        ("1", "Credit Hold"),
        ("2", "Closed"),
        ("3", "No Delivery"),
        ("Y", "Blocked"),
        ("N", "Active Legacy"),
    ]

    INTEREST_FLAG_CHOICES = [
        ("Y", "Yes - Charge Interest"),
        ("N", "No - Do Not Charge"),
    ]

    PRICE_LEVEL_CHOICES = [
        (1, "Retail"),
        (2, "Trade"),
        (3, "Wholesale"),
    ]

    dno = models.IntegerField(
        unique=True, db_index=True, help_text="Debtor Account Number (DNO) - Numeric 5"
    )
    dname = models.CharField(
        max_length=100, help_text="Customer/Debtor Name (DNAME) - Character 40"
    )
    dsname = models.CharField(
        max_length=20,
        blank=True,
        db_index=True,
        help_text="Short/Sort Name (DSNAME) - Character 5",
    )
    dcontact = models.CharField(
        max_length=50, blank=True, help_text="Contact Person (DCONTACT) - Character 20"
    )
    dtel = models.CharField(
        max_length=20, blank=True, help_text="Telephone Number (DTEL) - Character 15"
    )
    dtel2 = models.CharField(
        max_length=20,
        default="",
        blank=True,
        db_column="dtel2",
        help_text="Alternative Phone (TEL2) - Character 15",
    )
    tel2 = models.CharField(
        max_length=20,
        default="",
        blank=True,
        db_column="tel2",
        help_text="Legacy duplicate of dtel2 (TEL2)",
    )
    dfax = models.CharField(
        max_length=20, blank=True, help_text="Fax Number (DFAX) - Character 15"
    )
    email = models.EmailField(
        blank=True, db_column="email", help_text="Email Address (EMAIL) - Character 50"
    )
    address_line1 = models.CharField(
        max_length=100,
        blank=True,
        db_column="dadd1",
        help_text="Postal Address Line 1 (DADD1) - Character 25",
    )
    address_line2 = models.CharField(
        max_length=100,
        blank=True,
        db_column="dadd2",
        help_text="Postal Address Line 2 (DADD2) - Character 25",
    )
    address_line3 = models.CharField(
        max_length=100,
        blank=True,
        db_column="dadd3",
        help_text="Postal Address Line 3 (DADD3) - Character 25",
    )
    postal_code = models.CharField(
        max_length=10,
        blank=True,
        db_column="dpcode",
        help_text="Postal Code (DPCODE) - Character 4",
    )
    delivery_address1 = models.CharField(
        max_length=100,
        blank=True,
        db_column="delad1",
        help_text="Delivery Address Line 1 (DELAD1) - Character 25",
    )
    delivery_address2 = models.CharField(
        max_length=100,
        blank=True,
        db_column="delad2",
        help_text="Delivery Address Line 2 (DELAD2) - Character 25",
    )
    delivery_address3 = models.CharField(
        max_length=100,
        blank=True,
        db_column="delad3",
        help_text="Delivery Address Line 3 (DELAD3) - Character 25",
    )
    delivery_address4 = models.CharField(
        max_length=100,
        blank=True,
        db_column="delad4",
        help_text="Delivery Address Line 4 (DELAD4) - Character 25",
    )
    dtaxno = models.CharField(
        max_length=30,
        blank=True,
        help_text="Tax/Company Registration Number (DTAXNO) - Character 20",
    )
    vatref = models.CharField(
        max_length=20,
        blank=True,
        help_text="VAT Registration Number (VATREF) - Character 10",
    )
    darea = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(99)],
        help_text="Salesman/Area Number (DAREA) - Numeric 2",
    )
    acctype = models.CharField(
        max_length=1,
        choices=ACCOUNT_TYPE_CHOICES,
        default="",
        blank=True,
        help_text="Account Type (ACCTYPE)",
    )
    price = models.IntegerField(
        default=1,
        choices=PRICE_LEVEL_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(3)],
        help_text="Price Level (PRICE) - Numeric 1",
    )
    terms = models.IntegerField(
        default=30,
        validators=[MinValueValidator(0), MaxValueValidator(999)],
        help_text="Payment Terms in Days (TERMS) - Numeric 3",
    )
    ddiscper = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        help_text="Standard Discount % (DDISCPER) - Numeric 10.2",
    )
    pdisc = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        db_column="pdisc",
        help_text="Prompt Payment Discount % (PDISC) - Numeric 6.2",
    )
    discount_printable = models.CharField(
        max_length=1,
        choices=[("Y", "Yes"), ("N", "No")],
        default="N",
        db_column="discprn",
        help_text="Print Discount on Invoice (DISCPRN) - Y/N",
    )
    dclimit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
        help_text="Credit Limit (DCLIMIT) - Numeric 12.2",
    )
    blockflag = models.CharField(
        max_length=1,
        choices=BLOCK_FLAG_CHOICES,
        default="0",
        help_text="Block Account (BLOCKFLAG)",
    )
    dintflag = models.CharField(
        max_length=1,
        choices=INTEREST_FLAG_CHOICES,
        default="N",
        help_text="Charge Interest (DINTFLAG) - Y/N",
    )
    dposbal = models.CharField(
        max_length=1,
        choices=[("Y", "Yes"), ("N", "No")],
        default="Y",
        help_text="Print Account Balance on POS (DPOSBAL) - Y/N",
    )
    dbalbfwd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Balance Brought Forward (DBALBFWD) - Numeric 10.2",
    )
    dcrnt = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Current Month Balance (DCRNT) - Numeric 10.2",
    )
    d30 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="30 Days Balance (D30) - Numeric 10.2",
    )
    d60 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="60 Days Balance (D60) - Numeric 10.2",
    )
    d90 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="90 Days Balance (D90) - Numeric 10.2",
    )
    d120 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="120 Days Balance (D120) - Numeric 10.2",
    )
    d150 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="150 Days Balance (D150) - Numeric 10.2",
    )
    d180 = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="180+ Days Balance (D180) - Numeric 10.2",
    )
    dsalesm = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Sales Total for Current Month (DSALESM) - Numeric 10.2",
    )
    dsalesy = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Sales Total for Year (DSALESY) - Numeric 10.2",
    )
    dprofitm = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Profit for Current Month (DPROFITM) - Numeric 10.2",
    )
    dprofity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Profit for Year (DPROFITY) - Numeric 10.2",
    )
    damtlpd = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Amount of Last Payment (DAMTLPD) - Numeric 10.2",
    )
    ddatlpd = models.DateField(
        null=True, blank=True, help_text="Date of Last Payment (DDATLPD) - Date 8"
    )
    dateopened = models.DateField(
        null=True, blank=True, help_text="Date Account Opened (DATEOPENED) - Date 8"
    )
    notes = models.TextField(
        blank=True, db_column="notes", help_text="Additional Notes (NOTES) - Memo field"
    )
    is_active = models.BooleanField(
        default=True, help_text="Active status (for soft delete)"
    )

    class Meta:
        db_table = "dmast"
        ordering = ["dno"]
        verbose_name = "Debtor"
        verbose_name_plural = "Debtors"
        indexes = [
            models.Index(fields=["dno"], name="idx_dno"),
            models.Index(fields=["dsname"], name="idx_dsname"),
            models.Index(fields=["dname"], name="idx_dname"),
            models.Index(fields=["darea"], name="idx_darea"),
            models.Index(fields=["blockflag"], name="idx_blockflag"),
            models.Index(fields=["-dcrnt"], name="idx_balance_curr"),
            models.Index(fields=["is_active"], name="idx_is_active"),
        ]

    def __str__(self):
        return f"{self.dno} - {self.dname}"

    def clean(self):
        """Validate debtor data according to business rules."""
        errors = {}

        if self.dclimit < 0:
            errors["dclimit"] = "Credit limit cannot be negative."
        if not 0 <= self.ddiscper <= 100:
            errors["ddiscper"] = "Discount percentage must be between 0 and 100."
        if not 0 <= self.pdisc <= 100:
            errors["pdisc"] = "Prompt discount must be between 0 and 100."
        if not 1 <= self.price <= 3:
            errors["price"] = "Price level must be between 1 and 3."
        if self.terms < 0:
            errors["terms"] = "Payment terms cannot be negative."
        if self.acctype == "C" and self.dclimit > 0:
            errors["dclimit"] = "Cash customers should not have a credit limit."
        if self.vatref and len(self.vatref.replace(" ", "")) not in [0, 10]:
            errors["vatref"] = "VAT number should be 10 digits (South African format)."

        if errors:
            raise ValidationError(errors)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure all CharField fields have empty string defaults to avoid database NOT NULL violations
        for field in self._meta.get_fields():
            if isinstance(field, (models.CharField, models.TextField)):
                current_value = getattr(self, field.attname, None)
                if current_value is None:
                    setattr(self, field.attname, "")
        # Extra check for dtel2 specifically since it's causing issues
        if self.dtel2 is None:
            self.dtel2 = ""

    def save(self, *args, **kwargs):
        """Validate and save."""
        import logging

        logger = logging.getLogger(__name__)

        # Debug: Log dtel2 value before conversion
        logger.debug(
            f"[Debtor.save] Before conversion - dtel2={repr(self.dtel2)}, type={type(self.dtel2)}"
        )

        # Convert None to empty strings for CharField/TextField to avoid PostgreSQL NOT NULL violations
        for field in self._meta.get_fields():
            if isinstance(field, (models.CharField, models.TextField)):
                value = getattr(self, field.attname, None)
                if value is None:
                    setattr(self, field.attname, "")

        # Extra check for dtel2 specifically since it's causing issues
        if self.dtel2 is None:
            logger.warning("[Debtor.save] dtel2 was None, setting to empty string")
            self.dtel2 = ""

        # Keep tel2 in sync with dtel2 (legacy duplicate column)
        self.tel2 = self.dtel2

        logger.debug(f"[Debtor.save] After conversion - dtel2={repr(self.dtel2)}")

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_balance(self):
        return (
            self.dbalbfwd
            + self.dcrnt
            + self.d30
            + self.d60
            + self.d90
            + self.d120
            + self.d150
            + self.d180
        )

    @property
    def overdue_balance(self):
        return self.d30 + self.d60 + self.d90 + self.d120 + self.d150 + self.d180

    @property
    def is_over_credit_limit(self):
        return self.total_balance > self.dclimit

    @property
    def credit_available(self):
        return max(Decimal("0.00"), self.dclimit - self.total_balance)

    @property
    def is_blocked(self):
        return self.blockflag in ["1", "2", "3", "Y"]

    @property
    def is_trading(self):
        return self.blockflag not in ["2"] and self.is_active

    @property
    def charges_interest(self):
        return self.dintflag == "Y"

    def get_aged_balance(self, days):
        age_map = {
            0: self.dcrnt,
            30: self.d30,
            60: self.d60,
            90: self.d90,
            120: self.d120,
            150: self.d150,
            180: self.d180,
        }
        return age_map.get(days, Decimal("0.00"))

    def set_blocked(self, blocked=True, reason="1"):
        if blocked:
            self.blockflag = reason if reason in ["1", "2", "3"] else "1"
        else:
            self.blockflag = "0"
        self.save(update_fields=["blockflag", "updated_at"])

    def set_interest_flag(self, charge_interest=True):
        self.dintflag = "Y" if charge_interest else "N"
        self.save(update_fields=["dintflag", "updated_at"])

    def update_last_payment(self, amount, payment_date=None):
        self.damtlpd = amount
        self.ddatlpd = payment_date or date.today()
        self.save(update_fields=["damtlpd", "ddatlpd", "updated_at"])

    def get_aging_summary(self):
        return {
            "current": {"label": "Current", "amount": self.dcrnt},
            "30_days": {"label": "30 Days", "amount": self.d30},
            "60_days": {"label": "60 Days", "amount": self.d60},
            "90_days": {"label": "90 Days", "amount": self.d90},
            "120_days": {"label": "120 Days", "amount": self.d120},
            "150_days": {"label": "150 Days", "amount": self.d150},
            "180_days": {"label": "180+ Days", "amount": self.d180},
            "total": {"label": "Total Outstanding", "amount": self.total_balance},
        }

    def check_credit_approval(self, amount):
        if self.acctype == "C":
            return (True, "Cash customer")
        if self.is_blocked:
            return (False, f"Account blocked: {self.get_block_flag_display()}")
        new_balance = self.total_balance + amount
        if new_balance > self.dclimit:
            return (
                False,
                f"Would exceed credit limit by R{new_balance - self.dclimit:.2f}",
            )
        return (True, "Approved")


class DebtorTransactionQuerySet(models.QuerySet):
    def invoices(self):
        return self.filter(transaction_type__in=["IN", "CS"])

    def payments(self):
        return self.filter(transaction_type__in=["PM", "RCP"])

    def credits(self):
        return self.filter(transaction_type__in=["CN", "CR", "RF"])

    def journal_entries(self):
        return self.filter(transaction_type__in=["JD", "JC"])

    def interest_charges(self):
        return self.filter(transaction_type__in=["INT"])

    def by_period(self, start_date, end_date):
        return self.filter(transaction_date__range=[start_date, end_date])

    def outstanding(self):
        return self.filter(is_allocated=False)

    def allocated(self):
        return self.filter(is_allocated=True)

    def by_source(self, source):
        return self.filter(source_type=source)

    def aging_analysis(self, as_of_date=None):
        from datetime import timedelta

        from django.db.models import Sum

        as_of = as_of_date or date.today()
        outstanding = self.filter(is_allocated=False)
        return outstanding.aggregate(
            current=Sum(
                "total_amount",
                filter=Q(transaction_date__gte=as_of - timedelta(days=30)),
            ),
            days_30_60=Sum(
                "total_amount",
                filter=Q(transaction_date__gte=as_of - timedelta(days=60))
                & Q(transaction_date__lt=as_of - timedelta(days=30)),
            ),
            days_60_90=Sum(
                "total_amount",
                filter=Q(transaction_date__gte=as_of - timedelta(days=90))
                & Q(transaction_date__lt=as_of - timedelta(days=60)),
            ),
            days_90_plus=Sum(
                "total_amount",
                filter=Q(transaction_date__lt=as_of - timedelta(days=90)),
            ),
        )


class DebtorTransactionManager(models.Manager):
    def get_queryset(self):
        return DebtorTransactionQuerySet(self.model, using=self._db)

    def invoices(self):
        return self.get_queryset().invoices()

    def payments(self):
        return self.get_queryset().payments()

    def credits(self):
        return self.get_queryset().credits()

    def journal_entries(self):
        return self.get_queryset().journal_entries()

    def interest_charges(self):
        return self.get_queryset().interest_charges()

    def by_period(self, start_date, end_date):
        return self.get_queryset().by_period(start_date, end_date)

    def outstanding(self):
        return self.get_queryset().outstanding()

    def allocated(self):
        return self.get_queryset().allocated()

    def by_source(self, source):
        return self.get_queryset().by_source(source)

    def aging_analysis(self, as_of_date=None):
        return self.get_queryset().aging_analysis(as_of_date)


class DebtorTransaction(TimeStampedModel):
    """Debtor Transactions (DEBTRAN table)"""

    TRANSACTION_TYPE_CHOICES = [
        ("IN", "Invoice"),
        ("CN", "Credit Note"),
        ("CS", "Cash Sale"),
        ("CR", "Cash Return"),
        ("PM", "Payment"),
        ("RCP", "Receipt"),
        ("INT", "Interest Charge"),
        ("JD", "Journal Debit"),
        ("JC", "Journal Credit"),
        ("RF", "Refund"),
    ]
    VAT_STATUS_CHOICES = [
        ("S", "Standard Rated (15%)"),
        ("E", "Exempt"),
        ("Z", "Zero Rated"),
    ]
    SOURCE_CHOICES = [
        ("POS", "Point of Sale"),
        ("INVOICE", "Invoice Entry"),
        ("IMPORT", "Bulk Import"),
        ("MANUAL", "Manual Entry"),
    ]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("void", "Void"),
        ("reversed", "Reversed"),
    ]

    objects = DebtorTransactionManager()

    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.PROTECT,
        related_name="transactions",
        db_column="dno",
        help_text="Debtor Account Number (DNO)",
    )
    transaction_number = models.CharField(
        max_length=6,
        db_index=True,
        db_column="dtrano",
        help_text="Transaction Number (DTRANO) - Numeric 6",
    )
    transaction_type = models.CharField(
        max_length=3,
        choices=TRANSACTION_TYPE_CHOICES,
        db_column="dtype",
        help_text="Transaction Type (DTYPE) - Character 3",
    )
    transaction_date = models.DateField(
        db_index=True,
        db_column="dtdate",
        help_text="Transaction Date (DTDATE) - Date 8",
    )
    transaction_time = models.TimeField(
        null=True, blank=True, db_column="time", help_text="Transaction Time (TIME)"
    )
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        db_column="dtsub",
        help_text="Subtotal Excl. VAT (DTSUB)",
    )
    vat_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        db_column="dtgst",
        help_text="VAT Amount (DTGST)",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        db_column="dttot",
        help_text="Transaction Total Incl. VAT (DTTOT)",
    )
    vat_status = models.CharField(
        max_length=1,
        choices=VAT_STATUS_CHOICES,
        default="S",
        db_column="dtaxstat",
        help_text="VAT Status (DTAXSTAT)",
    )
    source_station = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(99)],
        db_column="source",
        help_text="Station/Till Number (SOURCE)",
    )
    order_number = models.CharField(
        max_length=10, blank=True, db_column="ordno", help_text="Order Number (ORDNO)"
    )
    customer_reference = models.CharField(
        max_length=10,
        blank=True,
        db_column="custref",
        help_text="Customer Reference (CUSTREF)",
    )
    vat_reference = models.CharField(
        max_length=10,
        blank=True,
        db_column="vatref",
        help_text="VAT Reference (VATREF)",
    )
    station = models.CharField(
        max_length=5,
        blank=True,
        db_column="station",
        help_text="Station Code (STATION)",
    )
    description_line1 = models.CharField(
        max_length=100,
        blank=True,
        db_column="del1",
        help_text="Delivery/Description Line 1 (DEL1)",
    )
    description_line2 = models.CharField(
        max_length=100,
        blank=True,
        db_column="del2",
        help_text="Delivery/Description Line 2 (DEL2)",
    )
    description_line3 = models.CharField(
        max_length=100,
        blank=True,
        db_column="del3",
        help_text="Delivery/Description Line 3 (DEL3)",
    )
    description_line4 = models.CharField(
        max_length=100,
        blank=True,
        db_column="del4",
        help_text="Delivery/Description Line 4 (DEL4)",
    )
    source_type = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="POS",
        help_text="Source of transaction",
    )
    source_reference = models.CharField(
        max_length=100, blank=True, help_text="Link to original record"
    )
    settlement_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Settlement/prompt-payment discount granted on this receipt (RCP transactions only)",
    )
    is_allocated = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether transaction has been fully allocated/paid",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="posted",
        help_text="Transaction status",
    )
    created_by = models.CharField(
        max_length=50, blank=True, help_text="User who created transaction"
    )

    class Meta:
        db_table = "debtran"
        ordering = ["-transaction_date", "-transaction_number"]
        verbose_name = "Debtor Transaction"
        verbose_name_plural = "Debtor Transactions"
        unique_together = [["debtor", "transaction_number", "transaction_date"]]
        indexes = [
            models.Index(
                fields=["debtor", "-transaction_date"], name="idx_deb_tran_date"
            ),
            models.Index(
                fields=["transaction_type", "-transaction_date"],
                name="idx_tran_type_date",
            ),
            models.Index(fields=["transaction_number"], name="idx_dtrano"),
            models.Index(fields=["status"], name="idx_tran_status"),
            models.Index(fields=["source_type"], name="idx_tran_source_type"),
            models.Index(fields=["is_allocated"], name="idx_tran_allocated"),
            models.Index(
                fields=["debtor", "is_allocated", "-transaction_date"],
                name="idx_deb_alloc_date",
            ),
        ]

    def __str__(self):
        return (
            f"{self.transaction_number} - {self.debtor.name} ({self.transaction_date})"
        )

    def clean(self):
        errors = {}
        if self.subtotal < 0 and self.transaction_type not in ["CN", "CR", "RF"]:
            errors["subtotal"] = (
                "Subtotal cannot be negative for this transaction type."
            )
        if self.vat_amount < 0:
            errors["vat_amount"] = "VAT amount cannot be negative."
        expected_total = self.subtotal + self.vat_amount
        if abs(self.total_amount - expected_total) > Decimal("0.01"):
            errors["total_amount"] = (
                f"Total should equal subtotal + VAT (expected {expected_total})"
            )
        if self.transaction_type in ["CN", "CR", "RF"] and self.total_amount > 0:
            errors["total_amount"] = "Credit transactions should have negative amounts"
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_debit(self):
        return self.transaction_type in ["IN", "CS", "JD", "INT"]

    @property
    def is_credit(self):
        return self.transaction_type in ["CN", "CR", "PM", "RCP", "JC", "RF"]

    @property
    def signed_amount(self):
        return self.total_amount if self.is_debit else -abs(self.total_amount)


class DebtorOpenItem(TimeStampedModel):
    """Open Item Transactions (DEBTOPEN table)"""

    TRANSACTION_TYPE_CHOICES = [
        ("IN", "Invoice"),
        ("CN", "Credit Note"),
        ("PY", "Payment"),
        ("JD", "Journal Debit"),
        ("JC", "Journal Credit"),
        ("DM", "Debit Memo"),
        ("CM", "Credit Memo"),
    ]
    AGING_CHOICES = [
        ("0", "Current"),
        ("1", "30 Days"),
        ("2", "60 Days"),
        ("3", "90 Days"),
        ("4", "120+ Days"),
    ]

    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name="open_items",
        db_column="dno",
        help_text="Debtor Number (DNO)",
    )
    transaction_number = models.CharField(
        max_length=6, db_column="dtrano", help_text="Transaction Number (DTRANO)"
    )
    transaction_type = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        db_column="type",
        help_text="Transaction Type (TYPE)",
    )
    transaction_date = models.DateField(
        db_index=True, db_column="date", help_text="Transaction Date (DATE)"
    )
    original_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        db_column="total",
        help_text="Original Transaction Total (TOTAL)",
    )
    balance_due = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        db_column="balancedue",
        help_text="Current Balance Due (BALANCEDUE)",
    )
    age_flag = models.CharField(
        max_length=1,
        choices=AGING_CHOICES,
        default="0",
        db_column="ageflag",
        help_text="Aging Flag (AGEFLAG)",
    )
    posted = models.CharField(
        max_length=10,
        default="Y",
        db_column="posted",
        help_text="Posted Status (POSTED)",
    )
    due_date = models.DateField(null=True, blank=True, help_text="Payment due date")
    fully_paid = models.BooleanField(
        default=False, help_text="Fully allocated/paid flag"
    )

    class Meta:
        db_table = "debtopen"
        ordering = ["transaction_date", "transaction_number"]
        verbose_name = "Open Item Transaction"
        verbose_name_plural = "Open Item Transactions"
        unique_together = [["debtor", "transaction_number"]]
        indexes = [
            models.Index(
                fields=["debtor", "transaction_date"], name="idx_dopen_deb_date"
            ),
            models.Index(fields=["posted", "age_flag"], name="idx_dopen_post_age"),
            models.Index(
                fields=["transaction_date", "age_flag"], name="idx_dopen_date_age"
            ),
            models.Index(fields=["fully_paid"], name="idx_dopen_paid"),
        ]

    def __str__(self):
        return (
            f"{self.transaction_number} - {self.debtor.name} (Due: R{self.balance_due})"
        )

    def clean(self):
        errors = {}
        if self.original_amount < 0:
            errors["original_amount"] = "Original amount cannot be negative."
        if self.balance_due < 0:
            errors["balance_due"] = "Balance due cannot be negative."
        if self.balance_due > self.original_amount:
            errors["balance_due"] = "Balance due cannot exceed original amount."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.due_date and self.debtor and self.transaction_date:
            self.due_date = self.transaction_date + timezone.timedelta(
                days=getattr(self.debtor, "terms", 30) or 30
            )
        self.update_age_flag()
        if self.balance_due == 0:
            self.fully_paid = True
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def allocated_amount(self):
        return self.original_amount - self.balance_due

    @property
    def days_overdue(self):
        if not self.due_date or self.due_date >= date.today():
            return 0
        return (date.today() - self.due_date).days

    def update_age_flag(self):
        days = self.days_overdue
        if days <= 0:
            self.age_flag = "0"
        elif days <= 30:
            self.age_flag = "1"
        elif days <= 60:
            self.age_flag = "2"
        elif days <= 90:
            self.age_flag = "3"
        else:
            self.age_flag = "4"

    def allocate_payment(self, amount):
        if amount <= 0:
            return Decimal("0.00")
        allocation = min(amount, self.balance_due)
        self.balance_due -= allocation
        if self.balance_due == 0:
            self.fully_paid = True
        self.save()
        return amount - allocation


class PostDatedCheque(TimeStampedModel):
    """Post-dated cheques for debtors."""

    debtor = models.ForeignKey(
        Debtor, on_delete=models.CASCADE, related_name="post_dated_cheques"
    )
    cheque_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reference = models.CharField(max_length=100, blank=True)
    is_processed = models.BooleanField(default=False)
    processed_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["cheque_date"]
        indexes = [
            models.Index(fields=["debtor", "is_processed"]),
            models.Index(fields=["cheque_date", "is_processed"]),
        ]

    def __str__(self):
        return f"PDC {self.debtor.name} - {self.cheque_date}"

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("PDC amount must be greater than zero.")
        if self.cheque_date < date.today() and not self.is_processed:
            raise ValidationError(
                "Cheque date cannot be in the past for unprocessed cheques."
            )


class Darea(TimeStampedModel):
    """Sales Area/Salesman (DAREA table)."""

    darea = models.CharField(
        max_length=2, unique=True, primary_key=True, help_text="Salesman/area number"
    )
    dareaname = models.CharField(max_length=20, help_text="Salesman/area name")
    arsls1 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls2 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls3 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls4 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls5 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls6 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls7 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls8 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls9 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls10 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls11 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )
    arsls12 = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ["darea"]
        verbose_name = "Daily Area Sales (DAREA)"
        verbose_name_plural = "Daily Area Sales (DAREA)"

    def __str__(self):
        return f"DAREA {self.darea} - {self.dareaname}"

    def get_total_sales(self):
        return sum(self.get_monthly_sales())

    def get_monthly_sales(self):
        return [
            self.arsls1,
            self.arsls2,
            self.arsls3,
            self.arsls4,
            self.arsls5,
            self.arsls6,
            self.arsls7,
            self.arsls8,
            self.arsls9,
            self.arsls10,
            self.arsls11,
            self.arsls12,
        ]


class Dpdc(TimeStampedModel):
    """Post-dated cheques (DPDC table)."""

    STATUS_CHOICES = [
        ("OUTSTANDING", "Outstanding"),
        ("RECEIVED", "Received"),
        ("CLEARED", "Cleared"),
        ("DISHONOURED", "Dishonoured"),
    ]

    dno = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name="dpdc_cheques",
        help_text="Debtor account number (DNO)",
    )
    date = models.DateField(db_index=True, help_text="Expected/cheque date")
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Cheque value",
    )
    cheque_number = models.CharField(
        max_length=30, blank=True, help_text="Cheque number"
    )
    bank = models.CharField(max_length=50, blank=True, help_text="Issuing bank")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="OUTSTANDING"
    )
    received_date = models.DateField(
        null=True, blank=True, help_text="Date the cheque was received/banked"
    )
    cleared_date = models.DateField(
        null=True, blank=True, help_text="Date the cheque cleared"
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["date"]
        verbose_name = "Post-Dated Cheque (DPDC)"
        verbose_name_plural = "Post-Dated Cheques (DPDC)"
        indexes = [
            models.Index(fields=["dno", "date"]),
            models.Index(fields=["status", "date"]),
        ]

    def __str__(self):
        return f"DPDC {self.dno.dno} - {self.date} - {self.amount}"

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Cheque amount must be greater than zero.")
        if self.date < date.today() and self.status == "OUTSTANDING":
            raise ValidationError("Outstanding cheque date cannot be in the past.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Debtopen(TimeStampedModel):
    """Open item transactions (DEBTOPEN table)."""

    TRANSACTION_TYPE_CHOICES = [
        ("IN", "Invoice"),
        ("CN", "Credit Note"),
        ("PY", "Payment"),
        ("JD", "Journal Debit"),
        ("JC", "Journal Credit"),
        ("DM", "Debit Memo"),
        ("CM", "Credit Memo"),
    ]
    AGEING_CHOICES = [
        ("0", "Current"),
        ("1", "30 Days"),
        ("2", "60 Days"),
        ("3", "90 Days"),
        ("4", "120+ Days"),
    ]
    POSTED_CHOICES = [("Y", "Yes"), ("N", "No")]

    dno = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name="debtopen_items",
        help_text="Debtor number (DNO)",
    )
    dtrano = models.CharField(max_length=6, help_text="Transaction number (DTRANO)")
    type = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        help_text="Transaction type (TYPE)",
    )
    date = models.DateField(db_index=True, help_text="Date of transaction (DATE)")
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Original transaction total (TOTAL)",
    )
    balancedue = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Balance due on transaction (BALANCEDUE)",
    )
    ageflag = models.CharField(
        max_length=1,
        choices=AGEING_CHOICES,
        default="0",
        help_text="Aging flag (AGEFLAG)",
    )
    posted = models.CharField(
        max_length=10, default="N", help_text="Posted status (POSTED)"
    )

    class Meta:
        ordering = ["date", "dtrano"]
        verbose_name = "Open Item Transaction (DEBTOPEN)"
        verbose_name_plural = "Open Item Transactions (DEBTOPEN)"
        unique_together = ["dno", "dtrano"]
        indexes = [
            models.Index(fields=["dno", "date"]),
            models.Index(fields=["posted", "ageflag"]),
            models.Index(fields=["date", "ageflag"]),
        ]

    def __str__(self):
        return f"DEBTOPEN {self.dno.dno} - {self.dtrano} ({self.date})"

    def clean(self):
        if self.total < 0:
            raise ValidationError("Transaction total cannot be negative.")
        if self.balancedue < 0:
            raise ValidationError("Balance due cannot be negative.")
        if self.balancedue > self.total:
            raise ValidationError(
                "Balance due cannot exceed original transaction total."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def get_allocated_amount(self):
        return self.total - self.balancedue

    def is_fully_allocated(self):
        return self.balancedue == 0


class ReceiptAllocation(TimeStampedModel):
    """
    One receipt's payment against one open item (DEBTOPEN row). Mirrors
    apps.creditors.OpenItemAllocation's pattern on the debtor side — see
    DebtorService.apply_receipt_allocation for the validation/mutation
    logic (full-settlement-only discount rule, balance subtraction).

    FKs to DebtorTransaction (not pos.ReceiptOnAccount) because
    DebtorTransaction is the one ledger record both the POS receipt flow
    and the direct debtors-app allocate endpoint converge on.
    """

    receipt = models.ForeignKey(
        DebtorTransaction,
        on_delete=models.CASCADE,
        related_name="allocations",
        help_text="The RCP DebtorTransaction this allocation was made from",
    )
    open_item = models.ForeignKey(
        Debtopen,
        on_delete=models.CASCADE,
        related_name="allocations",
        help_text="The open item (invoice/etc.) this allocation was applied to",
    )
    amount_paid = models.DecimalField(
        max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))]
    )
    settlement_discount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0"))],
    )
    allocated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "debtor_receipt_allocations"
        ordering = ["allocated_at"]
        indexes = [
            models.Index(fields=["receipt"]),
            models.Index(fields=["open_item"]),
        ]

    def __str__(self):
        return f"Allocation {self.amount_paid} from {self.receipt.transaction_number} to {self.open_item.dtrano}"


class DebtorAudit(models.Model):
    """Debtor Audit file (DEBTORAUD table)."""

    TRANSACTION_TYPE_CHOICES = [
        ("IN", "Invoice"),
        ("CR", "Credit Note"),
        ("PA", "Payment"),
        ("AD", "Adjustment"),
        ("DM", "Debit Memo"),
        ("CM", "Credit Memo"),
        ("AL", "Allocation"),
    ]

    dno = models.ForeignKey(
        Debtor,
        on_delete=models.CASCADE,
        related_name="debtoraud_records",
        db_column="dno",
        help_text="Debtor number (DNO)",
    )
    dtrano = models.CharField(
        max_length=6, db_column="dtrano", help_text="Transaction number (DTRANO)"
    )
    type = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        db_column="type",
        help_text="Transaction type (TYPE)",
    )
    thistype = models.CharField(
        max_length=2,
        choices=TRANSACTION_TYPE_CHOICES,
        db_column="thistype",
        help_text="Current transaction type (THISTYPE)",
    )
    thistran = models.CharField(
        max_length=6,
        db_column="thistran",
        help_text="Current transaction type identifier (THISTRAN)",
    )
    date = models.DateField(
        db_index=True, db_column="date", help_text="Audit date (DATE)"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        db_column="amount",
        help_text="Audit amount (AMOUNT)",
    )
    performed_by = models.CharField(
        max_length=50, blank=True, help_text="User who performed the action"
    )
    notes = models.TextField(blank=True, help_text="Audit notes")

    class Meta:
        db_table = "debtoraud"
        ordering = ["-date", "-dtrano"]
        verbose_name = "Debtor Audit (DEBTORAUD)"
        verbose_name_plural = "Debtor Audits (DEBTORAUD)"
        unique_together = [["dno", "dtrano", "date"]]
        indexes = [
            models.Index(fields=["dno", "date"], name="idx_daud_deb_date"),
            models.Index(fields=["date", "type"], name="idx_daud_date_type"),
            models.Index(fields=["type"], name="idx_daud_type"),
        ]

    def __str__(self):
        return f"DEBTORAUD {self.dno.customer_number} - {self.dtrano} ({self.date})"

    def clean(self):
        if self.amount < 0:
            raise ValidationError({"amount": "Amount cannot be negative."})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def log_transaction(
        debtor,
        transaction_number,
        transaction_type,
        amount,
        current_type=None,
        current_transaction=None,
        performed_by="",
        notes="",
    ):
        return DebtorAudit.objects.create(
            dno=debtor,
            dtrano=transaction_number,
            type=transaction_type,
            thistype=current_type or transaction_type,
            thistran=current_transaction or transaction_number,
            date=date.today(),
            amount=amount,
            performed_by=performed_by,
            notes=notes,
        )


class SalesOrder(TimeStampedModel):
    """Sales order (SORDER equivalent)."""

    STATUS_CHOICES = [
        ("O", "Outstanding"),
        ("P", "Partially Invoiced"),
        ("I", "Invoiced"),
        ("C", "Cancelled"),
        ("H", "On Hold"),
    ]
    DELIVERY_OPTION_CHOICES = [
        ("D", "Delivery"),
        ("C", "Collection"),
        ("M", "Mail"),
        ("X", "Collect Later"),
    ]

    sales_order_number = models.CharField(max_length=20, unique=True, db_index=True)
    order_date = models.DateField()
    order_time = models.TimeField(null=True, blank=True)
    debtor = models.ForeignKey(
        Debtor, on_delete=models.PROTECT, related_name="sales_orders"
    )
    customer_name = models.CharField(max_length=40, blank=True)
    delivery_address_line1 = models.CharField(max_length=20, blank=True)
    delivery_address_line2 = models.CharField(max_length=20, blank=True)
    delivery_address_line3 = models.CharField(max_length=20, blank=True)
    date_required = models.DateField(null=True, blank=True)
    time_required = models.TimeField(null=True, blank=True)
    customer_reference = models.CharField(max_length=10, blank=True)
    order_number = models.CharField(max_length=10, blank=True)
    transaction_number = models.PositiveIntegerField(null=True, blank=True)
    delivery_option = models.CharField(
        max_length=1, choices=DELIVERY_OPTION_CHOICES, default="D"
    )
    salesman_number = models.PositiveIntegerField(null=True, blank=True)
    station_number = models.CharField(max_length=2, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="O")

    class Meta:
        ordering = ["-order_date", "sales_order_number"]
        indexes = [
            models.Index(fields=["debtor", "status"]),
            models.Index(fields=["order_date"]),
            models.Index(fields=["status"]),
        ]
        verbose_name = "Sales Order (SORDER)"
        verbose_name_plural = "Sales Orders (SORDER)"

    def __str__(self):
        return f"Sales Order {self.sales_order_number} - {self.customer_name}"


class SalesOrderLine(TimeStampedModel):
    """Sales order line item (SORDTRN equivalent)."""

    sales_order = models.ForeignKey(
        SalesOrder, on_delete=models.CASCADE, related_name="lines"
    )
    line_number = models.PositiveIntegerField()
    stock_code = models.CharField(max_length=13)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    selling_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    comments = models.CharField(max_length=30, blank=True)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["line_number"]
        unique_together = ["sales_order", "line_number"]
        verbose_name = "Sales Order Line (SORDTRN)"
        verbose_name_plural = "Sales Order Lines (SORDTRN)"
        indexes = [models.Index(fields=["stock_code"])]

    def __str__(self):
        return f"{self.sales_order.sales_order_number} - Line {self.line_number}: {self.stock_code}"


class JobCosting(TimeStampedModel):
    """Job Costing Card (JMAST table)."""

    JOB_STATUS_CHOICES = [("A", "Active"), ("C", "Cancelled"), ("D", "Complete")]

    job_number = models.CharField(
        max_length=6, unique=True, db_index=True, help_text="Job # (6 digits)"
    )
    job_date = models.DateField(db_index=True)
    time_start = models.CharField(max_length=5, blank=True)
    customer_name = models.CharField(max_length=40)
    address_line1 = models.CharField(max_length=25, blank=True)
    address_line2 = models.CharField(max_length=25, blank=True)
    address_line3 = models.CharField(max_length=25, blank=True)
    order_number = models.CharField(max_length=10, blank=True)
    vehicle_registration = models.CharField(max_length=10, blank=True)
    vehicle_make_model = models.CharField(max_length=15, blank=True)
    odometer_reading = models.DecimalField(
        max_digits=7, decimal_places=0, null=True, blank=True
    )
    telephone = models.CharField(max_length=25, blank=True)
    contact_person = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=1, choices=JOB_STATUS_CHOICES, default="A")
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salesman_number = models.PositiveIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(99)]
    )
    station_number = models.PositiveIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(99)]
    )
    debtor = models.ForeignKey(
        Debtor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_costings",
    )
    completion_date = models.DateField(null=True, blank=True)
    time_completed = models.CharField(max_length=5, blank=True)
    amount_charged = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transaction_number = models.PositiveIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(999999)]
    )
    transaction_type = models.CharField(max_length=1, blank=True)
    station_completion = models.CharField(max_length=2, blank=True)
    operator_number = models.CharField(max_length=10, blank=True)
    comment_line1 = models.CharField(max_length=30, blank=True)
    comment_line2 = models.CharField(max_length=30, blank=True)
    comment_line3 = models.CharField(max_length=30, blank=True)
    comment_line4 = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["-job_date", "-job_number"]
        verbose_name = "Job Costing (JMAST)"
        verbose_name_plural = "Job Costing Records (JMAST)"
        indexes = [
            models.Index(fields=["job_date"]),
            models.Index(fields=["debtor", "job_date"]),
            models.Index(fields=["status", "job_date"]),
            models.Index(fields=["vehicle_registration"]),
        ]

    def __str__(self):
        return f"Job {self.job_number} - {self.customer_name} ({self.job_date})"

    def clean(self):
        if self.total_value < 0:
            raise ValidationError("Total value cannot be negative.")
        if self.amount_charged < 0:
            raise ValidationError("Amount charged cannot be negative.")
        if self.amount_charged > self.total_value and self.total_value > 0:
            raise ValidationError("Amount charged cannot exceed total job value.")
        if self.completion_date and self.job_date > self.completion_date:
            raise ValidationError("Completion date cannot be before job date.")
        if self.status == "D" and not self.completion_date:
            raise ValidationError(
                "Completion date is required when job status is Complete."
            )

    def mark_complete(self):
        self.status = "D"
        if not self.completion_date:
            self.completion_date = date.today()
        self.save()

    def cancel_job(self):
        self.status = "C"
        self.save()


class JobCostingTransaction(TimeStampedModel):
    """Job Costing Transaction Details (JTRAN table)."""

    job_costing = models.ForeignKey(
        JobCosting, on_delete=models.CASCADE, related_name="transactions"
    )
    code = models.CharField(max_length=13)
    quantity = models.DecimalField(max_digits=12, decimal_places=4)
    selling_price = models.DecimalField(max_digits=12, decimal_places=4)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    department = models.CharField(max_length=3, blank=True)
    tax_code = models.CharField(max_length=1, blank=True)
    comments = models.CharField(max_length=30, blank=True)
    transaction_date = models.DateField(db_index=True)

    class Meta:
        ordering = ["transaction_date", "created_at"]
        verbose_name = "Job Costing Transaction (JTRAN)"
        verbose_name_plural = "Job Costing Transactions (JTRAN)"
        indexes = [
            models.Index(fields=["job_costing", "transaction_date"]),
            models.Index(fields=["code"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self):
        return f"JTRAN - Job {self.job_costing.job_number} - {self.code} ({self.transaction_date})"

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity cannot be negative.")
        if self.selling_price < 0:
            raise ValidationError("Selling price cannot be negative.")
        if self.cost_price < 0:
            raise ValidationError("Cost price cannot be negative.")
        if not 0 <= self.discount <= 100:
            raise ValidationError("Discount must be between 0 and 100.")
        if self.transaction_date > date.today():
            raise ValidationError("Transaction date cannot be in the future.")

    def get_line_total(self):
        discount_factor = Decimal(1) - (self.discount / Decimal(100))
        return self.quantity * self.selling_price * discount_factor

    def get_line_cost(self):
        return self.quantity * self.cost_price

    def get_line_profit(self):
        return self.get_line_total() - self.get_line_cost()


class JobPerson(TimeStampedModel):
    """Job Operator/Person (JPERSON table)."""

    operator_number = models.CharField(
        max_length=10, unique=True, db_index=True, help_text="Operator number"
    )
    operator_name = models.CharField(max_length=20, help_text="Operator name")

    class Meta:
        ordering = ["operator_number"]
        verbose_name = "Job Operator (JPERSON)"
        verbose_name_plural = "Job Operators (JPERSON)"
        indexes = [
            models.Index(fields=["operator_number"]),
            models.Index(fields=["operator_name"]),
        ]

    def __str__(self):
        return f"{self.operator_number} - {self.operator_name}"


class JobPrinting(TimeStampedModel):
    """Job Printing Configuration (JPRINT table)."""

    station = models.CharField(
        max_length=2, unique=True, db_index=True, help_text="Station number"
    )
    job_cards_station = models.CharField(max_length=1, blank=True)
    job_invoices_station = models.CharField(max_length=1, blank=True)
    job_reports_station = models.CharField(max_length=1, blank=True)

    class Meta:
        ordering = ["station"]
        verbose_name = "Job Printing Configuration (JPRINT)"
        verbose_name_plural = "Job Printing Configurations (JPRINT)"
        indexes = [models.Index(fields=["station"])]

    def __str__(self):
        return f"JPRINT - Station {self.station}"
