from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np
import logging

# Redis imports
from backend.redis_config import redis_client
from backend.cache_service import (
    get_cached_recommendations,
    set_cached_recommendations,
    get_cache_stats
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =====================================================
# LOAD MODELS
# =====================================================

print("Loading models...")

vectorizer = joblib.load("models/vectorizer.pkl")
knn_model = joblib.load("models/knn_model.pkl")
books_df = pd.read_pickle("models/books_df.pkl")

print("Models loaded successfully!")

# =====================================================
# FASTAPI SETUP
# =====================================================

app = FastAPI()

# Allow frontend (React) to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://book-recommendation-system-9hci.vercel.app/" , "https://book-recommendation-system-9hci-git-main-shees-ikrams-projects.vercel.app/" , "https://book-recommend-pi.vercel.app/" , "*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from backend
from backend.books import router as books_router
from backend.cache_admin import router as cache_admin_router

app.include_router(books_router)
app.include_router(cache_admin_router)

# =====================================================
# STARTUP EVENT - Cache Warming
# =====================================================

@app.on_event("startup")
async def startup_event():
    """
    Warm cache on application startup with popular books.
    """
    logger.info("🚀 Starting application...")
    
    if redis_client.is_available:
        logger.info("🔥 Warming cache with popular books...")
        try:
            # Get top 10 most popular books by ratings_count
            popular_books = books_df.nlargest(10, 'ratings_count')
            
            for _, book in popular_books.iterrows():
                book_id = int(book['book_id'])
                try:
                    recommendations = get_recommendations(book_id)
                    result = {"book_id": book_id, "recommendations": recommendations}
                    set_cached_recommendations(book_id, result)
                    logger.info(f"  ✅ Cached recommendations for book {book_id}: {book['title']}")
                except Exception as e:
                    logger.warning(f"  ⚠️ Failed to cache book {book_id}: {e}")
            
            logger.info("✅ Cache warming completed")
        except Exception as e:
            logger.error(f"❌ Cache warming failed: {e}")
    else:
        logger.warning("⚠️ Redis not available, skipping cache warming")

# =====================================================
# HEALTH CHECK ENDPOINTS
# =====================================================

@app.get("/health")
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "Book Recommendation API"}

@app.get("/health/redis")
def redis_health_check():
    """Redis-specific health check."""
    health = redis_client.health_check()
    return health

@app.get("/cache/stats")
def cache_statistics():
    """Get cache statistics."""
    return get_cache_stats()

# =====================================================
#  Helper: get similar books
# =====================================================

def get_recommendations(book_id, n=10):
    # Check if book exists
    if book_id not in books_df["book_id"].values:
        raise HTTPException(status_code=404, detail="Book not found")

    # Get the index of selected book
    idx = books_df.index[books_df["book_id"] == book_id][0]

    # Prepare TF-IDF input
    text = books_df.loc[idx]["combined_text_clean"]
    text_vec = vectorizer.transform([text])

    # KNN search
    distances, indices = knn_model.kneighbors(text_vec, n_neighbors=n+1)

    # Skip the first index (it is the book itself)
    rec_indices = indices[0][1:]

    # Format output
    recommendations = []
    for rec_idx in rec_indices:
        row = books_df.iloc[rec_idx]
        recommendations.append({
            "book_id": int(row["book_id"]),
            "title": row["title"],
            "original_title": row["original_title"],
            "authors": row["authors"],
            "year": int(row["original_publication_year"]),
            "rating": float(row["average_rating"]),
            "ratings_count": int(row["ratings_count"]),
            "image_url": row["image_url"]
        })

    return recommendations


# =====================================================
#  API ROUTE: GET RECOMMENDATIONS
# =====================================================

@app.get("/recommend/{book_id}")
def recommend(book_id: int):
    """
    Get book recommendations with Redis caching.
    
    Flow:
    1. Check Redis cache first
    2. If cache hit, return cached data
    3. If cache miss, compute recommendations
    4. Store in cache and return
    """
    # Try to get from cache first
    cached_result = get_cached_recommendations(book_id)
    if cached_result:
        logger.info(f"📦 Cache HIT for book {book_id}")
        return cached_result
    
    # Cache miss - compute recommendations
    logger.info(f"🔍 Cache MISS for book {book_id}, computing...")
    recommendations = get_recommendations(book_id)
    result = {
        "book_id": book_id,
        "recommendations": recommendations
    }
    
    # Store in cache for future requests
    set_cached_recommendations(book_id, result)
    
    return result
