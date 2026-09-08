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


from app.dedup import generate_canonical_key, generate_fingerprint, normalize_url


async def get_existing_signatures(client: httpx.AsyncClient) -> tuple[Set[str], Set[str], Set[str]]:
    """
    Fetches ALL historical opportunities from Supabase regardless of status
    ('new', 'interested', 'applied', 'rejected', 'not_relevant', etc.).
    Returns:
      - existing_links: Set of sanitized & normalized URLs
      - existing_fingerprints: Set of SHA-256 content hashes (title|org|deadline)
      - existing_canonical_keys: Set of semantic canonical keys (title|org)
    """
    try:
        res = await client.get(
            f"{_BASE_URL}/skilledgeup_postdoc?select=link,research_focus,institution,deadline",
            headers=_HEADERS,
            timeout=20.0,
        )
        res.raise_for_status()
        rows = res.json()

        links = set()
        fingerprints = set()
        canonical_keys = set()

        for row in rows:
            raw_link = row.get("link", "")
            title = row.get("research_focus", "")
            org = row.get("institution", "")
            deadline = row.get("deadline", "")

            if raw_link:
                links.add(sanitize_job_url(raw_link))
                clean_norm = normalize_url(raw_link)
                if clean_norm:
                    links.add(clean_norm)
            if title and org:
                fingerprints.add(generate_fingerprint(title, org, deadline or ""))
                fingerprints.add(generate_fingerprint(title, org, ""))
                canonical_keys.add(generate_canonical_key(title, org))

        return links, fingerprints, canonical_keys
    except Exception as exc:
        print(f"  [supabase] Warning: could not fetch historical signatures — {exc}")
        return set(), set(), set()


async def get_existing_links(client: httpx.AsyncClient) -> Set[str]:
    """Return the set of all links already stored in Supabase (sanitized)."""
    links, _, _ = await get_existing_signatures(client)
    return links



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
