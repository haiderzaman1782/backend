from fastapi import APIRouter
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Redis cache imports
from backend.cache_service import (
    get_cached_books,
    set_cached_books,
    invalidate_books_list
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _connect():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Use SSL/TLS for managed Postgres (Supabase/Neon)
        return psycopg2.connect(database_url, sslmode="require")

    # Fallback to local settings
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "Books-recommendation-system"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "Strong123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )


@router.get("/books")
def fetch_books():
    """
    Fetch all books with Redis caching.
    
    Flow:
    1. Check Redis cache first
    2. If cache hit, return cached data
    3. If cache miss, query database
    4. Store in cache and return
    """
    # Try to get from cache first
    cached_books = get_cached_books()
    if cached_books:
        logger.info("📦 Cache HIT for books list")
        return cached_books
    
    # Cache miss - query database
    logger.info("🔍 Cache MISS for books list, querying database...")
    conn = _connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    # rows are RealDictRow; convert to plain dicts
    result = [dict(r) for r in rows]
    cursor.close()
    conn.close()
    
    # Store in cache for future requests (5 minutes TTL)
    set_cached_books(result)
    
    return result

