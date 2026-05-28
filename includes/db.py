import sqlite3
import os
from config.config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database from the SQL schema file."""
    conn = get_db_connection()
    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'database.sql')
    with open(sql_path, 'r') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()

def query_db(query, args=(), one=False):
    """
    Execute a query.
    SELECT  → returns row(s) or None
    INSERT/UPDATE/DELETE → commits and returns lastrowid (or rowcount for non-INSERT)
    """
    conn = get_db_connection()
    try:
        cursor = conn.execute(query, args)
        stripped = query.strip().upper()
        if stripped.startswith('SELECT'):
            results = cursor.fetchall()
            return (results[0] if results else None) if one else results
        else:
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()
