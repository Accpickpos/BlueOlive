"""
Invoice management router
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from decimal import Decimal

from db_tenant import get_db
from database import Invoice, InvoiceLineItem, TransactionStatus
import models
from services.drf_integration import DRFIntegrationService
from services.calculation_service import CalculationService, TaxCode
from services.number_generator import generate_transaction_number

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])

# Initialize services
drf_service = DRFIntegrationService()
calc_service = CalculationService()


@router.post("/", response_model=models.InvoiceResponse, status_code=201)
async def create_invoice(
    invoice_data: models.InvoiceCreate,
    db: Session = Depends(get_db)
):
    """Create a new invoice"""
    try:
        # Validate debtor exists
        debtor = await drf_service.get_debtor(invoice_data.debtor_account_number)
        if not debtor:
            raise HTTPException(
                status_code=404,
                detail=f"Debtor account {invoice_data.debtor_account_number} not found"
            )
        
        # Generate invoice number
        invoice_number = await generate_transaction_number("invoice")
        
        # Create invoice
        invoice = Invoice(
            invoice_number=invoice_number,
            debtor_account_number=invoice_data.debtor_account_number,
            invoice_date=invoice_data.invoice_date,
            delivery_date=invoice_data.delivery_date,
            delivery_details=invoice_data.delivery_details,
            reg_make_names=invoice_data.reg_make_names,
            credit_card=invoice_data.credit_card,
            order_number=invoice_data.order_number,
            customer_ref=invoice_data.customer_ref,
            sman_area=invoice_data.sman_area,
            status=TransactionStatus.DRAFT,
            created_at=datetime.utcnow(),
            notes=invoice_data.notes
        )
        
        # Process line items
        line_items_data = []
        for item in invoice_data.line_items:
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
            line_item = InvoiceLineItem(
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
            invoice.line_items.append(line_item)
            line_items_data.append(calc_result)
        
        # Calculate invoice totals
        totals = calc_service.calculate_invoice_totals(line_items_data)
        invoice.subtotal = totals["subtotal"]
        invoice.subtotal_discount = totals["subtotal_discount"]
        invoice.tax_amount = totals["tax_amount"]
        invoice.gross_profit = totals["gross_profit"]
        invoice.total_amount = totals["total_amount"]
        
        # Save invoice
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        # Update stock quantities
        for item in invoice_data.line_items:
            await drf_service.update_stock_quantity(
                item.item_code,
                -item.quantity,  # Negative for deduction
                invoice_number,
                "INVOICE"
            )
        
        return invoice
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}", response_model=models.InvoiceResponse)
async def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    """Get invoice by ID"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/", response_model=List[models.InvoiceListResponse])
async def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    debtor_account_number: str = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db)
):
    """List invoices with optional filtering"""
    query = db.query(Invoice)
    
    if debtor_account_number:
        query = query.filter(Invoice.debtor_account_number == debtor_account_number)
    
    if status:
        query = query.filter(Invoice.status == status)
    
    invoices = query.offset(skip).limit(limit).all()
    return invoices


@router.put("/{invoice_id}", response_model=models.InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice_data: models.InvoiceUpdate,
    db: Session = Depends(get_db)
):
    """Update invoice"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status != TransactionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only update draft invoices")
    
    if invoice_data.delivery_date:
        invoice.delivery_date = invoice_data.delivery_date
    if invoice_data.notes:
        invoice.notes = invoice_data.notes
    
    invoice.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(invoice)
    return invoice


@router.post("/{invoice_id}/post")
async def post_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Post invoice (move to POSTED status)"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status != TransactionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Only draft invoices can be posted")
    
    # Post to debtor account
    posted = await drf_service.post_transaction_to_debtor(
        invoice.debtor_account_number,
        invoice.total_amount,
        "INVOICE",
        invoice.invoice_number,
        f"Invoice {invoice.invoice_number}"
    )
    
    if not posted:
        raise HTTPException(status_code=500, detail="Failed to post to debtor account")
    
    invoice.status = TransactionStatus.POSTED
    invoice.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(invoice)
    
    return {"status": "posted", "invoice_number": invoice.invoice_number}


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Delete invoice (only draft)"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    if invoice.status != TransactionStatus.DRAFT:
        raise HTTPException(status_code=400, detail="Can only delete draft invoices")
    
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted"}


# Search endpoints
@router.get("/search/debtors")
async def search_debtors(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Search for debtors by account number or name"""
    try:
        results = await drf_service.search_debtors(query, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/search/stock")
async def search_stock(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Search for stock items by code or description"""
    try:
        results = await drf_service.search_stock(query, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.get("/search/creditors")
async def search_creditors(
    query: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Search for creditors by account number or name"""
    try:
        results = await drf_service.search_creditors(query, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
