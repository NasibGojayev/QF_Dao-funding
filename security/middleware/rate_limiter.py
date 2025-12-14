"""
Rate Limiting Middleware for DonCoin DAO
Implements per-IP and per-endpoint rate limiting with monitoring hooks.
"""
from typing import Optional, Callable, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict
import time
import json
import asyncio
from functools import wraps
from pathlib import Path
import sys

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import RATE_LIMIT_CONFIG, LOGS_DIR


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter.
    For production, use Redis-backed implementation.
    """
    
    def __init__(self):
        # Structure: {key: [(timestamp, count), ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked_ips: Dict[str, datetime] = {}
        self.lock = asyncio.Lock()
    
    def _parse_limit(self, limit_str: str) -> tuple[int, int]:
        """Parse limit string like '100/minute' into (count, seconds)"""
        count, period = limit_str.split('/')
        count = int(count)
        
        period_map = {
            'second': 1,
            'minute': 60,
            'hour': 3600,
            'day': 86400,
        }
        
        seconds = period_map.get(period, 60)
        return count, seconds
    
    async def is_rate_limited(
        self,
        key: str,
        limit: str = "100/minute"
    ) -> tuple[bool, dict]:
        """
        Check if key is rate limited.
        
        Returns:
            tuple of (is_limited, info_dict)
        """
        async with self.lock:
            # Check if IP is blocked
            if key in self.blocked_ips:
                if datetime.now() < self.blocked_ips[key]:
                    remaining_seconds = (self.blocked_ips[key] - datetime.now()).seconds
                    return True, {
                        'blocked': True,
                        'retry_after': remaining_seconds,
                        'reason': 'IP blocked due to abuse'
                    }
                else:
                    del self.blocked_ips[key]
            
            max_requests, window_seconds = self._parse_limit(limit)
            now = time.time()
            window_start = now - window_seconds
            
            # Clean old entries
            self.requests[key] = [
                (ts, c) for ts, c in self.requests[key] 
                if ts > window_start
            ]
            
            # Count requests in window
            request_count = sum(c for _, c in self.requests[key])
            
            if request_count >= max_requests:
                return True, {
                    'blocked': False,
                    'limit': max_requests,
                    'window': window_seconds,
                    'current': request_count,
                    'retry_after': int(window_seconds - (now - self.requests[key][0][0])) if self.requests[key] else window_seconds
                }
            
            # Add request
            self.requests[key].append((now, 1))
            
            return False, {
                'limit': max_requests,
                'remaining': max_requests - request_count - 1,
                'reset': int(now + window_seconds),
            }
    
    async def block_ip(self, ip: str, duration_seconds: int):
        """Block an IP for a specified duration"""
        async with self.lock:
            self.blocked_ips[ip] = datetime.now() + timedelta(seconds=duration_seconds)


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


# =============================================================================
# RATE LIMIT EVENT LOGGING
# =============================================================================

def log_rate_limit_event(
    ip_address: str,
    endpoint: str,
    limit: str,
    exceeded: bool,
    request_count: int,
    details: Optional[dict] = None
):
    """Log rate limit events for monitoring"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": "rate_limit",
        "ip_address": ip_address,
        "endpoint": endpoint,
        "limit": limit,
        "exceeded": exceeded,
        "request_count": request_count,
        "details": details or {}
    }
    
    log_file = LOGS_DIR / "rate_limit_events.jsonl"
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')


# =============================================================================
# MIDDLEWARE
# =============================================================================

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    Applies different limits based on endpoint patterns.
    """
    
    ENDPOINT_LIMITS = {
        "/auth/login": RATE_LIMIT_CONFIG['auth_limit'],
        "/admin": RATE_LIMIT_CONFIG['admin_limit'],
        "/webhook": RATE_LIMIT_CONFIG['webhook_limit'],
        "/api": RATE_LIMIT_CONFIG['api_limit'],
    }
    
    def _get_limit_for_path(self, path: str) -> str:
        """Get rate limit for a specific path"""
        for pattern, limit in self.ENDPOINT_LIMITS.items():
            if path.startswith(pattern):
                return limit
        return RATE_LIMIT_CONFIG['default_limit']
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        if not RATE_LIMIT_CONFIG['enabled']:
            return await call_next(request)
        
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        ip = self._get_client_ip(request)
        limit = self._get_limit_for_path(request.url.path)
        key = f"{ip}:{request.url.path.split('/')[1]}"  # Group by IP and first path segment
        
        is_limited, info = await rate_limiter.is_rate_limited(key, limit)
        
        if is_limited:
            log_rate_limit_event(
                ip_address=ip,
                endpoint=request.url.path,
                limit=limit,
                exceeded=True,
                request_count=info.get('current', 0),
                details=info
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Too many requests",
                    "retry_after": info.get('retry_after', 60),
                    "message": "Rate limit exceeded. Please slow down."
                },
                headers={
                    "Retry-After": str(info.get('retry_after', 60)),
                    "X-RateLimit-Limit": str(info.get('limit', 0)),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info.get('limit', 100))
        response.headers["X-RateLimit-Remaining"] = str(info.get('remaining', 0))
        response.headers["X-RateLimit-Reset"] = str(info.get('reset', 0))
        
        return response


# =============================================================================
# DECORATOR FOR CUSTOM RATE LIMITS
# =============================================================================

def rate_limit(limit: str = "10/minute"):
    """
    Decorator for applying custom rate limits to specific endpoints.
    
    Usage:
        @app.get("/sensitive")
        @rate_limit("5/minute")
        async def sensitive_endpoint():
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            if not RATE_LIMIT_CONFIG['enabled']:
                return await func(request, *args, **kwargs)
            
            ip = request.client.host if request.client else "unknown"
            key = f"{ip}:{func.__name__}"
            
            is_limited, info = await rate_limiter.is_rate_limited(key, limit)
            
            if is_limited:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Too many requests",
                        "retry_after": info.get('retry_after', 60),
                    }
                )
            
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


# =============================================================================
# BRUTE FORCE DETECTION
# =============================================================================

class BruteForceDetector:
    """Detect and respond to brute force attacks"""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, block_seconds: int = 900):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.block_seconds = block_seconds
        self.attempts: Dict[str, list] = defaultdict(list)
    
    async def record_failure(self, ip: str, username: str) -> bool:
        """
        Record a failed login attempt.
        Returns True if IP should be blocked.
        """
        now = time.time()
        key = f"{ip}:{username}"
        
        # Clean old attempts
        self.attempts[key] = [t for t in self.attempts[key] if t > now - self.window_seconds]
        
        # Add this attempt
        self.attempts[key].append(now)
        
        # Check if should block
        if len(self.attempts[key]) >= self.max_attempts:
            # Block the IP
            await rate_limiter.block_ip(ip, self.block_seconds)
            
            log_rate_limit_event(
                ip_address=ip,
                endpoint="/auth/login",
                limit=f"{self.max_attempts}/{self.window_seconds}s",
                exceeded=True,
                request_count=len(self.attempts[key]),
                details={
                    "username": username,
                    "action": "blocked",
                    "block_duration": self.block_seconds
                }
            )
            
            return True
        
        return False
    
    def reset(self, ip: str, username: str):
        """Reset attempts after successful login"""
        key = f"{ip}:{username}"
        self.attempts.pop(key, None)


# Global brute force detector
brute_force_detector = BruteForceDetector()


# =============================================================================
# USAGE STATISTICS
# =============================================================================

class RateLimitStats:
    """Track rate limiting statistics for monitoring"""
    
    def __init__(self):
        self.total_requests = 0
        self.blocked_requests = 0
        self.blocked_by_endpoint: Dict[str, int] = defaultdict(int)
        self.blocked_by_ip: Dict[str, int] = defaultdict(int)
    
    def record_request(self, blocked: bool, endpoint: str, ip: str):
        """Record a request for statistics"""
        self.total_requests += 1
        if blocked:
            self.blocked_requests += 1
            self.blocked_by_endpoint[endpoint] += 1
            self.blocked_by_ip[ip] += 1
    
    def get_stats(self) -> dict:
        """Get current statistics"""
        return {
            "total_requests": self.total_requests,
            "blocked_requests": self.blocked_requests,
            "block_rate": self.blocked_requests / self.total_requests if self.total_requests > 0 else 0,
            "top_blocked_endpoints": dict(sorted(
                self.blocked_by_endpoint.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            "top_blocked_ips": dict(sorted(
                self.blocked_by_ip.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
        }


# Global stats
rate_limit_stats = RateLimitStats()
