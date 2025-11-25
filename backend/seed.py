import psycopg2
import pandas as pd

# =========================
# CONFIGURATION
# =========================
DB_NAME = "Books-recommendation-system"
DB_USER = "postgres"
DB_PASSWORD = "Strong123"
DB_HOST = "localhost"  # or your host
DB_PORT = "5432"

CSV_FILE = "../books.csv"
TABLE_NAME = "books"

# =========================
# LOAD CSV
# =========================
df = pd.read_csv(CSV_FILE)

# =========================
# CONNECT TO POSTGRES
# =========================
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cursor = conn.cursor()
    print("Connected to PostgreSQL successfully!")
except Exception as e:
    print("Error connecting to PostgreSQL:", e)
    exit()

# =========================
# CREATE TABLE IF NOT EXISTS
# =========================
columns_with_types = ", ".join([f"{col} TEXT" for col in df.columns])
create_table_query = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    {columns_with_types}
);
"""

cursor.execute(create_table_query)
print(f"Table '{TABLE_NAME}' ready.")

# =========================
# INSERT DATA INTO TABLE
# =========================
for i, row in df.iterrows():
    placeholders = ", ".join(["%s"] * len(row))
    insert_query = f"INSERT INTO {TABLE_NAME} ({', '.join(df.columns)}) VALUES ({placeholders})"
    cursor.execute(insert_query, tuple(row))

print(f"Inserted {len(df)} rows into '{TABLE_NAME}' successfully!")

# =========================
# CLOSE CONNECTION
# =========================
cursor.close()
conn.close()
print("PostgreSQL connection closed.")
