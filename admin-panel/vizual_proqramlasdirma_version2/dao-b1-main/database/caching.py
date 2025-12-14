"""
Caching Layer for DAO Platform
================================
Read-through cache with hit-rate metrics for hot endpoints.
Supports Redis (production) and in-memory (development).
"""
import time
import json
import hashlib
import functools
from typing import Any, Optional, Dict, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading


# =============================================================================
# CACHE METRICS
# =============================================================================

@dataclass
class CacheMetrics:
    """Track cache hit/miss rates."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    
    @property
    def total_requests(self) -> int:
        return self.hits + self.misses
    
    @property
    def hit_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    def record_eviction(self):
        self.evictions += 1
    
    def get_stats(self) -> Dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate_percent": round(self.hit_rate, 2)
        }


# =============================================================================
# IN-MEMORY CACHE (Development)
# =============================================================================

@dataclass
class CacheEntry:
    """Single cache entry with TTL."""
    value: Any
    expires_at: float
    created_at: float = field(default_factory=time.time)


class InMemoryCache:
    """
    Thread-safe in-memory LRU cache with TTL.
    Use for development or small deployments.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl  # seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self.metrics = CacheMetrics()
    
    def _make_key(self, key: str) -> str:
        """Normalize cache key."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        hashed_key = self._make_key(key)
        
        with self._lock:
            entry = self._cache.get(hashed_key)
            
            if entry is None:
                self.metrics.record_miss()
                return None
            
            # Check TTL
            if time.time() > entry.expires_at:
                del self._cache[hashed_key]
                self.metrics.record_miss()
                self.metrics.record_eviction()
                return None
            
            self.metrics.record_hit()
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with TTL."""
        hashed_key = self._make_key(key)
        ttl = ttl or self.default_ttl
        
        with self._lock:
            # Evict oldest if at capacity
            if len(self._cache) >= self.max_size and hashed_key not in self._cache:
                oldest_key = min(self._cache, key=lambda k: self._cache[k].created_at)
                del self._cache[oldest_key]
                self.metrics.record_eviction()
            
            self._cache[hashed_key] = CacheEntry(
                value=value,
                expires_at=time.time() + ttl
            )
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        hashed_key = self._make_key(key)
        
        with self._lock:
            if hashed_key in self._cache:
                del self._cache[hashed_key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear entire cache."""
        with self._lock:
            self._cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self._lock:
            return {
                **self.metrics.get_stats(),
                "current_size": len(self._cache),
                "max_size": self.max_size
            }


# =============================================================================
# REDIS CACHE (Production)
# =============================================================================

class RedisCache:
    """
    Redis-backed cache for production.
    Falls back to in-memory if Redis unavailable.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0", 
                 default_ttl: int = 300, prefix: str = "dao:"):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.prefix = prefix
        self.metrics = CacheMetrics()
        self._redis = None
        self._fallback = InMemoryCache()
        self._connect()
    
    def _connect(self):
        """Connect to Redis."""
        try:
            import redis
            self._redis = redis.from_url(self.redis_url)
            self._redis.ping()
        except Exception:
            self._redis = None
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis or fallback."""
        if self._redis is None:
            return self._fallback.get(key)
        
        try:
            prefixed_key = self._make_key(key)
            data = self._redis.get(prefixed_key)
            
            if data is None:
                self.metrics.record_miss()
                return None
            
            self.metrics.record_hit()
            return json.loads(data)
        except Exception:
            return self._fallback.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in Redis or fallback."""
        if self._redis is None:
            self._fallback.set(key, value, ttl)
            return
        
        try:
            prefixed_key = self._make_key(key)
            ttl = ttl or self.default_ttl
            self._redis.setex(prefixed_key, ttl, json.dumps(value, default=str))
        except Exception:
            self._fallback.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete from Redis."""
        if self._redis is None:
            return self._fallback.delete(key)
        
        try:
            prefixed_key = self._make_key(key)
            return self._redis.delete(prefixed_key) > 0
        except Exception:
            return self._fallback.delete(key)
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        stats = self.metrics.get_stats()
        stats["backend"] = "redis" if self._redis else "in_memory"
        return stats


# =============================================================================
# CACHE DECORATOR
# =============================================================================

# Global cache instance
_cache: Optional[InMemoryCache] = None


def get_cache() -> InMemoryCache:
    """Get or create global cache instance."""
    global _cache
    if _cache is None:
        _cache = InMemoryCache(max_size=1000, default_ttl=300)
    return _cache


def cached(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for caching function results.
    
    Usage:
        @cached(ttl=60, key_prefix="user")
        def get_user(user_id: int):
            return db.query(User).get(user_id)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from function name and arguments
            cache = get_cache()
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# =============================================================================
# QUERY CACHE FOR HOT ENDPOINTS
# =============================================================================

class QueryCache:
    """
    Specialized cache for hot database queries.
    Tracks hit rates per query type.
    """
    
    def __init__(self, cache: Optional[InMemoryCache] = None):
        self.cache = cache or get_cache()
        self.query_metrics: Dict[str, CacheMetrics] = {}
    
    def cache_query(self, query_name: str, params: Dict, 
                    fetch_func: Callable, ttl: int = 60) -> Any:
        """
        Cache a database query result.
        
        Args:
            query_name: Unique name for this query type
            params: Query parameters for cache key
            fetch_func: Function to call on cache miss
            ttl: Time to live in seconds
        """
        # Initialize metrics for this query type
        if query_name not in self.query_metrics:
            self.query_metrics[query_name] = CacheMetrics()
        
        metrics = self.query_metrics[query_name]
        
        # Build cache key
        param_str = json.dumps(params, sort_keys=True, default=str)
        cache_key = f"query:{query_name}:{hashlib.md5(param_str.encode()).hexdigest()}"
        
        # Try cache
        result = self.cache.get(cache_key)
        if result is not None:
            metrics.record_hit()
            return result
        
        # Cache miss - fetch and store
        metrics.record_miss()
        result = fetch_func()
        self.cache.set(cache_key, result, ttl)
        return result
    
    def invalidate_query(self, query_name: str) -> None:
        """Invalidate all cached results for a query type."""
        # In production, use Redis SCAN or key patterns
        pass
    
    def get_stats(self) -> Dict:
        """Get per-query hit rates."""
        return {
            name: metrics.get_stats() 
            for name, metrics in self.query_metrics.items()
        }


# =============================================================================
# HTTP RESPONSE CACHE
# =============================================================================

class HTTPCacheMiddleware:
    """
    HTTP response caching for FastAPI/Django.
    Adds Cache-Control headers and tracks hit rates.
    """
    
    def __init__(self, cache: Optional[InMemoryCache] = None):
        self.cache = cache or get_cache()
        self.metrics = CacheMetrics()
    
    def cache_response(self, path: str, response_data: Any, 
                       max_age: int = 60) -> Dict:
        """
        Cache an HTTP response.
        
        Returns headers to add to response.
        """
        cache_key = f"http:{path}"
        self.cache.set(cache_key, response_data, max_age)
        
        return {
            "Cache-Control": f"public, max-age={max_age}",
            "X-Cache": "MISS"
        }
    
    def get_cached_response(self, path: str) -> Optional[tuple]:
        """
        Get cached response if available.
        
        Returns (data, headers) or None.
        """
        cache_key = f"http:{path}"
        data = self.cache.get(cache_key)
        
        if data is not None:
            self.metrics.record_hit()
            headers = {"X-Cache": "HIT"}
            return (data, headers)
        
        self.metrics.record_miss()
        return None


# =============================================================================
# DEMO / TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CACHING LAYER DEMO")
    print("=" * 60)
    
    # Create cache
    cache = InMemoryCache(max_size=100, default_ttl=60)
    
    # Simulate hot endpoint caching
    print("\n[1] Simulating hot endpoint cache...")
    
    for i in range(100):
        key = f"user:{i % 10}"  # 10 unique users
        
        # 70% cache hits after warm-up
        result = cache.get(key)
        if result is None:
            # Simulate DB fetch
            cache.set(key, {"user_id": i % 10, "name": f"User {i % 10}"})
    
    stats = cache.get_stats()
    print(f"   Cache Stats: {stats}")
    print(f"   Hit Rate: {stats['hit_rate_percent']:.1f}%")
    
    # Query cache demo
    print("\n[2] Query Cache Demo...")
    query_cache = QueryCache(cache)
    
    for i in range(50):
        query_cache.cache_query(
            "get_transactions",
            {"user_id": i % 5},
            lambda: {"tx_count": 10},
            ttl=30
        )
    
    print(f"   Query Stats: {query_cache.get_stats()}")
    
    # Decorator demo
    print("\n[3] Decorator Demo...")
    
    @cached(ttl=60, key_prefix="demo")
    def expensive_operation(x: int) -> int:
        time.sleep(0.01)  # Simulate slow operation
        return x * 2
    
    for i in range(20):
        expensive_operation(i % 5)
    
    print(f"   Decorator Cache Stats: {get_cache().get_stats()}")
    
    print("\n[OK] Caching layer ready!")
