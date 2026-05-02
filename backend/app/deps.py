"""FastAPI dependencies: tenant routing and registry sessions."""

from typing import Annotated, Generator, Optional

from fastapi import Depends, Header, HTTPException
from sqlmodel import Session

from .database import (
    MULTITENANT_ENABLED,
    engine,
    get_tenant_engine,
    normalize_tenant_code,
    registry_engine,
)


def resolve_tenant_code(
    x_solarapp_tenant: Annotated[Optional[str], Header(alias="X-Solarapp-Tenant")] = None,
) -> Optional[str]:
    """Legacy mode: no tenant routing. Multitenant: require firm code header."""
    if not MULTITENANT_ENABLED:
        return None
    if not x_solarapp_tenant or not x_solarapp_tenant.strip():
        raise HTTPException(
            status_code=400,
            detail="Lipseste header-ul X-Solarapp-Tenant (cod firma, ex. freevoltsrl.ro).",
        )
    return normalize_tenant_code(x_solarapp_tenant.strip())


def get_session(
    tenant_key: Optional[str] = Depends(resolve_tenant_code),
) -> Generator[Session, None, None]:
    if tenant_key is None:
        if engine is None:
            raise HTTPException(
                status_code=503,
                detail="Mod legacy fara SOLARAPP_DB_URL valid — folositi SOLARAPP_MULTITENANT=true.",
            )
        with Session(engine) as session:
            yield session
    else:
        eng = get_tenant_engine(tenant_key)
        with Session(eng) as session:
            yield session


def get_registry_session() -> Generator[Session, None, None]:
    with Session(registry_engine) as session:
        yield session
