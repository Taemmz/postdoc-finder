"""supabase_db.py — Supabase REST API interactions."""

import httpx
from typing import List, Set

from app.config import settings
from app.models import PostdocRecord
from app.processor import sanitize_job_url

_BASE_URL = f"https://{settings.SKILLEDGEUP_SUPABASE_PROJECT_REF}.supabase.co/rest/v1"

_HEADERS = {
    "apikey": settings.SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {settings.SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


async def get_existing_links(client: httpx.AsyncClient) -> Set[str]:
    """Return the set of all links already stored in Supabase (sanitized)."""
    try:
        res = await client.get(
            f"{_BASE_URL}/skilledgeup_postdoc?select=link",
            headers=_HEADERS,
            timeout=15.0,
        )
        res.raise_for_status()
        return {sanitize_job_url(row["link"]) for row in res.json() if "link" in row}
    except Exception as exc:
        print(f"  [supabase] Warning: could not fetch existing links — {exc}")
        return set()


async def insert_postdocs(client: httpx.AsyncClient, records: List[PostdocRecord]) -> None:
    """Bulk-insert new records into Supabase (skips duplicates via UNIQUE constraint)."""
    if not records:
        return
    payload = [r.model_dump() for r in records]
    try:
        res = await client.post(
            f"{_BASE_URL}/skilledgeup_postdoc",
            headers=_HEADERS,
            json=payload,
            timeout=20.0,
        )
        res.raise_for_status()
        print(f"  [supabase] Inserted {len(records)} records.")
    except Exception as exc:
        print(f"  [supabase] Error inserting records — {exc}")


async def log_activity(client: httpx.AsyncClient, count: int) -> None:
    """Write a run summary to the activity log table."""
    try:
        await client.post(
            f"{_BASE_URL}/skilledgeup_activity_log",
            headers={k: v for k, v in _HEADERS.items() if k != "Prefer"},
            json={
                "staff_id": None,
                "staff_name": "System (Python Post-Doc Finder)",
                "action": f"Post-Doc Finder found {count} new opportunities",
                "entity_type": "postdoc",
                "entity_id": None,
                "metadata": {"count": count},
            },
            timeout=15.0,
        )
    except Exception as exc:
        print(f"  [supabase] Warning: activity log failed — {exc}")
