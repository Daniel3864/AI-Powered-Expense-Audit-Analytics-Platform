import sqlite3
import pandas as pd
import os
from pinecone import Pinecone

DB_PATH = "expenses.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS master_segments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            segment_name TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            merchant TEXT,
            amount REAL,
            segment_name TEXT,
            status TEXT
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM master_segments")
    if cursor.fetchone()[0] == 0:
        default_segments = [('Travel',), ('Meals & Entertainment',), ('Software & IT',), ('Office Supplies',)]
        cursor.executemany("INSERT INTO master_segments (segment_name) VALUES (?)", default_segments)
    conn.commit()
    conn.close()

def get_segments():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT segment_name FROM master_segments", conn)
    conn.close()
    return df['segment_name'].tolist()

def auto_update_segment(new_segment_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO master_segments (segment_name) VALUES (?)", (new_segment_name,))
        conn.commit()
    finally:
        conn.close()

def fetch_transactions():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM transactions", conn)
    conn.close()
    return df

def sync_new_segment_to_vector_db(segment_name):
    try:
        api_key = os.getenv("PINECONE_API_KEY", "your-api-key")
        pc = Pinecone(api_key=api_key)
        index = pc.Index("expense-policy-index")
        dummy_vector = [0.01] * 1536
        index.upsert(
            vectors=[
                {
                    "id": f"segment_{segment_name}",
                    "values": dummy_vector,
                    "metadata": {"text": f"Policy rules and classification context for segment: {segment_name}"}
                }
            ]
        )
        return True
    except Exception as e:
        print(f"Vector sync skipped/failed: {e}")
        return False