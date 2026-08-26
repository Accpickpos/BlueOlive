"""
Period End Services - Day-End, Month-End, and Year-End Processing

This module provides services for:
- Day-End Process: Daily closing, balancing, and reset operations
- Month-End Process: Monthly closing, statistics generation, debtor aging
- Year-End Process: Annual closing and rollover

Each process can be run manually or scheduled via Celery Beat.
"""

import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.utils import timezone

logger = logging.getLogger(__name__)


class PeriodEndResult:
    """Result container for period-end operations"""

    def __init__(
        self,
        success: bool,
        message: str,
        details: Dict[str, Any] = None,
        errors: List[str] = None,
    ):
        self.success = success
        self.message = message
        self.details = details or {}
        self.errors = errors or []

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "message": self.message,
            "details": self.details,
            "errors": self.errors,
        }

    def __str__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{status}] {self.message}"


class DayEndService:
    """
    Day-End Process Service

    Performs daily closing operations including:
    - Daily sales summary
    - Daily cash book reconciliation status
    - Daily stock movement summary
    - Reset daily counters (optional)
    """

    @staticmethod
    @transaction.atomic
    def run_day_end(process_date: date = None, shop_id: int = None) -> PeriodEndResult:
        """
        Execute day-end process for a specific date.

        Args:
            process_date: Date to process (defaults to yesterday)
            shop_id: Optional shop ID to filter by (None = all shops)

        Returns:
            PeriodEndResult with operation status and details
        """
        if process_date is None:
            process_date = date.today() - timedelta(days=1)

        logger.info(f"Starting day-end process for {process_date}, shop_id={shop_id}")

        try:
            details = {
                "process_date": str(process_date),
                "shop_id": shop_id,
                "operations": [],
            }

            # 1. Generate daily sales summary
            sales_summary = DayEndService._generate_sales_summary(process_date, shop_id)
            details["operations"].append(sales_summary)

            # 2. Generate daily cash book summary
            cashbook_summary = DayEndService._generate_cashbook_summary(
                process_date, shop_id
            )
            details["operations"].append(cashbook_summary)

            # 3. Generate daily stock movement summary
            stock_summary = DayEndService._generate_stock_summary(process_date, shop_id)
            details["operations"].append(stock_summary)

            # 3b. Apply due future pricing (manual §3.1 [313.htm]: "Accpick
            # automatically updates the future prices for the following day
            # when Day End procedures are run")
            future_pricing_summary = DayEndService._apply_future_pricing(process_date)
            details["operations"].append(future_pricing_summary)

            # 4. Update last day-end date in configuration
            DayEndService._update_day_end_date(process_date)

            # Check for any errors
            errors = [
                op["message"]
                for op in details["operations"]
                if not op.get("success", True)
            ]

            if errors:
                result = PeriodEndResult(
                    success=False,
                    message=f"Day-end completed with {len(errors)} errors",
                    details=details,
                    errors=errors,
                )
            else:
                result = PeriodEndResult(
                    success=True,
                    message=f"Day-end completed successfully for {process_date}",
                    details=details,
                )

            DayEndService._save_report(process_date, shop_id, result)
            return result

        except Exception as e:
            logger.error(f"Day-end process failed: {str(e)}")
            result = PeriodEndResult(
                success=False,
                message=f"Day-end process failed: {str(e)}",
                errors=[str(e)],
            )
            DayEndService._save_report(process_date, shop_id, result)
            return result

    @staticmethod
    def _save_report(
        process_date: date, shop_id: Optional[int], result: "PeriodEndResult"
    ):
        """Persist the run so it can be listed/reprinted later (manual §8.6)."""
        try:
            from apps.settings.models import DayEndReport

            DayEndReport.objects.update_or_create(
                process_date=process_date,
                shop_id=shop_id,
                defaults={
                    "success": result.success,
                    "message": result.message,
                    "details": result.details,
                    "errors": result.errors,
                },
            )
        except Exception as e:
            # logger.error, not .warning: run_day_end() still reports success
            # to its caller even when this fails (the day-end operations
            # themselves genuinely succeeded) — this is the only signal that
            # the report itself, the whole point of this persistence layer,
            # didn't actually get saved and won't be listed/reprintable.
            logger.error(
                f"Could not save day-end report for {process_date} (shop_id={shop_id}): {e}"
            )

    @staticmethod
    def _generate_sales_summary(process_date: date, shop_id: int = None) -> Dict:
        """Generate daily sales summary"""
        try:
            from apps.pos.models import CashSale

            queryset = CashSale.objects.filter(
                sale_date=process_date, is_posted=True, is_cancelled=False
            )

            # Note: CashSale has no shop_id field yet - POS transactions aren't
            # shop-scoped, so shop_id filtering isn't applicable here.

            total_sales = queryset.aggregate(
                count=Count("id"), total=Sum("total_amount")
            )

            return {
                "operation": "sales_summary",
                "success": True,
                "message": f"Sales: {total_sales['count']} transactions, R{total_sales['total'] or 0}",
                "data": {
                    "transaction_count": total_sales["count"] or 0,
                    "total_amount": float(total_sales["total"] or 0),
                },
            }
        except Exception as e:
            return {
                "operation": "sales_summary",
                "success": False,
                "message": f"Sales summary failed: {str(e)}",
            }

    @staticmethod
    def _generate_cashbook_summary(process_date: date, shop_id: int = None) -> Dict:
        """Generate daily cash book summary"""
        try:
            from apps.cash_book.models import CashBookTransaction

            queryset = CashBookTransaction.objects.filter(
                transaction_date__date=process_date
            )

            if shop_id:
                queryset = queryset.filter(shop_id=shop_id)

            totals = queryset.aggregate(
                count=Count("id"),
                total_income=Sum("income_amount"),
                total_expense=Sum("expense_amount"),
            )

            return {
                "operation": "cashbook_summary",
                "success": True,
                "message": f"CashBook: {totals['count'] or 0} transactions",
                "data": {
                    "transaction_count": totals["count"] or 0,
                    "total_income": float(totals["total_income"] or 0),
                    "total_expense": float(totals["total_expense"] or 0),
                },
            }
        except Exception as e:
            return {
                "operation": "cashbook_summary",
                "success": False,
                "message": f"CashBook summary failed: {str(e)}",
            }

    @staticmethod
    def _generate_stock_summary(process_date: date, shop_id: int = None) -> Dict:
        """Generate daily stock movement summary"""
        try:
            from apps.stock_control.models import StockTransaction

            queryset = StockTransaction.objects.filter(
                transaction_date__date=process_date
            )

            if shop_id:
                queryset = queryset.filter(shop_id=shop_id)

            totals = queryset.aggregate(
                count=Count("id"),
                total_in=(
                    Sum("quantity_in")
                    if hasattr(StockTransaction, "quantity_in")
                    else 0
                ),
                total_out=(
                    Sum("quantity_out")
                    if hasattr(StockTransaction, "quantity_out")
                    else 0
                ),
            )

            return {
                "operation": "stock_summary",
                "success": True,
                "message": f"Stock: {totals['count'] or 0} movements",
                "data": {"movement_count": totals["count"] or 0},
            }
        except Exception as e:
            return {
                "operation": "stock_summary",
                "success": False,
                "message": f"Stock summary failed: {str(e)}",
            }

    @staticmethod
    def _apply_future_pricing(process_date: date) -> Dict:
        """
        Apply any FuturePricing records whose effective_date has arrived.
        Manual (§3.1 [313.htm]): future prices are set ahead of time and
        auto-applied "for the following day when Day End procedures are
        run" — this was previously only reachable via the manual, one-at-
        a-time FuturePricingViewSet.apply action (confirmed via repo-wide
        grep: no automatic trigger existed anywhere).
        """
        try:
            from apps.stock_control.models import FuturePricing

            due = FuturePricing.objects.filter(
                is_applied=False, effective_date__lte=process_date
            )
            applied_count = 0
            for fp in due:
                if fp.apply():
                    applied_count += 1

            return {
                "operation": "future_pricing",
                "success": True,
                "message": f"Future pricing: {applied_count} price change(s) applied",
                "data": {"applied_count": applied_count},
            }
        except Exception as e:
            return {
                "operation": "future_pricing",
                "success": False,
                "message": f"Future pricing apply failed: {str(e)}",
            }

    @staticmethod
    def _update_day_end_date(process_date: date):
        """Update the last day-end date in system configuration"""
        try:
            from apps.settings.models import SystemConfiguration

            config = SystemConfiguration.objects.first()
            if config:
                config.last_day_end_date = process_date
                config.save(update_fields=["last_day_end_date"])
        except Exception as e:
            logger.warning(f"Could not update day-end date: {e}")


class MonthEndService:
    """
    Month-End Process Service

    Performs monthly closing operations including:
    - Debtor aging (age balances by one period)
    - Generate monthly statistics (departments, sales areas)
    - Month-end cash book reconciliation
    - Advance accounting period
    """

    @staticmethod
    @transaction.atomic
    def run_month_end(
        process_date: date = None, advance_period: bool = True
    ) -> PeriodEndResult:
        """
        Execute month-end process for a specific date.

        Args:
            process_date: Month-end date to process (defaults to last month)
            advance_period: Whether to advance the accounting period

        Returns:
            PeriodEndResult with operation status and details
        """
        if process_date is None:
            # Default to last month
            today = date.today()
            if today.month == 1:
                process_date = date(today.year - 1, 12, 1)
            else:
                process_date = date(today.year, today.month - 1, 1)

        logger.info(f"Starting month-end process for {process_date}")

        try:
            details = {"process_date": str(process_date), "operations": []}

            # 1. Age debtor balances
            debtor_aging = MonthEndService._age_debtor_balances()
            details["operations"].append(debtor_aging)

            # 2. Generate department monthly stats
            dept_stats = MonthEndService._generate_department_stats(process_date)
            details["operations"].append(dept_stats)

            # 3. Generate sales area monthly stats
            area_stats = MonthEndService._generate_sales_area_stats(process_date)
            details["operations"].append(area_stats)

            # 4. Update last month-end date
            MonthEndService._update_month_end_date(process_date)

            # 5. Optionally advance accounting period
            if advance_period:
                period_advance = MonthEndService._advance_accounting_period(
                    process_date
                )
                details["operations"].append(period_advance)

            # Check for errors
            errors = [
                op["message"]
                for op in details["operations"]
                if not op.get("success", True)
            ]

            if errors:
                return PeriodEndResult(
                    success=False,
                    message=f"Month-end completed with {len(errors)} errors",
                    details=details,
                    errors=errors,
                )

            return PeriodEndResult(
                success=True,
                message=f"Month-end completed successfully for {process_date}",
                details=details,
            )

        except Exception as e:
            logger.error(f"Month-end process failed: {str(e)}")
            return PeriodEndResult(
                success=False,
                message=f"Month-end process failed: {str(e)}",
                errors=[str(e)],
            )

    @staticmethod
    @transaction.atomic
    def _age_debtor_balances() -> Dict:
        """Age debtor balances by one period"""
        try:
            from apps.debtors.services import DebtorService

            # Use the existing debtor aging service
            # Note: DebtorService.age_balances() is already decorated with @transaction.atomic
            # Additional wrapping here ensures the entire period-end operation can be rolled back
            # if this step fails
            count = DebtorService.age_balances()

            return {
                "operation": "debtor_aging",
                "success": True,
                "message": f"Aged {count} debtor accounts",
                "data": {"debtors_aged": count},
            }
        except Exception as e:
            logger.error(f"Debtor aging failed: {str(e)}")
            return {
                "operation": "debtor_aging",
                "success": False,
                "message": f"Debtor aging failed: {str(e)}",
            }

    @staticmethod
    def _generate_department_stats(process_date: date) -> Dict:
        """Generate monthly statistics for departments"""
        try:
            from apps.pos.models import CashSaleLine
            from apps.settings.models import DepartmentMonthlyStats, SalesDepartment
            from apps.stock_control.models import StockItem

            year = process_date.year
            month = process_date.month

            # Get all departments
            departments = SalesDepartment.objects.filter(is_active=True)
            created_count = 0

            for dept in departments:
                # CashSaleLine has no direct FK to StockItem, only a stock_code
                # CharField, so the department join goes through StockItem.
                dept_stock_codes = StockItem.objects.filter(
                    department=dept
                ).values_list("stock_code", flat=True)

                # Calculate stats for this department in the given month
                stats = CashSaleLine.objects.filter(
                    cash_sale__sale_date__year=year,
                    cash_sale__sale_date__month=month,
                    cash_sale__is_posted=True,
                    cash_sale__is_cancelled=False,
                    stock_code__in=dept_stock_codes,
                ).aggregate(
                    sales_value=Sum("line_total"),
                    profit_value=Sum("line_profit"),
                    count=Count("id"),
                )

                sales_value = stats["sales_value"] or Decimal("0")
                profit_value = stats["profit_value"] or Decimal("0")

                # Calculate profit percentage
                profit_percent = (
                    (profit_value / sales_value * 100)
                    if sales_value > 0
                    else Decimal("0")
                )

                # Create or update stats record
                DepartmentMonthlyStats.objects.update_or_create(
                    department=dept,
                    year=year,
                    month=month,
                    defaults={
                        "sales_value": sales_value,
                        "profit_value": profit_value,
                        "profit_percent": profit_percent,
                    },
                )
                created_count += 1

            return {
                "operation": "department_stats",
                "success": True,
                "message": f"Generated stats for {created_count} departments",
                "data": {"departments_processed": created_count},
            }
        except Exception as e:
            return {
                "operation": "department_stats",
                "success": False,
                "message": f"Department stats generation failed: {str(e)}",
            }

    @staticmethod
    def _generate_sales_area_stats(process_date: date) -> Dict:
        """Generate monthly statistics for sales areas"""
        try:
            from apps.pos.models import CashSale
            from apps.settings.models import SalesArea, SalesAreaMonthlyStats

            year = process_date.year
            month = process_date.month

            # Get all sales areas
            areas = SalesArea.objects.filter(is_active=True)
            created_count = 0

            for area in areas:
                # Calculate stats for this area in the given month
                sales = CashSale.objects.filter(
                    sale_date__year=year,
                    sale_date__month=month,
                    is_posted=True,
                    is_cancelled=False,
                    sales_area=area,
                ).aggregate(
                    sales_value=Sum("total_amount"),
                    profit_value=Sum("gross_profit"),
                    count=Count("id"),
                )

                sales_value = sales["sales_value"] or Decimal("0")
                profit_value = sales["profit_value"] or Decimal("0")

                # Calculate profit percentage
                profit_percent = (
                    (profit_value / sales_value * 100)
                    if sales_value > 0
                    else Decimal("0")
                )

                # Create or update stats record
                SalesAreaMonthlyStats.objects.update_or_create(
                    sales_area=area,
                    year=year,
                    month=month,
                    defaults={
                        "sales_value": sales_value,
                        "profit_value": profit_value,
                        "profit_percent": profit_percent,
                        "commission_earned": Decimal(
                            "0"
                        ),  # Could be calculated from sales
                    },
                )
                created_count += 1

            return {
                "operation": "sales_area_stats",
                "success": True,
                "message": f"Generated stats for {created_count} sales areas",
                "data": {"areas_processed": created_count},
            }
        except Exception as e:
            return {
                "operation": "sales_area_stats",
                "success": False,
                "message": f"Sales area stats generation failed: {str(e)}",
            }

    @staticmethod
    def _update_month_end_date(process_date: date):
        """Update the last month-end date in system configuration"""
        try:
            from apps.settings.models import SystemConfiguration

            config = SystemConfiguration.objects.first()
            if config:
                config.last_month_end_date = process_date
                config.save(update_fields=["last_month_end_date"])
        except Exception as e:
            logger.warning(f"Could not update month-end date: {e}")

    @staticmethod
    def _advance_accounting_period(process_date: date) -> Dict:
        """Advance the accounting period"""
        try:
            from apps.settings.models import SystemConfiguration

            config = SystemConfiguration.objects.first()
            if config:
                # Calculate next period
                current_period = config.current_period
                current_year = config.current_financial_year

                if current_period == 12:
                    new_period = 1
                    new_year = current_year + 1
                else:
                    new_period = current_period + 1
                    new_year = current_year

                config.current_period = new_period
                config.current_financial_year = new_year
                config.save(update_fields=["current_period", "current_financial_year"])

                return {
                    "operation": "advance_period",
                    "success": True,
                    "message": f"Advanced to period {new_period}/{new_year}",
                    "data": {"new_period": new_period, "new_year": new_year},
                }
            else:
                return {
                    "operation": "advance_period",
                    "success": False,
                    "message": "No system configuration found",
                }
        except Exception as e:
            return {
                "operation": "advance_period",
                "success": False,
                "message": f"Period advance failed: {str(e)}",
            }


class YearEndService:
    """
    Year-End Process Service

    Performs annual closing operations including:
    - Generate year-end financial snapshots
    - Archive old data (optional)
    - Reset year-to-date counters
    - Advance financial year
    """

    @staticmethod
    @transaction.atomic
    def run_year_end(
        process_year: int = None, advance_year: bool = True
    ) -> PeriodEndResult:
        """
        Execute year-end process for a specific year.

        Args:
            process_year: Year to process (defaults to previous year)
            advance_year: Whether to advance the financial year

        Returns:
            PeriodEndResult with operation status and details
        """
        if process_year is None:
            process_year = date.today().year - 1

        logger.info(f"Starting year-end process for {process_year}")

        try:
            details = {"process_year": process_year, "operations": []}

            # 1. Generate year-end summary
            summary = YearEndService._generate_year_end_summary(process_year)
            details["operations"].append(summary)

            # 2. Generate department year-to-date stats
            dept_ytd = YearEndService._generate_department_ytd(process_year)
            details["operations"].append(dept_ytd)

            # 3. Generate sales area year-to-date stats
            area_ytd = YearEndService._generate_sales_area_ytd(process_year)
            details["operations"].append(area_ytd)

            # 4. Update last year-end date
            YearEndService._update_year_end_date(process_year)

            # 5. Optionally advance financial year
            if advance_year:
                year_advance = YearEndService._advance_financial_year(process_year)
                details["operations"].append(year_advance)

            # Check for errors
            errors = [
                op["message"]
                for op in details["operations"]
                if not op.get("success", True)
            ]

            if errors:
                return PeriodEndResult(
                    success=False,
                    message=f"Year-end completed with {len(errors)} errors",
                    details=details,
                    errors=errors,
                )

            return PeriodEndResult(
                success=True,
                message=f"Year-end completed successfully for {process_year}",
                details=details,
            )

        except Exception as e:
            logger.error(f"Year-end process failed: {str(e)}")
            return PeriodEndResult(
                success=False,
                message=f"Year-end process failed: {str(e)}",
                errors=[str(e)],
            )

    @staticmethod
    def _generate_year_end_summary(process_year: int) -> Dict:
        """Generate year-end summary"""
        try:
            from apps.cash_book.models import CashBookTransaction
            from apps.creditors.models import Creditor
            from apps.debtors.models import Debtor
            from apps.pos.models import CashSale

            # Sales summary
            sales = CashSale.objects.filter(
                sale_date__year=process_year, is_posted=True, is_cancelled=False
            ).aggregate(
                count=Count("id"), total=Sum("total_amount"), profit=Sum("gross_profit")
            )

            # Cash book summary
            cashbook = CashBookTransaction.objects.filter(
                transaction_date__year=process_year
            ).aggregate(income=Sum("income_amount"), expense=Sum("expense_amount"))

            # Debtor summary
            total_debtors = Debtor.objects.count()
            total_debtor_balance = Debtor.objects.aggregate(
                total=Sum("dcrnt")
                + Sum("d30")
                + Sum("d60")
                + Sum("d90")
                + Sum("d120")
                + Sum("d150")
                + Sum("d180")
            )

            # Creditor summary
            total_creditors = Creditor.objects.count()
            total_creditor_balance = Creditor.objects.aggregate(total=Sum("balance"))

            return {
                "operation": "year_end_summary",
                "success": True,
                "message": f"Year-end summary generated for {process_year}",
                "data": {
                    "sales_count": sales["count"] or 0,
                    "sales_total": float(sales["total"] or 0),
                    "sales_profit": float(sales["profit"] or 0),
                    "cashbook_income": float(cashbook["income"] or 0),
                    "cashbook_expense": float(cashbook["expense"] or 0),
                    "total_debtors": total_debtors,
                    "total_debtor_balance": float(total_debtor_balance["total"] or 0),
                    "total_creditors": total_creditors,
                    "total_creditor_balance": float(
                        total_creditor_balance["total"] or 0
                    ),
                },
            }
        except Exception as e:
            return {
                "operation": "year_end_summary",
                "success": False,
                "message": f"Year-end summary failed: {str(e)}",
            }

    @staticmethod
    def _generate_department_ytd(process_year: int) -> Dict:
        """Generate year-to-date statistics for departments"""
        try:
            from apps.pos.models import CashSaleLine
            from apps.settings.models import DepartmentMonthlyStats, SalesDepartment
            from apps.stock_control.models import StockItem

            # Aggregate all months for the year
            departments = SalesDepartment.objects.filter(is_active=True)
            created_count = 0

            for dept in departments:
                dept_stock_codes = StockItem.objects.filter(
                    department=dept
                ).values_list("stock_code", flat=True)

                ytd_stats = CashSaleLine.objects.filter(
                    cash_sale__sale_date__year=process_year,
                    cash_sale__is_posted=True,
                    cash_sale__is_cancelled=False,
                    stock_code__in=dept_stock_codes,
                ).aggregate(
                    sales_value=Sum("line_total"), profit_value=Sum("line_profit")
                )

                sales_value = ytd_stats["sales_value"] or Decimal("0")
                profit_value = ytd_stats["profit_value"] or Decimal("0")

                dept.sales_ytd = sales_value
                dept.profit_ytd = profit_value
                dept.save(update_fields=["sales_ytd", "profit_ytd"])
                created_count += 1

            return {
                "operation": "department_ytd",
                "success": True,
                "message": f"Generated YTD stats for {created_count} departments",
                "data": {"departments_processed": created_count},
            }
        except Exception as e:
            return {
                "operation": "department_ytd",
                "success": False,
                "message": f"Department YTD failed: {str(e)}",
            }

    @staticmethod
    def _generate_sales_area_ytd(process_year: int) -> Dict:
        """Generate year-to-date statistics for sales areas"""
        try:
            from apps.pos.models import CashSale
            from apps.settings.models import SalesArea, SalesAreaMonthlyStats

            areas = SalesArea.objects.filter(is_active=True)
            created_count = 0

            for area in areas:
                ytd_stats = CashSale.objects.filter(
                    sale_date__year=process_year,
                    is_posted=True,
                    is_cancelled=False,
                    sales_area=area,
                ).aggregate(
                    sales_value=Sum("total_amount"), profit_value=Sum("gross_profit")
                )

                sales_value = ytd_stats["sales_value"] or Decimal("0")
                profit_value = ytd_stats["profit_value"] or Decimal("0")

                area.sales_ytd = sales_value
                area.profit_ytd = profit_value
                area.save(update_fields=["sales_ytd", "profit_ytd"])
                created_count += 1

            return {
                "operation": "sales_area_ytd",
                "success": True,
                "message": f"Generated YTD stats for {created_count} sales areas",
                "data": {"areas_processed": created_count},
            }
        except Exception as e:
            return {
                "operation": "sales_area_ytd",
                "success": False,
                "message": f"Sales area YTD failed: {str(e)}",
            }

    @staticmethod
    def _update_year_end_date(process_year: int):
        """Update the last year-end date in system configuration"""
        try:
            from apps.settings.models import SystemConfiguration

            config = SystemConfiguration.objects.first()
            if config:
                config.last_year_end_date = date(process_year, 12, 31)
                config.save(update_fields=["last_year_end_date"])
        except Exception as e:
            logger.warning(f"Could not update year-end date: {e}")

    @staticmethod
    def _advance_financial_year(process_year: int) -> Dict:
        """Advance the financial year"""
        try:
            from apps.settings.models import SystemConfiguration

            config = SystemConfiguration.objects.first()
            if config:
                new_year = process_year + 1
                config.current_financial_year = new_year
                config.current_period = 1  # Reset to first period
                config.save(update_fields=["current_financial_year", "current_period"])

                return {
                    "operation": "advance_year",
                    "success": True,
                    "message": f"Advanced to financial year {new_year}",
                    "data": {"new_year": new_year},
                }
            else:
                return {
                    "operation": "advance_year",
                    "success": False,
                    "message": "No system configuration found",
                }
        except Exception as e:
            return {
                "operation": "advance_year",
                "success": False,
                "message": f"Year advance failed: {str(e)}",
            }
