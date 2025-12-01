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


# Database connection
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


# ---------------------------------------------------------
# GET /books  → fetch all books (with Redis caching)
# ---------------------------------------------------------
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
            author,
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


# ---------------------------------------------------------
# POST /books  → insert book into DB + CSV
# ---------------------------------------------------------
@router.post("/books")
def add_book(book: dict):
    required_fields = [
        "title",
        "author",
        "original_publication_year",
        "average_rating",
        "image_url"
    ]

    # Validate required fields
    for field in required_fields:
        if field not in book:
            raise HTTPException(status_code=400, detail=f"Missing field: {field}")

    conn = _connect()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO books (
                title,
                author,
                original_publication_year,
                average_rating,
                image_url
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            book["title"],
            book["author"],
            book["original_publication_year"],
            book["average_rating"],
            book["image_url"]
        ))

        new_id = cursor.fetchone()[0]
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()

    # Invalidate Redis cache
    invalidate_books_list()

    # Append to CSV for your ML model
    csv_file = "books_dataset.csv"
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Write header if file didn't exist
        if not file_exists:
            writer.writerow([
                "title",
                "author",
                "original_publication_year",
                "average_rating",
                "image_url"
            ])

        writer.writerow([
            book["title"],
            book["author"],
            book["original_publication_year"],
            book["average_rating"],
            book["image_url"]
        ])

    return {
        "message": "Book added successfully",
        "book_id": new_id
    }
