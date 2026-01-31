"""
SQLAlchemy ORM Models for POS System
Handles all transaction types, customer data, and cash control
Multi-tenant architecture with automatic schema routing
"""
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Boolean, ForeignKey,
    Enum, Text, Date, TIMESTAMP
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db_tenant import Base


# ==================== ENUMS ====================

class TransactionStatus(str, PyEnum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


class TransactionType(str, PyEnum):
    INVOICE = "INVOICE"
    CASH_SALE = "CASH_SALE"
    CREDIT_NOTE = "CREDIT_NOTE"
    CASH_RETURN = "CASH_RETURN"
    RECEIPT = "RECEIPT"
    LAYBYE = "LAYBYE"
    QUOTATION = "QUOTATION"
    JOB_COSTING = "JOB_COSTING"
    REPAIR_CONTROL = "REPAIR_CONTROL"
    PAYOUT = "PAYOUT"
    CASH_CHEQUE = "CASH_CHEQUE"
    PDC = "POST_DATED_CHEQUE"


class TaxCode(str, PyEnum):
    ZERO = "ZERO"
    STANDARD = "STANDARD"
    REDUCED = "REDUCED"


class TenderType(str, PyEnum):
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    CREDIT_CARD = "CREDIT_CARD"
    EFT = "EFT"
    SPEEDPOINT = "SPEEDPOINT"
    VOUCHER = "VOUCHER"


class ReceiptType(str, PyEnum):
    BALANCE_FORWARD = "BALANCE_FORWARD"
    OPEN_ITEM = "OPEN_ITEM"
    POST_DATED_CHEQUE = "POST_DATED_CHEQUE"


class LaybieStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FORFEITED = "FORFEITED"


class QuotationStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    CHARGED_OUT = "CHARGED_OUT"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    CONVERTED_TO_JOB = "CONVERTED_TO_JOB"


class JobStatus(str, PyEnum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    INVOICED = "INVOICED"


class RepairStatus(str, PyEnum):
    ISSUED_TO_SUPPLIER = "ISSUED_TO_SUPPLIER"
    RECEIVED = "RECEIVED"
    INVOICED = "INVOICED"
    CANCELLED = "CANCELLED"


# ==================== TRANSACTION HEADERS ====================

class Invoice(Base):
    """Invoice header - credit sale to debtors"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    debtor_account_number = Column(String(50), nullable=False, index=True)
    debtor_name = Column(String(255), nullable=False)
    
    invoice_date = Column(Date, nullable=False, index=True)
    delivery_date = Column(Date)
    
    subtotal = Column(Numeric(12, 2), default=0)
    discount_total = Column(Numeric(12, 2), default=0)
    tax_total = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), default=0)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.DRAFT)
    posted_at = Column(DateTime)
    
    order_number = Column(String(100))
    customer_reference = Column(String(100))
    job_card_number = Column(String(100))
    area_salesman_number = Column(String(100))
    comments = Column(Text)
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    
    __table_args__ = {'extend_existing': True}


class InvoiceLineItem(Base):
    """Invoice line items"""
    __tablename__ = "invoice_line_items"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    
    item_code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2))
    selling_price = Column(Numeric(10, 2), nullable=False)
    
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    
    tax_code = Column(Enum(TaxCode), default=TaxCode.STANDARD)
    tax_rate = Column(Numeric(5, 2), default=15)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    line_total = Column(Numeric(12, 2), default=0)
    gross_profit = Column(Numeric(12, 2))
    
    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")
    
    __table_args__ = {'extend_existing': True}


class CashSale(Base):
    """Cash sale transaction - immediate payment"""
    __tablename__ = "cash_sales"

    id = Column(Integer, primary_key=True)
    sale_number = Column(String(50), unique=True, nullable=False, index=True)
    
    sale_date = Column(Date, nullable=False, index=True)
    
    subtotal = Column(Numeric(12, 2), default=0)
    discount_total = Column(Numeric(12, 2), default=0)
    tax_total = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), default=0)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.DRAFT)
    posted_at = Column(DateTime)
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    line_items = relationship("CashSaleLineItem", back_populates="sale", cascade="all, delete-orphan")
    tenders = relationship("CashSaleTender", back_populates="sale", cascade="all, delete-orphan")
    
    __table_args__ = {'extend_existing': True}


class CashSaleLineItem(Base):
    """Cash sale line items"""
    __tablename__ = "cash_sale_line_items"

    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("cash_sales.id"), nullable=False)
    
    item_code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2))
    selling_price = Column(Numeric(10, 2), nullable=False)
    
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    
    tax_code = Column(Enum(TaxCode), default=TaxCode.STANDARD)
    tax_rate = Column(Numeric(5, 2), default=15)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    line_total = Column(Numeric(12, 2), default=0)
    
    sale = relationship("CashSale", back_populates="line_items")
    
    __table_args__ = {'extend_existing': True}


class CashSaleTender(Base):
    """Tenders received for cash sale"""
    __tablename__ = "cash_sale_tenders"

    id = Column(Integer, primary_key=True)
    sale_id = Column(Integer, ForeignKey("cash_sales.id"), nullable=False)
    
    tender_type = Column(Enum(TenderType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    
    # Cheque details
    cheque_number = Column(String(50))
    drawer_name = Column(String(255))
    bank = Column(String(255))
    account_number = Column(String(50))
    id_number = Column(String(50))
    phone = Column(String(20))
    
    created_at = Column(DateTime, server_default=func.now())
    
    sale = relationship("CashSale", back_populates="tenders")
    
    __table_args__ = {'extend_existing': True}


class Receipt(Base):
    """Receipt on account - payment from debtor"""
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True)
    receipt_number = Column(String(50), unique=True, nullable=False, index=True)
    debtor_account_number = Column(String(50), nullable=False, index=True)
    debtor_name = Column(String(255), nullable=False)
    
    receipt_date = Column(Date, nullable=False, index=True)
    receipt_type = Column(Enum(ReceiptType), default=ReceiptType.BALANCE_FORWARD)
    
    amount = Column(Numeric(12, 2), nullable=False)
    settlement_discount = Column(Numeric(12, 2), default=0)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.DRAFT)
    posted_at = Column(DateTime)
    
    notes = Column(Text)
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    tenders = relationship("ReceiptTender", back_populates="receipt", cascade="all, delete-orphan")
    
    __table_args__ = {'extend_existing': True}


class ReceiptTender(Base):
    """Tender details for receipt"""
    __tablename__ = "receipt_tenders"

    id = Column(Integer, primary_key=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False)
    
    tender_type = Column(Enum(TenderType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    
    # Cheque details
    cheque_number = Column(String(50))
    drawer_name = Column(String(255))
    bank = Column(String(255))
    account_number = Column(String(50))
    id_number = Column(String(50))
    phone = Column(String(20))
    
    created_at = Column(DateTime, server_default=func.now())
    
    receipt = relationship("Receipt", back_populates="tenders")
    
    __table_args__ = {'extend_existing': True}


class CreditNote(Base):
    """Credit note - return from invoice"""
    __tablename__ = "credit_notes"

    id = Column(Integer, primary_key=True)
    credit_note_number = Column(String(50), unique=True, nullable=False, index=True)
    debtor_account_number = Column(String(50), nullable=False, index=True)
    debtor_name = Column(String(255), nullable=False)
    
    credit_date = Column(Date, nullable=False, index=True)
    original_invoice_number = Column(String(50))  # If from invoice
    
    subtotal = Column(Numeric(12, 2), default=0)
    discount_total = Column(Numeric(12, 2), default=0)
    tax_total = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), default=0)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.DRAFT)
    posted_at = Column(DateTime)
    
    reason = Column(String(255))
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    line_items = relationship("CreditNoteLineItem", back_populates="credit_note", cascade="all, delete-orphan")
    
    __table_args__ = {'extend_existing': True}


class CreditNoteLineItem(Base):
    """Credit note line items"""
    __tablename__ = "credit_note_line_items"

    id = Column(Integer, primary_key=True)
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id"), nullable=False)
    
    item_code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    
    tax_code = Column(Enum(TaxCode), default=TaxCode.STANDARD)
    tax_rate = Column(Numeric(5, 2), default=15)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    line_total = Column(Numeric(12, 2), default=0)
    
    credit_note = relationship("CreditNote", back_populates="line_items")
    
    __table_args__ = {'extend_existing': True}


class CashReturn(Base):
    """Cash return - refund from cash sale"""
    __tablename__ = "cash_returns"

    id = Column(Integer, primary_key=True)
    return_number = Column(String(50), unique=True, nullable=False, index=True)
    
    return_date = Column(Date, nullable=False, index=True)
    original_sale_number = Column(String(50))  # If from cash sale
    
    subtotal = Column(Numeric(12, 2), default=0)
    discount_total = Column(Numeric(12, 2), default=0)
    tax_total = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), default=0)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.DRAFT)
    posted_at = Column(DateTime)
    
    reason = Column(String(255))
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    line_items = relationship("CashReturnLineItem", back_populates="cash_return", cascade="all, delete-orphan")
    tenders = relationship("CashReturnTender", back_populates="cash_return", cascade="all, delete-orphan")
    
    __table_args__ = {'extend_existing': True}


class CashReturnLineItem(Base):
    """Cash return line items"""
    __tablename__ = "cash_return_line_items"

    id = Column(Integer, primary_key=True)
    return_id = Column(Integer, ForeignKey("cash_returns.id"), nullable=False)
    
    item_code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    
    tax_code = Column(Enum(TaxCode), default=TaxCode.STANDARD)
    tax_rate = Column(Numeric(5, 2), default=15)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    line_total = Column(Numeric(12, 2), default=0)
    
    cash_return = relationship("CashReturn", back_populates="line_items")
    
    __table_args__ = {'extend_existing': True}


class CashReturnTender(Base):
    """Tenders for cash return"""
    __tablename__ = "cash_return_tenders"

    id = Column(Integer, primary_key=True)
    return_id = Column(Integer, ForeignKey("cash_returns.id"), nullable=False)
    
    tender_type = Column(Enum(TenderType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    
    cash_return = relationship("CashReturn", back_populates="tenders")
    
    __table_args__ = {'extend_existing': True}


class Laybye(Base):
    """Laybye - deferred payment arrangement"""
    __tablename__ = "laybyes"

    id = Column(Integer, primary_key=True)
    laybye_number = Column(String(50), unique=True, nullable=False, index=True)
    debtor_account_number = Column(String(50), nullable=False, index=True)
    debtor_name = Column(String(255), nullable=False)
    
    laybye_date = Column(Date, nullable=False, index=True)
    expiry_date = Column(Date, nullable=False)
    
    total_amount = Column(Numeric(12, 2), nullable=False)
    deposit_amount = Column(Numeric(12, 2), nullable=False)
    deposit_paid = Column(Numeric(12, 2), default=0)
    balance_remaining = Column(Numeric(12, 2), nullable=False)
    
    status = Column(Enum(LaybieStatus), default=LaybieStatus.ACTIVE)
    
    retention_percentage = Column(Numeric(5, 2), default=0)
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    line_items = relationship("LaybyeLineItem", back_populates="laybye", cascade="all, delete-orphan")
    payments = relationship("LaybyePayment", back_populates="laybye", cascade="all, delete-orphan")
    
    __table_args__ = {'extend_existing': True}


class LaybyeLineItem(Base):
    """Laybye stock items"""
    __tablename__ = "laybye_line_items"

    id = Column(Integer, primary_key=True)
    laybye_id = Column(Integer, ForeignKey("laybyes.id"), nullable=False)
    
    item_code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    
    tax_code = Column(Enum(TaxCode), default=TaxCode.STANDARD)
    tax_rate = Column(Numeric(5, 2), default=15)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    line_total = Column(Numeric(12, 2), default=0)
    
    laybye = relationship("Laybye", back_populates="line_items")
    
    __table_args__ = {'extend_existing': True}


class LaybyePayment(Base):
    """Laybye payment history"""
    __tablename__ = "laybye_payments"

    id = Column(Integer, primary_key=True)
    laybye_id = Column(Integer, ForeignKey("laybyes.id"), nullable=False)
    
    payment_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    
    tender_type = Column(Enum(TenderType), nullable=False)
    
    payment_number = Column(String(50))  # Cheque, reference, etc.
    
    created_at = Column(DateTime, server_default=func.now())
    
    laybye = relationship("Laybye", back_populates="payments")
    
    __table_args__ = {'extend_existing': True}


class Quotation(Base):
    """Quotation - price estimate"""
    __tablename__ = "quotations"

    id = Column(Integer, primary_key=True)
    quotation_number = Column(String(50), unique=True, nullable=False, index=True)
    debtor_account_number = Column(String(50), nullable=False, index=True)
    debtor_name = Column(String(255), nullable=False)
    
    quote_date = Column(Date, nullable=False, index=True)
    expiry_date = Column(Date, nullable=False)
    
    subtotal = Column(Numeric(12, 2), default=0)
    discount_total = Column(Numeric(12, 2), default=0)
    tax_total = Column(Numeric(12, 2), default=0)
    grand_total = Column(Numeric(12, 2), default=0)
    
    status = Column(Enum(QuotationStatus), default=QuotationStatus.ACTIVE)
    
    price_level = Column(String(50))  # Cost Price, Cost+Markup%, GP%, Selling Price 1-3
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    line_items = relationship("QuotationLineItem", back_populates="quotation", cascade="all, delete-orphan")
    
    __table_args__ = {'extend_existing': True}


class QuotationLineItem(Base):
    """Quotation line items"""
    __tablename__ = "quotation_line_items"

    id = Column(Integer, primary_key=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), nullable=False)
    
    item_code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2))
    selling_price = Column(Numeric(10, 2), nullable=False)
    
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    
    tax_code = Column(Enum(TaxCode), default=TaxCode.STANDARD)
    tax_rate = Column(Numeric(5, 2), default=15)
    tax_amount = Column(Numeric(10, 2), default=0)
    
    line_total = Column(Numeric(12, 2), default=0)
    
    quotation = relationship("Quotation", back_populates="line_items")
    
    __table_args__ = {'extend_existing': True}


class JobCosting(Base):
    """Job costing - service invoice"""
    __tablename__ = "job_costings"

    id = Column(Integer, primary_key=True)
    job_number = Column(String(50), unique=True, nullable=False, index=True)
    debtor_account_number = Column(String(50), nullable=False, index=True)
    debtor_name = Column(String(255), nullable=False)
    
    job_date = Column(Date, nullable=False, index=True)
    
    job_description = Column(String(255))
    job_location = Column(String(255))
    
    total_cost = Column(Numeric(12, 2), default=0)
    total_value = Column(Numeric(12, 2), default=0)
    job_margin = Column(Numeric(12, 2), default=0)
    
    status = Column(Enum(JobStatus), default=JobStatus.ACTIVE)
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    line_items = relationship("JobCostingLineItem", back_populates="job", cascade="all, delete-orphan")
    
    __table_args__ = {'extend_existing': True}


class JobCostingLineItem(Base):
    """Job costing line items - allocated stock"""
    __tablename__ = "job_costing_line_items"

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("job_costings.id"), nullable=False)
    
    item_code = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    cost_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)
    
    line_cost = Column(Numeric(12, 2), default=0)
    line_value = Column(Numeric(12, 2), default=0)
    
    job = relationship("JobCosting", back_populates="line_items")
    
    __table_args__ = {'extend_existing': True}


class RepairControl(Base):
    """Repair control - warranty/repair service"""
    __tablename__ = "repair_controls"

    id = Column(Integer, primary_key=True)
    repair_number = Column(String(50), unique=True, nullable=False, index=True)
    debtor_account_number = Column(String(50), nullable=False, index=True)
    debtor_name = Column(String(255), nullable=False)
    
    issue_date = Column(Date, nullable=False, index=True)
    
    repair_description = Column(String(255))
    supplier_name = Column(String(255))
    
    repair_cost = Column(Numeric(12, 2), default=0)
    repair_cost_vat_inclusive = Column(Boolean, default=False)
    repair_vat = Column(Numeric(12, 2), default=0)
    repair_total = Column(Numeric(12, 2), default=0)
    
    status = Column(Enum(RepairStatus), default=RepairStatus.ISSUED_TO_SUPPLIER)
    
    received_date = Column(Date)
    invoiced_date = Column(Date)
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = {'extend_existing': True}


class Payout(Base):
    """Payout - cash outflow/petty cash"""
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True)
    payout_number = Column(String(50), unique=True, nullable=False, index=True)
    
    payout_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    
    payout_type = Column(String(100))  # Petty cash, expense, etc.
    description = Column(String(255))
    
    approved_by = Column(String(100))
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = {'extend_existing': True}


class PostDatedCheque(Base):
    """Post-dated cheque tracking"""
    __tablename__ = "post_dated_cheques"

    id = Column(Integer, primary_key=True)
    pdc_number = Column(String(50), unique=True, nullable=False, index=True)
    
    debtor_account_number = Column(String(50), nullable=False, index=True)
    debtor_name = Column(String(255), nullable=False)
    
    cheque_number = Column(String(50), nullable=False)
    drawer_name = Column(String(255))
    bank = Column(String(255))
    account_number = Column(String(50))
    id_number = Column(String(50))
    phone = Column(String(20))
    
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = {'extend_existing': True}


class CashControl(Base):
    """Daily cash control & hourly analysis"""
    __tablename__ = "cash_control"

    id = Column(Integer, primary_key=True)
    
    control_date = Column(Date, nullable=False, index=True)
    control_hour = Column(Integer)  # 0-23 for hourly analysis
    cashier_id = Column(String(100), index=True)
    
    cash_sales = Column(Numeric(12, 2), default=0)
    cash_refunds = Column(Numeric(12, 2), default=0)
    account_invoices = Column(Numeric(12, 2), default=0)
    account_credits = Column(Numeric(12, 2), default=0)
    receipts = Column(Numeric(12, 2), default=0)
    settlement_discounts = Column(Numeric(12, 2), default=0)
    
    new_laybyes = Column(Numeric(12, 2), default=0)
    cancelled_laybyes = Column(Numeric(12, 2), default=0)
    completed_laybyes = Column(Numeric(12, 2), default=0)
    laybye_payments = Column(Numeric(12, 2), default=0)
    laybye_refunds = Column(Numeric(12, 2), default=0)
    
    payouts = Column(Numeric(12, 2), default=0)
    
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = {'extend_existing': True}


class TransactionQuery(Base):
    """Archive transaction details for historical query"""
    __tablename__ = "transaction_queries"

    id = Column(Integer, primary_key=True)
    
    transaction_type = Column(Enum(TransactionType), nullable=False)
    transaction_number = Column(String(50), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    transaction_time = Column(DateTime, server_default=func.now())
    
    debtor_account_number = Column(String(50), index=True)
    debtor_name = Column(String(255))
    
    amount = Column(Numeric(12, 2), nullable=False)
    profit = Column(Numeric(12, 2))
    gross_profit_percentage = Column(Numeric(5, 2))
    
    first_delivery_line_details = Column(String(500))  # For search
    
    created_by = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = {'extend_existing': True}
