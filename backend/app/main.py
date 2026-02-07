"""FastAPI main application."""

import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import Material, Stock, Project
from .api import materials, stock, projects, purchases, invoices

# Create FastAPI app
app = FastAPI(
    title="SolarApp API",
    description="Solar Panel Management System API",
    version="1.0.0"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(materials.router)
app.include_router(stock.router)
app.include_router(projects.router)
app.include_router(purchases.router)
app.include_router(invoices.router)


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


@app.get("/")
def read_root():
    """Root endpoint."""
    return {
        "message": "Welcome to SolarApp API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/v1/dashboard/stats")
def get_dashboard_stats(session: Session = Depends(get_session)):
    """Get dashboard statistics."""
    # Total materials
    total_materials = len(session.exec(select(Material)).all())
    
    # Low stock count
    low_stock_count = 0
    stocks = session.exec(select(Stock)).all()
    for stock in stocks:
        material = session.get(Material, stock.material_id)
        if material and stock.quantity < material.min_stock:
            low_stock_count += 1
    
    # Active projects
    active_projects = len(
        session.exec(
            select(Project).where(
                (Project.status == "planned") | 
                (Project.status == "in_progress")
            )
        ).all()
    )
    
    # Total projects
    total_projects = len(session.exec(select(Project)).all())
    
    return {
        "total_materials": total_materials,
        "low_stock_count": low_stock_count,
        "active_projects": active_projects,
        "total_projects": total_projects
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
