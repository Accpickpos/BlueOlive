"""
Debtors services.
Business logic for debtor transactions and operations.
"""
from django.db import transaction
from django.db.models import Sum, F, Q
from decimal import Decimal
from datetime import date, timedelta
from .models import Debtor, DebtorTransaction, Debtopen, Dpdc, DebtorAudit, Darea


class DebtorService:
    """Service class for debtor operations."""
    
    @staticmethod
    def calculate_age_analysis(debtor):
        """Calculate age analysis for a debtor."""
        return {
            'dno': debtor.dno,
            'dname': debtor.dname,
            'dcontact': debtor.dcontact,
            'dtel': debtor.dtel,
            'dclimit': debtor.dclimit,
            'current': debtor.dcrnt,
            'days_30': debtor.d30,
            'days_60': debtor.d60,
            'days_90': debtor.d90,
            'days_120': debtor.d120,
            'days_150': debtor.d150,
            'days_180': debtor.d180,
            'total_balance': debtor.get_total_balance(),
            'overdue_balance': debtor.get_overdue_balance(),
            'ddatlpd': debtor.ddatlpd,
            'damtlpd': debtor.damtlpd,
        }
    
    @staticmethod
    def get_debtors_summary():
        """Get summary statistics for all debtors."""
        debtors = Debtor.objects.all()
        
        total_debtors = debtors.count()
        blocked_debtors = debtors.filter(blockflag='Y').count()
        active_debtors = total_debtors - blocked_debtors
        
        aggregates = debtors.aggregate(
            total_balance=Sum(F('dcrnt') + F('d30') + 
                            F('d60') + F('d90') +
                            F('d120') + F('d150') +
                            F('d180')),
            current_balance=Sum('dcrnt'),
            overdue_30=Sum('d30'),
            overdue_60=Sum('d60'),
            overdue_90=Sum('d90'),
            overdue_120=Sum(F('d120') + F('d150') + 
                          F('d180')),
            total_credit_limit=Sum('dclimit'),
        )
        
        total_balance = aggregates['total_balance'] or Decimal('0.00')
        total_credit_limit = aggregates['total_credit_limit'] or Decimal('0.00')
        
        # Calculate utilization percentage
        utilization_percentage = float(total_credit_limit) / 100 if total_credit_limit > 0 else 0
        
        return {
            'total_debtors': total_debtors,
            'active_debtors': active_debtors,
            'blocked_debtors': blocked_debtors,
            'total_balance': total_balance,
            'current_balance': aggregates['current_balance'] or Decimal('0.00'),
            'overdue_30': aggregates['overdue_30'] or Decimal('0.00'),
            'overdue_60': aggregates['overdue_60'] or Decimal('0.00'),
            'overdue_90': aggregates['overdue_90'] or Decimal('0.00'),
            'overdue_120_plus': aggregates['overdue_120'] or Decimal('0.00'),
            'total_credit_limit': total_credit_limit,
            'utilization_percentage': utilization_percentage,
            'total_receivable': total_balance,
            'aging_summary': {
                'current': aggregates['current_balance'] or Decimal('0.00'),
                'days_30': aggregates['overdue_30'] or Decimal('0.00'),
                'days_60': aggregates['overdue_60'] or Decimal('0.00'),
                'days_90': aggregates['overdue_90'] or Decimal('0.00'),
                'days_120_plus': aggregates['overdue_120'] or Decimal('0.00'),
            },
            'critical_aging': aggregates['overdue_120'] or Decimal('0.00'),
        }
    
    @staticmethod
    @transaction.atomic
    def post_debtran(debtor, dtype, dttot, dtsub=None, dtgst=None, ordno='',
                     custref='', del1='', del2='', del3='', del4=''):
        """
        Post a transaction to the debtor's account (DEBTRAN).
        Updates debtor balance and creates transaction record.
        
        Args:
            debtor: Debtor instance
            dtype: Transaction type (IN=Invoice, CN=Credit Note, RCP=Receipt, etc.)
            dttot: Total amount
            dtsub: Amount excl VAT
            dtgst: VAT amount
            ordno: Order number
            custref: Customer reference
            del1-4: Delivery details
        """
        if debtor.blockflag == 'Y':
            raise ValueError(f"Account {debtor.dno} is blocked")
        
        # Calculate defaults if not provided
        if dtsub is None:
            dtsub = dttot
        if dtgst is None:
            dtgst = Decimal('0.00')
        
        # Create sequential transaction number
        last_tran = DebtorTransaction.objects.filter(dno=debtor).order_by('-dtrano').first()
        new_dtrano = str(int(last_tran.dtrano) + 1).zfill(6) if last_tran else '000001'
        
        # Create debtor transaction (DEBTRAN)
        trans = DebtorTransaction.objects.create(
            dno=debtor,
            dtrano=new_dtrano,
            dtype=dtype,
            dtdate=date.today(),
            dtsub=dtsub,
            dtgst=dtgst,
            dttot=dttot,
            dtaxstat='S',  # Default to Taxable
            source='API',
            ordno=ordno,
            custref=custref,
            del1=del1,
            del2=del2,
            del3=del3,
            del4=del4,
        )
        
        # Determine if transaction increases or decreases balance
        if dtype in ['IN', 'DM']:  # Invoice, Debit Memo
            balance_change = dttot
        elif dtype in ['CN', 'CM']:  # Credit Note, Credit Memo
            balance_change = -dttot
        elif dtype in ['RCP', 'JC']:  # Receipt, Journal Credit
            balance_change = -dttot
        else:
            balance_change = dttot
        
        # Update debtor balance (goes to current)
        debtor.dcrnt += balance_change
        debtor.dsalesm += dttot if dtype == 'IN' else Decimal('0.00')
        debtor.dsalesy += dttot if dtype == 'IN' else Decimal('0.00')
        debtor.save()
        
        # Create open item record (DEBTOPEN) for Balance Forward accounts
        if debtor.acctype != 'O':  # Only for Balance Forward accounts
            Debtopen.objects.create(
                dno=debtor,
                dtrano=new_dtrano,
                type=dtype,
                date=date.today(),
                total=abs(dttot),
                balancedue=abs(dttot) if balance_change > 0 else Decimal('0.00'),
                ageflag=0,  # Current
                posted=True,
            )
        
        # Create audit record (DEBTORAUD)
        DebtorAudit.objects.create(
            dno=debtor,
            dtrano=new_dtrano,
            type=dtype,
            thistype=dtype,
            thistran=new_dtrano,
            date=date.today(),
            amount=dttot,
        )
        
        return trans
    
    @staticmethod
    @transaction.atomic
    def post_receipt(debtor, amount, ordno='', custref=''):
        """
        Post a receipt (payment) to the debtor's account.
        
        Args:
            debtor: Debtor instance
            amount: Payment amount
            ordno: Order reference
            custref: Customer reference
        """
        if debtor.blockflag == 'Y':
            raise ValueError(f"Account {debtor.dno} is blocked")
        
        if amount <= 0:
            raise ValueError("Receipt amount must be positive")
        
        # Create receipt transaction
        trans = DebtorService.post_debtran(
            debtor=debtor,
            dtype='RCP',
            dttot=amount,
            dtsub=amount,
            dtgst=Decimal('0.00'),
            ordno=ordno,
            custref=custref,
        )
        
        # Update payment tracking
        debtor.ddatlpd = date.today()
        debtor.damtlpd = amount
        debtor.save()
        
        return trans
    
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
        if debtor.dintflag != 'Y':
            return Decimal('0.00')
        
        interest_base = Decimal('0.00')
        
        if start_period <= 2:
            interest_base += debtor.d30
        if start_period <= 3:
            interest_base += debtor.d60
        if start_period <= 4:
            interest_base += debtor.d90
        if start_period <= 5:
            interest_base += debtor.d120
        if start_period <= 6:
            interest_base += debtor.d150
        if start_period <= 7:
            interest_base += debtor.d180
        
        interest = interest_base * Decimal(str(rate))
        return interest.quantize(Decimal('0.01'))
    
    @staticmethod
    @transaction.atomic
    def charge_interest_batch(rate=0.01, start_period=2):
        """
        Charge interest on all debtors who have dintflag=Y.
        
        Returns:
            dict: Summary of interest charged
        """
        debtors = Debtor.objects.filter(dintflag='Y')
        
        total_interest = Decimal('0.00')
        debtors_charged = 0
        
        for debtor in debtors:
            interest = DebtorService.calculate_interest(
                debtor, rate, start_period
            )
            
            if interest > 0:
                # Create interest transaction (INT type)
                trans = DebtorService.post_debtran(
                    debtor=debtor,
                    dtype='INT',
                    dttot=interest,
                    dtsub=interest,
                    dtgst=Decimal('0.00'),
                    custref='Monthly Interest Charge',
                )
                
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
            dno=debtor,
            dtdate__gte=start_date,
            dtdate__lte=end_date
        ).order_by('dtdate')
        
        # Calculate opening balance (transactions before start_date)
        opening_transactions = DebtorTransaction.objects.filter(
            dno=debtor,
            dtdate__lt=start_date
        ).aggregate(
            total=Sum('dttot')
        )
        opening_balance = opening_transactions['total'] or Decimal('0.00')
        
        # Calculate closing balance
        closing_balance = opening_balance + transactions.aggregate(
            total=Sum('dttot')
        )['total'] or Decimal('0.00')
        
        return {
            'debtor': debtor,
            'opening_balance': opening_balance,
            'transactions': transactions,
            'closing_balance': closing_balance,
            'current_balance': debtor.dcrnt,
            'balance_30_days': debtor.d30,
            'balance_60_days': debtor.d60,
            'balance_90_days': debtor.d90,
            'balance_120_days': debtor.d120,
            'balance_150_days': debtor.d150,
            'balance_180_days': debtor.d180,
        }
    
    @staticmethod
    @transaction.atomic
    def age_balances():
        """
        Age all debtor balances by one period.
        This should be run at month-end.
        Shifts all aging buckets forward and resets current to zero.
        """
        debtors = Debtor.objects.all()
        
        for debtor in debtors:
            # Shift balances forward (age by one period)
            debtor.d180 = debtor.d150
            debtor.d150 = debtor.d120
            debtor.d120 = debtor.d90
            debtor.d90 = debtor.d60
            debtor.d60 = debtor.d30
            debtor.d30 = debtor.dcrnt
            debtor.dcrnt = Decimal('0.00')
            
            # Reset MTD stats but keep YTD
            debtor.dsalesm = Decimal('0.00')
            debtor.dprofitm = Decimal('0.00')
            
            debtor.save()
        
        return debtors.count()
    
    @staticmethod
    def check_credit_limit(debtor):
        """
        Check if debtor is over credit limit.
        
        Returns:
            dict: Credit limit status
        """
        total_balance = debtor.get_total_balance()
        credit_limit = debtor.dclimit
        
        over_limit = total_balance > credit_limit
        available_credit = credit_limit - total_balance
        
        return {
            'dno': debtor.dno,
            'dname': debtor.dname,
            'dclimit': credit_limit,
            'total_balance': total_balance,
            'available_credit': available_credit,
            'over_limit': over_limit,
            'percentage_used': (total_balance / credit_limit * 100) if credit_limit > 0 else 0,
        }
        
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