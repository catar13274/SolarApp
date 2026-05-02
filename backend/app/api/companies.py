"""Companies API — central registry + optional per-firm SQLite when multitenant."""

import re
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..database import (
    MULTITENANT_ENABLED,
    invalidate_tenant_engine,
    normalize_tenant_code,
    provision_tenant_database,
    tenant_db_path,
    tenant_has_any_material,
)
from ..deps import get_registry_session
from ..models import Company, CompanyCreate, CompanyUpdate
from ..registry_models import TenantRegistry

router = APIRouter(prefix="/api/v1/companies", tags=["companies"])


def _normalize_company_code(code: str) -> str:
    c = (code or "").strip().lower()
    c = re.sub(r"\s+", "-", c)
    if not c:
        raise HTTPException(status_code=400, detail="Company code is required")
    return c


def _to_company(row: TenantRegistry) -> Company:
    return Company.model_validate(row)


@router.get("/", response_model=List[Company])
def list_companies(session: Session = Depends(get_registry_session)):
    rows = session.exec(select(TenantRegistry).order_by(TenantRegistry.name.asc())).all()
    return [_to_company(r) for r in rows]


@router.post("/", response_model=Company)
def create_company(payload: CompanyCreate, session: Session = Depends(get_registry_session)):
    code = _normalize_company_code(payload.code)
    if session.exec(select(TenantRegistry).where(TenantRegistry.code == code)).first():
        raise HTTPException(status_code=400, detail="A company with this code already exists")

    row = TenantRegistry(
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

    if MULTITENANT_ENABLED:
        provision_tenant_database(code)

    return _to_company(row)


@router.get("/{company_id}", response_model=Company)
def get_company(company_id: int, session: Session = Depends(get_registry_session)):
    row = session.get(TenantRegistry, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")
    return _to_company(row)


@router.put("/{company_id}", response_model=Company)
def update_company(
    company_id: int,
    payload: CompanyUpdate,
    session: Session = Depends(get_registry_session),
):
    row = session.get(TenantRegistry, company_id)
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
    return _to_company(row)


@router.delete("/{company_id}")
def delete_company(company_id: int, session: Session = Depends(get_registry_session)):
    row = session.get(TenantRegistry, company_id)
    if not row:
        raise HTTPException(status_code=404, detail="Company not found")

    code = normalize_tenant_code(row.code)
    if MULTITENANT_ENABLED:
        if tenant_has_any_material(code):
            raise HTTPException(
                status_code=400,
                detail="Nu se poate sterge firma: exista materiale in baza acestei firme.",
            )
        path = tenant_db_path(code)
        invalidate_tenant_engine(code)
        if path.is_file():
            try:
                for extra in (Path(str(path) + "-wal"), Path(str(path) + "-shm")):
                    if extra.is_file():
                        extra.unlink()
                path.unlink()
            except OSError as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Nu s-a putut sterge fisierul bazei: {exc}",
                ) from exc
        parent = path.parent
        try:
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass

    session.delete(row)
    session.commit()
    return {"message": "Company deleted"}
