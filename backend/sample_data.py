"""Sample data script for SolarApp."""

from datetime import date, datetime
from sqlmodel import Session, create_engine
from app.models import Material, Stock, Project, ProjectMaterial, Purchase, PurchaseItem
from app.database import DATABASE_URL

# Create engine
engine = create_engine(DATABASE_URL)


def create_sample_data():
    """Create sample materials, projects, and stock."""
    with Session(engine) as session:
        print("Creating sample materials...")
        
        # Sample materials
        materials = [
            Material(
                name="Solar Panel 450W Monocrystalline",
                sku="PANEL-450W-MONO",
                description="High efficiency 450W monocrystalline solar panel",
                category="panel",
                unit="buc",
                unit_price=850.00,
                min_stock=20
            ),
            Material(
                name="Solar Panel 550W Bifacial",
                sku="PANEL-550W-BIFA",
                description="Bifacial 550W solar panel with enhanced performance",
                category="panel",
                unit="buc",
                unit_price=1100.00,
                min_stock=15
            ),
            Material(
                name="Inverter 5kW Hybrid",
                sku="INV-5KW-HYB",
                description="5kW hybrid inverter with battery backup support",
                category="inverter",
                unit="buc",
                unit_price=3500.00,
                min_stock=5
            ),
            Material(
                name="Inverter 10kW Three Phase",
                sku="INV-10KW-3PH",
                description="10kW three phase grid-tie inverter",
                category="inverter",
                unit="buc",
                unit_price=5500.00,
                min_stock=3
            ),
            Material(
                name="Battery Storage 10kWh LiFePO4",
                sku="BAT-10KWH-LIFEPO4",
                description="10kWh LiFePO4 battery storage system",
                category="battery",
                unit="buc",
                unit_price=8000.00,
                min_stock=5
            ),
            Material(
                name="Battery Storage 15kWh LiFePO4",
                sku="BAT-15KWH-LIFEPO4",
                description="15kWh LiFePO4 battery storage system",
                category="battery",
                unit="buc",
                unit_price=11500.00,
                min_stock=3
            ),
            Material(
                name="Solar Cable 6mm2 Black",
                sku="CABLE-6MM-BLK",
                description="6mm2 solar cable, black, UV resistant",
                category="cable",
                unit="m",
                unit_price=12.50,
                min_stock=500
            ),
            Material(
                name="Solar Cable 4mm2 Red",
                sku="CABLE-4MM-RED",
                description="4mm2 solar cable, red, UV resistant",
                category="cable",
                unit="m",
                unit_price=10.00,
                min_stock=500
            ),
            Material(
                name="Roof Mounting System - Tiled Roof",
                sku="MOUNT-TILE-KIT",
                description="Complete mounting system for tiled roofs",
                category="mounting",
                unit="set",
                unit_price=450.00,
                min_stock=10
            ),
            Material(
                name="Roof Mounting System - Metal Roof",
                sku="MOUNT-METAL-KIT",
                description="Complete mounting system for metal roofs",
                category="mounting",
                unit="set",
                unit_price=400.00,
                min_stock=10
            ),
            Material(
                name="MC4 Connectors Pair",
                sku="CONN-MC4-PAIR",
                description="MC4 connector pair (male + female)",
                category="other",
                unit="pair",
                unit_price=8.50,
                min_stock=100
            ),
            Material(
                name="Junction Box IP65",
                sku="JBOX-IP65",
                description="Waterproof junction box IP65 rated",
                category="other",
                unit="buc",
                unit_price=85.00,
                min_stock=20
            ),
            Material(
                name="AC Protection Box",
                sku="ACBOX-PROT",
                description="AC protection box with circuit breakers",
                category="other",
                unit="buc",
                unit_price=250.00,
                min_stock=15
            ),
            Material(
                name="DC Protection Box",
                sku="DCBOX-PROT",
                description="DC protection box with surge protection",
                category="other",
                unit="buc",
                unit_price=180.00,
                min_stock=15
            ),
            Material(
                name="Grounding Kit",
                sku="GROUND-KIT",
                description="Complete grounding kit for solar installation",
                category="other",
                unit="set",
                unit_price=120.00,
                min_stock=20
            ),
        ]
        
        for material in materials:
            session.add(material)
        
        session.commit()
        
        # Create initial stock for materials
        print("Creating initial stock...")
        for material in materials:
            session.refresh(material)
            
            # Set some initial stock quantities
            initial_qty = material.min_stock * 1.5 if material.category in ["panel", "inverter", "battery"] else material.min_stock * 2
            
            stock = Stock(
                material_id=material.id,
                quantity=initial_qty,
                location="Main Warehouse"
            )
            session.add(stock)
        
        session.commit()
        
        # Create sample projects
        print("Creating sample projects...")
        
        projects = [
            Project(
                name="Residential Installation - Popescu Family",
                client_name="Popescu Ion",
                client_contact="+40 723 456 789",
                location="Bucharest, Sector 3",
                capacity_kw=6.3,
                status="in_progress",
                start_date=date(2024, 1, 15),
                estimated_cost=25000.00,
                notes="14 panels, 5kW hybrid inverter, 10kWh battery"
            ),
            Project(
                name="Commercial Installation - Tech Office",
                client_name="TechCorp SRL",
                client_contact="+40 721 123 456",
                location="Cluj-Napoca",
                capacity_kw=22.0,
                status="planned",
                start_date=date(2024, 2, 1),
                estimated_cost=85000.00,
                notes="40 panels, 10kW three-phase inverter, no battery"
            ),
            Project(
                name="Farm Installation - Green Energy Farm",
                client_name="Agro Green SRL",
                client_contact="+40 745 987 654",
                location="Timisoara",
                capacity_kw=33.0,
                status="planned",
                start_date=date(2024, 3, 1),
                estimated_cost=120000.00,
                notes="60 panels, 15kWh battery storage, ground mounting"
            ),
            Project(
                name="Residential Installation - Ionescu Villa",
                client_name="Ionescu Maria",
                client_contact="+40 732 111 222",
                location="Brasov",
                capacity_kw=8.8,
                status="completed",
                start_date=date(2023, 11, 1),
                end_date=date(2023, 11, 20),
                estimated_cost=35000.00,
                actual_cost=34500.00,
                notes="20 panels, 5kW hybrid inverter, 10kWh battery"
            ),
        ]
        
        for project in projects:
            session.add(project)
        
        session.commit()
        
        print("Sample data created successfully!")
        print(f"- {len(materials)} materials")
        print(f"- {len(projects)} projects")
        print("\nUse the API to explore the data.")


if __name__ == "__main__":
    create_sample_data()
