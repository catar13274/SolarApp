#!/usr/bin/env python3
"""Database initialization script for SolarApp.

This script creates the database and all tables if they don't exist.
Run this script to initialize the database before starting the application.
"""

import os
import sys
from pathlib import Path

# Add the backend directory to the path so we can import app modules
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import create_db_and_tables, DATABASE_URL

def main():
    """Initialize the database."""
    print("=" * 60)
    print("SolarApp Database Initialization")
    print("=" * 60)
    print(f"\nDatabase URL: {DATABASE_URL}")
    
    # Extract database file path from URL
    if "sqlite:///" in DATABASE_URL:
        db_path = DATABASE_URL.replace("sqlite:///", "")
        # Handle relative paths
        if db_path.startswith("./"):
            db_path = backend_dir / db_path[2:]
        else:
            db_path = Path(db_path)
        
        print(f"Database file: {db_path}")
        
        # Check if database already exists
        if db_path.exists():
            print(f"\n⚠️  Database file already exists: {db_path}")
            response = input("Do you want to continue? This will NOT delete existing data. (y/N): ")
            if response.lower() != 'y':
                print("Database initialization cancelled.")
                return
        else:
            print(f"\n✓ Database file does not exist. Creating new database...")
    
    try:
        # Create database and tables
        create_db_and_tables()
        print("\n✓ Database initialized successfully!")
        print("\nNext steps:")
        print("1. Start the backend server: uvicorn app.main:app --reload")
        print("2. (Optional) Load sample data: python3 sample_data.py")
        print("3. Access the API documentation: http://localhost:8000/docs")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Error initializing database: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
