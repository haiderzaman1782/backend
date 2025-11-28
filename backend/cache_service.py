import json
import logging
from typing import Any, Optional
from backend.redis_config import redis_client

logger = logging.getLogger(__name__)

# Cache TTL settings (in seconds)
CACHE_TTL_RECOMMENDATIONS = 3600  # 1 hour
CACHE_TTL_BOOKS = 300  # 5 minutes
CACHE_TTL_BOOK_DETAIL = 1800  # 30 minutes

# Cache key prefixes
KEY_PREFIX_RECOMMENDATIONS = "book:recommendations:"
KEY_PREFIX_BOOKS_LIST = "book:list:all"
KEY_PREFIX_BOOK_DETAIL = "book:detail:"
KEY_PREFIX_STATS_HITS = "stats:cache:hits"
KEY_PREFIX_STATS_MISSES = "stats:cache:misses"


def _get_cache(key: str) -> Optional[Any]:
    """
    Internal helper to get data from cache.
    
    Args:
        key: Cache key
        
    Returns:
        Cached data or None if not found or Redis unavailable
    """
    if not redis_client.is_available:
        return None
    
    try:
        data = redis_client.client.get(key)
        if data:
            # Increment hit counter
            redis_client.client.incr(KEY_PREFIX_STATS_HITS)
            logger.debug(f"✅ Cache HIT: {key}")
            return json.loads(data)
        else:
            # Increment miss counter
            redis_client.client.incr(KEY_PREFIX_STATS_MISSES)
            logger.debug(f"❌ Cache MISS: {key}")
            return None
    except Exception as e:
        logger.error(f"Error reading from cache: {e}")
        return None


def _set_cache(key: str, value: Any, ttl: int) -> bool:
    """
    Internal helper to set data in cache.
    
    Args:
        key: Cache key
        value: Data to cache
        ttl: Time to live in seconds
        
    Returns:
        True if successful, False otherwise
    """
    if not redis_client.is_available:
        return False
    
    try:
        serialized = json.dumps(value)
        redis_client.client.setex(key, ttl, serialized)
        logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Error writing to cache: {e}")
        return False


def _delete_cache(key: str) -> bool:
    """
    Internal helper to delete data from cache.
    
    Args:
        key: Cache key
        
    Returns:
        True if successful, False otherwise
    """
    if not redis_client.is_available:
        return False
    
    try:
        redis_client.client.delete(key)
        logger.debug(f"🗑️ Cache DELETE: {key}")
        return True
    except Exception as e:
        logger.error(f"Error deleting from cache: {e}")
        return False


# =====================================================
# PUBLIC API - Recommendations
# =====================================================

def get_cached_recommendations(book_id: int) -> Optional[dict]:
    """
    Get cached recommendations for a book.
    
    Args:
        book_id: Book ID
        
    Returns:
        Cached recommendations or None
    """
    key = f"{KEY_PREFIX_RECOMMENDATIONS}{book_id}"
    return _get_cache(key)


def set_cached_recommendations(book_id: int, data: dict, ttl: int = CACHE_TTL_RECOMMENDATIONS) -> bool:
    """
    Cache recommendations for a book.
    
    Args:
        book_id: Book ID
        data: Recommendation data
        ttl: Time to live in seconds
        
    Returns:
        True if successful
    """
    key = f"{KEY_PREFIX_RECOMMENDATIONS}{book_id}"
    return _set_cache(key, data, ttl)


def invalidate_recommendations(book_id: int) -> bool:
    """
    Invalidate cached recommendations for a book.
    
    Args:
        book_id: Book ID
        
    Returns:
        True if successful
    """
    key = f"{KEY_PREFIX_RECOMMENDATIONS}{book_id}"
    return _delete_cache(key)


# =====================================================
# PUBLIC API - Books List
# =====================================================

def get_cached_books() -> Optional[list]:
    """
    Get cached books list.
    
    Returns:
        Cached books list or None
    """
    return _get_cache(KEY_PREFIX_BOOKS_LIST)


def set_cached_books(data: list, ttl: int = CACHE_TTL_BOOKS) -> bool:
    """
    Cache books list.
    
    Args:
        data: Books list data
        ttl: Time to live in seconds
        
    Returns:
        True if successful
    """
    return _set_cache(KEY_PREFIX_BOOKS_LIST, data, ttl)


def invalidate_books_list() -> bool:
    """
    Invalidate cached books list.
    
    Returns:
        True if successful
    """
    return _delete_cache(KEY_PREFIX_BOOKS_LIST)


# =====================================================
# PUBLIC API - Book Details
# =====================================================

def get_cached_book_detail(book_id: int) -> Optional[dict]:
    """
    Get cached book detail.
    
    Args:
        book_id: Book ID
        
    Returns:
        Cached book detail or None
    """
    key = f"{KEY_PREFIX_BOOK_DETAIL}{book_id}"
    return _get_cache(key)


def set_cached_book_detail(book_id: int, data: dict, ttl: int = CACHE_TTL_BOOK_DETAIL) -> bool:
    """
    Cache book detail.
    
    Args:
        book_id: Book ID
        data: Book detail data
        ttl: Time to live in seconds
        
    Returns:
        True if successful
    """
    key = f"{KEY_PREFIX_BOOK_DETAIL}{book_id}"
    return _set_cache(key, data, ttl)


# =====================================================
# PUBLIC API - Cache Management
# =====================================================

def get_cache_stats() -> dict:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache stats
    """
    if not redis_client.is_available:
        return {
            "status": "unavailable",
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0
        }
    
    try:
        hits = int(redis_client.client.get(KEY_PREFIX_STATS_HITS) or 0)
        misses = int(redis_client.client.get(KEY_PREFIX_STATS_MISSES) or 0)
        total = hits + misses
        hit_rate = (hits / total * 100) if total > 0 else 0.0
        
        return {
            "status": "available",
            "hits": hits,
            "misses": misses,
            "total_requests": total,
            "hit_rate": round(hit_rate, 2)
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def clear_all_cache() -> bool:
    """
    Clear all cache data (admin function).
    
    Returns:
        True if successful
    """
    if not redis_client.is_available:
        return False
    
    try:
        redis_client.client.flushdb()
        logger.info("🗑️ All cache cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False


def get_all_cache_keys() -> list:
    """
    Get all cache keys (for debugging).
    
    Returns:
        List of cache keys
    """
    if not redis_client.is_available:
        return []
    
    try:
        keys = redis_client.client.keys("*")
        return keys
    except Exception as e:
        logger.error(f"Error getting cache keys: {e}")
        return []
