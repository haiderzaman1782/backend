from fastapi import APIRouter
import os
import psycopg2
from psycopg2.extras import RealDictCursor

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
    conn = _connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    # rows are RealDictRow; convert to plain dicts
    result = [dict(r) for r in rows]
    cursor.close()
    conn.close()
    return result

