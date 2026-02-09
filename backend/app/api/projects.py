"""Projects API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlmodel import Session, select
from datetime import datetime

from ..database import get_session
from ..models import Project, ProjectMaterial, Material, StockMovement, ProjectMaterialUpdate, MaterialUsed, ProjectUpdate
from ..pdf_service import generate_commercial_offer_pdf, remove_diacritics

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


@router.get("/", response_model=List[Project])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """List all projects with filters."""
    query = select(Project)
    
    if status:
        query = query.where(Project.status == status)
    
    if search:
        query = query.where(
            (Project.name.contains(search)) | 
            (Project.client_name.contains(search))
        )
    
    query = query.offset(skip).limit(limit)
    projects = session.exec(query).all()
    
    return projects


@router.get("/{project_id}", response_model=dict)
def get_project(project_id: int, session: Session = Depends(get_session)):
    """Get project details with materials."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get project materials
    project_materials = session.exec(
        select(ProjectMaterial).where(ProjectMaterial.project_id == project_id)
    ).all()
    
    materials_list = []
    for pm in project_materials:
        material = session.get(Material, pm.material_id)
        if material:
            materials_list.append({
                "id": pm.id,
                "material_id": material.id,
                "material_name": material.name,
                "material_sku": material.sku,
                "quantity_planned": pm.quantity_planned,
                "quantity_used": pm.quantity_used,
                "unit_price": pm.unit_price,
                "total_cost": pm.quantity_planned * pm.unit_price
            })
    
    project_dict = project.model_dump()
    project_dict["materials"] = materials_list
    
    return project_dict


@router.post("/", response_model=Project)
def create_project(project: Project, session: Session = Depends(get_session)):
    """Create a new project."""
    project.created_at = datetime.utcnow()
    project.updated_at = datetime.utcnow()
    
    session.add(project)
    session.commit()
    session.refresh(project)
    
    return project


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    session: Session = Depends(get_session)
):
    """Update an existing project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Update fields
    project.name = project_update.name
    project.client_name = project_update.client_name
    project.client_contact = project_update.client_contact
    project.location = project_update.location
    project.capacity_kw = project_update.capacity_kw
    project.status = project_update.status
    
    # Handle date conversion from string to date object
    if project_update.start_date:
        try:
            project.start_date = datetime.fromisoformat(project_update.start_date).date()
        except (ValueError, AttributeError):
            project.start_date = None
    else:
        project.start_date = None
    
    if project_update.end_date:
        try:
            project.end_date = datetime.fromisoformat(project_update.end_date).date()
        except (ValueError, AttributeError):
            project.end_date = None
    else:
        project.end_date = None
    
    project.estimated_cost = project_update.estimated_cost
    project.actual_cost = project_update.actual_cost
    project.labor_cost_estimated = project_update.labor_cost_estimated
    project.labor_cost_actual = project_update.labor_cost_actual
    project.transport_cost_estimated = project_update.transport_cost_estimated
    project.transport_cost_actual = project_update.transport_cost_actual
    project.other_costs_estimated = project_update.other_costs_estimated
    project.other_costs_actual = project_update.other_costs_actual
    project.notes = project_update.notes
    project.updated_at = datetime.utcnow()
    
    session.add(project)
    session.commit()
    session.refresh(project)
    
    return project


@router.delete("/{project_id}")
def delete_project(project_id: int, session: Session = Depends(get_session)):
    """Delete a project."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete associated materials
    materials = session.exec(
        select(ProjectMaterial).where(ProjectMaterial.project_id == project_id)
    ).all()
    for material in materials:
        session.delete(material)
    
    session.delete(project)
    session.commit()
    
    return {"message": "Project deleted successfully"}


@router.post("/{project_id}/materials", response_model=ProjectMaterial)
def add_material_to_project(
    project_id: int,
    project_material: ProjectMaterial,
    session: Session = Depends(get_session)
):
    """Add material to project."""
    # Verify project exists
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify material exists
    material = session.get(Material, project_material.material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    project_material.project_id = project_id
    
    session.add(project_material)
    session.commit()
    session.refresh(project_material)
    
    return project_material


@router.put("/{project_id}/materials/{material_id}", response_model=ProjectMaterial)
def update_project_material(
    project_id: int,
    material_id: int,
    updates: ProjectMaterialUpdate,
    session: Session = Depends(get_session)
):
    """Update project material quantities and prices."""
    project_material = session.exec(
        select(ProjectMaterial).where(
            (ProjectMaterial.project_id == project_id) &
            (ProjectMaterial.material_id == material_id)
        )
    ).first()
    
    if not project_material:
        raise HTTPException(status_code=404, detail="Project material not found")
    
    if updates.quantity_planned is not None:
        project_material.quantity_planned = updates.quantity_planned
    if updates.quantity_used is not None:
        project_material.quantity_used = updates.quantity_used
    if updates.unit_price is not None:
        project_material.unit_price = updates.unit_price
    
    session.add(project_material)
    session.commit()
    session.refresh(project_material)
    
    return project_material


@router.delete("/{project_id}/materials/{material_id}")
def remove_material_from_project(
    project_id: int,
    material_id: int,
    session: Session = Depends(get_session)
):
    """Remove material from project."""
    project_material = session.exec(
        select(ProjectMaterial).where(
            (ProjectMaterial.project_id == project_id) &
            (ProjectMaterial.material_id == material_id)
        )
    ).first()
    
    if not project_material:
        raise HTTPException(status_code=404, detail="Project material not found")
    
    session.delete(project_material)
    session.commit()
    
    return {"message": "Material removed from project"}


@router.post("/{project_id}/use-materials")
def use_materials(
    project_id: int,
    materials_used: List[MaterialUsed],
    session: Session = Depends(get_session)
):
    """Mark materials as used in project and update stock."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    for item in materials_used:
        if item.quantity <= 0:
            continue
        
        # Update project material
        project_material = session.exec(
            select(ProjectMaterial).where(
                (ProjectMaterial.project_id == project_id) &
                (ProjectMaterial.material_id == item.material_id)
            )
        ).first()
        
        if project_material:
            project_material.quantity_used += item.quantity
            session.add(project_material)
        
        # Create stock movement
        movement = StockMovement(
            material_id=item.material_id,
            movement_type="out",
            quantity=item.quantity,
            reference_type="project",
            reference_id=project_id,
            notes=f"Used in project: {project.name}"
        )
        session.add(movement)
    
    session.commit()
    
    return {"message": "Materials marked as used successfully"}


@router.get("/{project_id}/export-pdf")
def export_project_pdf(project_id: int, session: Session = Depends(get_session)):
    """Export project as a commercial offer PDF."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get project materials
    project_materials = session.exec(
        select(ProjectMaterial).where(ProjectMaterial.project_id == project_id)
    ).all()
    
    materials_list = []
    for pm in project_materials:
        material = session.get(Material, pm.material_id)
        if material:
            materials_list.append({
                "material_id": material.id,
                "material_name": material.name,
                "material_sku": material.sku,
                "quantity_planned": pm.quantity_planned,
                "quantity_used": pm.quantity_used,
                "unit_price": pm.unit_price,
                "total_cost": pm.quantity_planned * pm.unit_price
            })
    
    # Prepare project data for PDF
    project_data = project.model_dump()
    
    # Generate PDF
    try:
        pdf_bytes = generate_commercial_offer_pdf(project_data, materials_list)
        
        # Create filename
        filename = f"Oferta_Comerciala_{remove_diacritics(project.name.replace(' ', '_'))}_{datetime.now().strftime('%Y%m%d')}.pdf"
        
        # Return PDF as response
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
