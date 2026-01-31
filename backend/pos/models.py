"""
Pydantic models for request/response validation
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, validator


# Enums
class TransactionStatus(str, Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"
    CANCELLED = "CANCELLED"


class TaxCode(str, Enum):
    ZERO = "ZERO"
    STANDARD = "STANDARD"
    REDUCED = "REDUCED"


class TenderType(str, Enum):
    CASH = "CASH"
    CHEQUE = "CHEQUE"
    CREDIT_CARD = "CREDIT_CARD"
    EFT = "EFT"


class ReceiptType(str, Enum):
    BALANCE_FORWARD = "BALANCE_FORWARD"
    OPEN_ITEM = "OPEN_ITEM"
    POST_DATED_CHEQUE = "POST_DATED_CHEQUE"


class LaybieStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FORFEITED = "FORFEITED"


# Base schemas
class LineItemBase(BaseModel):
    """Base line item schema"""
    item_code: str
    description: str
    quantity: Decimal
    cost_price: Decimal
    selling_price: Decimal
    discount_percentage: Decimal = Decimal("0")
    tax_code: TaxCode = TaxCode.STANDARD


class LineItemResponse(LineItemBase):
    """Line item response schema"""
    id: int
    discount_amount: Decimal
    tax_amount: Decimal
    line_total: Decimal
    gross_profit: Optional[Decimal] = None
    
    class Config:
        from_attributes = True


# Invoice schemas
class InvoiceLineItemCreate(LineItemBase):
    """Invoice line item creation schema"""
    pass


class InvoiceLineItemResponse(LineItemResponse):
    """Invoice line item response schema"""
    pass


class InvoiceCreate(BaseModel):
    """Invoice creation schema"""
    debtor_account_number: str
    invoice_date: datetime
    delivery_date: Optional[datetime] = None
    delivery_details: Optional[str] = None
    reg_make_names: Optional[str] = None
    credit_card: Optional[str] = None
    order_number: Optional[str] = None
    customer_ref: Optional[str] = None
    sman_area: Optional[str] = None
    line_items: List[InvoiceLineItemCreate]
    notes: Optional[str] = None


class InvoiceUpdate(BaseModel):
    """Invoice update schema"""
    delivery_date: Optional[datetime] = None
    delivery_details: Optional[str] = None
    reg_make_names: Optional[str] = None
    credit_card: Optional[str] = None
    order_number: Optional[str] = None
    customer_ref: Optional[str] = None
    sman_area: Optional[str] = None
    notes: Optional[str] = None


class InvoiceResponse(BaseModel):
    """Invoice response schema"""
    id: int
    invoice_number: str
    debtor_account_number: str
    invoice_date: datetime
    delivery_date: Optional[datetime]
    delivery_details: Optional[str]
    reg_make_names: Optional[str]
    credit_card: Optional[str]
    order_number: Optional[str]
    customer_ref: Optional[str]
    sman_area: Optional[str]
    status: TransactionStatus
    subtotal: Decimal
    subtotal_discount: Decimal
    tax_amount: Decimal
    gross_profit: Decimal
    total_amount: Decimal
    line_items: List[InvoiceLineItemResponse]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# Cash Sale schemas
class CashSaleLineItemCreate(LineItemBase):
    """Cash sale line item creation schema"""
    pass


class CashSaleLineItemResponse(LineItemResponse):
    """Cash sale line item response schema"""
    pass


class CashSaleTenderCreate(BaseModel):
    """Cash sale tender creation schema"""
    tender_type: TenderType = TenderType.CASH
    amount: Decimal
    reference: Optional[str] = None


class CashSaleTenderResponse(BaseModel):
    """Cash sale tender response schema"""
    id: int
    tender_type: TenderType
    amount: Decimal
    change_amount: Decimal
    reference: Optional[str]
    
    class Config:
        from_attributes = True


class CashSaleCreate(BaseModel):
    """Cash sale creation schema"""
    receipt_date: datetime
    line_items: List[CashSaleLineItemCreate]
    tenders: List[CashSaleTenderCreate]
    notes: Optional[str] = None


class CashSaleResponse(BaseModel):
    """Cash sale response schema"""
    id: int
    receipt_number: str
    receipt_date: datetime
    status: TransactionStatus
    subtotal: Decimal
    subtotal_discount: Decimal
    tax_amount: Decimal
    gross_profit: Decimal
    total_amount: Decimal
    rounding_adjustment: Decimal
    final_amount: Decimal
    line_items: List[CashSaleLineItemResponse]
    tenders: List[CashSaleTenderResponse]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# Credit Note schemas
class CreditNoteLineItemCreate(LineItemBase):
    """Credit note line item creation schema"""
    pass


class CreditNoteLineItemResponse(LineItemResponse):
    """Credit note line item response schema"""
    pass


class CreditNoteCreate(BaseModel):
    """Credit note creation schema"""
    debtor_account_number: str
    reference_invoice_number: Optional[str] = None
    credit_note_date: datetime
    line_items: List[CreditNoteLineItemCreate]
    reason: Optional[str] = None


class CreditNoteResponse(BaseModel):
    """Credit note response schema"""
    id: int
    credit_note_number: str
    debtor_account_number: str
    reference_invoice_number: Optional[str]
    credit_note_date: datetime
    status: TransactionStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    line_items: List[CreditNoteLineItemResponse]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    reason: Optional[str]
    
    class Config:
        from_attributes = True


# Receipt schemas
class ReceiptTenderCreate(BaseModel):
    """Receipt tender creation schema"""
    tender_type: TenderType = TenderType.CASH
    amount: Decimal
    reference: Optional[str] = None


class ReceiptTenderResponse(BaseModel):
    """Receipt tender response schema"""
    id: int
    tender_type: TenderType
    amount: Decimal
    reference: Optional[str]
    
    class Config:
        from_attributes = True


class ReceiptCreate(BaseModel):
    """Receipt creation schema"""
    debtor_account_number: str
    receipt_date: datetime
    receipt_type: ReceiptType = ReceiptType.OPEN_ITEM
    receipt_amount: Decimal
    cash_discount: Decimal = Decimal("0")
    tenders: List[ReceiptTenderCreate]
    notes: Optional[str] = None


class ReceiptResponse(BaseModel):
    """Receipt response schema"""
    id: int
    receipt_number: str
    debtor_account_number: str
    receipt_date: datetime
    receipt_type: ReceiptType
    status: TransactionStatus
    receipt_amount: Decimal
    cash_discount: Decimal
    final_amount: Decimal
    tenders: List[ReceiptTenderResponse]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# Laybye schemas
class LaybeyLineItemCreate(LineItemBase):
    """Laybye line item creation schema"""
    pass


class LaybeyLineItemResponse(LineItemResponse):
    """Laybye line item response schema"""
    pass


class LaybeyPaymentCreate(BaseModel):
    """Laybye payment creation schema"""
    payment_date: datetime
    payment_amount: Decimal
    tender_type: TenderType = TenderType.CASH
    reference: Optional[str] = None


class LaybeyPaymentResponse(BaseModel):
    """Laybye payment response schema"""
    id: int
    payment_date: datetime
    payment_amount: Decimal
    tender_type: TenderType
    reference: Optional[str]
    
    class Config:
        from_attributes = True


class LaybeyCreate(BaseModel):
    """Laybye creation schema"""
    debtor_account_number: Optional[str] = None
    laybye_date: datetime
    deposit_amount: Decimal
    retention_amount: Decimal = Decimal("0")
    line_items: List[LaybeyLineItemCreate]


class LaybeyResponse(BaseModel):
    """Laybye response schema"""
    id: int
    laybye_number: str
    debtor_account_number: Optional[str]
    laybye_date: datetime
    deposit_amount: Decimal
    retention_amount: Decimal
    status: LaybieStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    line_items: List[LaybeyLineItemResponse]
    payments: List[LaybeyPaymentResponse]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


# Quotation schemas
class QuotationLineItemCreate(LineItemBase):
    """Quotation line item creation schema"""
    pass


class QuotationLineItemResponse(LineItemResponse):
    """Quotation line item response schema"""
    pass


class QuotationCreate(BaseModel):
    """Quotation creation schema"""
    debtor_account_number: Optional[str] = None
    quotation_date: datetime
    valid_until: Optional[datetime] = None
    line_items: List[QuotationLineItemCreate]


class QuotationResponse(BaseModel):
    """Quotation response schema"""
    id: int
    quotation_number: str
    debtor_account_number: Optional[str]
    quotation_date: datetime
    valid_until: Optional[datetime]
    status: TransactionStatus
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    line_items: List[QuotationLineItemResponse]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


# Job Costing schemas
class JobCostingLineItemCreate(BaseModel):
    """Job costing line item creation schema"""
    item_code: Optional[str] = None
    description: str
    quantity: Decimal
    cost_per_unit: Decimal
    cost_type: str  # labour, material, other, overhead


class JobCostingLineItemResponse(BaseModel):
    """Job costing line item response schema"""
    id: int
    item_code: Optional[str]
    description: str
    quantity: Decimal
    cost_per_unit: Decimal
    total_cost: Decimal
    cost_type: str
    
    class Config:
        from_attributes = True


class JobCostingCreate(BaseModel):
    """Job costing creation schema"""
    debtor_account_number: str
    job_date: datetime
    description: str
    line_items: List[JobCostingLineItemCreate]
    selling_price: Decimal


class JobCostingResponse(BaseModel):
    """Job costing response schema"""
    id: int
    job_number: str
    debtor_account_number: str
    job_date: datetime
    description: str
    status: TransactionStatus
    labour_cost: Decimal
    material_cost: Decimal
    other_cost: Decimal
    overhead_cost: Decimal
    total_cost: Decimal
    selling_price: Decimal
    gross_profit: Decimal
    line_items: List[JobCostingLineItemResponse]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


# Repair Control schemas
class RepairControlCreate(BaseModel):
    """Repair control creation schema"""
    debtor_account_number: str
    repair_date: datetime
    description: str
    estimated_cost: Decimal


class RepairControlResponse(BaseModel):
    """Repair control response schema"""
    id: int
    repair_number: str
    debtor_account_number: str
    repair_date: datetime
    description: str
    status: TransactionStatus
    estimated_cost: Decimal
    actual_cost: Decimal
    labour_charge: Decimal
    total_charge: Decimal
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


# Payout schemas
class PayoutCreate(BaseModel):
    """Payout creation schema"""
    payout_date: datetime
    payout_amount: Decimal
    tender_type: TenderType = TenderType.CASH
    reference: Optional[str] = None
    notes: Optional[str] = None


class PayoutResponse(BaseModel):
    """Payout response schema"""
    id: int
    payout_number: str
    payout_date: datetime
    payout_amount: Decimal
    tender_type: TenderType
    reference: Optional[str]
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    notes: Optional[str]
    
    class Config:
        from_attributes = True


# Cash Control schemas
class CashControlCreate(BaseModel):
    """Cash control creation schema"""
    control_date: datetime
    cashier_name: str
    opening_balance: Decimal
    actual_balance: Decimal


class CashControlResponse(BaseModel):
    """Cash control response schema"""
    id: int
    control_number: str
    control_date: datetime
    cashier_name: str
    opening_balance: Decimal
    cash_receipts: Decimal
    cash_payouts: Decimal
    expected_balance: Decimal
    actual_balance: Decimal
    variance: Decimal
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# List schemas
class InvoiceListResponse(BaseModel):
    """Invoice list response schema"""
    id: int
    invoice_number: str
    debtor_account_number: str
    invoice_date: datetime
    status: TransactionStatus
    total_amount: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class CashSaleListResponse(BaseModel):
    """Cash sale list response schema"""
    id: int
    receipt_number: str
    receipt_date: datetime
    status: TransactionStatus
    final_amount: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


# Error schemas
class ErrorResponse(BaseModel):
    """Error response schema"""
    detail: str
    code: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(BaseModel):
    """Validation error response schema"""
    detail: List[dict]
    code: str = "VALIDATION_ERROR"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
