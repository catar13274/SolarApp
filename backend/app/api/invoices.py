"""Invoices API endpoints."""

import os
import re
import logging
from uuid import uuid4
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlmodel import Session, select
from datetime import datetime, date
import httpx

from ..database import get_session
from ..models import Invoice, Purchase, PurchaseItem
from ..document_parser import parse_document, extract_document_text, parse_invoice_materials

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])

# Configure logging
logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {"xml", "pdf", "doc", "docx", "xls", "xlsx", "txt"}
MAX_UPLOAD_SIZE_BYTES = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(10 * 1024 * 1024)))
INVOICE_PARSER_DEBUG_ENABLED = os.getenv("INVOICE_PARSER_DEBUG_ENABLED", "false").lower() in ("1", "true", "yes")


def _sanitize_filename(filename: str) -> str:
    """Keep filename safe for local filesystem use."""
    base = os.path.basename((filename or "").strip())
    if not base:
        return "invoice"
    name, _dot, ext = base.rpartition(".")
    name = name or "invoice"
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", name).strip("._-") or "invoice"
    safe_ext = re.sub(r"[^A-Za-z0-9]", "", ext).lower()
    return f"{safe_name}.{safe_ext}" if safe_ext else safe_name


def _store_upload(file: UploadFile, content: bytes) -> tuple[str, str, str]:
    """Persist upload and return (safe_filename, extension, file_path)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    safe_filename = _sanitize_filename(file.filename)
    file_extension = safe_filename.split('.')[-1].lower() if '.' in safe_filename else ''
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed formats: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_SIZE_BYTES} bytes."
        )

    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    unique_filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid4().hex}_{safe_filename}"
    file_path = os.path.join(upload_dir, unique_filename)
    with open(file_path, 'wb') as f:
        f.write(content)

    return safe_filename, file_extension, file_path


@router.post("/parse-preview")
async def parse_invoice_preview(file: UploadFile = File(...)):
    """Preview parser output without creating purchase/invoice records."""
    if not INVOICE_PARSER_DEBUG_ENABLED:
        raise HTTPException(status_code=403, detail="Parser preview is disabled.")

    content = await file.read()
    safe_filename, file_extension, file_path = _store_upload(file, content)

    try:
        if file_extension == "xml":
            raise HTTPException(
                status_code=400,
                detail="Use /upload for XML files. Preview is intended for PDF/DOC/TXT calibration."
            )

        extracted_text = extract_document_text(file_path, file_extension)
        parsed_data = parse_invoice_materials(extracted_text) if extracted_text else {
            'invoice_number': '',
            'invoice_date': '',
            'supplier_name': '',
            'currency': 'RON',
            'total_amount': 0.0,
            'items': []
        }
        return {
            "filename": safe_filename,
            "file_format": file_extension,
            "text_preview": extracted_text[:4000],
            "text_length": len(extracted_text),
            "parsed_data": parsed_data,
        }
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                logger.warning("Failed to remove preview upload file: %s", file_path)


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


@router.delete("/{invoice_id}")
def delete_invoice(invoice_id: int, session: Session = Depends(get_session)):
    """Delete an invoice and its associated purchase record."""
    invoice = session.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete associated file if it exists
    if invoice.xml_file_path and os.path.exists(invoice.xml_file_path):
        try:
            os.remove(invoice.xml_file_path)
            logger.info(f"Deleted invoice file: {invoice.xml_file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete invoice file: {e}")
    
    # Delete associated purchase and its items if they exist
    if invoice.purchase_id:
        purchase = session.get(Purchase, invoice.purchase_id)
        if purchase:
            # Delete all purchase items first
            items_query = select(PurchaseItem).where(PurchaseItem.purchase_id == purchase.id)
            items = session.exec(items_query).all()
            for item in items:
                session.delete(item)
            
            # Delete the purchase
            session.delete(purchase)
            logger.info(f"Deleted purchase #{purchase.id} with {len(items)} items")
    
    # Delete the invoice
    session.delete(invoice)
    session.commit()
    
    return {
        "message": "Invoice deleted successfully",
        "invoice_id": invoice_id
    }


@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """Upload invoice file (XML, PDF, DOC, XLS, TXT), parse XML and create purchase."""
    content = await file.read()
    safe_filename, file_extension, file_path = _store_upload(file, content)
    
    # Only parse XML files
    if file_extension == 'xml':
        # Read configuration from environment
        xml_parser_url = os.getenv("XML_PARSER_URL", "http://localhost:5000")
        xml_parser_token = os.getenv("XML_PARSER_TOKEN", "dev-token-12345")
        
        # Security warning for default token
        if xml_parser_token == "dev-token-12345":
            logger.warning(
                "Using default XML_PARSER_TOKEN='dev-token-12345'. "
                "This is insecure for production! Set XML_PARSER_TOKEN environment variable."
            )
        
        # Parse XML using parser service
        try:
            async with httpx.AsyncClient() as client:
                with open(file_path, 'rb') as f:
                    files = {'file': (safe_filename, f, 'application/xml')}
                    headers = {'X-API-Token': xml_parser_token}
                    
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
        
        # Extract invoice data from parsed XML
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
        
        # Create purchase items from parsed invoice items
        items_data = parsed_data.get('items', [])
        for item_data in items_data:
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                material_id=None,  # Will be matched manually later
                description=item_data.get('description', ''),
                sku=item_data.get('sku', ''),
                quantity=item_data.get('quantity', 0.0),
                unit_price=item_data.get('unit_price', 0.0),
                total_price=item_data.get('total_price', 0.0)
            )
            session.add(purchase_item)
        
        session.commit()
        
        # Create invoice record
        invoice = Invoice(
            invoice_number=invoice_number,
            supplier=supplier,
            invoice_date=invoice_date,
            total_amount=total_amount,
            currency=currency,
            xml_file_path=file_path,
            file_format=file_extension,
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
    else:
        # For non-XML files, parse using document parser
        try:
            parsed_data = parse_document(file_path, file_extension)
        except Exception as e:
            logger.error(f"Error parsing {file_extension} document: {e}")
            # If parsing fails, create a basic record
            parsed_data = {
                'invoice_number': '',
                'invoice_date': '',
                'supplier_name': '',
                'currency': 'RON',
                'total_amount': 0.0,
                'items': []
            }
        
        # Use filename as fallback for invoice number
        invoice_number = parsed_data.get('invoice_number') or safe_filename.rsplit('.', 1)[0]
        
        # Get other fields with fallbacks
        supplier = parsed_data.get('supplier_name') or 'Pending'
        invoice_date_str = parsed_data.get('invoice_date')
        total_amount = float(parsed_data.get('total_amount', 0))
        currency = parsed_data.get('currency', 'RON')
        
        # Parse date
        try:
            if invoice_date_str:
                invoice_date = date.fromisoformat(invoice_date_str)
            else:
                invoice_date = date.today()
        except (ValueError, TypeError):
            invoice_date = date.today()
        
        # Check if invoice already exists
        existing = session.exec(
            select(Invoice).where(Invoice.invoice_number == invoice_number)
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Invoice with this number already uploaded"
            )
        
        # Create purchase record
        purchase = Purchase(
            supplier=supplier,
            purchase_date=invoice_date,
            invoice_number=invoice_number,
            total_amount=total_amount,
            currency=currency,
            notes=f"Created from uploaded invoice {file.filename} ({file_extension.upper()} format)",
            created_at=datetime.utcnow()
        )
        
        session.add(purchase)
        session.commit()
        session.refresh(purchase)
        
        # Create purchase items from parsed data
        items_data = parsed_data.get('items', [])
        for item_data in items_data:
            purchase_item = PurchaseItem(
                purchase_id=purchase.id,
                material_id=None,  # Will be matched manually later
                description=item_data.get('description', ''),
                sku=item_data.get('sku', ''),
                quantity=item_data.get('quantity', 0.0),
                unit_price=item_data.get('unit_price', 0.0),
                total_price=item_data.get('total_price', 0.0)
            )
            session.add(purchase_item)
        
        session.commit()
        
        # Create invoice record
        invoice = Invoice(
            invoice_number=invoice_number,
            supplier=supplier,
            invoice_date=invoice_date,
            total_amount=total_amount,
            currency=currency,
            xml_file_path=file_path,
            file_format=file_extension,
            purchase_id=purchase.id,
            created_at=datetime.utcnow()
        )
        
        session.add(invoice)
        session.commit()
        session.refresh(invoice)
        
        # Determine message based on whether items were found
        if items_data:
            message = f"Invoice file ({file_extension.upper()}) uploaded and processed successfully. Found {len(items_data)} items."
        else:
            message = f"Invoice file ({file_extension.upper()}) uploaded. No items could be extracted automatically. Please update purchase details manually."
        
        return {
            "message": message,
            "invoice": invoice.model_dump(),
            "purchase_id": purchase.id,
            "parsed_data": parsed_data,
            "items_found": len(items_data)
        }
