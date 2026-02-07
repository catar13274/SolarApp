"""Database models for SolarApp."""

from datetime import date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel


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
    purchase_id: Optional[int] = Field(foreign_key="purchase.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
