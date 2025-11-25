import pandas as pd
import re
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import joblib

DATA_PATH = "./books.csv"

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

# Keep only important columns
required_cols = [
    "book_id",
    "title",
    "original_title",
    "authors",
    "original_publication_year",
    "average_rating",
    "ratings_count",
    "image_url"
]

df = df[required_cols].dropna()

# Create combined text feature

def combine_text(row):
    return f"{row['title']} {row['authors']} {row['original_publication_year']} rating {row['average_rating']}"

df["combined_text"] = df.apply(combine_text, axis=1)

# Clean text

def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

df["combined_text_clean"] = df["combined_text"].apply(clean_text)

# TF-IDF Vectorization

print("Vectorizing text with TF-IDF...")
vectorizer = TfidfVectorizer(stop_words="english", max_features=50000)
tfidf_matrix = vectorizer.fit_transform(df["combined_text_clean"])

# Train KNN model

print("Training KNN model...")
knn_model = NearestNeighbors(
    n_neighbors=11,
    metric="cosine",
    algorithm="brute"
)
knn_model.fit(tfidf_matrix)

# Save models

print("Saving models...")

os.makedirs("models", exist_ok=True)

joblib.dump(vectorizer, "models/vectorizer.pkl")
joblib.dump(knn_model, "models/knn_model.pkl")
df.to_pickle("models/books_df.pkl")

print("\n🎉 Training complete!")
print("Models saved inside /models folder:")
print(" - vectorizer.pkl")
print(" - knn_model.pkl")
print(" - books_df.pkl")
