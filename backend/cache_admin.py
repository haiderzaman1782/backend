from fastapi import APIRouter, HTTPException
from backend.redis_config import redis_client
from backend.cache_service import (
    get_cache_stats,
    clear_all_cache,
    get_all_cache_keys,
    invalidate_recommendations,
    invalidate_books_list
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/cache", tags=["Cache Admin"])


@router.get("/stats")
def get_statistics():
    """
    Get cache statistics including hit/miss rates.
    
    Returns:
        dict: Cache statistics
    """
    stats = get_cache_stats()
    health = redis_client.health_check()
    
    return {
        "cache_stats": stats,
        "redis_health": health
    }


@router.post("/clear")
def clear_cache():
    """
    Clear all cache data (admin function).
    
    Returns:
        dict: Success message
    """
    success = clear_all_cache()
    
    if success:
        logger.info("🗑️ Admin cleared all cache")
        return {"message": "Cache cleared successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear cache")


@router.get("/keys")
def list_cache_keys():
    """
    List all cache keys (for debugging).
    
    Returns:
        dict: List of cache keys
    """
    keys = get_all_cache_keys()
    return {
        "total_keys": len(keys),
        "keys": keys
    }


@router.delete("/book/{book_id}")
def invalidate_book_cache(book_id: int):
    """
    Invalidate cache for a specific book's recommendations.
    
    Args:
        book_id: Book ID to invalidate
        
    Returns:
        dict: Success message
    """
    success = invalidate_recommendations(book_id)
    
    if success:
        logger.info(f"🗑️ Admin invalidated cache for book {book_id}")
        return {"message": f"Cache invalidated for book {book_id}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


@router.post("/invalidate/books")
def invalidate_books_cache():
    """
    Invalidate the books list cache.
    
    Returns:
        dict: Success message
    """
    success = invalidate_books_list()
    
    if success:
        logger.info("🗑️ Admin invalidated books list cache")
        return {"message": "Books list cache invalidated"}
    else:
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")


@router.post("/reconnect")
def reconnect_redis():
    """
    Attempt to reconnect to Redis.
    
    Returns:
        dict: Reconnection status
    """
    success = redis_client.reconnect()
    
    if success:
        return {"message": "Redis reconnected successfully", "status": "connected"}
    else:
        raise HTTPException(status_code=500, detail="Failed to reconnect to Redis")
