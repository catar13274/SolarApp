"""Purchases API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from datetime import datetime

from ..database import get_session
from ..models import Purchase, PurchaseItem, StockMovement, Material

router = APIRouter(prefix="/api/v1/purchases", tags=["purchases"])


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
    purchase_data: dict,
    session: Session = Depends(get_session)
):
    """Create purchase and automatically update stock."""
    # Create purchase
    purchase = Purchase(
        supplier=purchase_data.get("supplier"),
        purchase_date=purchase_data.get("purchase_date"),
        invoice_number=purchase_data.get("invoice_number"),
        total_amount=purchase_data.get("total_amount", 0.0),
        currency=purchase_data.get("currency", "RON"),
        notes=purchase_data.get("notes"),
        created_at=datetime.utcnow()
    )
    
    session.add(purchase)
    session.commit()
    session.refresh(purchase)
    
    # Create purchase items and stock movements
    items = purchase_data.get("items", [])
    for item_data in items:
        item = PurchaseItem(
            purchase_id=purchase.id,
            material_id=item_data.get("material_id"),
            description=item_data.get("description"),
            sku=item_data.get("sku"),
            quantity=item_data.get("quantity"),
            unit_price=item_data.get("unit_price"),
            total_price=item_data.get("total_price")
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
