from fastapi import APIRouter, HTTPException
import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
import csv

# Redis cache functions
from backend.cache_service import (
    get_cached_books,
    set_cached_books,
    invalidate_books_list
)

router = APIRouter()
logger = logging.getLogger(__name__)

# -------------------------
# Database connection
# -------------------------
def _connect():
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url, sslmode="require")
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "Books-recommendation-system"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "Strong123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
    )

# -------------------------
# GET /books → fetch all books
# -------------------------
@router.get("/books")
def fetch_books():
    cached_books = get_cached_books()
    if cached_books:
        logger.info("📦 Cache HIT")
        return cached_books

    logger.info("❌ Cache MISS — querying database")
    conn = _connect()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT 
            id,
            title,
            authors,
            original_publication_year,
            average_rating,
            image_url
        FROM books
    """)
    
    rows = cursor.fetchall()
    result = [dict(r) for r in rows]

    cursor.close()
    conn.close()

    # Cache for 5 mins
    set_cached_books(result)

    return result

# -------------------------
# POST /books → CSV update only
# -------------------------
@router.post("/books")
def add_book(book: dict):
    required_fields = ["title", "authors", "original_publication_year", "average_rating", "image_url"]

    for field in required_fields:
        if field not in book:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    # Only update CSV
    csv_file = "books.csv"
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(required_fields)

        writer.writerow([
            book["title"],
            book["authors"],
            book["original_publication_year"],
            book["average_rating"],
            book["image_url"]
        ])

    return {"message": "Book processed for ML CSV"}

# -------------------------
# DELETE /books/{id} → delete from DB
# -------------------------
@router.delete("/books/{book_id}")
async def delete_book(book_id: int):
    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Book not found")

        # Invalidate cache
        invalidate_books_list()

        return {"message": "Book deleted successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

# -------------------------
# PUT /books/{id} → update book in DB
# -------------------------
@router.put("/books/{book_id}")
async def update_book(book_id: int, payload: dict):
    required_fields = ["title", "authors", "original_publication_year", "average_rating", "image_url"]
    for field in required_fields:
        if field not in payload:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE books SET
                title=%s,
                authors=%s,
                original_publication_year=%s,
                average_rating=%s,
                image_url=%s
            WHERE id=%s
        """, (
            payload["title"],
            payload["authors"],
            payload["original_publication_year"],
            payload["average_rating"],
            payload["image_url"],
            book_id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Book not found")

        # Invalidate cache
        invalidate_books_list()

        return {"message": "Book updated successfully"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()
