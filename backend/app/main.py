from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import os
import traceback

app = FastAPI(
    title="Code Radar API",
    description="API for code analysis and repository scanning",
    version="1.0.0"
)

# ============================================================================
# FILE UPLOAD SIZE MIDDLEWARE
# ============================================================================
class FileSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce file upload size limits.
    
    Prevents memory exhaustion from large uploads by checking
    Content-Length header before reading the body.
    """
    
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB in bytes
    
    async def dispatch(self, request: Request, call_next):
        # Check if this is a file upload endpoint
        if request.url.path.startswith("/api/repo/zip"):
            content_length = request.headers.get("content-length")
            
            if content_length:
                try:
                    content_length_int = int(content_length)
                    if content_length_int > self.MAX_UPLOAD_SIZE:
                        return JSONResponse(
                            status_code=413,
                            content={
                                "detail": f"File size ({content_length_int / (1024*1024):.1f}MB) exceeds maximum allowed size (100MB)"
                            }
                        )
                except ValueError:
                    pass  # Invalid Content-Length, let the endpoint handle it
        
        response = await call_next(request)
        return response

# Add file size middleware
app.add_middleware(FileSizeLimitMiddleware)

# ============================================================================
# RATE LIMITING MIDDLEWARE
# ============================================================================
try:
    from app.middleware.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    print("[OK] Rate limiting enabled")
except ImportError as e:
    print(f"[WARN] Rate limiting disabled: {e}")

# ============================================================================
# PRODUCTION-READY CORS CONFIGURATION
# ============================================================================
# This configuration allows:
# ✅ Cross-origin requests from Next.js frontend
# ✅ Credentials (cookies, Authorization headers)
# ✅ All HTTP methods needed for REST API
# ✅ All headers needed for authentication
# ✅ Preflight request caching (improves performance)
# ============================================================================

# Define allowed origins
ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Next.js dev server (primary)
    "http://127.0.0.1:3000",      # Alternative localhost
    "http://localhost:3001",      # Alternative port
    "http://127.0.0.1:3001",      # Alternative port + host
]

# Add production frontend URL from environment variable
if production_origin := os.getenv("FRONTEND_URL"):
    ALLOWED_ORIGINS.append(production_origin)
    if production_origin.startswith("https://"):
        # Also add www variant if production
        www_origin = production_origin.replace("https://", "https://www.")
        ALLOWED_ORIGINS.append(www_origin)

# Apply CORS middleware
# CRITICAL: This MUST be added BEFORE any routes
app.add_middleware(
    CORSMiddleware,
    # Origins that can access this API
    allow_origins=ALLOWED_ORIGINS,
    
    # MUST be True for authentication (cookies, JWT in Authorization header)
    # NEVER use allow_origins=["*"] with allow_credentials=True
    allow_credentials=True,
    
    # All HTTP methods - required for REST API and preflight requests
    # OPTIONS is critical for preflight requests
    allow_methods=[
        "GET",      # Read operations
        "POST",     # Create operations (signup, login, etc.)
        "PUT",      # Full update operations
        "PATCH",    # Partial update operations
        "DELETE",   # Delete operations
        "OPTIONS",  # Preflight requests (CRITICAL - don't remove!)
        "HEAD",     # Header-only requests
    ],
    
    # Headers the browser can send in requests
    # These are checked during preflight (OPTIONS) requests
    allow_headers=[
        "Content-Type",           # JSON, form data, etc.
        "Authorization",          # Bearer tokens (CRITICAL for JWT)
        "Accept",                 # Response format preferences
        "Accept-Language",        # Internationalization
        "Origin",                 # Request origin
        "User-Agent",             # Client information
        "Referer",                # Referring page
        "X-Requested-With",       # AJAX requests identifier
        "X-CSRF-Token",           # CSRF protection
        "Cache-Control",          # Caching preferences
        "DNT",                    # Do Not Track
        "Connection",             # Connection management
        "Pragma",                 # HTTP/1.0 caching
        "Access-Control-Allow-Origin",  # CORS headers
    ],
    
    # Headers the browser can read from responses
    # Without this, JavaScript cannot access these headers
    expose_headers=[
        "Content-Length",         # Response size
        "Content-Type",           # Response format
        "X-Total-Count",          # Pagination (total items)
        "X-Page-Count",           # Pagination (total pages)
        "Authorization",          # Token refresh
    ],
    
    # Cache preflight requests for 1 hour (3600 seconds)
    # Reduces OPTIONS requests, improves performance
    # Browser won't send OPTIONS for same request within this time
    max_age=3600,
)


# Global exception handler — prevents unhandled errors from crashing the API
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler with CORS headers.
    Ensures even error responses include proper CORS headers.
    """
    # Print the FULL traceback so we can see the real cause
    print(f"[ERROR] Unhandled exception on {request.method} {request.url}")
    print(f"[ERROR] Exception type: {type(exc).__name__}")
    print(f"[ERROR] Exception message: {exc}")
    traceback.print_exc()

    # Re-raise HTTPExceptions with their proper status code
    if isinstance(exc, HTTPException):
        origin = request.headers.get("origin", "")
        response = JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    # Get origin for CORS
    origin = request.headers.get("origin", "")

    # Create error response
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

    # Add CORS headers to error response
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"

    return response


@app.get("/")
async def root():
    return {
        "message": "Welcome to Code Radar API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/status")
async def api_status():
    return {
        "api": "operational",
        "database": "connected",
        "services": "ready"
    }

@app.get("/api/cors-test")
async def cors_test(request: Request):
    """Test endpoint to verify CORS is working correctly"""
    return {
        "message": "CORS is working!",
        "origin": request.headers.get("origin"),
        "method": request.method,
        "cors_enabled": True,
        "allowed_origins": ALLOWED_ORIGINS,
        "credentials_allowed": True,
    }

# Import all models so SQLAlchemy resolves relationships BEFORE routers
# This ensures models are registered before routers try to use them
from app.models import User, OTP, Repository, Scan, Payment  # noqa: E402

# Import and register routers
try:
    from app.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
    print("[OK] Auth router loaded")
except Exception as e:
    print(f"[FAIL] Failed to load auth router: {e}")

try:
    from app.api.repo import router as repo_router
    app.include_router(repo_router, prefix="/api/repo", tags=["Repository"])
    print("[OK] Repo router loaded")
except Exception as e:
    print(f"[FAIL] Failed to load repo router: {e}")

try:
    from app.api.analysis import router as analysis_router
    app.include_router(analysis_router, prefix="/api/analysis", tags=["Analysis"])
    print("[OK] Analysis router loaded")
except Exception as e:
    print(f"[FAIL] Failed to load analysis router: {e}")

try:
    from app.api.dashboard import router as dashboard_router
    app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
    print("[OK] Dashboard router loaded")
except Exception as e:
    print(f"[FAIL] Failed to load dashboard router: {e}")

try:
    from app.api.payments import router as payments_router
    app.include_router(payments_router, prefix="/api/payments", tags=["Payments"])
    print("[OK] Payments router loaded")
except Exception as e:
    print(f"[FAIL] Failed to load payments router: {e}")

try:
    from app.api.admin import router as admin_router
    app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
    print("[OK] Admin router loaded")
except Exception as e:
    print(f"[FAIL] Failed to load admin router: {e}")


@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    
    This runs once when the FastAPI application starts.
    Perfect place for:
    - Database initialization
    - Cache warming
    - External service connections
    - Configuration validation
    """
    print("=" * 70)
    print("Code Radar API - Starting Up")
    print("=" * 70)
    
    # ========================================================================
    # DATABASE INITIALIZATION
    # ========================================================================
    # Create all tables if they don't exist
    # This is safe to run on every startup (idempotent)
    try:
        from app.core.database import create_tables
        create_tables()
    except Exception as e:
        print(f"[WARN] Database initialization failed: {e}")
        print("   Tables may need to be created manually.")
    
    # ========================================================================
    # DISPLAY CONFIGURATION
    # ========================================================================
    print("=" * 70)
    print("Configuration:")
    print(f"   Total Routes: {len(app.routes)}")
    print(f"   API Version: 1.0.0")
    print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print()
    print("CORS Configuration:")
    print(f"   Credentials Enabled: Yes")
    print(f"   Allowed Origins:")
    for origin in ALLOWED_ORIGINS:
        print(f"      [OK] {origin}")
    print()
    print("Key API Endpoints:")
    print("   Health:      GET  http://localhost:8000/health")
    print("   API Docs:    GET  http://localhost:8000/docs")
    print("   CORS Test:   GET  http://localhost:8000/api/cors-test")
    print("   Signup:      POST http://localhost:8000/api/auth/signup")
    print("   Login:       POST http://localhost:8000/api/auth/login")
    print("   Google Auth: POST http://localhost:8000/api/auth/google")
    print("=" * 70)
    print("[OK] Application startup complete!")
    print("=" * 70)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
