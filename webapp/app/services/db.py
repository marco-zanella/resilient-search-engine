import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv("POSTGRES_DB", "search-engine"),
        user=os.getenv("POSTGRES_USER", "user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432)
    )