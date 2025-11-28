import redis
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """
    Redis client singleton for managing cache connections.
    Supports both local and cloud Redis with automatic reconnection.
    """
    
    _instance: Optional[redis.Redis] = None
    _is_available: bool = False
    
    def __init__(self):
        """Initialize Redis connection with error handling."""
        try:
            self._instance = self._create_connection()
            # Test connection
            self._instance.ping()
            self._is_available = True
            logger.info("✅ Redis connection established successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Running without cache.")
            self._is_available = False
            self._instance = None
    
    def _create_connection(self) -> redis.Redis:
        """
        Create Redis connection from environment configuration.
        Supports both local Redis and cloud providers (Upstash, Redis Cloud, etc.)
        
        Returns:
            redis.Redis: Configured Redis client instance
        """
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        # For Upstash, we need to use rediss:// (SSL) protocol
        # Replace redis:// with rediss:// for Upstash
        if "upstash.io" in redis_url and redis_url.startswith("redis://"):
            redis_url = redis_url.replace("redis://", "rediss://", 1)
            logger.info("🔒 Using SSL/TLS connection for Upstash Redis")
        
        return redis.from_url(
            redis_url,
            decode_responses=True,  # Automatically decode responses to strings
            socket_connect_timeout=5,  # Connection timeout in seconds
            socket_keepalive=True,  # Keep connection alive
            health_check_interval=30,  # Health check every 30 seconds
            retry_on_timeout=True,  # Retry on timeout
            max_connections=50  # Connection pool size
        )
    
    @property
    def client(self) -> Optional[redis.Redis]:
        """Get Redis client instance."""
        return self._instance
    
    @property
    def is_available(self) -> bool:
        """Check if Redis is available."""
        return self._is_available
    
    def reconnect(self) -> bool:
        """
        Attempt to reconnect to Redis.
        
        Returns:
            bool: True if reconnection successful, False otherwise
        """
        try:
            self._instance = self._create_connection()
            self._instance.ping()
            self._is_available = True
            logger.info("✅ Redis reconnected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Redis reconnection failed: {e}")
            self._is_available = False
            return False
    
    def health_check(self) -> dict:
        """
        Perform health check on Redis connection.
        
        Returns:
            dict: Health status information
        """
        if not self._is_available or not self._instance:
            return {
                "status": "unavailable",
                "message": "Redis is not connected"
            }
        
        try:
            self._instance.ping()
            info = self._instance.info()
            return {
                "status": "healthy",
                "version": info.get("redis_version", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "uptime_in_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"❌ Redis health check failed: {e}")
            self._is_available = False
            return {
                "status": "unhealthy",
                "message": str(e)
            }


# Global Redis client instance
redis_client = RedisClient()
