"""Materials API endpoints."""

from datetime import datetime
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from openpyxl import Workbook, load_workbook
from sqlmodel import Session, select

from ..database import get_session
from ..models import Material, Stock

router = APIRouter(prefix="/api/v1/materials", tags=["materials"])


@router.get("/", response_model=List[dict])
def list_materials(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    company: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """List all materials with optional search and filters."""
    query = select(Material)
    
    if search:
        query = query.where(
            (Material.name.contains(search)) | 
            (Material.sku.contains(search)) |
            ((Material.description.is_not(None)) & (Material.description.contains(search)))
        )
    
    if category:
        query = query.where(Material.category == category)

    if company:
        query = query.where(Material.company == company)
    
    query = query.order_by(Material.name.asc()).offset(skip).limit(limit)
    materials = session.exec(query).all()
    
    # Enrich with stock information
    result = []
    for material in materials:
        stock = session.exec(
            select(Stock).where(Stock.material_id == material.id)
        ).first()
        
        material_dict = material.model_dump()
        material_dict["current_stock"] = stock.quantity if stock else 0
        result.append(material_dict)
    
    return result


@router.get("/export")
def export_materials(
    company: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    """Export materials to an Excel file."""
    query = select(Material)
    if company:
        query = query.where(Material.company == company)
    materials = session.exec(query.order_by(Material.name.asc())).all()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Materials"
    headers = [
        "name",
        "sku",
        "description",
        "company",
        "category",
        "unit",
        "unit_price",
        "min_stock",
    ]
    sheet.append(headers)

    for material in materials:
        sheet.append(
            [
                material.name,
                material.sku,
                material.description or "",
                material.company,
                material.category,
                material.unit,
                material.unit_price,
                material.min_stock,
            ]
        )

    output = BytesIO()
    workbook.save(output)
    output.seek(0)

    filename = f"materials_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
async def import_materials(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """Import materials from an Excel file."""
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported for import.")

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        workbook = load_workbook(BytesIO(file_bytes), data_only=True)
        sheet = workbook.active
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Excel file: {exc}") from exc

    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=400, detail="Excel file does not contain any rows.")

    raw_headers = [str(cell).strip().lower() if cell is not None else "" for cell in rows[0]]
    required_headers = {"name", "sku", "category", "unit", "unit_price", "min_stock"}
    if not required_headers.issubset(set(raw_headers)):
        raise HTTPException(
            status_code=400,
            detail=(
                "Missing required columns. Required: "
                "name, sku, category, unit, unit_price, min_stock "
                "(description is optional)."
            ),
        )

    header_index = {header: idx for idx, header in enumerate(raw_headers)}
    created = 0
    updated = 0
    skipped = 0
    errors: List[str] = []

    for row_num, row in enumerate(rows[1:], start=2):
        if row is None:
            skipped += 1
            continue

        def get_val(key: str):
            idx = header_index[key]
            return row[idx] if idx < len(row) else None

        sku = str(get_val("sku") or "").strip()
        name = str(get_val("name") or "").strip()
        category = str(get_val("category") or "").strip() or "other"
        company = str(get_val("company") or "").strip() or "freevoltsrl.ro"
        unit = str(get_val("unit") or "").strip() or "buc"
        description = str(get_val("description") or "").strip() if "description" in header_index else ""

        if not sku or not name:
            skipped += 1
            continue

        try:
            unit_price = float(get_val("unit_price") or 0)
            min_stock = int(float(get_val("min_stock") or 0))
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: invalid numeric values for unit_price/min_stock")
            continue

        existing = session.exec(select(Material).where(Material.sku == sku)).first()
        if existing:
            existing.name = name
            existing.description = description or None
            existing.category = category
            existing.company = company
            existing.unit = unit
            existing.unit_price = unit_price
            existing.min_stock = min_stock
            existing.updated_at = datetime.utcnow()
            session.add(existing)
            updated += 1
        else:
            material = Material(
                name=name,
                sku=sku,
                description=description or None,
                company=company,
                category=category,
                unit=unit,
                unit_price=unit_price,
                min_stock=min_stock,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(material)
            session.flush()

            stock = Stock(material_id=material.id, quantity=0.0, location="Main Warehouse")
            session.add(stock)
            created += 1

    session.commit()
    return {
        "message": "Import completed",
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    }


@router.get("/{material_id}", response_model=dict)
def get_material(material_id: int, session: Session = Depends(get_session)):
    """Get material details with current stock."""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    stock = session.exec(
        select(Stock).where(Stock.material_id == material_id)
    ).first()
    
    material_dict = material.model_dump()
    material_dict["current_stock"] = stock.quantity if stock else 0
    material_dict["stock_location"] = stock.location if stock else "Main Warehouse"
    
    return material_dict


@router.post("/", response_model=Material)
def create_material(material: Material, session: Session = Depends(get_session)):
    """Create a new material."""
    # Check if SKU already exists
    existing = session.exec(
        select(Material).where(Material.sku == material.sku)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="SKU already exists")
    
    material.created_at = datetime.utcnow()
    material.updated_at = datetime.utcnow()
    
    session.add(material)
    session.commit()
    session.refresh(material)
    
    # Create initial stock entry
    stock = Stock(
        material_id=material.id,
        quantity=0.0,
        location="Main Warehouse"
    )
    session.add(stock)
    session.commit()
    
    return material


@router.put("/{material_id}", response_model=Material)
def update_material(
    material_id: int,
    material_update: Material,
    session: Session = Depends(get_session)
):
    """Update an existing material."""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Check SKU uniqueness if changed
    if material_update.sku != material.sku:
        existing = session.exec(
            select(Material).where(Material.sku == material_update.sku)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU already exists")
    
    # Update fields
    material.name = material_update.name
    material.sku = material_update.sku
    material.description = material_update.description
    material.company = material_update.company
    material.category = material_update.category
    material.unit = material_update.unit
    material.unit_price = material_update.unit_price
    material.min_stock = material_update.min_stock
    material.updated_at = datetime.utcnow()
    
    session.add(material)
    session.commit()
    session.refresh(material)
    
    return material


@router.delete("/{material_id}")
def delete_material(material_id: int, session: Session = Depends(get_session)):
    """Delete a material."""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Delete associated stock
    stock = session.exec(
        select(Stock).where(Stock.material_id == material_id)
    ).first()
    if stock:
        session.delete(stock)
    
    session.delete(material)
    session.commit()
    
    return {"message": "Material deleted successfully"}
