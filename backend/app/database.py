"""Database connection and initialization."""

import os
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy import event
from sqlalchemy.engine import Engine


# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("SOLARAPP_DB_URL", "sqlite:///./data/solarapp.db")

def get_sqlite_file_path():
    """Absolute path to the SQLite database file, or None if DATABASE_URL is not SQLite."""
    if "sqlite:///" not in DATABASE_URL:
        return None
    db_path = DATABASE_URL.replace("sqlite:///", "")
    if db_path.startswith("./"):
        return (Path.cwd() / db_path[2:]).resolve()
    return Path(db_path).resolve()


# Ensure the database directory exists for SQLite databases
if "sqlite:///" in DATABASE_URL:
    db_path = DATABASE_URL.replace("sqlite:///", "")
    # Convert to absolute path
    if db_path.startswith("./"):
        # Relative to the current working directory (typically the backend directory)
        db_file = (Path.cwd() / db_path[2:]).resolve()
    else:
        # Absolute path
        db_file = Path(db_path).resolve()
    
    # Create parent directory if it doesn't exist
    db_file.parent.mkdir(parents=True, exist_ok=True)

# Optimize SQLite settings for Raspberry Pi and SD card performance
sqlite_connect_args = {"check_same_thread": False}

# Create engine with optimizations
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    connect_args=sqlite_connect_args if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,  # Check connection health
    pool_recycle=3600,  # Recycle connections every hour
)


# Set SQLite-specific pragmas for Raspberry Pi optimization
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better performance on Raspberry Pi."""
    if "sqlite" in DATABASE_URL:
        cursor = dbapi_conn.cursor()
        # Use Write-Ahead Logging for better concurrency and less SD card wear
        cursor.execute("PRAGMA journal_mode=WAL")
        # Faster writes, minimal data loss risk
        cursor.execute("PRAGMA synchronous=NORMAL")
        # 32MB cache (-32000 = 32000KB = ~31.25MB)
        cursor.execute("PRAGMA cache_size=-32000")
        # Keep temp tables in memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)
    _ensure_material_company_column()
    _ensure_project_billing_columns()
    _ensure_project_client_id_column()
    _seed_default_companies()


def _ensure_material_company_column():
    """Backfill schema for older databases without material.company."""
    if "sqlite" not in DATABASE_URL:
        return

    with engine.connect() as conn:
        columns = conn.exec_driver_sql("PRAGMA table_info(material)").fetchall()
        column_names = {col[1] for col in columns}
        if "company" not in column_names:
            conn.exec_driver_sql(
                "ALTER TABLE material ADD COLUMN company VARCHAR DEFAULT 'freevoltsrl.ro'"
            )
            conn.exec_driver_sql(
                "UPDATE material SET company='freevoltsrl.ro' WHERE company IS NULL OR company=''"
            )
            conn.commit()


def _ensure_project_client_id_column():
    """Add optional client link on project for SQLite legacy DBs."""
    if "sqlite" not in DATABASE_URL:
        return

    with engine.connect() as conn:
        columns = conn.exec_driver_sql("PRAGMA table_info(project)").fetchall()
        column_names = {col[1] for col in columns}
        if "client_id" not in column_names:
            conn.exec_driver_sql("ALTER TABLE project ADD COLUMN client_id INTEGER")
            conn.commit()


def _seed_default_companies():
    """Insert starter companies when the table is empty."""
    from .models import Company

    with Session(engine) as session:
        if session.exec(select(Company)).first():
            return
        session.add(
            Company(
                code="freevoltsrl.ro",
                name="Freevolt SRL",
                legal_name="Freevolt SRL",
            )
        )
        session.add(
            Company(
                code="energoteamconect.ro",
                name="Energoteam Conect",
                legal_name="Energoteam Conect",
            )
        )
        session.commit()


def _ensure_project_billing_columns():
    """Backfill schema for older databases without client billing fields on project."""
    if "sqlite" not in DATABASE_URL:
        return

    with engine.connect() as conn:
        columns = conn.exec_driver_sql("PRAGMA table_info(project)").fetchall()
        column_names = {col[1] for col in columns}
        alters = []
        if "client_tax_id" not in column_names:
            alters.append("ALTER TABLE project ADD COLUMN client_tax_id VARCHAR")
        if "client_registration" not in column_names:
            alters.append("ALTER TABLE project ADD COLUMN client_registration VARCHAR")
        if "client_billing_address" not in column_names:
            alters.append("ALTER TABLE project ADD COLUMN client_billing_address VARCHAR")
        for stmt in alters:
            conn.exec_driver_sql(stmt)
        if alters:
            conn.commit()


def get_session():
    """Get database session for dependency injection."""
    with Session(engine) as session:
        yield session
