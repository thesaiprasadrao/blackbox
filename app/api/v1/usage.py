"""
GET /v1/usage

Returns a filtered list of logged requests. Useful for seeing how much
each API key has used, which models are being hit, etc.

Query params (all optional):
  - api_key_id : filter by key ID
  - model      : filter by model name
  - date_from  : ISO date string, e.g. "2026-05-01"
  - date_to    : ISO date string, e.g. "2026-05-07"
  - limit      : max rows to return (default 100, max 1000)
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.auth import verify_api_key
from app.db.database import get_usage

router = APIRouter()


class UsageRecord(BaseModel):
    id: int
    api_key_id: int | None
    endpoint: str
    model: str
    tokens_used: int | None
    latency_ms: int
    timestamp: str


class UsageResponse(BaseModel):
    count: int
    records: list[UsageRecord]


@router.get("/v1/usage", response_model=UsageResponse)
def usage(
    api_key_id: int | None = Query(default=None, description="Filter by API key ID"),
    model: str | None = Query(default=None, description="Filter by model name"),
    date_from: str | None = Query(default=None, description="Start date (YYYY-MM-DD)"),
    date_to: str | None = Query(default=None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(default=100, le=1000, description="Max rows to return"),
    _api_key_id: int = Depends(verify_api_key),   # auth check — must have a valid key
):
    records = get_usage(
        api_key_id=api_key_id,
        model=model,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return UsageResponse(count=len(records), records=[UsageRecord(**r) for r in records])
