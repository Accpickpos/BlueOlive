"""
Database configuration and SQLAlchemy models
Now with Multi-Tenant Schema Support
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, ForeignKey, 
    Numeric, Text, Enum as SQLEnum, Index, Table
)
from sqlalchemy.orm import relationship

# Import Base and get_db from db_tenant for multi-tenant support
# This ensures all models work with tenant-specific schemas
from db_tenant import Base, get_db


# Enums
class TransactionStatus(str, __import__('enum').Enum):
    """Transaction status values"""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


class TaxCode(str, __import__('enum').Enum):
    """Tax code values"""
    ZERO = "ZERO"
    STANDARD = "STANDARD"
    REDUCED = "REDUCED"


class TenderType(str, __import__('enum').Enum):
    """Tender type values"""
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    CREDIT_CARD = "CREDIT_CARD"
    EFT = "EFT"


class ReceiptType(str, __import__('enum').Enum):
    """Receipt type values"""
    BALANCE_FORWARD = "BALANCE_FORWARD"
    OPEN_ITEM = "OPEN_ITEM"
    POST_DATED_CHEQUE = "POST_DATED_CHEQUE"


class LaybieStatus(str, __import__('enum').Enum):
    """Laybye status values"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FORFEITED = "FORFEITED"


# Models - All stored in tenant-specific schema

class Invoice(Base):
    """Invoice transaction model"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, index=True)
    debtor_account_number = Column(String(50), index=True)
    invoice_date = Column(DateTime, default=datetime.utcnow, index=True)
    delivery_date = Column(DateTime, nullable=True)
    delivery_details = Column(String(500), nullable=True)
    reg_make_names = Column(String(500), nullable=True)
    credit_card = Column(String(50), nullable=True)
    order_number = Column(String(50), nullable=True)
    customer_ref = Column(String(100), nullable=True)
    sman_area = Column(String(100), nullable=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    # Financial fields
    subtotal = Column(Numeric(15, 2), default=0)
    subtotal_discount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    gross_profit = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_invoice_number", "invoice_number"),
        Index("idx_debtor_account", "debtor_account_number"),
        Index("idx_invoice_date", "invoice_date"),
    )


class InvoiceLineItem(Base):
    """Invoice line item model"""
    __tablename__ = "invoice_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), index=True)
    item_code = Column(String(50), index=True)
    description = Column(String(255))
    quantity = Column(Numeric(10, 2))
    cost_price = Column(Numeric(15, 2))
    selling_price = Column(Numeric(15, 2))
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_code = Column(SQLEnum(TaxCode), default=TaxCode.STANDARD)
    tax_amount = Column(Numeric(15, 2), default=0)
    line_total = Column(Numeric(15, 2))
    gross_profit = Column(Numeric(15, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    invoice = relationship("Invoice", back_populates="line_items")


class CashSale(Base):
    """Cash sale transaction model"""
    __tablename__ = "cash_sales"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String(50), unique=True, index=True)
    receipt_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    # Financial fields
    subtotal = Column(Numeric(15, 2), default=0)
    subtotal_discount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    gross_profit = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    
    # Rounding
    rounding_adjustment = Column(Numeric(15, 4), default=0)
    final_amount = Column(Numeric(15, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    line_items = relationship("CashSaleLineItem", back_populates="cash_sale", cascade="all, delete-orphan")
    tenders = relationship("CashSaleTender", back_populates="cash_sale", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_receipt_number", "receipt_number"),
        Index("idx_receipt_date", "receipt_date"),
    )


class CashSaleLineItem(Base):
    """Cash sale line item model"""
    __tablename__ = "cash_sale_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    cash_sale_id = Column(Integer, ForeignKey("cash_sales.id"), index=True)
    item_code = Column(String(50), index=True)
    description = Column(String(255))
    quantity = Column(Numeric(10, 2))
    cost_price = Column(Numeric(15, 2))
    selling_price = Column(Numeric(15, 2))
    discount_percentage = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_code = Column(SQLEnum(TaxCode), default=TaxCode.STANDARD)
    tax_amount = Column(Numeric(15, 2), default=0)
    line_total = Column(Numeric(15, 2))
    gross_profit = Column(Numeric(15, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    cash_sale = relationship("CashSale", back_populates="line_items")


class CashSaleTender(Base):
    """Cash sale tender model"""
    __tablename__ = "cash_sale_tenders"
    
    id = Column(Integer, primary_key=True, index=True)
    cash_sale_id = Column(Integer, ForeignKey("cash_sales.id"), index=True)
    tender_type = Column(SQLEnum(TenderType), default=TenderType.CASH)
    amount = Column(Numeric(15, 2))
    change_amount = Column(Numeric(15, 2), default=0)
    reference = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    cash_sale = relationship("CashSale", back_populates="tenders")


class CreditNote(Base):
    """Credit note transaction model"""
    __tablename__ = "credit_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    credit_note_number = Column(String(50), unique=True, index=True)
    debtor_account_number = Column(String(50), index=True)
    reference_invoice_number = Column(String(50), nullable=True)
    credit_note_date = Column(DateTime, default=datetime.utcnow, index=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    # Financial fields
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    
    # Relationships
    line_items = relationship("CreditNoteLineItem", back_populates="credit_note", cascade="all, delete-orphan")


class CreditNoteLineItem(Base):
    """Credit note line item model"""
    __tablename__ = "credit_note_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    credit_note_id = Column(Integer, ForeignKey("credit_notes.id"), index=True)
    item_code = Column(String(50), index=True)
    description = Column(String(255))
    quantity = Column(Numeric(10, 2))
    cost_price = Column(Numeric(15, 2))
    selling_price = Column(Numeric(15, 2))
    discount_percentage = Column(Numeric(5, 2), default=0)
    tax_code = Column(SQLEnum(TaxCode), default=TaxCode.STANDARD)
    tax_amount = Column(Numeric(15, 2), default=0)
    line_total = Column(Numeric(15, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    credit_note = relationship("CreditNote", back_populates="line_items")


class Receipt(Base):
    """Receipt on account transaction model"""
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_number = Column(String(50), unique=True, index=True)
    debtor_account_number = Column(String(50), index=True)
    receipt_date = Column(DateTime, default=datetime.utcnow, index=True)
    receipt_type = Column(SQLEnum(ReceiptType), default=ReceiptType.OPEN_ITEM)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    # Financial fields
    receipt_amount = Column(Numeric(15, 2))
    cash_discount = Column(Numeric(15, 2), default=0)
    final_amount = Column(Numeric(15, 2))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    tenders = relationship("ReceiptTender", back_populates="receipt", cascade="all, delete-orphan")


class ReceiptTender(Base):
    """Receipt tender model"""
    __tablename__ = "receipt_tenders"
    
    id = Column(Integer, primary_key=True, index=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), index=True)
    tender_type = Column(SQLEnum(TenderType), default=TenderType.CASH)
    amount = Column(Numeric(15, 2))
    reference = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    receipt = relationship("Receipt", back_populates="tenders")


class Laybye(Base):
    """Laybye transaction model"""
    __tablename__ = "laybyes"
    
    id = Column(Integer, primary_key=True, index=True)
    laybye_number = Column(String(50), unique=True, index=True)
    debtor_account_number = Column(String(50), nullable=True, index=True)
    laybye_date = Column(DateTime, default=datetime.utcnow, index=True)
    deposit_amount = Column(Numeric(15, 2))
    retention_amount = Column(Numeric(15, 2), default=0)
    status = Column(SQLEnum(LaybieStatus), default=LaybieStatus.ACTIVE)
    
    # Financial fields
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    paid_amount = Column(Numeric(15, 2), default=0)
    outstanding_amount = Column(Numeric(15, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    line_items = relationship("LaybeyLineItem", back_populates="laybye", cascade="all, delete-orphan")
    payments = relationship("LaybeyPayment", back_populates="laybye", cascade="all, delete-orphan")


class LaybeyLineItem(Base):
    """Laybye line item model"""
    __tablename__ = "laybye_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    laybye_id = Column(Integer, ForeignKey("laybyes.id"), index=True)
    item_code = Column(String(50), index=True)
    description = Column(String(255))
    quantity = Column(Numeric(10, 2))
    cost_price = Column(Numeric(15, 2))
    selling_price = Column(Numeric(15, 2))
    discount_percentage = Column(Numeric(5, 2), default=0)
    tax_code = Column(SQLEnum(TaxCode), default=TaxCode.STANDARD)
    tax_amount = Column(Numeric(15, 2), default=0)
    line_total = Column(Numeric(15, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    laybye = relationship("Laybye", back_populates="line_items")


class LaybeyPayment(Base):
    """Laybye payment model"""
    __tablename__ = "laybye_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    laybye_id = Column(Integer, ForeignKey("laybyes.id"), index=True)
    payment_date = Column(DateTime, default=datetime.utcnow, index=True)
    payment_amount = Column(Numeric(15, 2))
    tender_type = Column(SQLEnum(TenderType), default=TenderType.CASH)
    reference = Column(String(100), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    laybye = relationship("Laybye", back_populates="payments")


class Quotation(Base):
    """Quotation model"""
    __tablename__ = "quotations"
    
    id = Column(Integer, primary_key=True, index=True)
    quotation_number = Column(String(50), unique=True, index=True)
    debtor_account_number = Column(String(50), nullable=True, index=True)
    quotation_date = Column(DateTime, default=datetime.utcnow, index=True)
    valid_until = Column(DateTime, nullable=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    # Financial fields
    subtotal = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    line_items = relationship("QuotationLineItem", back_populates="quotation", cascade="all, delete-orphan")


class QuotationLineItem(Base):
    """Quotation line item model"""
    __tablename__ = "quotation_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    quotation_id = Column(Integer, ForeignKey("quotations.id"), index=True)
    item_code = Column(String(50), index=True)
    description = Column(String(255))
    quantity = Column(Numeric(10, 2))
    cost_price = Column(Numeric(15, 2))
    selling_price = Column(Numeric(15, 2))
    discount_percentage = Column(Numeric(5, 2), default=0)
    tax_code = Column(SQLEnum(TaxCode), default=TaxCode.STANDARD)
    tax_amount = Column(Numeric(15, 2), default=0)
    line_total = Column(Numeric(15, 2))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    quotation = relationship("Quotation", back_populates="line_items")


class JobCosting(Base):
    """Job costing/card model"""
    __tablename__ = "job_costings"
    
    id = Column(Integer, primary_key=True, index=True)
    job_number = Column(String(50), unique=True, index=True)
    debtor_account_number = Column(String(50), index=True)
    job_date = Column(DateTime, default=datetime.utcnow, index=True)
    description = Column(String(255))
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    # Financial fields
    labour_cost = Column(Numeric(15, 2), default=0)
    material_cost = Column(Numeric(15, 2), default=0)
    other_cost = Column(Numeric(15, 2), default=0)
    overhead_cost = Column(Numeric(15, 2), default=0)
    total_cost = Column(Numeric(15, 2), default=0)
    selling_price = Column(Numeric(15, 2), default=0)
    gross_profit = Column(Numeric(15, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    # Relationships
    line_items = relationship("JobCostingLineItem", back_populates="job_costing", cascade="all, delete-orphan")


class JobCostingLineItem(Base):
    """Job costing line item model"""
    __tablename__ = "job_costing_line_items"
    
    id = Column(Integer, primary_key=True, index=True)
    job_costing_id = Column(Integer, ForeignKey("job_costings.id"), index=True)
    item_code = Column(String(50), nullable=True)
    description = Column(String(255))
    quantity = Column(Numeric(10, 2))
    cost_per_unit = Column(Numeric(15, 2))
    total_cost = Column(Numeric(15, 2))
    cost_type = Column(String(50))  # labour, material, other, overhead
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    job_costing = relationship("JobCosting", back_populates="line_items")


class RepairControl(Base):
    """Repair voucher/control model"""
    __tablename__ = "repair_controls"
    
    id = Column(Integer, primary_key=True, index=True)
    repair_number = Column(String(50), unique=True, index=True)
    debtor_account_number = Column(String(50), index=True)
    repair_date = Column(DateTime, default=datetime.utcnow, index=True)
    description = Column(String(255))
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    # Financial fields
    estimated_cost = Column(Numeric(15, 2), default=0)
    actual_cost = Column(Numeric(15, 2), default=0)
    labour_charge = Column(Numeric(15, 2), default=0)
    total_charge = Column(Numeric(15, 2), default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)


class Payout(Base):
    """Cash payout model"""
    __tablename__ = "payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    payout_number = Column(String(50), unique=True, index=True)
    payout_date = Column(DateTime, default=datetime.utcnow, index=True)
    payout_amount = Column(Numeric(15, 2))
    tender_type = Column(SQLEnum(TenderType), default=TenderType.CASH)
    reference = Column(String(100), nullable=True)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)


class CashControl(Base):
    """Cash control/reconciliation model"""
    __tablename__ = "cash_controls"
    
    id = Column(Integer, primary_key=True, index=True)
    control_number = Column(String(50), unique=True, index=True)
    control_date = Column(DateTime, default=datetime.utcnow, index=True)
    cashier_name = Column(String(100))
    
    # Cash counts
    opening_balance = Column(Numeric(15, 2))
    cash_receipts = Column(Numeric(15, 2), default=0)
    cash_payouts = Column(Numeric(15, 2), default=0)
    expected_balance = Column(Numeric(15, 2))
    actual_balance = Column(Numeric(15, 2))
    variance = Column(Numeric(15, 2))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.DRAFT)


class TransactionLog(Base):
    """Transaction audit log"""
    __tablename__ = "transaction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(50), index=True)
    transaction_number = Column(String(50), index=True)
    action = Column(String(50))  # CREATE, UPDATE, POST, REVERSE
    user = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    changes = Column(Text, nullable=True)
    status = Column(String(50))


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
