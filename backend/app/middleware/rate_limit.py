"""
Rate Limiting Middleware

Production-ready rate limiting with:
- Per-user limits (based on JWT authentication)
- IP-based limits for unauthenticated requests  
- Sliding window algorithm
- Multiple tiers (global, per-endpoint)
"""

import time
from collections import defaultdict, deque
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Sliding window rate limiter.
    
    Features:
    - Per-user tracking
    - Clean up old entries automatically
    - Configurable limits per endpoint
    """
    
    def __init__(self):
        # Store: {identifier: deque of timestamps}
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.last_cleanup = time.time()
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (user ID, IP, etc.)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds
        
        # Get request history for this identifier
        history = self.requests[identifier]
        
        # Remove old requests outside the window
        while history and history[0] < cutoff:
            history.popleft()
        
        # Check if under limit
        if len(history) < max_requests:
            history.append(now)
            return True, None
        else:
            # Calculate when the oldest request will expire
            oldest = history[0]
            retry_after = int(oldest + window_seconds - now) + 1
            return False, retry_after
    
    def cleanup(self):
        """Remove expired entries to prevent memory leak."""
        now = time.time()
        
        # Only cleanup every 5 minutes
        if now - self.last_cleanup < 300:
            return
        
        self.last_cleanup = now
        
        # Remove identifiers with no recent requests (older than 1 hour)
        to_remove = []
        cutoff = now - 3600
        
        for identifier, history in self.requests.items():
            while history and history[0] < cutoff:
                history.popleft()
            
            if not history:
                to_remove.append(identifier)
        
        for identifier in to_remove:
            del self.requests[identifier]
        
        if to_remove:
            logger.info(f"Rate limiter cleanup: removed {len(to_remove)} expired entries")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API rate limiting.
    
    Rate limits by endpoint type:
    - Scan endpoints: 10 requests per hour per user
    - Upload endpoints: 5 uploads per hour per user
    - General API: 100 requests per minute per user
    - Unauthenticated: 20 requests per minute per IP
    """
    
    # Rate limit configurations
    LIMITS = {
        "scan": (10, 3600),      # 10 requests per hour
        "upload": (5, 3600),      # 5 uploads per hour
        "general": (100, 60),     # 100 requests per minute
        "unauth": (20, 60),       # 20 requests per minute (unauthenticated)
    }
    
    def __init__(self, app):
        super().__init__(app)
        self.limiter = RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)
        
        # Get identifier (user ID or IP)
        identifier = await self._get_identifier(request)
        
        # Determine rate limit tier
        limit_type = self._get_limit_type(request.url.path)
        max_requests, window_seconds = self.LIMITS[limit_type]
        
        # Check rate limit
        is_allowed, retry_after = self.limiter.is_allowed(
            identifier,
            max_requests,
            window_seconds
        )
        
        if not is_allowed:
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    "retry_after": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )
        
        # Periodic cleanup
        self.limiter.cleanup()
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        requests_used = len(self.limiter.requests.get(identifier, []))
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, max_requests - requests_used))
        
        return response
    
    async def _get_identifier(self, request: Request) -> str:
        """
        Get unique identifier for rate limiting.
        
        Priority:
        1. Authenticated user ID (from JWT)
        2. IP address
        
        Returns:
            Unique identifier string
        """
        # Try to extract user from JWT token (if authenticated)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # Import here to avoid circular imports
                from app.core.jwt import decode_access_token
                token = auth_header.replace("Bearer ", "")
                payload = decode_access_token(token)
                if payload and "user_id" in payload:
                    return f"user:{payload['user_id']}"
            except Exception:
                pass  # Invalid token, fall back to IP
        
        # Fall back to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _get_limit_type(self, path: str) -> str:
        """
        Determine rate limit tier based on endpoint path.
        
        Args:
            path: Request URL path
            
        Returns:
            Limit type key
        """
        # Scan endpoints (trigger background jobs)
        if "/repo/github" in path or "/repo/zip" in path:
            return "upload" if "/zip" in path else "scan"
        
        # Authenticated endpoints
        if path.startswith("/api/"):
            return "general"
        
        # Unauthenticated
        return "unauth"


from fastapi.responses import JSONResponse
