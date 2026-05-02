"""Central registry: one row per firm / tenant (multitenant mode)."""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from .tenant_metadata import REGISTRY_METADATA


class TenantRegistry(SQLModel, table=True, metadata=REGISTRY_METADATA):
    """Maps firm code -> dedicated SQLite file under data/tenants/<code>/."""

    __tablename__ = "tenant"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(unique=True, index=True)
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    registration: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
