"""
Redis Cache Module
Provides caching utilities for frequently accessed data.

# ══════════════════════════════════════════════════════════════════════════════
# MODULE STRUCTURE MAP
# ══════════════════════════════════════════════════════════════════════════════
#
# FUNCTIONS:
#
# Connection:
# - get_redis_client() -> Redis client or None
# - is_cache_available() -> bool
#
# Basic Operations:
# - cache_get(key) -> value or None
# - cache_set(key, value, ttl) -> bool
# - cache_delete(key) -> bool
# - cache_exists(key) -> bool
#
# Specialized Caching:
# - cache_hierarchy(ctv_code, tree) -> cache CTV hierarchy
# - get_cached_hierarchy(ctv_code) -> get cached hierarchy
# - cache_commission_rates() -> cache commission rates
# - get_cached_commission_rates() -> get cached rates
#
# Decorators:
# - cached(key_prefix, ttl) -> decorator for caching function results
#
# Cache Invalidation:
# - invalidate_hierarchy(ctv_code) -> invalidate specific hierarchy
# - invalidate_all_hierarchies() -> invalidate all hierarchies
# - invalidate_commission_cache() -> invalidate commission data
#
# CACHE KEY PATTERNS:
# - hierarchy:{ctv_code} -> CTV hierarchy tree (TTL: 15 min)
# - commissions:{ctv_code}:{month} -> Commission reports (TTL: 1 hour)
# - duplicate_check:{phone} -> Duplicate check results (TTL: 1 hour)
# - ctv_info:{ctv_code} -> CTV details (TTL: 30 min)
# - commission_rates -> Commission rate config (TTL: 1 hour)
#
# Created: January 2, 2026
# ══════════════════════════════════════════════════════════════════════════════
"""

import os
import json
from functools import wraps
from datetime import timedelta

# Try to import redis, but don't fail if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("WARNING: Redis not installed. Caching will be disabled.")

# Redis configuration
REDIS_CONFIG = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', 6379)),
    'db': int(os.environ.get('REDIS_DB', 0)),
    'password': os.environ.get('REDIS_PASSWORD', None),
    'decode_responses': True
}

# Default TTLs (in seconds)
TTL_HIERARCHY = 900        # 15 minutes
TTL_COMMISSION_RATES = 3600  # 1 hour
TTL_CTV_INFO = 1800        # 30 minutes
TTL_DUPLICATE_CHECK = 3600  # 1 hour
TTL_COMMISSION_REPORT = 3600  # 1 hour

# Singleton Redis client
_redis_client = None


def get_redis_client():
    """
    DOES: Get or create the singleton Redis client
    OUTPUTS: Redis client instance or None if not available
    """
    global _redis_client
    
    if not REDIS_AVAILABLE:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(**REDIS_CONFIG)
            # Test connection
            _redis_client.ping()
            print("Redis connection established")
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"Redis connection failed: {e}")
            _redis_client = None
    
    return _redis_client


def is_cache_available():
    """
    DOES: Check if caching is available
    OUTPUTS: True if Redis is connected, False otherwise
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        return client.ping()
    except:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# BASIC CACHE OPERATIONS
# ══════════════════════════════════════════════════════════════════════════════

def cache_get(key):
    """
    DOES: Get a value from cache
    INPUTS: key - cache key
    OUTPUTS: Deserialized value or None
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except (redis.RedisError, json.JSONDecodeError) as e:
        print(f"Cache get error: {e}")
        return None


def cache_set(key, value, ttl=3600):
    """
    DOES: Set a value in cache
    INPUTS: key - cache key, value - value to cache, ttl - time to live in seconds
    OUTPUTS: True if successful, False otherwise
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        serialized = json.dumps(value)
        client.setex(key, ttl, serialized)
        return True
    except (redis.RedisError, TypeError) as e:
        print(f"Cache set error: {e}")
        return False


def cache_delete(key):
    """
    DOES: Delete a key from cache
    INPUTS: key - cache key
    OUTPUTS: True if deleted, False otherwise
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except redis.RedisError as e:
        print(f"Cache delete error: {e}")
        return False


def cache_delete_pattern(pattern):
    """
    DOES: Delete all keys matching a pattern
    INPUTS: pattern - key pattern (e.g., "hierarchy:*")
    OUTPUTS: Number of deleted keys
    """
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except redis.RedisError as e:
        print(f"Cache delete pattern error: {e}")
        return 0


def cache_exists(key):
    """
    DOES: Check if a key exists in cache
    INPUTS: key - cache key
    OUTPUTS: True if exists, False otherwise
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        return client.exists(key) > 0
    except redis.RedisError:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# SPECIALIZED CACHING FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def cache_hierarchy(ctv_code, tree):
    """
    DOES: Cache a CTV hierarchy tree
    INPUTS: ctv_code - CTV code, tree - hierarchy tree dict
    OUTPUTS: True if successful
    """
    key = f"hierarchy:{ctv_code}"
    return cache_set(key, tree, TTL_HIERARCHY)


def get_cached_hierarchy(ctv_code):
    """
    DOES: Get cached CTV hierarchy tree
    INPUTS: ctv_code - CTV code
    OUTPUTS: Hierarchy tree dict or None
    """
    key = f"hierarchy:{ctv_code}"
    return cache_get(key)


def invalidate_hierarchy(ctv_code):
    """
    DOES: Invalidate a specific CTV's hierarchy cache
    INPUTS: ctv_code - CTV code
    """
    key = f"hierarchy:{ctv_code}"
    cache_delete(key)


def invalidate_all_hierarchies():
    """
    DOES: Invalidate all hierarchy caches
    Call this when CTV relationships change
    """
    cache_delete_pattern("hierarchy:*")


def cache_ctv_info(ctv_code, info):
    """
    DOES: Cache CTV information
    INPUTS: ctv_code - CTV code, info - CTV info dict
    OUTPUTS: True if successful
    """
    key = f"ctv_info:{ctv_code}"
    return cache_set(key, info, TTL_CTV_INFO)


def get_cached_ctv_info(ctv_code):
    """
    DOES: Get cached CTV information
    INPUTS: ctv_code - CTV code
    OUTPUTS: CTV info dict or None
    """
    key = f"ctv_info:{ctv_code}"
    return cache_get(key)


def cache_commission_rates(rates):
    """
    DOES: Cache commission rates configuration
    INPUTS: rates - dict of level: rate
    OUTPUTS: True if successful
    """
    key = "commission_rates"
    return cache_set(key, rates, TTL_COMMISSION_RATES)


def get_cached_commission_rates():
    """
    DOES: Get cached commission rates
    OUTPUTS: Dict of level: rate or None
    """
    key = "commission_rates"
    return cache_get(key)


def invalidate_commission_cache():
    """
    DOES: Invalidate all commission-related caches
    Call this when new transactions are created
    """
    cache_delete("commission_rates")
    cache_delete_pattern("commissions:*")


def cache_duplicate_check(phone, is_duplicate):
    """
    DOES: Cache phone duplicate check result
    INPUTS: phone - phone number, is_duplicate - bool
    OUTPUTS: True if successful
    """
    key = f"duplicate_check:{phone}"
    return cache_set(key, {'is_duplicate': is_duplicate}, TTL_DUPLICATE_CHECK)


def get_cached_duplicate_check(phone):
    """
    DOES: Get cached phone duplicate check result
    INPUTS: phone - phone number
    OUTPUTS: Dict with is_duplicate key or None
    """
    key = f"duplicate_check:{phone}"
    return cache_get(key)


# ══════════════════════════════════════════════════════════════════════════════
# CACHING DECORATOR
# ══════════════════════════════════════════════════════════════════════════════

def cached(key_prefix, ttl=3600, key_builder=None):
    """
    DOES: Decorator to cache function results
    
    INPUTS:
    - key_prefix: Prefix for cache key
    - ttl: Time to live in seconds
    - key_builder: Optional function to build cache key from args
    
    USAGE:
    @cached("user", ttl=300)
    def get_user(user_id):
        # This will be cached for 5 minutes
        return db.get_user(user_id)
    
    @cached("report", ttl=3600, key_builder=lambda ctv, month: f"{ctv}:{month}")
    def get_report(ctv_code, month):
        return calculate_report(ctv_code, month)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Default: use first positional argument
                if args:
                    cache_key = f"{key_prefix}:{args[0]}"
                else:
                    cache_key = key_prefix
            
            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache_set(cache_key, result, ttl)
            
            return result
        
        # Add method to bypass cache
        def bypass(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.bypass = bypass
        
        # Add method to invalidate cache
        def invalidate(*args, **kwargs):
            if key_builder:
                cache_key = f"{key_prefix}:{key_builder(*args, **kwargs)}"
            elif args:
                cache_key = f"{key_prefix}:{args[0]}"
            else:
                cache_key = key_prefix
            cache_delete(cache_key)
        wrapper.invalidate = invalidate
        
        return wrapper
    return decorator


# ══════════════════════════════════════════════════════════════════════════════
# CACHE STATISTICS
# ══════════════════════════════════════════════════════════════════════════════

def get_cache_stats():
    """
    DOES: Get cache statistics
    OUTPUTS: Dict with cache stats or None if unavailable
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        info = client.info('stats')
        memory = client.info('memory')
        
        return {
            'connected': True,
            'hits': info.get('keyspace_hits', 0),
            'misses': info.get('keyspace_misses', 0),
            'hit_rate': round(
                info.get('keyspace_hits', 0) / 
                max(info.get('keyspace_hits', 0) + info.get('keyspace_misses', 0), 1) * 100, 2
            ),
            'used_memory': memory.get('used_memory_human', 'N/A'),
            'total_keys': client.dbsize()
        }
    except redis.RedisError as e:
        return {'connected': False, 'error': str(e)}


def clear_all_cache():
    """
    DOES: Clear all cached data (use with caution)
    OUTPUTS: True if successful
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.flushdb()
        print("All cache cleared")
        return True
    except redis.RedisError as e:
        print(f"Error clearing cache: {e}")
        return False


# Initialize Redis connection on module import
if REDIS_AVAILABLE:
    _redis_client = get_redis_client()

