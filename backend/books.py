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
            book_id,
            original_title,
            title,
            authors,
            original_publication_year,
            average_rating,
            image_url,
            small_image_url
        FROM books
    """)
# ---------------------------------------------------------
# POST /books  → insert book into DB + CSV
# ---------------------------------------------------------
@router.post("/books")
def add_book(book: dict):

    # validate fields
    ...

    # DO NOT INSERT INTO DB HERE
    # Supabase already did that

    # Only update CSV
    csv_file = "../books.csv"
    file_exists = os.path.isfile(csv_file)

    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "book_id", "title", "original_title", "authors", "original_publication_year",
                "average_rating", "image_url"
            ])

        writer.writerow([
            book["book_id"],
            book["title"],
            book["original_title"],
            book["authors"],
            book["original_publication_year"],
            book["average_rating"],
            book["image_url"]
        ])

    return {"message": "Book processed for ML CSV"}

