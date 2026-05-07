"""
/v1/keys — API key management

All endpoints here require a valid API key (any key works to call GET /keys,
but only the admin pattern is enforced at the app level for now — future
improvement: add an "is_admin" flag to the api_keys table).

POST   /v1/keys          — create a new key (returns the raw key once, never again)
GET    /v1/keys          — list all keys (metadata only, no raw key hashes)
DELETE /v1/keys/{key_id} — revoke a key by its ID
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import generate_api_key, hash_api_key, verify_api_key
from app.db.database import create_api_key, list_api_keys, revoke_api_key

router = APIRouter()


# ── Request / Response models ─────────────────────────────────────────────────

class CreateKeyRequest(BaseModel):
    name: str   # human-readable label, e.g. "my-laptop" or "ci-bot"


class CreateKeyResponse(BaseModel):
    id: int
    name: str
    key: str    # raw key — shown ONCE here, never stored, never returned again


class KeyInfo(BaseModel):
    id: int
    name: str
    created_at: str
    revoked: bool
    last_used_at: str | None


class ListKeysResponse(BaseModel):
    keys: list[KeyInfo]


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/v1/keys", response_model=CreateKeyResponse)
def create_key(
    body: CreateKeyRequest,
    api_key_id: int = Depends(verify_api_key),   # must be authenticated to create keys
):
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    new_id = create_api_key(key_hash, body.name)

    # Return the raw key here — this is the only time it's ever visible
    return CreateKeyResponse(id=new_id, name=body.name, key=raw_key)


@router.get("/v1/keys", response_model=ListKeysResponse)
def get_keys(api_key_id: int = Depends(verify_api_key)):
    keys = list_api_keys()
    return ListKeysResponse(keys=[KeyInfo(**k) for k in keys])


@router.delete("/v1/keys/{key_id}")
def delete_key(
    key_id: int,
    api_key_id: int = Depends(verify_api_key),
):
    # Prevent revoking your own key — that would lock the caller out immediately
    if key_id == api_key_id:
        raise HTTPException(status_code=400, detail="Cannot revoke the key you are currently using")

    success = revoke_api_key(key_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"API key {key_id} not found")

    return {"message": f"Key {key_id} has been revoked"}
