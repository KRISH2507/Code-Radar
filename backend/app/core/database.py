from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================
# This module provides:
# 1. Base - declarative base for all models
# 2. engine - database connection engine
# 3. SessionLocal - session factory
# 4. get_db() - dependency injection for FastAPI routes
# ============================================================================

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/coderadar"
)

# ============================================================================
# CREATE ENGINE
# ============================================================================
# Configure connection pool and behavior
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # Verify connections before using
    pool_size=10,            # Number of connections to maintain
    max_overflow=20,         # Additional connections when pool is full
    echo=False,              # Set to True for SQL query logging (debug)
    # For PostgreSQL with SSL (Neon, etc.):
    connect_args={
        "sslmode": "require" if "neon.tech" in DATABASE_URL or "sslmode=require" in DATABASE_URL else "prefer"
    } if "postgresql" in DATABASE_URL else {}
)

# ============================================================================
# CREATE SESSION FACTORY
# ============================================================================
# Sessions are created from this factory
SessionLocal = sessionmaker(
    autocommit=False,        # Manual commits for transaction control
    autoflush=False,         # Manual flushes for better control
    bind=engine             # Bind to our engine
)

# ============================================================================
# DECLARATIVE BASE
# ============================================================================
# ALL models must inherit from this Base
# This is how SQLAlchemy tracks which classes are database models
Base = declarative_base()


# ============================================================================
# DEPENDENCY INJECTION FOR FASTAPI
# ============================================================================
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides a database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Usage in FastAPI routes:
        @router.get("/items")
        def read_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
            
    Note: Session is automatically closed after request completes
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# TABLE CREATION FUNCTION
# ============================================================================
def create_tables():
    """
    Create all tables defined in models.
    
    This function:
    1. Imports all models (registers them with Base.metadata)
    2. Creates all tables that don't exist
    3. Does NOT drop existing tables
    4. Is idempotent (safe to run multiple times)
    
    Usage:
        from app.core.database import create_tables
        create_tables()
    """
    # Import all models to register them with Base.metadata
    # This MUST happen before create_all()
    from app.models import (
        User, 
        OTP, 
        Repository, 
        Scan,
    )
    
    # Import file_metrics model if it exists
    try:
        from app.models.file_metrics import FileMetrics
    except ImportError:
        pass  # Optional model
    
    # Create all tables
    print("[DB] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("[DB] Database tables created successfully!")


def drop_tables():
    """
    Drop all tables. USE WITH CAUTION!
    
    This will delete all data in the database.
    Only use in development or with explicit confirmation.
    """
    print("[WARN] WARNING: Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("[DB] All tables dropped!")


def reset_database():
    """
    Drop all tables and recreate them.
    USE WITH EXTREME CAUTION - ALL DATA WILL BE LOST!
    
    Only use in development.
    """
    print("[DB] Resetting database (DROP + CREATE)...")
    drop_tables()
    create_tables()
    print("[DB] Database reset complete!")
