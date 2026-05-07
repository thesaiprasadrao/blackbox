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
            revoked INTEGER NOT NULL DEFAULT 0,
            last_used_at TEXT         -- updated every time the key is used to auth a request
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


def touch_api_key(api_key_id: int):
    """Update last_used_at for a key every time it successfully authenticates."""
    timestamp = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
        (timestamp, api_key_id)
    )
    conn.commit()
    conn.close()


def revoke_api_key(api_key_id: int) -> bool:
    """Mark a key as revoked. Returns False if the key doesn't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE api_keys SET revoked = 1 WHERE id = ?", (api_key_id,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def list_api_keys() -> list[dict]:
    """Return all keys as a list of dicts (no raw key hashes exposed)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, created_at, revoked, last_used_at FROM api_keys ORDER BY id"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": row[0],
            "name": row[1],
            "created_at": row[2],
            "revoked": bool(row[3]),
            "last_used_at": row[4],
        }
        for row in rows
    ]


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


def get_usage(
    api_key_id: int | None = None,
    model: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """
    Query the requests log with optional filters.
    All date strings should be ISO-8601 (e.g. "2026-05-01").
    Results are newest-first, capped at `limit` rows.
    """
    query = "SELECT id, api_key_id, endpoint, model, tokens_used, latency_ms, timestamp FROM requests WHERE 1=1"
    params: list = []

    if api_key_id is not None:
        query += " AND api_key_id = ?"
        params.append(api_key_id)
    if model is not None:
        query += " AND model = ?"
        params.append(model)
    if date_from is not None:
        query += " AND timestamp >= ?"
        params.append(date_from)
    if date_to is not None:
        query += " AND timestamp <= ?"
        params.append(date_to + "T23:59:59")   # include the full end day

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "api_key_id": row[1],
            "endpoint": row[2],
            "model": row[3],
            "tokens_used": row[4],
            "latency_ms": row[5],
            "timestamp": row[6],
        }
        for row in rows
    ]
