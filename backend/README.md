# Code Radar Backend

FastAPI + Celery backend for code analysis and repository scanning.

## Features

- **FastAPI** REST API for repository management and analysis
- **Celery** distributed task queue for background scanning
- **Redis** as message broker and result backend
- **PostgreSQL** database for persistent storage
- **JWT Authentication** with OTP support

## Environment Configuration

All configuration is environment-driven through `.env` file. **No hardcoded values in code.**

### Required Environment Variables

```bash
# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:port/database

# JWT Secret Key
JWT_SECRET=your-super-secret-key-here

# Redis Configuration (REQUIRED)
# Local Development:
REDIS_URL=redis://localhost:6379/0

# Redis Cloud (Production):
REDIS_URL=redis://:YOUR_PASSWORD@redis-xxxxx.c1.cloud.redislabs.com:16379/0

# With TLS (recommended for production):
REDIS_URL=rediss://:YOUR_PASSWORD@redis-xxxxx.c1.cloud.redislabs.com:16379/0

# Email Service (Optional)
EMAILJS_SERVICE_ID=your_service_id
EMAILJS_TEMPLATE_ID=your_template_id
EMAILJS_PUBLIC_KEY=your_public_key
EMAILJS_PRIVATE_KEY=your_private_key
```

## Redis Setup

### Local Development

1. **Install Redis:**
   ```bash
   # Windows (using Chocolatey)
   choco install redis-64
   
   # macOS
   brew install redis
   
   # Linux
   sudo apt-get install redis-server
   ```

2. **Start Redis:**
   ```bash
   redis-server
   ```

3. **Configure `.env`:**
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

### Redis Cloud (Production)

1. **Create a Redis Cloud account** at [redis.com](https://redis.com/try-free/)

2. **Create a new database:**
   - Choose your cloud provider (AWS/GCP/Azure)
   - Select a region close to your application
   - Note the password and endpoint provided

3. **Get your Redis URL:**
   - Format: `redis://:PASSWORD@HOST:PORT/0`
   - Example: `redis://:dYourPassword123@redis-12345.c1.cloud.redislabs.com:16379/0`
   - For TLS: Use `rediss://` instead of `redis://`

4. **Update `.env`:**
   ```bash
   REDIS_URL=redis://:YOUR_PASSWORD@YOUR_HOST:YOUR_PORT/0
   ```

   **That's it!** No code changes required. The backend will automatically connect to Redis Cloud.

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   - Copy `.env.example` to `.env` (if available)
   - Or create `.env` with required variables
   - **Ensure REDIS_URL is set** (local or cloud)

3. **Verify configuration:**
   ```bash
   python -c "from app.core.config import settings; print(f'Redis URL configured: {bool(settings.REDIS_URL)}')"
   ```

## Running the Application

### Start FastAPI Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Start Celery Worker

```bash
# Windows
celery -A app.core.celery_app worker --pool=solo --loglevel=info

# Linux/macOS
celery -A app.core.celery_app worker --loglevel=info
```

### Health Check

Visit `http://localhost:8000/health` to verify:
- API is running
- Redis is connected
- Configuration is valid

## Switching Environments

To switch from local Redis to Redis Cloud (or vice versa):

1. **Update only `.env`:**
   ```bash
   # Change this line:
   REDIS_URL=redis://:cloud_password@redis-12345.c1.cloud.redislabs.com:16379/0
   ```

2. **Restart services:**
   ```bash
   # Stop and restart FastAPI + Celery
   ```

3. **Verify connection:**
   ```bash
   curl http://localhost:8000/health
   ```

**No code changes needed!** The application reads `REDIS_URL` on startup.

## Architecture

- **FastAPI** handles HTTP requests and queues Celery tasks
- **Celery Workers** execute long-running repository scans
- **Redis** brokers messages between FastAPI and Celery
- **PostgreSQL** stores users, repositories, and scan results

## Troubleshooting

### "Missing required environment variable: REDIS_URL"

**Solution:** Add `REDIS_URL` to your `.env` file:
```bash
REDIS_URL=redis://localhost:6379/0
```

### "Invalid REDIS_URL format"

**Solution:** Ensure URL follows the pattern:
- Local: `redis://localhost:6379/0`
- Cloud: `redis://:PASSWORD@HOST:PORT/0`
- Cloud with TLS: `rediss://:PASSWORD@HOST:PORT/0`

### Celery can't connect to Redis

**Verify Redis is running:**
```bash
# Test local Redis
redis-cli ping
# Should return: PONG

# Test Redis Cloud
redis-cli -h YOUR_HOST -p YOUR_PORT -a YOUR_PASSWORD ping
```

### Health check shows Redis errors

**Check Celery worker is running:** The worker must be started separately from FastAPI.

## Development

- API documentation: `http://localhost:8000/docs`
- API status: `http://localhost:8000/api/status`
- Health check: `http://localhost:8000/health`

## Deployment

1. Set production `REDIS_URL` in environment
2. Use `rediss://` (TLS) for Redis Cloud in production
3. Ensure `DATABASE_URL` points to production PostgreSQL
4. Use strong `JWT_SECRET` (min 32 characters)
5. Deploy FastAPI and Celery worker separately

## License

MIT
