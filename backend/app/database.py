"""Database connection and initialization."""

import os
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import event
from sqlalchemy.engine import Engine


# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("SOLARAPP_DB_URL", "sqlite:///./solarapp.db")

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


def get_session():
    """Get database session for dependency injection."""
    with Session(engine) as session:
        yield session
