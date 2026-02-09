"""Database models for SolarApp."""

from datetime import date, datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


class Material(SQLModel, table=True):
    """Material model for tracking inventory items."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    sku: str = Field(unique=True, index=True)
    description: Optional[str] = None
    category: str  # "panel", "inverter", "battery", "cable", "mounting", "other"
    unit: str = "buc"  # Unit of measurement
    unit_price: float = 0.0
    min_stock: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Stock(SQLModel, table=True):
    """Stock model for tracking current inventory levels."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="material.id")
    quantity: float = 0.0
    location: Optional[str] = "Main Warehouse"
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class StockMovement(SQLModel, table=True):
    """Stock movement model for tracking inventory changes."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    material_id: int = Field(foreign_key="material.id")
    movement_type: str  # "in", "out", "adjustment", "transfer"
    quantity: float
    unit_price: Optional[float] = None  # Acquisition price per unit (for "in" movements)
    reference_type: Optional[str] = None  # "purchase", "project", "manual"
    reference_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class Project(SQLModel, table=True):
    """Project model for tracking solar panel installations."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    client_name: str
    client_contact: Optional[str] = None
    location: Optional[str] = None
    capacity_kw: Optional[float] = None  # System capacity in kW
    status: str = "planned"  # "planned", "in_progress", "completed", "cancelled"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    # Cost breakdown fields
    labor_cost_estimated: Optional[float] = None
    labor_cost_actual: Optional[float] = None
    transport_cost_estimated: Optional[float] = None
    transport_cost_actual: Optional[float] = None
    other_costs_estimated: Optional[float] = None
    other_costs_actual: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectMaterial(SQLModel, table=True):
    """Many-to-many relationship between projects and materials."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="project.id")
    material_id: int = Field(foreign_key="material.id")
    quantity_planned: float = 0.0
    quantity_used: float = 0.0
    unit_price: float = 0.0


class Purchase(SQLModel, table=True):
    """Purchase model for tracking material purchases."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    supplier: str
    purchase_date: date
    invoice_number: Optional[str] = None
    total_amount: float = 0.0
    currency: str = "RON"
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PurchaseItem(SQLModel, table=True):
    """Purchase items model for individual items in a purchase."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_id: int = Field(foreign_key="purchase.id")
    material_id: Optional[int] = Field(foreign_key="material.id")
    description: str
    sku: Optional[str] = None
    quantity: float
    unit_price: float
    total_price: float


class Invoice(SQLModel, table=True):
    """Invoice model for uploaded invoices."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_number: str = Field(unique=True, index=True)
    supplier: str
    invoice_date: date
    total_amount: float
    currency: str = "RON"
    xml_file_path: Optional[str] = None
    file_format: Optional[str] = None  # File extension: xml, pdf, doc, xls, txt
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


class ProjectUpdate(BaseModel):
    """Model for updating projects with proper date handling.
    
    Dates should be provided as ISO 8601 strings (YYYY-MM-DD format).
    For example: "2024-03-15" for March 15, 2024.
    """
    name: str
    client_name: str
    client_contact: Optional[str] = None
    location: Optional[str] = None
    capacity_kw: Optional[float] = None
    status: str
    start_date: Optional[str] = None  # ISO 8601 date string (YYYY-MM-DD)
    end_date: Optional[str] = None    # ISO 8601 date string (YYYY-MM-DD)
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    labor_cost_estimated: Optional[float] = None
    labor_cost_actual: Optional[float] = None
    transport_cost_estimated: Optional[float] = None
    transport_cost_actual: Optional[float] = None
    other_costs_estimated: Optional[float] = None
    other_costs_actual: Optional[float] = None
    notes: Optional[str] = None
