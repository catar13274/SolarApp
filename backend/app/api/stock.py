"""Stock API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from ..database import get_session
from ..models import Stock, StockMovement, Material

router = APIRouter(prefix="/api/v1/stock", tags=["stock"])


@router.get("/", response_model=List[dict])
def list_stock(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List all stock with material information."""
    query = select(Stock).offset(skip).limit(limit)
    stocks = session.exec(query).all()
    
    result = []
    for stock in stocks:
        material = session.get(Material, stock.material_id)
        if material:
            stock_dict = stock.model_dump()
            stock_dict["material_name"] = material.name
            stock_dict["material_sku"] = material.sku
            stock_dict["material_category"] = material.category
            stock_dict["min_stock"] = material.min_stock
            stock_dict["is_low"] = stock.quantity < material.min_stock
            result.append(stock_dict)
    
    return result


@router.get("/low", response_model=List[dict])
def get_low_stock(session: Session = Depends(get_session)):
    """Get items with stock below minimum threshold."""
    stocks = session.exec(select(Stock)).all()
    
    result = []
    for stock in stocks:
        material = session.get(Material, stock.material_id)
        if material and stock.quantity < material.min_stock:
            stock_dict = stock.model_dump()
            stock_dict["material_name"] = material.name
            stock_dict["material_sku"] = material.sku
            stock_dict["material_category"] = material.category
            stock_dict["min_stock"] = material.min_stock
            stock_dict["shortage"] = material.min_stock - stock.quantity
            result.append(stock_dict)
    
    return result


@router.get("/{material_id}", response_model=dict)
def get_stock(material_id: int, session: Session = Depends(get_session)):
    """Get stock for specific material."""
    stock = session.exec(
        select(Stock).where(Stock.material_id == material_id)
    ).first()
    
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    material = session.get(Material, material_id)
    stock_dict = stock.model_dump()
    
    if material:
        stock_dict["material_name"] = material.name
        stock_dict["material_sku"] = material.sku
        stock_dict["min_stock"] = material.min_stock
    
    return stock_dict


@router.get("/movements/", response_model=List[dict])
def list_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    material_id: Optional[int] = Query(None),
    movement_type: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """List stock movements with filters."""
    query = select(StockMovement)
    
    if material_id:
        query = query.where(StockMovement.material_id == material_id)
    
    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type)
    
    query = query.order_by(StockMovement.created_at.desc()).offset(skip).limit(limit)
    movements = session.exec(query).all()
    
    result = []
    for movement in movements:
        material = session.get(Material, movement.material_id)
        movement_dict = movement.model_dump()
        if material:
            movement_dict["material_name"] = material.name
            movement_dict["material_sku"] = material.sku
        result.append(movement_dict)
    
    return result


@router.post("/movement", response_model=StockMovement)
def create_movement(movement: StockMovement, session: Session = Depends(get_session)):
    """Record stock movement and update stock levels."""
    # Verify material exists
    material = session.get(Material, movement.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Get or create stock entry
    stock = session.exec(
        select(Stock).where(Stock.material_id == movement.material_id)
    ).first()
    
    if not stock:
        stock = Stock(
            material_id=movement.material_id,
            quantity=0.0,
            location="Main Warehouse"
        )
        session.add(stock)
    
    # Update stock based on movement type
    if movement.movement_type == "in":
        stock.quantity += movement.quantity
    elif movement.movement_type == "out":
        if stock.quantity < movement.quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock"
            )
        stock.quantity -= movement.quantity
    elif movement.movement_type == "adjustment":
        stock.quantity = movement.quantity
    elif movement.movement_type == "transfer":
        # For transfers, we just adjust the quantity
        stock.quantity += movement.quantity
    
    stock.updated_at = datetime.utcnow()
    
    # Create movement record
    movement.created_at = datetime.utcnow()
    session.add(movement)
    session.add(stock)
    session.commit()
    session.refresh(movement)
    
    return movement
