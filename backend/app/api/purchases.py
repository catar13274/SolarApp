"""Purchases API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime
from pydantic import BaseModel

from ..database import get_session
from ..models import Purchase, PurchaseItem, StockMovement, Material, PurchaseCreate

router = APIRouter(prefix="/api/v1/purchases", tags=["purchases"])


class AddItemToStockRequest(BaseModel):
    """Request model for adding purchase item to stock."""
    material_id: int
    

@router.post("/{purchase_id}/items/{item_id}/add-to-stock")
def add_purchase_item_to_stock(
    purchase_id: int,
    item_id: int,
    request: AddItemToStockRequest,
    session: Session = Depends(get_session)
):
    """Add a purchase item to material stock."""
    # Get purchase
    purchase = session.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Get purchase item
    purchase_item = session.get(PurchaseItem, item_id)
    if not purchase_item or purchase_item.purchase_id != purchase_id:
        raise HTTPException(status_code=404, detail="Purchase item not found")
    
    # Verify material exists
    material = session.get(Material, request.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Update purchase item with material_id
    purchase_item.material_id = request.material_id
    session.add(purchase_item)
    
    # Create stock movement
    movement = StockMovement(
        material_id=request.material_id,
        movement_type="in",
        quantity=purchase_item.quantity,
        reference_type="purchase",
        reference_id=purchase_id,
        notes=f"Added from purchase {purchase.invoice_number or purchase_id} - {purchase_item.description}",
        created_at=datetime.utcnow()
    )
    session.add(movement)
    
    session.commit()
    session.refresh(purchase_item)
    
    return {
        "message": "Item added to stock successfully",
        "purchase_item": purchase_item.model_dump(),
        "stock_movement_id": movement.id
    }



@router.get("/", response_model=List[Purchase])
def list_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: Session = Depends(get_session)
):
    """List all purchases."""
    query = select(Purchase).offset(skip).limit(limit).order_by(Purchase.created_at.desc())
    purchases = session.exec(query).all()
    return purchases


@router.get("/{purchase_id}", response_model=dict)
def get_purchase(purchase_id: int, session: Session = Depends(get_session)):
    """Get purchase details with items."""
    purchase = session.get(Purchase, purchase_id)
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    
    # Get purchase items
    items = session.exec(
        select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id)
    ).all()
    
    items_list = []
    for item in items:
        item_dict = item.model_dump()
        if item.material_id:
            material = session.get(Material, item.material_id)
            if material:
                item_dict["material_name"] = material.name
        items_list.append(item_dict)
    
    purchase_dict = purchase.model_dump()
    purchase_dict["items"] = items_list
    
    return purchase_dict


@router.post("/", response_model=Purchase)
def create_purchase(
    purchase_data: PurchaseCreate,
    session: Session = Depends(get_session)
):
    """Create purchase and automatically update stock."""
    # Create purchase
    purchase = Purchase(
        supplier=purchase_data.supplier,
        purchase_date=purchase_data.purchase_date,
        invoice_number=purchase_data.invoice_number,
        total_amount=purchase_data.total_amount,
        currency=purchase_data.currency,
        notes=purchase_data.notes,
        created_at=datetime.utcnow()
    )
    
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    
    # Create purchase items and stock movements
    for item_data in purchase_data.items:
        item = PurchaseItem(
            purchase_id=purchase.id,
            material_id=item_data.material_id,
            description=item_data.description,
            sku=item_data.sku,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=item_data.total_price
        )
        session.add(item)
        
        # Create stock movement if material is matched
        if item.material_id:
            movement = StockMovement(
                material_id=item.material_id,
                movement_type="in",
                quantity=item.quantity,
                reference_type="purchase",
                reference_id=purchase.id,
                notes=f"Purchase from {purchase.supplier}",
                created_at=datetime.utcnow()
            )
            session.add(movement)
    
    session.commit()
    session.refresh(purchase)
    
    return purchase
