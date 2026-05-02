"""Clients API."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..deps import get_session
from ..models import Client, ClientCreate, ClientUpdate

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.get("/", response_model=List[Client])
def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = Query(None),
    session: Session = Depends(get_session),
):
    query = select(Client)
    if search:
        query = query.where(Client.name.contains(search))
    rows = session.exec(query.order_by(Client.name.asc()).offset(skip).limit(limit)).all()
    return rows


@router.post("/", response_model=Client)
def create_client(payload: ClientCreate, session: Session = Depends(get_session)):
    row = Client(
        name=payload.name.strip(),
        contact=payload.contact,
        tax_id=payload.tax_id,
        registration=payload.registration,
        billing_address=payload.billing_address,
        location=payload.location,
        notes=payload.notes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.get("/{client_id}", response_model=Client)
def get_client(client_id: int, session: Session = Depends(get_session)):
    row = session.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")
    return row


@router.put("/{client_id}", response_model=Client)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    session: Session = Depends(get_session),
):
    row = session.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")

    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if value is not None and key == "name":
            setattr(row, key, str(value).strip())
        elif value is not None:
            setattr(row, key, value)

    row.updated_at = datetime.utcnow()
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.delete("/{client_id}")
def delete_client(client_id: int, session: Session = Depends(get_session)):
    from ..models import Project

    row = session.get(Client, client_id)
    if not row:
        raise HTTPException(status_code=404, detail="Client not found")

    linked = session.exec(select(Project).where(Project.client_id == client_id)).first()
    if linked:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete client linked to one or more projects.",
        )

    session.delete(row)
    session.commit()
    return {"message": "Client deleted"}
