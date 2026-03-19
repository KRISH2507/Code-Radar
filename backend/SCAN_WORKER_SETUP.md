# 🚀 Redis + Celery Scan Worker - Complete Setup Guide

## ✅ Implementation Summary

Your FastAPI backend now has a fully functional Redis + Celery background scan worker that:

1. **Asynchronously processes GitHub repositories** - No blocking API requests
2. **Updates scan status** - pending → processing → completed/failed  
3. **Computes metrics** - File count, line count
4. **Works with local Redis** - For development
5. **Ready for Redis Cloud** - For production (just change REDIS_URL)

---

## 📁 Files Created/Modified

### Core Implementation
- ✅ **[app/workers/scan_worker.py](app/workers/scan_worker.py)** - Celery task for scanning repositories
- ✅ **[app/models/repository.py](app/models/repository.py)** - Added: `completed_at`, `file_count`, `line_count`
- ✅ **[app/api/repo.py](app/api/repo.py)** - Triggers `scan_repository.delay()` after creating repo
- ✅ **[app/core/celery_app.py](app/core/celery_app.py)** - Celery configuration (already done)
- ✅ **[app/core/config.py](app/core/config.py)** - Environment-driven config (already done)
- ✅ **[app/main.py](app/main.py)** - Removed test code

### Support Files
- ✅ **[init_db.py](init_db.py)** - Initialize database schema
- ✅ **[migrate_repository_metrics.py](migrate_repository_metrics.py)** - Add scan metrics columns
- ✅ **[test_scan_worker.py](test_scan_worker.py)** - Comprehensive test suite
- ✅ **[test_redis_config.py](test_redis_config.py)** - Configuration testing

---

## 🛠️ Setup Instructions

### Prerequisites
```powershell
# 1. Make sure you're in the backend directory
cd E:\Code-Radar\backend

# 2. Activate virtual environment (if not already activated)
.\venv\Scripts\activate

# 3. Install dependencies (already done via your previous commands)
pip install celery redis python-dotenv
```

### Step 1: Start Docker Desktop
```powershell
# Start Docker Desktop application first
# Then verify it's running:
docker --version
```

### Step 2: Start Redis
```powershell
# Start Redis container
docker-compose up -d redis

# Verify Redis is running
docker ps
# Should show: coderadar-redis running on port 6379

# Test Redis connection
docker exec coderadar-redis redis-cli ping
# Should return: PONG
```

### Step 3: Initialize Database
```powershell
# Create all tables
e:/Code-Radar/backend/venv/Scripts/python.exe init_db.py

# Expected output:
# ✅ Database tables created successfully!
```

### Step 4: Run Tests
```powershell
# Test configuration
e:/Code-Radar/backend/venv/Scripts/python.exe test_redis_config.py

# Test scan worker (requires Redis running)
e:/Code-Radar/backend/venv/Scripts/python.exe test_scan_worker.py

# Expected: All 5 tests should pass
```

### Step 5: Start FastAPI Server
```powershell
# Terminal 1: Start FastAPI
e:/Code-Radar/backend/venv/Scripts/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Start Celery Worker
```powershell
# Terminal 2: Start Celery worker (Windows requires --pool=solo)
cd E:\Code-Radar\backend
e:/Code-Radar/backend/venv/Scripts/celery.exe -A app.core.celery_app worker --pool=solo --loglevel=info

# Expected output:
# [tasks]
#   . scan_repository
# [2026-02-08 15:30:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
# [2026-02-08 15:30:00,000: INFO/MainProcess] celery@hostname ready.
```

### Step 7: Test the API
```powershell
# Terminal 3: Test health endpoint
curl http://localhost:8000/health

# Expected:
# {"status":"healthy","redis":"connected","redis_url_configured":true}

# View API docs
# Open: http://localhost:8000/docs
```

---

## 🧪 Test the Scan Worker

### Test 1: Submit a GitHub Repository

```powershell
# You'll need a JWT token first. Use the API docs or:
# 1. Sign up: POST /auth/signup
# 2. Login: POST /auth/login  
# 3. Copy the access_token

# Submit a small test repository
curl -X POST http://localhost:8000/repo/github \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d "{\"repo_url\": \"https://github.com/octocat/Hello-World\"}"

# Expected response:
# {
#   "id": 1,
#   "name": "Hello-World",
#   "status": "pending",
#   "source_type": "github",
#   ...
# }
```

### Test 2: Watch the Worker Process It

In the Celery worker terminal, you should see:

```
[2026-02-08 15:30:01,000: INFO/MainProcess] Task scan_repository[abc-123] received
Starting scan for repository: Hello-World (ID: 1)
Created temporary directory: C:\Users\...\coderadar_xyz
Cloning GitHub repository: https://github.com/octocat/Hello-World
Repository cloned successfully
Counting files and lines...
Scan complete: 3 files, 150 lines
Repository Hello-World scan completed successfully
[2026-02-08 15:30:15,000: INFO/MainProcess] Task scan_repository[abc-123] succeeded
```

### Test 3: Check Status Updates

```powershell
# Get repository details (replace {id} with actual ID)
curl http://localhost:8000/repo/{id} \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Status progression:
# 1. "pending" - Just created
# 2. "processing" - Worker is scanning
# 3. "completed" - Done! (with file_count and line_count)
# 4. "failed" - If something went wrong
```

---

## 🔧 How It Works

### Request Flow

```
1. User submits GitHub URL
   ↓
2. API validates URL and creates Repository record (status: pending)
   ↓
3. API triggers: scan_repository.delay(repository_id)
   ↓
4. API returns immediately with repository details
   ↓
5. Celery worker picks up task from Redis queue
   ↓
6. Worker updates status to "processing"
   ↓
7. Worker clones repo (shallow, depth=1)
   ↓
8. Worker counts files and lines (ignores .git, node_modules)
   ↓
9. Worker updates: status="completed", file_count, line_count, completed_at
   ↓
10. Worker cleans up temp files
```

### Database Schema

```sql
-- repositories table (updated)
CREATE TABLE repositories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'github' or 'zip'
    repo_url VARCHAR(512),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,  -- NEW
    file_count INTEGER DEFAULT 0,           -- NEW
    line_count INTEGER DEFAULT 0            -- NEW
);
```

---

## 🚀 Production Deployment (Redis Cloud)

### Step 1: Create Redis Cloud Database

1. Go to [redis.com/try-free](https://redis.com/try-free/)
2. Create a free database (30MB)
3. Note your credentials:
   - Host: `redis-12345.c1.cloud.redislabs.com`
   - Port: `16379`
   - Password: `your_password`

### Step 2: Update Environment

```bash
# In .env file, change ONLY this line:
REDIS_URL=redis://:your_password@redis-12345.c1.cloud.redislabs.com:16379/0

# Or use TLS (recommended):
REDIS_URL=rediss://:your_password@redis-12345.c1.cloud.redislabs.com:16379/0
```

### Step 3: Deploy

```bash
# No code changes needed!
# Just restart your services with the new .env
```

---

## 📊 Monitoring & Debugging

### Check Worker Status
```powershell
# Is Celery running?
Get-Process | Where-Object {$_.ProcessName -like "*celery*"}

# Check Redis connection
docker exec coderadar-redis redis-cli ping
```

### View Queued Tasks
```python
# In Python shell
from app.core.celery_app import celery_app
inspect = celery_app.control.inspect()

# Active tasks
inspect.active()

# Scheduled tasks
inspect.scheduled()

# Registered tasks
inspect.registered()
```

### Common Issues

**Issue: Worker doesn't pick up tasks**
```powershell
# Check Redis is running
docker ps | findstr redis

# Check Celery worker is running
# Terminal should show: "celery@hostname ready."

# Restart worker if needed
# Ctrl+C, then restart: celery -A app.core.celery_app worker --pool=solo --loglevel=info
```

**Issue: Repository stays in "pending" status**
```powershell
# Check Celery worker terminal for errors
# Check Redis connection in worker logs
# Verify task was enqueued (check API terminal output)
```

**Issue: Scan fails**
```powershell
# Check Celery worker logs for error message
# Common causes:
# - Git not installed: choco install git
# - Repository is private (authentication needed)
# - Network issues
# - Timeout (large repositories)
```

---

## ✅ Success Criteria

Your implementation is working if:

1. ✅ FastAPI starts without errors
2. ✅ Celery worker starts and shows "celery@hostname ready"
3. ✅ `/health` returns `"redis": "connected"`
4. ✅ Submitting a GitHub repo returns `"status": "pending"`
5. ✅ Worker logs show "Starting scan for repository"
6. ✅ Repository status changes to "completed"
7. ✅ Repository has `file_count` and `line_count` populated

---

## 🎯 What You Can Do Now

### Local Development
- ✅ Submit GitHub repositories
- ✅ Scan processes asynchronously
- ✅ Get file and line counts
- ✅ No blocking API requests

### Production Ready
- ✅ Switch to Redis Cloud by changing `.env` only
- ✅ No code changes needed
- ✅ Same commands to start services
- ✅ Environment-driven configuration

---

## 📚 Next Steps

1. **Add more metrics**: Edit `scan_worker.py` to compute:
   - Language breakdown
   - Complexity scores
   - Dependency analysis

2. **Add progress tracking**: Update status with percentage complete

3. **Add retry logic**: Configure Celery task retries

4. **Add monitoring**: Integrate Flower for Celery monitoring

5. **Add notifications**: Send email/webhook when scan completes

---

## 🔗 Related Documentation

- [REDIS_DEPLOYMENT.md](REDIS_DEPLOYMENT.md) - Redis setup guide
- [LOCAL_VS_CLOUD.md](LOCAL_VS_CLOUD.md) - Environment comparison
- [README.md](README.md) - Full project documentation

---

**🎉 Your Redis + Celery scan worker is fully implemented and production-ready!**
