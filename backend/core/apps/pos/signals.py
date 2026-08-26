"""
POS Signals for automatic calculations and updates.
Handles pre_save and post_save operations for POS models.
"""

import logging
from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .calculation_service import CalculationService
from .models import (
    CashReturn,
    CashReturnLine,
    CashSale,
    CashSaleLine,
    CreditNote,
    CreditNoteLine,
    JobCard,
    JobCardLine,
    Laybye,
    LaybyeLine,
    Quotation,
    QuotationLine,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Cash Sale Signals
# ============================================================================


@receiver(pre_save, sender=CashSaleLine)
def calculate_cash_sale_line_totals(sender, instance, **kwargs):
    """Calculate totals for cash sale line before saving."""
    if True:  # Recalculate on every save
        try:
            calcs = CalculationService.calculate_line_totals(
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                discount_percentage=instance.discount_percentage,
                tax_code=instance.tax_code,
                cost_price=instance.cost_price,
            )

            instance.line_total = calcs["line_total"]
            instance.vat_amount = calcs["vat_amount"]
            instance.line_profit = calcs["line_profit"]

        except Exception as e:
            logger.error(f"Error calculating cash sale line totals: {str(e)}")


@receiver(post_save, sender=CashSaleLine)
def update_cash_sale_header_after_line(sender, instance, created, **kwargs):
    """Update parent cash sale totals after line changes."""
    if True:  # recalculate on every save
        try:
            cash_sale = instance.cash_sale

            # Get all lines for this sale
            lines = cash_sale.lines.all()
            line_data = [
                {
                    "line_total_before_vat": line.line_total - line.vat_amount,
                    "vat_amount": line.vat_amount,
                    "line_cost": (
                        (line.quantity * line.cost_price)
                        if line.cost_price
                        else Decimal(0)
                    ),
                    "discount_amount": (
                        (
                            line.quantity
                            * line.unit_price
                            * (line.discount_percentage / 100)
                        )
                        if line.discount_percentage
                        else Decimal(0)
                    ),
                }
                for line in lines
            ]

            if line_data:
                totals = CalculationService.calculate_document_totals(line_data)

                cash_sale.subtotal = totals["subtotal"]
                cash_sale.vat_amount = totals["vat_amount"]
                cash_sale.total_amount = totals["total_amount"]
                cash_sale.discount_amount = totals["discount_total"]
                cash_sale.total_cost = totals["total_cost"]
                cash_sale.gross_profit = totals["gross_profit"]

                # Recalculate change
                if cash_sale.cash_tendered > 0:
                    cash_sale.change_given = (
                        cash_sale.cash_tendered - cash_sale.total_amount
                    )

                cash_sale.save(
                    update_fields=[
                        "subtotal",
                        "vat_amount",
                        "total_amount",
                        "discount_amount",
                        "total_cost",
                        "gross_profit",
                        "change_given",
                    ]
                )

        except Exception as e:
            logger.error(f"Error updating cash sale header: {str(e)}")


# ============================================================================
# Laybye Signals
# ============================================================================


@receiver(pre_save, sender=LaybyeLine)
def calculate_laybye_line_totals(sender, instance, **kwargs):
    """Calculate totals for laybye line before saving."""
    try:
        calcs = CalculationService.calculate_line_totals(
            quantity=instance.quantity,
            unit_price=instance.unit_price,
            discount_percentage=instance.discount_percentage,
            tax_code=instance.tax_code,
            cost_price=instance.cost_price,
        )

        instance.line_total = calcs["line_total"]
        instance.vat_amount = calcs["vat_amount"]

    except Exception as e:
        logger.error(f"Error calculating laybye line totals: {str(e)}")


@receiver(post_save, sender=LaybyeLine)
def update_laybye_header_after_line(sender, instance, created, **kwargs):
    """Update parent laybye totals after line changes."""
    if created or not created:  # recalculate on every save
        try:
            laybye = instance.laybye
            lines = laybye.lines.all()

            if lines.exists():
                total_amount = sum((line.line_total or Decimal(0)) for line in lines)

                laybye.total_amount = total_amount
                laybye.balance_due = total_amount - laybye.amount_paid

                laybye.save(update_fields=["total_amount", "balance_due"])

        except Exception as e:
            logger.error(f"Error updating laybye header: {str(e)}")


# ============================================================================
# Quotation Signals
# ============================================================================


@receiver(pre_save, sender=QuotationLine)
def calculate_quotation_line_totals(sender, instance, **kwargs):
    """Calculate totals for quotation line before saving."""
    if True:  # Recalculate on every save
        try:
            calcs = CalculationService.calculate_line_totals(
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                discount_percentage=instance.discount_percentage,
                tax_code=instance.tax_code,
                cost_price=instance.cost_price,
            )

            instance.line_total = calcs["line_total"]
            instance.vat_amount = calcs["vat_amount"]

        except Exception as e:
            logger.error(f"Error calculating quotation line totals: {str(e)}")


@receiver(post_save, sender=QuotationLine)
def update_quotation_header_after_line(sender, instance, created, **kwargs):
    """Update parent quotation totals after line changes."""
    if True:  # recalculate on every save
        try:
            quotation = instance.quotation
            lines = quotation.lines.all()

            if lines.exists():
                line_data = [
                    {
                        "line_total_before_vat": line.line_total - line.vat_amount,
                        "vat_amount": line.vat_amount,
                        "line_cost": (
                            (line.quantity * line.cost_price)
                            if line.cost_price
                            else Decimal(0)
                        ),
                    }
                    for line in lines
                ]

                totals = CalculationService.calculate_document_totals(line_data)

                quotation.subtotal = totals["subtotal"]
                quotation.vat_amount = totals["vat_amount"]
                quotation.total_amount = totals["total_amount"]
                quotation.gross_profit = totals["gross_profit"]

                quotation.save(
                    update_fields=[
                        "subtotal",
                        "vat_amount",
                        "total_amount",
                        "gross_profit",
                    ]
                )

        except Exception as e:
            logger.error(f"Error updating quotation header: {str(e)}")


# ============================================================================
# JobCard Signals
# ============================================================================


@receiver(pre_save, sender=JobCardLine)
def calculate_jobcard_line_totals(sender, instance, **kwargs):
    """Calculate totals for job card line before saving."""
    if True:  # Recalculate on every save
        try:
            calcs = CalculationService.calculate_line_totals(
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                discount_percentage=instance.discount_percentage,
                tax_code=instance.tax_code,
                cost_price=instance.cost_price,
            )

            instance.line_total = calcs["line_total"]
            instance.vat_amount = calcs["vat_amount"]
            instance.line_profit = calcs["line_profit"]

        except Exception as e:
            logger.error(f"Error calculating job card line totals: {str(e)}")


@receiver(post_save, sender=JobCardLine)
def update_jobcard_header_after_line(sender, instance, created, **kwargs):
    """Update parent job card totals after line changes."""
    if True:  # recalculate on every save
        try:
            job_card = instance.job_card
            lines = job_card.lines.all()

            if lines.exists():
                line_data = [
                    {
                        "line_total_before_vat": line.line_total - line.vat_amount,
                        "vat_amount": line.vat_amount,
                        "line_cost": (
                            (line.quantity * line.cost_price)
                            if line.cost_price
                            else Decimal(0)
                        ),
                    }
                    for line in lines
                ]

                totals = CalculationService.calculate_document_totals(line_data)

                job_card.subtotal = totals["subtotal"]
                job_card.vat_amount = totals["vat_amount"]
                job_card.total_amount = totals["total_amount"]
                job_card.total_cost = totals["total_cost"]
                job_card.gross_profit = totals["gross_profit"]

                job_card.save(
                    update_fields=[
                        "subtotal",
                        "vat_amount",
                        "total_amount",
                        "total_cost",
                        "gross_profit",
                    ]
                )

        except Exception as e:
            logger.error(f"Error updating job card header: {str(e)}")


# ============================================================================
# CreditNote Signals
# ============================================================================


@receiver(pre_save, sender=CreditNoteLine)
def calculate_creditnote_line_totals(sender, instance, **kwargs):
    """Calculate totals for credit note line before saving."""
    if True:  # Recalculate on every save
        try:
            calcs = CalculationService.calculate_line_totals(
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                discount_percentage=Decimal(0),  # Usually no discount on returns
                tax_code=instance.tax_code,
            )

            instance.line_total = calcs["line_total"]
            instance.vat_amount = calcs["vat_amount"]

        except Exception as e:
            logger.error(f"Error calculating credit note line totals: {str(e)}")


@receiver(post_save, sender=CreditNoteLine)
def update_creditnote_header_after_line(sender, instance, created, **kwargs):
    """Update parent credit note totals after line changes."""
    if True:  # recalculate on every save
        try:
            credit_note = instance.credit_note
            lines = credit_note.lines.all()

            if lines.exists():
                subtotal = sum(
                    (line.line_total or Decimal(0)) - (line.vat_amount or Decimal(0))
                    for line in lines
                )
                vat_amount = sum((line.vat_amount or Decimal(0)) for line in lines)
                total_amount = subtotal + vat_amount

                credit_note.subtotal = subtotal
                credit_note.vat_amount = vat_amount
                credit_note.total_amount = total_amount

                credit_note.save(
                    update_fields=["subtotal", "vat_amount", "total_amount"]
                )

        except Exception as e:
            logger.error(f"Error updating credit note header: {str(e)}")


# ============================================================================
# CashReturn Signals
# ============================================================================


@receiver(pre_save, sender=CashReturnLine)
def calculate_cashreturn_line_totals(sender, instance, **kwargs):
    """Calculate totals for cash return line before saving."""
    if True:  # Recalculate on every save
        try:
            calcs = CalculationService.calculate_line_totals(
                quantity=instance.quantity,
                unit_price=instance.unit_price,
                discount_percentage=Decimal(0),
                tax_code=instance.tax_code,
            )

            instance.line_total = calcs["line_total"]
            instance.vat_amount = calcs["vat_amount"]

        except Exception as e:
            logger.error(f"Error calculating cash return line totals: {str(e)}")


@receiver(post_save, sender=CashReturnLine)
def update_cashreturn_header_after_line(sender, instance, created, **kwargs):
    """Update parent cash return totals after line changes."""
    if True:  # recalculate on every save
        try:
            cash_return = instance.cash_return
            lines = cash_return.lines.all()

            if lines.exists():
                subtotal = sum(
                    (line.line_total or Decimal(0)) - (line.vat_amount or Decimal(0))
                    for line in lines
                )
                vat_amount = sum((line.vat_amount or Decimal(0)) for line in lines)
                total_amount = subtotal + vat_amount

                cash_return.subtotal = subtotal
                cash_return.vat_amount = vat_amount
                cash_return.total_amount = total_amount

                cash_return.save(
                    update_fields=["subtotal", "vat_amount", "total_amount"]
                )

        except Exception as e:
            logger.error(f"Error updating cash return header: {str(e)}")
