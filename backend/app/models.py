"""Database models for SolarApp."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from sqlmodel import Field, SQLModel

from .tenant_metadata import TENANT_METADATA


class Company(BaseModel):
    """Registered firm (API shape; stored in central registry when multitenant)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    registration: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class Client(SQLModel, table=True, metadata=TENANT_METADATA):
    """Saved customer used when creating projects."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    contact: Optional[str] = None
    tax_id: Optional[str] = None
    registration: Optional[str] = None
    billing_address: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Material(SQLModel, table=True, metadata=TENANT_METADATA):
    """Material model for tracking inventory items (scoped by tenant DB when multitenant)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    description: Optional[str] = None
    category: str  # "panel", "inverter", "battery", "cable", "mounting", "other"
    unit: str = "buc"
    unit_price: float = 0.0
    min_stock: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Stock(SQLModel, table=True, metadata=TENANT_METADATA):
    """Stock model for tracking current inventory levels."""

    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="material.id")
    quantity: float = 0.0
    location: Optional[str] = "Main Warehouse"
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StockMovement(SQLModel, table=True, metadata=TENANT_METADATA):
    """Stock movement model for tracking inventory changes."""

    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="material.id")
    movement_type: str  # "in", "out", "adjustment", "transfer"
    quantity: float
    unit_price: Optional[float] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class Project(SQLModel, table=True, metadata=TENANT_METADATA):
    """Project model for tracking solar panel installations."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    client_name: str
    client_contact: Optional[str] = None
    client_tax_id: Optional[str] = None
    client_registration: Optional[str] = None
    client_billing_address: Optional[str] = None
    location: Optional[str] = None
    capacity_kw: Optional[float] = None
    status: str = "planned"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    labor_cost_estimated: Optional[float] = None
    labor_cost_actual: Optional[float] = None
    transport_cost_estimated: Optional[float] = None
    transport_cost_actual: Optional[float] = None
    other_costs_estimated: Optional[float] = None
    other_costs_actual: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectMaterial(SQLModel, table=True, metadata=TENANT_METADATA):
    """Many-to-many relationship between projects and materials."""

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    material_id: int = Field(foreign_key="material.id")
    quantity_planned: float = 0.0
    quantity_used: float = 0.0
    unit_price: float = 0.0


class Purchase(SQLModel, table=True, metadata=TENANT_METADATA):
    """Purchase model for tracking material purchases."""

    id: Optional[int] = Field(default=None, primary_key=True)
    supplier: str
    purchase_date: date
    invoice_number: Optional[str] = None
    total_amount: float = 0.0
    currency: str = "RON"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PurchaseItem(SQLModel, table=True, metadata=TENANT_METADATA):
    """Purchase items model for individual items in a purchase."""

    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_id: int = Field(foreign_key="purchase.id")
    material_id: Optional[int] = Field(foreign_key="material.id")
    description: str
    sku: Optional[str] = None
    quantity: float
    unit_price: float
    total_price: float


class Invoice(SQLModel, table=True, metadata=TENANT_METADATA):
    """Invoice model for uploaded invoices."""

    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_number: str = Field(unique=True, index=True)
    supplier: str
    invoice_date: date
    total_amount: float
    currency: str = "RON"
    xml_file_path: Optional[str] = None
    file_format: Optional[str] = None
    purchase_id: Optional[int] = Field(foreign_key="purchase.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response Models (Pydantic models for API validation)


class PurchaseItemCreate(BaseModel):
    """Model for creating purchase items."""

    material_id: Optional[int] = None
    description: str
    sku: Optional[str] = None
    quantity: float
    unit_price: float
    total_price: float


class PurchaseItemUpdate(BaseModel):
    """Model for updating purchase items."""

    description: Optional[str] = None
    sku: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None


class PurchaseCreate(BaseModel):
    """Model for creating purchases."""

    supplier: str
    purchase_date: date
    invoice_number: Optional[str] = None
    total_amount: float = 0.0
    currency: str = "RON"
    notes: Optional[str] = None
    items: List[PurchaseItemCreate] = []


class ProjectMaterialUpdate(BaseModel):
    """Model for updating project materials."""

    quantity_planned: Optional[float] = None
    quantity_used: Optional[float] = None
    unit_price: Optional[float] = None


class MaterialUsed(BaseModel):
    """Model for materials used in a project."""

    material_id: int
    quantity: float


class CompanyCreate(BaseModel):
    code: str
    name: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    registration: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    registration: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ClientCreate(BaseModel):
    name: str
    contact: Optional[str] = None
    tax_id: Optional[str] = None
    registration: Optional[str] = None
    billing_address: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    tax_id: Optional[str] = None
    registration: Optional[str] = None
    billing_address: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class ProjectUpdate(BaseModel):
    """Model for updating projects with proper date handling."""

    name: str
    client_id: Optional[int] = None
    client_name: str
    client_contact: Optional[str] = None
    client_tax_id: Optional[str] = None
    client_registration: Optional[str] = None
    client_billing_address: Optional[str] = None
    location: Optional[str] = None
    capacity_kw: Optional[float] = None
    status: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    labor_cost_estimated: Optional[float] = None
    labor_cost_actual: Optional[float] = None
    transport_cost_estimated: Optional[float] = None
    transport_cost_actual: Optional[float] = None
    other_costs_estimated: Optional[float] = None
    other_costs_actual: Optional[float] = None
    notes: Optional[str] = None
