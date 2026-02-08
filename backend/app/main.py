"""FastAPI main application."""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Depends
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from sqlmodel import Session, select

# Load environment variables from .env file
load_dotenv()

from .database import create_db_and_tables, get_session
from .models import Material, Stock, Project
from .api import materials, stock, projects, purchases, invoices

# Configure logging
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SolarApp API",
    description="Solar Panel Management System API",
    version="1.0.0"
)

# Add GZip compression middleware for better performance on slow connections
app.add_middleware(GZipMiddleware, minimum_size=1000)

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


# Get the path to the frontend dist directory
# First check if frontend is built in the parent directory structure
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"

# Mount static files if frontend is built
if frontend_dist.exists() and frontend_dist.is_dir():
    # Mount static assets (js, css, images, etc.)
    app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")


@app.on_event("startup")
def on_startup():
    """Initialize database on startup."""
    create_db_and_tables()


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


# Serve frontend for all other routes (catch-all for SPA)
# This must be defined last, after all API routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve frontend application for all non-API routes."""
    # Use the module-level frontend_dist variable
    # If frontend is not built, return a helpful message
    if not frontend_dist.exists():
        return {
            "message": "Frontend not built",
            "info": "Run 'cd frontend && npm install && npm run build' to build the frontend",
            "api_docs": "/docs"
        }
    
    # Check if specific file exists (for static assets like vite.svg, favicon.ico)
    # Prevent path traversal attacks by resolving and validating the path
    try:
        file_path = (frontend_dist / full_path).resolve()
        # Ensure the resolved path is within frontend_dist
        if file_path.is_relative_to(frontend_dist) and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
    except (ValueError, RuntimeError, OSError) as e:
        # Invalid path or OS error, continue to serve index.html
        # Log the error in development mode without exposing full paths
        if os.getenv("ENVIRONMENT") == "development":
            logger.warning(f"Could not serve static file: {type(e).__name__}")
        pass
    
    # For all other routes, serve index.html (SPA routing)
    index_path = frontend_dist / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    # Fallback if index.html doesn't exist
    return {"message": "Frontend index.html not found", "api_docs": "/docs"}
