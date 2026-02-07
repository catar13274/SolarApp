"""Database connection and initialization."""

import os
from sqlmodel import SQLModel, create_engine, Session


# Get database URL from environment or use default SQLite
DATABASE_URL = os.getenv("SOLARAPP_DB_URL", "sqlite:///./solarapp.db")

# Optimize SQLite settings for Raspberry Pi and SD card performance
sqlite_connect_args = {"check_same_thread": False}
if "sqlite" in DATABASE_URL:
    # Add SQLite-specific optimizations for Raspberry Pi
    sqlite_connect_args.update({
        "check_same_thread": False,
        # Use Write-Ahead Logging for better concurrency and less SD card wear
        "pragma": {
            "journal_mode": "WAL",
            "synchronous": "NORMAL",  # Faster writes, minimal data loss risk
            "cache_size": -32000,  # 32MB cache (negative = KB)
            "temp_store": "MEMORY",  # Keep temp tables in memory
            "mmap_size": 30000000000,  # Enable memory-mapped I/O
        }
    })

# Create engine with optimizations
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL logging
    connect_args=sqlite_connect_args if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,  # Check connection health
    pool_recycle=3600,  # Recycle connections every hour
)


def create_db_and_tables():
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session for dependency injection."""
    with Session(engine) as session:
        yield session
