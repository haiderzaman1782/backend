from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np

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
app.include_router(books_router)

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
    return {
        "book_id": book_id,
        "recommendations": get_recommendations(book_id)
    }
