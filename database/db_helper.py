import sqlite3
import pandas as pd
from pathlib import Path

# Path to SQLite database file in the project root
DB_PATH = Path(__file__).resolve().parent.parent / "expense_ledger.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT,
            Segment TEXT,
            Merchant_Source TEXT,
            Amount REAL,
            Channel TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_transactions_to_db(df):
    init_db()
    conn = get_connection()
    df.to_sql("transactions", conn, if_exists="append", index=False)
    conn.close()

def fetch_transactions():
    init_db()
    conn = get_connection()
    try:
        df = pd.read_sql("SELECT Date, Segment, Merchant_Source, Amount, Channel FROM transactions", conn)
        return df
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        return pd.DataFrame(columns=["Date", "Segment", "Merchant_Source", "Amount", "Channel"])
    finally:
        conn.close()