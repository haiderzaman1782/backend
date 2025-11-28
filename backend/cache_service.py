import json
import logging
from typing import Any, Optional
from decimal import Decimal
from datetime import datetime
from backend.redis_config import redis_client

logger = logging.getLogger(__name__)

# =====================================================
# Custom JSON Encoder (Decimal + Datetime support)
# =====================================================
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)

        if isinstance(obj, datetime):
            return obj.isoformat()

        return super().default(obj)


# =====================================================
# Cache TTL settings (seconds)
# =====================================================
CACHE_TTL_RECOMMENDATIONS = 3600    # 1 hour
CACHE_TTL_BOOKS = 300               # 5 minutes
CACHE_TTL_BOOK_DETAIL = 1800        # 30 minutes

# Cache key prefixes
KEY_PREFIX_RECOMMENDATIONS = "book:recommendations:"
KEY_PREFIX_BOOKS_LIST = "book:list:all"
KEY_PREFIX_BOOK_DETAIL = "book:detail:"
KEY_PREFIX_STATS_HITS = "stats:cache:hits"
KEY_PREFIX_STATS_MISSES = "stats:cache:misses"


# =====================================================
# Internal Cache Helpers
# =====================================================

def _get_cache(key: str) -> Optional[Any]:
    if not redis_client.is_available:
        return None

    try:
        data = redis_client.client.get(key)

        if data:
            redis_client.client.incr(KEY_PREFIX_STATS_HITS)
            logger.debug(f"✅ Cache HIT: {key}")
            return json.loads(data)
        else:
            redis_client.client.incr(KEY_PREFIX_STATS_MISSES)
            logger.debug(f"❌ Cache MISS: {key}")
            return None

    except Exception as e:
        logger.error(f"Error reading from cache: {e}")
        return None


def _set_cache(key: str, value: Any, ttl: int) -> bool:
    if not redis_client.is_available:
        return False

    try:
        serialized = json.dumps(value, cls=CustomJSONEncoder)
        redis_client.client.setex(key, ttl, serialized)
        logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
        return True

    except Exception as e:
        logger.error(f"Error writing to cache: {e}")
        return False


def _delete_cache(key: str) -> bool:
    if not redis_client.is_available:
        return False

    try:
        redis_client.client.delete(key)
        logger.debug(f"🗑️ Cache DELETE: {key}")
        return True

    except Exception as e:
        logger.error(f"Error deleting cache: {e}")
        return False


# =====================================================
# PUBLIC API — RECOMMENDATIONS
# =====================================================

def get_cached_recommendations(book_id: int) -> Optional[dict]:
    key = f"{KEY_PREFIX_RECOMMENDATIONS}{book_id}"
    return _get_cache(key)


def set_cached_recommendations(book_id: int, data: dict, ttl: int = CACHE_TTL_RECOMMENDATIONS) -> bool:
    key = f"{KEY_PREFIX_RECOMMENDATIONS}{book_id}"
    return _set_cache(key, data, ttl)


def invalidate_recommendations(book_id: int) -> bool:
    key = f"{KEY_PREFIX_RECOMMENDATIONS}{book_id}"
    return _delete_cache(key)


# =====================================================
# PUBLIC API — BOOK LIST
# =====================================================

def get_cached_books() -> Optional[list]:
    return _get_cache(KEY_PREFIX_BOOKS_LIST)


def set_cached_books(data: list, ttl: int = CACHE_TTL_BOOKS) -> bool:
    return _set_cache(KEY_PREFIX_BOOKS_LIST, data, ttl)


def invalidate_books_list() -> bool:
    return _delete_cache(KEY_PREFIX_BOOKS_LIST)


# =====================================================
# PUBLIC API — BOOK DETAILS
# =====================================================

def get_cached_book_detail(book_id: int) -> Optional[dict]:
    key = f"{KEY_PREFIX_BOOK_DETAIL}{book_id}"
    return _get_cache(key)


def set_cached_book_detail(book_id: int, data: dict, ttl: int = CACHE_TTL_BOOK_DETAIL) -> bool:
    key = f"{KEY_PREFIX_BOOK_DETAIL}{book_id}"
    return _set_cache(key, data, ttl)


# =====================================================
# PUBLIC API — CACHE MANAGEMENT
# =====================================================

def get_cache_stats() -> dict:
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
        logger.error(f"Error reading cache stats: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


def clear_all_cache() -> bool:
    if not redis_client.is_available:
        return False

    try:
        redis_client.client.flushdb()
        logger.info("🧹 All cache cleared")
        return True

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False


def get_all_cache_keys() -> list:
    if not redis_client.is_available:
        return []

    try:
        return redis_client.client.keys("*")

    except Exception as e:
        logger.error(f"Error getting cache keys: {e}")
        return []
