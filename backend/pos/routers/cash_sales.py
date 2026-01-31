"""
Cash sales router
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from decimal import Decimal

from db_tenant import get_db
from database import CashSale, CashSaleLineItem, CashSaleTender, TransactionStatus
import models
from services.drf_integration import DRFIntegrationService
from services.calculation_service import CalculationService, TaxCode
from services.number_generator import generate_transaction_number

router = APIRouter(prefix="/api/v1/cash-sales", tags=["cash_sales"])

# Initialize services
drf_service = DRFIntegrationService()
calc_service = CalculationService()


@router.post("/", response_model=models.CashSaleResponse, status_code=201)
async def create_cash_sale(
    cash_sale_data: models.CashSaleCreate,
    db: Session = Depends(get_db)
):
    """Create a new cash sale"""
    try:
        # Validate tenders
        if not cash_sale_data.tenders:
            raise HTTPException(status_code=400, detail="At least one tender is required")
        
        # Generate receipt number
        receipt_number = await generate_transaction_number("cash_sale")
        
        # Create cash sale
        cash_sale = CashSale(
            receipt_number=receipt_number,
            receipt_date=cash_sale_data.receipt_date,
            status=TransactionStatus.DRAFT,
            created_at=datetime.utcnow(),
            notes=cash_sale_data.notes
        )
        
        # Process line items
        line_items_data = []
        for item in cash_sale_data.line_items:
            # Validate stock
            stock = await drf_service.get_stock_item(item.item_code)
            if not stock:
                raise HTTPException(
                    status_code=404,
                    detail=f"Stock item {item.item_code} not found"
                )
            
            # Check quantity available
            available = await drf_service.get_stock_quantity(item.item_code)
            if available and available < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient quantity for {item.item_code}. Available: {available}"
                )
            
            # Calculate line item
            calc_result = calc_service.calculate_line_item(
                quantity=item.quantity,
                selling_price=item.selling_price,
                discount_percentage=item.discount_percentage,
                tax_code=TaxCode(item.tax_code.value),
                cost_price=item.cost_price
            )
            
            # Create line item
            line_item = CashSaleLineItem(
                item_code=item.item_code,
                description=item.description,
                quantity=item.quantity,
                cost_price=item.cost_price,
                selling_price=item.selling_price,
                discount_percentage=item.discount_percentage,
                discount_amount=calc_result["discount_amount"],
                tax_code=item.tax_code,
                tax_amount=calc_result["tax_amount"],
                line_total=calc_result["line_total"],
                gross_profit=calc_result["gross_profit"]
            )
            cash_sale.line_items.append(line_item)
            line_items_data.append(calc_result)
        
        # Calculate cash sale totals
        totals = calc_service.calculate_invoice_totals(line_items_data)
        cash_sale.subtotal = totals["subtotal"]
        cash_sale.subtotal_discount = totals["subtotal_discount"]
        cash_sale.tax_amount = totals["tax_amount"]
        cash_sale.gross_profit = totals["gross_profit"]
        cash_sale.total_amount = totals["total_amount"]
        
        # Process tenders and calculate change
        total_tendered = Decimal("0")
        for tender_data in cash_sale_data.tenders:
            total_tendered += tender_data.amount
            tender = CashSaleTender(
                tender_type=tender_data.tender_type,
                amount=tender_data.amount,
                reference=tender_data.reference
            )
            cash_sale.tenders.append(tender)
        
        # Calculate change
        change = calc_service.calculate_change(total_tendered, cash_sale.total_amount)
        if cash_sale.tenders:
            cash_sale.tenders[-1].change_amount = change
        
        # Apply cash rounding
        rounding_result = calc_service.calculate_cash_rounding(cash_sale.total_amount)
        cash_sale.rounding_adjustment = rounding_result["rounding_adjustment"]
        cash_sale.final_amount = rounding_result["rounded_amount"]
        
        # Save cash sale
        db.add(cash_sale)
        db.commit()
        db.refresh(cash_sale)
        
        # Update stock quantities
        for item in cash_sale_data.line_items:
            await drf_service.update_stock_quantity(
                item.item_code,
                -item.quantity,
                receipt_number,
                "CASH_SALE"
            )
        
        # Post to cashbook
        await drf_service.post_cashbook_entry(
            cash_sale.final_amount,
            "RECEIPT",
            f"Cash sale {receipt_number}",
            receipt_number
        )
        
        return cash_sale
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{cash_sale_id}", response_model=models.CashSaleResponse)
async def get_cash_sale(cash_sale_id: int, db: Session = Depends(get_db)):
    """Get cash sale by ID"""
    cash_sale = db.query(CashSale).filter(CashSale.id == cash_sale_id).first()
    if not cash_sale:
        raise HTTPException(status_code=404, detail="Cash sale not found")
    return cash_sale


@router.get("/", response_model=List[models.CashSaleListResponse])
async def list_cash_sales(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """List cash sales with optional filtering"""
    query = db.query(CashSale)
    
    if status:
        query = query.filter(CashSale.status == status)
    
    sales = query.offset(skip).limit(limit).order_by(CashSale.receipt_date.desc()).all()
    return sales


@router.post("/{cash_sale_id}/post")
async def post_cash_sale(
    cash_sale_id: int,
    db: Session = Depends(get_db)
):
    """Post cash sale (move to POSTED status)"""
    cash_sale = db.query(CashSale).filter(CashSale.id == cash_sale_id).first()
    if not cash_sale:
        raise HTTPException(status_code=404, detail="Cash sale not found")
    
    if cash_sale.status != TransactionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft cash sales can be posted")
    
    cash_sale.status = TransactionStatus.POSTED
    cash_sale.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(cash_sale)
    
    return {"status": "posted", "receipt_number": cash_sale.receipt_number}


@router.post("/{cash_sale_id}/convert-to-account")
async def convert_to_account_sale(
    cash_sale_id: int,
    debtor_account_number: str,
    db: Session = Depends(get_db)
):
    """Convert cash sale to account sale (invoice)"""
    cash_sale = db.query(CashSale).filter(CashSale.id == cash_sale_id).first()
    if not cash_sale:
        raise HTTPException(status_code=404, detail="Cash sale not found")
    
    if cash_sale.status != TransactionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft cash sales can be converted")
    
    # Validate debtor
    debtor = await drf_service.get_debtor(debtor_account_number)
    if not debtor:
        raise HTTPException(status_code=404, detail=f"Debtor {debtor_account_number} not found")
    
    # Create invoice from cash sale
    from database import Invoice, InvoiceLineItem
    
    invoice_number = await generate_transaction_number("invoice")
    invoice = Invoice(
        invoice_number=invoice_number,
        debtor_account_number=debtor_account_number,
        invoice_date=cash_sale.receipt_date,
        status=TransactionStatus.DRAFT,
        subtotal=cash_sale.subtotal,
        subtotal_discount=cash_sale.subtotal_discount,
        tax_amount=cash_sale.tax_amount,
        gross_profit=cash_sale.gross_profit,
        total_amount=cash_sale.total_amount,
        created_at=datetime.utcnow()
    )
    
    # Copy line items
    for cash_item in cash_sale.line_items:
        invoice_item = InvoiceLineItem(
            item_code=cash_item.item_code,
            description=cash_item.description,
            quantity=cash_item.quantity,
            cost_price=cash_item.cost_price,
            selling_price=cash_item.selling_price,
            discount_percentage=cash_item.discount_percentage,
            discount_amount=cash_item.discount_amount,
            tax_code=cash_item.tax_code,
            tax_amount=cash_item.tax_amount,
            line_total=cash_item.line_total,
            gross_profit=cash_item.gross_profit
        )
        invoice.line_items.append(invoice_item)
    
    db.add(invoice)
    cash_sale.status = TransactionStatus.POSTED
    db.commit()
    
    return {
        "message": "Cash sale converted to invoice",
        "invoice_number": invoice_number,
        "invoice_id": invoice.id
    }


@router.delete("/{cash_sale_id}")
async def delete_cash_sale(
    cash_sale_id: int,
    db: Session = Depends(get_db)
):
    """Delete cash sale (only draft)"""
    cash_sale = db.query(CashSale).filter(CashSale.id == cash_sale_id).first()
    if not cash_sale:
        raise HTTPException(status_code=404, detail="Cash sale not found")
    
    if cash_sale.status != TransactionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only delete draft cash sales")
    
    db.delete(cash_sale)
    db.commit()
    
    return {"message": "Cash sale deleted"}
