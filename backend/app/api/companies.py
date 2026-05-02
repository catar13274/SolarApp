"""Companies (stock owners) API."""

import re
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import get_session
from ..models import Company, CompanyCreate, CompanyUpdate, Material

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def _normalize_company_code(code: str) -> str:
    c = (code or "").strip().lower()
    c = re.sub(r"\s+", "-", c)
    if not c:
        raise HTTPException(status_code=400, detail="Company code is required")
    return c


@router.get("/", response_model=List[Company])
def list_companies(session: Session = Depends(get_session)):
    """List all registered companies for stock management."""
    rows = session.exec(select(Company).order_by(Company.name.asc())).all()
    return rows


@router.post("/", response_model=Company)
def create_company(payload: CompanyCreate, session: Session = Depends(get_session)):
    """Register a new company."""
    code = _normalize_company_code(payload.code)
    if session.exec(select(Company).where(Company.code == code)).first():
        raise HTTPException(status_code=400, detail="A company with this code already exists")

    row = Company(
        code=code,
        name=payload.name.strip(),
        legal_name=payload.legal_name,
        tax_id=payload.tax_id,
        registration=payload.registration,
        address=payload.address,
        phone=payload.phone,
        email=payload.email,
        notes=payload.notes,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


@router.get("/{company_id}", response_model=Company)
def get_company(company_id: int, session: Session = Depends(get_session)):
    row = session.get(Company, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return row


@router.put("/{company_id}", response_model=Company)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    session: Session = Depends(get_session),
):
    row = session.get(Company, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")

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


@router.delete("/{company_id}")
def delete_company(company_id: int, session: Session = Depends(get_session)):
    row = session.get(Company, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")

    in_use = session.exec(select(Material).where(Material.company == row.code)).first()
    if in_use:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete company: materials still reference this company code.",
        )

    session.delete(row)
    session.commit()
    return {"message": "Company deleted"}
