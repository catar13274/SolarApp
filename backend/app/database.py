"""Database connection and initialization."""

import os
from sqlmodel import SQLModel, create_engine, Session


# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("SOLARAPP_DB_URL", "sqlite:///./solarapp.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session for dependency injection."""
    with Session(engine) as session:
        yield session
