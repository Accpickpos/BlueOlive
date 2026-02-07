"""
Debtors services.
Business logic for debtor transactions and operations.
"""
from django.db import transaction
from django.db.models import Sum, F, Q
from decimal import Decimal
from datetime import date, timedelta
from .models import Debtor, DebtorTransaction, Invoice, InvoiceLine


class DebtorService:
    """Service class for debtor operations."""
    
    @staticmethod
    def calculate_age_analysis(debtor):
        """Calculate age analysis for a debtor."""
        return {
            'account_number': debtor.account_number,
            'name': debtor.name,
            'contact_person': debtor.contact_person,
            'telephone1': debtor.telephone1,
            'credit_limit': debtor.credit_limit,
            'current': debtor.current_balance,
            'days_30': debtor.balance_30_days,
            'days_60': debtor.balance_60_days,
            'days_90': debtor.balance_90_days,
            'days_120': debtor.balance_120_days,
            'days_150': debtor.balance_150_days,
            'days_180': debtor.balance_180_days,
            'total_balance': debtor.total_balance,
            'last_payment_date': debtor.last_payment_date,
            'last_payment_amount': debtor.last_payment_amount,
        }
    
    @staticmethod
    def get_debtors_summary():
        """Get summary statistics for all debtors."""
        debtors = Debtor.objects.all()
        
        total_debtors = debtors.count()
        active_debtors = debtors.filter(is_active=True).count()
        blocked_debtors = debtors.filter(is_blocked=True).count()
        
        aggregates = debtors.aggregate(
            total_balance=Sum(F('current_balance') + F('balance_30_days') + 
                            F('balance_60_days') + F('balance_90_days') +
                            F('balance_120_days') + F('balance_150_days') +
                            F('balance_180_days')),
            current_balance=Sum('current_balance'),
            overdue_30=Sum('balance_30_days'),
            overdue_60=Sum('balance_60_days'),
            overdue_90=Sum('balance_90_days'),
            overdue_120=Sum(F('balance_120_days') + F('balance_150_days') + 
                          F('balance_180_days')),
        )
        
        return {
            'total_debtors': total_debtors,
            'active_debtors': active_debtors,
            'blocked_debtors': blocked_debtors,
            'total_balance': aggregates['total_balance'] or Decimal('0.00'),
            'current_balance': aggregates['current_balance'] or Decimal('0.00'),
            'overdue_30': aggregates['overdue_30'] or Decimal('0.00'),
            'overdue_60': aggregates['overdue_60'] or Decimal('0.00'),
            'overdue_90': aggregates['overdue_90'] or Decimal('0.00'),
            'overdue_120_plus': aggregates['overdue_120'] or Decimal('0.00'),
        }
    
    @staticmethod
    @transaction.atomic
    def post_invoice(invoice):
        """
        Post an invoice to the debtor's account.
        Updates debtor balance and creates transaction record.
        """
        if invoice.is_posted:
            raise ValueError("Invoice is already posted")
        
        if invoice.is_cancelled:
            raise ValueError("Cannot post a cancelled invoice")
        
        debtor = invoice.debtor
        
        # Create debtor transaction
        DebtorTransaction.objects.create(
            debtor=debtor,
            transaction_type='INV',
            transaction_number=invoice.invoice_number,
            transaction_date=invoice.invoice_date,
            amount=invoice.subtotal,
            vat_amount=invoice.vat_amount,
            total_amount=invoice.total_amount,
            reference=invoice.order_number or '',
            additional_reference=invoice.customer_reference or '',
            age_current=invoice.total_amount,  # All goes to current
        )
        
        # Update debtor balance
        debtor.current_balance += invoice.total_amount
        debtor.sales_mtd += invoice.total_amount
        debtor.sales_ytd += invoice.total_amount
        debtor.save()
        
        # Mark invoice as posted
        invoice.is_posted = True
        invoice.save()
        
        return invoice
    
    @staticmethod
    @transaction.atomic
    def cancel_invoice(invoice, reason=''):
        """Cancel an invoice."""
        if invoice.is_cancelled:
            raise ValueError("Invoice is already cancelled")
        
        if invoice.is_posted:
            # If posted, need to reverse the transaction
            debtor = invoice.debtor
            
            # Create reversing transaction
            DebtorTransaction.objects.create(
                debtor=debtor,
                transaction_type='CRJ',
                transaction_number=f"CANC-{invoice.invoice_number}",
                transaction_date=date.today(),
                amount=-invoice.subtotal,
                vat_amount=-invoice.vat_amount,
                total_amount=-invoice.total_amount,
                reference=invoice.invoice_number,
                additional_reference=f"Cancelled: {reason}",
                age_current=-invoice.total_amount,
            )
            
            # Update debtor balance
            debtor.current_balance -= invoice.total_amount
            debtor.sales_mtd -= invoice.total_amount
            debtor.sales_ytd -= invoice.total_amount
            debtor.save()
        
        # Mark invoice as cancelled
        invoice.is_cancelled = True
        invoice.save()
        
        return invoice
    
    @staticmethod
    def calculate_interest(debtor, rate=0.01, start_period=2):
        """
        Calculate interest on overdue balances.
        
        Args:
            debtor: Debtor instance
            rate: Monthly interest rate (default 1%)
            start_period: Period from which to charge interest
                         (2=30days, 3=60days, etc.)
        
        Returns:
            Decimal: Interest amount
        """
        if not debtor.charge_interest:
            return Decimal('0.00')
        
        interest_base = Decimal('0.00')
        
        if start_period <= 2:
            interest_base += debtor.balance_30_days
        if start_period <= 3:
            interest_base += debtor.balance_60_days
        if start_period <= 4:
            interest_base += debtor.balance_90_days
        if start_period <= 5:
            interest_base += debtor.balance_120_days
        if start_period <= 6:
            interest_base += debtor.balance_150_days
        if start_period <= 7:
            interest_base += debtor.balance_180_days
        
        interest = interest_base * Decimal(str(rate))
        return interest.quantize(Decimal('0.01'))
    
    @staticmethod
    @transaction.atomic
    def charge_interest_batch(rate=0.01, start_period=2):
        """
        Charge interest on all debtors who have charge_interest=True.
        
        Returns:
            dict: Summary of interest charged
        """
        debtors = Debtor.objects.filter(
            charge_interest=True,
            is_active=True
        )
        
        total_interest = Decimal('0.00')
        debtors_charged = 0
        
        for debtor in debtors:
            interest = DebtorService.calculate_interest(
                debtor, rate, start_period
            )
            
            if interest > 0:
                # Create interest transaction
                DebtorTransaction.objects.create(
                    debtor=debtor,
                    transaction_type='INT',
                    transaction_number=f"INT-{date.today().strftime('%Y%m%d')}-{debtor.account_number}",
                    transaction_date=date.today(),
                    amount=interest,
                    vat_amount=Decimal('0.00'),
                    total_amount=interest,
                    reference='Monthly Interest Charge',
                    age_current=interest,
                )
                
                # Update debtor balance
                debtor.current_balance += interest
                debtor.save()
                
                total_interest += interest
                debtors_charged += 1
        
        return {
            'debtors_charged': debtors_charged,
            'total_interest': total_interest,
        }
    
    @staticmethod
    def get_debtor_statement(debtor, start_date=None, end_date=None):
        """
        Generate debtor statement for a period.
        
        Args:
            debtor: Debtor instance
            start_date: Start date (default: first day of current month)
            end_date: End date (default: today)
        
        Returns:
            dict: Statement data
        """
        if not start_date:
            start_date = date.today().replace(day=1)
        if not end_date:
            end_date = date.today()
        
        # Get transactions for period
        transactions = DebtorTransaction.objects.filter(
            debtor=debtor,
            transaction_date__gte=start_date,
            transaction_date__lte=end_date
        ).order_by('transaction_date')
        
        # Calculate opening balance (transactions before start_date)
        opening_transactions = DebtorTransaction.objects.filter(
            debtor=debtor,
            transaction_date__lt=start_date
        ).aggregate(
            total=Sum('total_amount')
        )
        opening_balance = opening_transactions['total'] or Decimal('0.00')
        
        # Calculate closing balance
        closing_balance = opening_balance + transactions.aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        return {
            'debtor': debtor,
            'opening_balance': opening_balance,
            'transactions': transactions,
            'closing_balance': closing_balance,
            'current_balance': debtor.current_balance,
            'balance_30_days': debtor.balance_30_days,
            'balance_60_days': debtor.balance_60_days,
            'balance_90_days': debtor.balance_90_days,
            'balance_120_days': debtor.balance_120_days,
            'balance_150_days': debtor.balance_150_days,
            'balance_180_days': debtor.balance_180_days,
        }
    
    @staticmethod
    @transaction.atomic
    def age_balances():
        """
        Age all debtor balances by one period.
        This should be run at month-end.
        """
        debtors = Debtor.objects.filter(is_active=True)
        
        for debtor in debtors:
            # Shift balances forward
            debtor.balance_180_days = debtor.balance_150_days
            debtor.balance_150_days = debtor.balance_120_days
            debtor.balance_120_days = debtor.balance_90_days
            debtor.balance_90_days = debtor.balance_60_days
            debtor.balance_60_days = debtor.balance_30_days
            debtor.balance_30_days = debtor.current_balance
            debtor.current_balance = Decimal('0.00')
            
            # Reset MTD stats
            debtor.sales_mtd = Decimal('0.00')
            
            debtor.save()
        
        return debtors.count()
    
    @staticmethod
    def check_credit_limit(debtor):
        """
        Check if debtor is over credit limit.
        
        Returns:
            dict: Credit limit status
        """
        total_balance = debtor.total_balance
        credit_limit = debtor.credit_limit
        
        over_limit = total_balance > credit_limit
        available_credit = credit_limit - total_balance
        
        return {
            'debtor': debtor.account_number,
            'credit_limit': credit_limit,
            'current_balance': total_balance,
            'available_credit': available_credit,
            'over_limit': over_limit,
            'percentage_used': (total_balance / credit_limit * 100) if credit_limit > 0 else 0,
        }


class InvoiceService:
    """Service class for invoice operations."""
    
    @staticmethod
    def calculate_totals(invoice):
        """Recalculate invoice totals from lines."""
        lines = invoice.lines.all()
        
        subtotal = Decimal('0.00')
        vat_amount = Decimal('0.00')
        total_cost = Decimal('0.00')
        
        for line in lines:
            subtotal += line.line_total
            vat_amount += line.vat_amount
            total_cost += (line.cost_price * line.quantity)
        
        invoice.subtotal = subtotal
        invoice.vat_amount = vat_amount
        invoice.total_amount = subtotal + vat_amount
        invoice.total_cost = total_cost
        invoice.gross_profit = subtotal - total_cost
        invoice.save()
        
        return invoice
    
    @staticmethod
    def get_top_customers(limit=10, period='month'):
        """
        Get top customers by sales value.
        
        Args:
            limit: Number of customers to return
            period: 'month', 'year', or 'all'
        
        Returns:
            QuerySet: Top debtors
        """
        today = date.today()
        
        if period == 'month':
            # This month
            start_date = today.replace(day=1)
            field = 'sales_mtd'
        elif period == 'year':
            # This year
            start_date = today.replace(month=1, day=1)
            field = 'sales_ytd'
        else:
            # All time - use YTD as proxy
            field = 'sales_ytd'
        
        return Debtor.objects.filter(
            is_active=True
        ).order_by(f'-{field}')[:limit]