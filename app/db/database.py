import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(__file__).parent.parent.parent / "blackbox.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    return conn


def create_api_key(key_hash: str, name: str) -> int:
    timestamp = datetime.now(timezone.utc).isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO api_keys (key_hash, name, created_at, revoked) VALUES (?, ?, ?, 0)",
        (key_hash, name, timestamp)
    )
    
    api_key_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return api_key_id


def get_api_key_count() -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM api_keys")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_hash TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            revoked INTEGER NOT NULL DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api_key_id INTEGER,
            endpoint TEXT NOT NULL,
            model TEXT NOT NULL,
            tokens_used INTEGER,
            latency_ms INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


def log_request(api_key_id: int, endpoint: str, model: str, tokens_used: int | None, latency_ms: int):
    timestamp = datetime.now(timezone.utc).isoformat()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO requests (api_key_id, endpoint, model, tokens_used, latency_ms, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (api_key_id, endpoint, model, tokens_used, latency_ms, timestamp)
    )
    
    conn.commit()
    conn.close()
