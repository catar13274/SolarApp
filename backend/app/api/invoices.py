"""Invoices API endpoints."""

import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlmodel import Session, select
from datetime import datetime, date
import httpx

from ..database import get_session
from ..models import Invoice, Purchase

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


@router.get("/", response_model=List[Invoice])
def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List all invoices."""
    query = select(Invoice).offset(skip).limit(limit).order_by(Invoice.created_at.desc())
    invoices = session.exec(query).all()
    return invoices


@router.get("/{invoice_id}", response_model=dict)
def get_invoice(invoice_id: int, session: Session = Depends(get_session)):
    """Get invoice details."""
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice_dict = invoice.model_dump()
    
    # Add purchase info if linked
    if invoice.purchase_id:
        purchase = session.get(Purchase, invoice.purchase_id)
        if purchase:
            invoice_dict["purchase"] = purchase.model_dump()
    
    return invoice_dict


@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """Upload and parse XML invoice, create purchase and update stock."""
    # Read configuration from environment
    xml_parser_url = os.getenv("XML_PARSER_URL", "http://localhost:5000")
    xml_parser_token = os.getenv("XML_PARSER_TOKEN", "")
    
    if not file.filename.endswith('.xml'):
        raise HTTPException(status_code=400, detail="Only XML files are allowed")
    
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    content = await file.read()
    with open(file_path, 'wb') as f:
        f.write(content)
    
    # Parse XML using parser service
    try:
        async with httpx.AsyncClient() as client:
            with open(file_path, 'rb') as f:
                files = {'file': (file.filename, f, 'application/xml')}
                headers = {'X-API-Token': xml_parser_token} if xml_parser_token else {}
                
                response = await client.post(
                    f"{xml_parser_url}/parse",
                    files=files,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=502,
                        detail="XML parser authentication failed. Please check XML_PARSER_TOKEN configuration."
                    )
                elif response.status_code != 200:
                    error_detail = "Failed to parse XML invoice"
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_detail = f"XML parser error: {error_data['error']}"
                    except Exception:
                        pass
                    raise HTTPException(
                        status_code=502,
                        detail=error_detail
                    )
                
                parsed_data = response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"XML parser service is not available at {xml_parser_url}. Please ensure the service is running."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="XML parser service timed out. Please try again later."
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error parsing invoice: {str(e)}"
        )
    
    # Extract invoice data
    invoice_number = parsed_data.get('invoice_number', '')
    supplier = parsed_data.get('supplier_name', '')
    invoice_date_str = parsed_data.get('invoice_date', '')
    total_amount = float(parsed_data.get('total_amount', 0))
    currency = parsed_data.get('currency', 'RON')
    
    # Parse date
    try:
        invoice_date = date.fromisoformat(invoice_date_str)
    except:
        invoice_date = date.today()
    
    # Check if invoice already exists
    existing = session.exec(
        select(Invoice).where(Invoice.invoice_number == invoice_number)
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Invoice already uploaded"
        )
    
    # Create purchase from invoice
    purchase = Purchase(
        supplier=supplier,
        purchase_date=invoice_date,
        invoice_number=invoice_number,
        total_amount=total_amount,
        currency=currency,
        notes=f"Created from uploaded invoice {file.filename}",
        created_at=datetime.utcnow()
    )
    
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    
    # Create invoice record
    invoice = Invoice(
        invoice_number=invoice_number,
        supplier=supplier,
        invoice_date=invoice_date,
        total_amount=total_amount,
        currency=currency,
        xml_file_path=file_path,
        purchase_id=purchase.id,
        created_at=datetime.utcnow()
    )
    
    session.add(invoice)
    session.commit()
    session.refresh(invoice)
    
    return {
        "message": "Invoice uploaded and processed successfully",
        "invoice": invoice.model_dump(),
        "purchase_id": purchase.id,
        "parsed_data": parsed_data
    }
