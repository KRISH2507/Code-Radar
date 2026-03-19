# ✅ Database Table Auto-Creation Fix

## Problem
After dropping the `users` table manually, the backend failed with:
```
psycopg2.errors.UndefinedTable: relation 'users' does not exist
```

The root cause: **SQLAlchemy models were imported but `Base.metadata.create_all()` was never called**, so tables were never created.

---

## Solution Implemented

### 1. Enhanced `database.py` with Table Management Functions

**File:** `backend/app/core/database.py`

Added three new functions:

```python
def create_tables():
    """Create all database tables."""
    # Import all models to register them with Base.metadata
    from app.models import ALL_MODELS
    
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

def drop_tables():
    """Drop all database tables. WARNING: This deletes all data!"""
    print("⚠️  Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ All tables dropped.")

def reset_database():
    """Drop and recreate all tables. WARNING: This deletes all data!"""
    drop_tables()
    create_tables()
```

### 2. Updated `models/__init__.py` with Comprehensive Registry

**File:** `backend/app/models/__init__.py`

Added `ALL_MODELS` list for easy iteration:

```python
from app.models.user import User
from app.models.otp import OTP
from app.models.repository import Repository
from app.models.scan import Scan

try:
    from app.models.file_metrics import FileMetrics
    ALL_MODELS = [User, OTP, Repository, Scan, FileMetrics]
except ImportError:
    ALL_MODELS = [User, OTP, Repository, Scan]

__all__ = ["User", "OTP", "Repository", "Scan", "FileMetrics", "ALL_MODELS"]
```

### 3. Modified `main.py` Startup Event

**File:** `backend/app/main.py`

Added automatic table creation on application startup:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("=" * 80)
    logger.info("🚀 Starting Code Radar Backend")
    logger.info("=" * 80)
    
    # Create database tables if they don't exist
    logger.info("📊 Initializing database...")
    from app.core.database import create_tables
    create_tables()
    
    # ... rest of startup code
```

### 4. Updated `init_db.py` Script

**File:** `backend/init_db.py`

Now uses the new functions and provides better user experience:

```python
python init_db.py           # Create tables
python init_db.py --create  # Create tables (explicit)
python init_db.py --drop    # Drop all tables (requires confirmation)
python init_db.py --reset   # Drop and recreate (requires confirmation)
```

---

## Verification

### ✅ Table Creation Test
```bash
cd backend
python test_user_creation.py
```

**Result:**
```
✅ Users table exists! Found 0 existing users.
✅ User created successfully!
✅ SUCCESS: Users table is working correctly!
```

### ✅ Database Tables Created
```
📋 Database Tables:
  ✓ otps
  ✓ repositories
  ✓ scans
  ✓ users

Total: 4 tables
```

### ✅ Backend Health Check
```bash
curl http://localhost:8000/health
```

**Result:**
```json
{"status":"healthy"}
```

---

## How It Works

### Why SQLAlchemy Needs Explicit create_all()

SQLAlchemy's `Base.metadata` only knows about models that:
1. **Inherit from `Base`** (declarative base)
2. **Have been imported** before `create_all()` is called

Simply importing models in `main.py` doesn't create tables. You must explicitly call:
```python
Base.metadata.create_all(bind=engine)
```

### Idempotent Design

The `create_all()` function is **idempotent** - it only creates tables that don't exist:
- ✅ Safe to run on every startup
- ✅ Won't duplicate existing tables
- ✅ Won't overwrite data in existing tables

### Import Order Matters

**Before (Broken):**
```python
# main.py
from app.models import User, OTP, Repository, Scan  # Models imported
# No create_all() called → Tables never created!
```

**After (Fixed):**
```python
# main.py
@app.on_event("startup")
async def startup_event():
    from app.core.database import create_tables
    create_tables()  # ✅ Tables created on startup
```

---

## Usage

### Automatic (Recommended)
Just start the backend:
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tables are created automatically in the startup event!

### Manual (Alternative)
Run the initialization script:
```bash
cd backend
python init_db.py
```

### Reset Database
If you need to recreate all tables:
```bash
cd backend
python init_db.py --reset
```

---

## Files Modified

| File | Changes | Purpose |
|------|---------|---------|
| `app/core/database.py` | Added `create_tables()`, `drop_tables()`, `reset_database()` | Table management utilities |
| `app/models/__init__.py` | Added `ALL_MODELS` registry | Centralized model imports |
| `app/main.py` | Added `create_tables()` call in startup event | Automatic table creation |
| `init_db.py` | Complete rewrite using new functions | Improved CLI tool |

---

## Testing

### Test User Creation
```bash
cd backend
python test_user_creation.py
```

### Test Signup Endpoint
```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123456", "name": "Test User"}'
```

### Check Tables
```bash
cd backend
python -c "from app.core.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

---

## Key Takeaways

1. **SQLAlchemy doesn't auto-create tables** - You must call `Base.metadata.create_all()`
2. **Models must be imported** - SQLAlchemy only creates tables for imported models
3. **Startup event is perfect** - Tables are created automatically when backend starts
4. **Idempotent design** - Safe to run `create_all()` multiple times
5. **Centralized imports** - `models/__init__.py` ensures all models are loaded

---

## Status: ✅ COMPLETE

- ✅ Tables auto-create on backend startup
- ✅ Manual initialization script available
- ✅ Tested and verified working
- ✅ Cannot drop tables without confirmation
- ✅ Reset functionality for development

**No more "relation does not exist" errors!** 🎉
