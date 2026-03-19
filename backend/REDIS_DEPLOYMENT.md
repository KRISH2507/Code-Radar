# 🚀 Redis Cloud Deployment Guide

## ✅ Implementation Complete!

Your backend is now fully configured for **local Redis** and **Redis Cloud** with zero code changes needed when switching environments.

## 📋 What Was Implemented

### 1. **Environment-Driven Configuration** ([app/core/config.py](app/core/config.py))
   - ✅ All settings load from `.env` file automatically
   - ✅ Validates `REDIS_URL` is present on startup
   - ✅ Validates Redis URL format (local or cloud)
   - ✅ Clear error messages if configuration is missing

### 2. **Celery Configuration** ([app/core/celery_app.py](app/core/celery_app.py))
   - ✅ Reads `REDIS_URL` from centralized config
   - ✅ No hardcoded localhost anywhere
   - ✅ Redis Cloud connection retry settings
   - ✅ JSON serialization for cross-platform compatibility

### 3. **Environment File** ([.env](.env))
   - ✅ `REDIS_URL=redis://localhost:6379/0` (local development)
   - ✅ Comments showing Redis Cloud format
   - ✅ Ready to switch by changing one line

### 4. **Docker Setup** ([docker-compose.yml](docker-compose.yml))
   - ✅ Local Redis on port 6379
   - ✅ PostgreSQL database
   - ✅ Ready for local development

---

## 🏃 Quick Start (Local Development)

### Step 1: Start Redis with Docker
```bash
cd E:\Code-Radar\backend
docker-compose up -d redis
```

### Step 2: Verify Redis is running
```bash
docker ps
# Should show: coderadar-redis running on port 6379
```

### Step 3: Test configuration
```bash
e:/Code-Radar/backend/venv/Scripts/python.exe test_redis_config.py
```

### Step 4: Start FastAPI server
```bash
# Using venv
e:/Code-Radar/backend/venv/Scripts/python.exe -m uvicorn app.main:app --reload

# OR if venv is activated
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Start Celery worker (new terminal)
```bash
# Navigate to backend folder
cd E:\Code-Radar\backend

# Start Celery worker (Windows)
e:/Code-Radar/backend/venv/Scripts/celery.exe -A app.core.celery_app worker --pool=solo --loglevel=info
```

### Step 6: Test endpoints
```bash
# Health check (includes Redis status)
curl http://localhost:8000/health

# API status
curl http://localhost:8000/api/status

# API docs
# Open: http://localhost:8000/docs
```

---

## ☁️ Deploy to Redis Cloud (Production)

### Step 1: Create Redis Cloud Account
1. Go to [redis.com/try-free](https://redis.com/try-free/)
2. Sign up for free tier (30MB, perfect for testing)
3. Create a new database

### Step 2: Get Redis Cloud Credentials
After creating your database, you'll get:
- **Host**: `redis-12345.c1.cloud.redislabs.com`
- **Port**: `16379` (or similar)
- **Password**: `dYourPassword123`

### Step 3: Update `.env` file
**Only change this ONE line:**

```bash
# Change from:
REDIS_URL=redis://localhost:6379/0

# To:
REDIS_URL=redis://:dYourPassword123@redis-12345.c1.cloud.redislabs.com:16379/0

# For TLS (recommended for production):
REDIS_URL=rediss://:dYourPassword123@redis-12345.c1.cloud.redislabs.com:16379/0
```

**Note:** Don't forget the `:` before the password!

### Step 4: Test configuration
```bash
e:/Code-Radar/backend/venv/Scripts/python.exe test_redis_config.py
```

Output should show:
```
✅ Test 3: Redis URL format validation
   Format: Valid ✓
   Mode: Redis Cloud (Production)
```

### Step 5: Restart services
```bash
# Stop FastAPI and Celery (Ctrl+C)
# Restart them with the same commands as before
```

### Step 6: Verify connection
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "redis": "connected",
  "redis_url_configured": true
}
```

---

## 🔧 Troubleshooting

### ❌ "Missing required environment variable: REDIS_URL"

**Solution:** Ensure `.env` file exists with `REDIS_URL` set:
```bash
REDIS_URL=redis://localhost:6379/0
```

### ❌ "Invalid REDIS_URL format"

**Solution:** Check your URL follows the correct format:
- Local: `redis://localhost:6379/0`
- Cloud: `redis://:PASSWORD@HOST:PORT/0`
- Cloud TLS: `rediss://:PASSWORD@HOST:PORT/0`

### ❌ Celery can't connect to Redis

**Local Redis:**
```bash
# Check if Redis is running
docker ps | grep redis

# Or test connection
docker exec coderadar-redis redis-cli ping
# Should return: PONG
```

**Redis Cloud:**
```bash
# Test connection with redis-cli
redis-cli -h redis-12345.c1.cloud.redislabs.com -p 16379 -a YOUR_PASSWORD ping
# Should return: PONG
```

### ❌ Health check shows Redis error

**Check:**
1. Is Celery worker running? (It must be started separately)
2. Is Redis accessible from your machine?
3. Is the password correct in Redis Cloud URL?

---

## 📊 Architecture Overview

```
┌─────────────┐         ┌──────────────┐
│   FastAPI   │────────▶│    Redis     │ ◀─── Broker & Result Backend
│   Server    │         │ (Local/Cloud)│
└─────────────┘         └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │    Celery    │
                        │    Worker    │
                        └──────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │   Database   │
                        └──────────────┘
```

**Flow:**
1. FastAPI receives HTTP request
2. Queues background task to Redis
3. Celery worker picks up task from Redis
4. Worker processes repository scan
5. Results stored in PostgreSQL
6. Task status stored in Redis

---

## 🎯 Key Features

✅ **Environment-driven**: All config from `.env`  
✅ **No hardcoded values**: No localhost in code  
✅ **Startup validation**: Fails fast with clear errors  
✅ **Cloud-ready**: Works with Redis Cloud authentication  
✅ **TLS support**: Use `rediss://` for secure connections  
✅ **Zero code changes**: Switch environments by changing `.env` only  
✅ **Docker support**: Local Redis via docker-compose  
✅ **Production-safe**: Connection retries, proper serialization  

---

## 📝 Files Changed

| File | Purpose | Changes |
|------|---------|---------|
| `app/core/config.py` | Configuration management | Created - loads and validates all env vars |
| `app/core/celery_app.py` | Celery setup | Updated - uses centralized config |
| `app/main.py` | FastAPI app | Updated - imports config, enhanced health check |
| `.env` | Environment variables | Updated - added Redis Cloud format examples |
| `test_redis_config.py` | Testing | Created - validates configuration |
| `README.md` | Documentation | Created - complete setup guide |

---

## 🚀 Deployment Checklist

### Local Development
- [x] Redis running in Docker
- [x] `.env` has `REDIS_URL=redis://localhost:6379/0`
- [x] FastAPI server running
- [x] Celery worker running
- [x] Health check passes

### Production (Redis Cloud)
- [ ] Redis Cloud database created
- [ ] `.env` updated with Redis Cloud URL
- [ ] TLS enabled (use `rediss://`)
- [ ] Connection tested
- [ ] Services restarted
- [ ] Health check passes

---

## 💡 Next Steps

1. **Today**: Run locally with Docker Redis
2. **Tomorrow**: Switch to Redis Cloud by updating `.env`
3. **Deploy**: Use Redis Cloud URL in production environment

**No code changes needed at any point!** ✨

---

## 📚 Additional Resources

- [Redis Cloud Free Tier](https://redis.com/try-free/)
- [Celery Documentation](https://docs.celeryq.dev/)
- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)

---

## ✅ Success Criteria

Your implementation is working correctly if:

1. ✅ `test_redis_config.py` runs without errors
2. ✅ FastAPI starts without configuration errors
3. ✅ Celery worker connects to Redis
4. ✅ `/health` endpoint returns `"redis": "connected"`
5. ✅ You can switch to Redis Cloud by only changing `.env`

**All tests passed!** 🎉
