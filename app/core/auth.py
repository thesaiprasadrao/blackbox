import hashlib
import secrets

from fastapi import Depends, HTTPException, Header

from app.db.database import get_connection, touch_api_key


def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def verify_api_key(authorization: str = Header(None)) -> int:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    api_key = authorization.replace("Bearer ", "", 1)
    
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    
    key_hash = hash_api_key(api_key)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, revoked FROM api_keys WHERE key_hash = ?",
        (key_hash,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    api_key_id, revoked = row
    
    if revoked:
        raise HTTPException(status_code=403, detail="API key has been revoked")

    # Record that this key was just used
    touch_api_key(api_key_id)

    return api_key_id