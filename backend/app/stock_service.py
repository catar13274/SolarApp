"""Shared stock movement business logic."""

from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from .models import Material, Stock, StockMovement


def apply_stock_movement(
    session: Session,
    material_id: int,
    movement_type: str,
    quantity: float,
    unit_price: float | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    notes: str | None = None,
) -> StockMovement:
    """Apply a stock movement and keep Stock.quantity in sync."""
    material = session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    stock = session.exec(select(Stock).where(Stock.material_id == material_id)).first()
    if not stock:
        stock = Stock(material_id=material_id, quantity=0.0, location="Main Warehouse")
        session.add(stock)

    if movement_type == "in":
        stock.quantity += quantity
    elif movement_type == "out":
        if stock.quantity < quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")
        stock.quantity -= quantity
    elif movement_type == "adjustment":
        stock.quantity = quantity
    elif movement_type == "transfer":
        stock.quantity += quantity
    else:
        raise HTTPException(status_code=400, detail="Invalid movement type")

    stock.updated_at = datetime.utcnow()

    movement = StockMovement(
        material_id=material_id,
        movement_type=movement_type,
        quantity=quantity,
        unit_price=unit_price,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        created_at=datetime.utcnow(),
    )

    session.add(stock)
    session.add(movement)
    return movement
