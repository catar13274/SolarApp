"""Materials API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from ..database import get_session
from ..models import Material, Stock

router = APIRouter(prefix="/api/v1/materials", tags=["materials"])


@router.get("/", response_model=List[dict])
def list_materials(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
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
    
    query = query.offset(skip).limit(limit)
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
