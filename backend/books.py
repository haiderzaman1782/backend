from fastapi import APIRouter
import psycopg2

router = APIRouter()


@router.get("/books")
def fetch_books():
    conn = psycopg2.connect(
        dbname="Books-recommendation-system",
        user="postgres",
        password="Strong123",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books LIMIT 1000")
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    result = [dict(zip(columns, row)) for row in rows]
    cursor.close()
    conn.close()
    return result

