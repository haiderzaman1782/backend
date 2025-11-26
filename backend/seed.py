import os
import psycopg2
import pandas as pd
from psycopg2.extras import execute_values

# =========================
# CONFIGURATION
# =========================
CSV_FILE = "../books.csv"
TABLE_NAME = "books"

# LOAD CSV
df = pd.read_csv(CSV_FILE)


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


# Connect and create table
try:
    conn = _connect()
    conn.autocommit = True
    cursor = conn.cursor()
    print("Connected to PostgreSQL successfully!")
except Exception as e:
    print("Error connecting to PostgreSQL:", e)
    raise


# Create table if not exists
columns_with_types = ", ".join([f"{col} TEXT" for col in df.columns])
create_table_query = f"""
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    {columns_with_types}
);
"""

cursor.execute(create_table_query)
print(f"Table '{TABLE_NAME}' ready.")


# Insert data using execute_values for performance
cols = list(df.columns)
values = [tuple(x) for x in df[cols].fillna("").values]
insert_query = f"INSERT INTO {TABLE_NAME} ({', '.join(cols)}) VALUES %s"
execute_values(cursor, insert_query, values)

print(f"Inserted {len(values)} rows into '{TABLE_NAME}' successfully!")

# Close connection
cursor.close()
conn.close()
print("PostgreSQL connection closed.")
