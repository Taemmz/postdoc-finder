"""purge_not_relevant.py - Safely archive rejected / not_relevant records to skilledgeup_postdoc_archive."""
import asyncio
import httpx
from collections import Counter
from app.config import settings

async def archive_not_relevant(dry_run: bool = True):
    """
    Safely archives records marked as 'not_relevant' to the archive table.
    Set dry_run=False to execute. Never performs unlogged hard deletes.
    """
    headers = {
        "apikey": settings.SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    base_url = f"https://{settings.SKILLEDGEUP_SUPABASE_PROJECT_REF}.supabase.co/rest/v1"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Fetch records marked as not_relevant
        res = await client.get(
            f"{base_url}/skilledgeup_postdoc?status=eq.not_relevant",
            headers=headers,
        )
        res.raise_for_status()
        records = res.json()
        print(f"Found {len(records)} 'not_relevant' records.")

        if not records:
            print("No 'not_relevant' records to archive.")
            return

        if dry_run:
            print("[DRY RUN] Would archive the following records without deleting:")
            for r in records[:5]:
                print(f"  - [{r.get('id')}] {r.get('title', 'N/A')} @ {r.get('institution', 'N/A')} (Reason: {r.get('not_relevant_reason', 'N/A')})")
            print("To execute archiving, run with dry_run=False.")
            return

        # 2. Insert into archive table first (preserving full audit history)
        archive_res = await client.post(
            f"{base_url}/skilledgeup_postdoc_archive",
            headers=headers,
            json=records,
        )
        if archive_res.status_code not in (200, 201):
            print(f"Error archiving records: {archive_res.text}")
            return

        archived_count = len(archive_res.json())
        print(f"Successfully archived {archived_count} records into 'skilledgeup_postdoc_archive'.")

        # 3. Log to activity log
        await client.post(
            f"{base_url}/skilledgeup_activity_log",
            headers={k: v for k, v in headers.items() if k != "Prefer"},
            json={
                "staff_id": None,
                "staff_name": "System (Archive Utility)",
                "action": f"Archived {archived_count} not_relevant records to archive table",
                "entity_type": "postdoc",
                "entity_id": None,
                "metadata": {"count": archived_count, "archived_ids": [r.get("id") for r in records]},
            },
        )
        print("Logged action to 'skilledgeup_activity_log'.")

if __name__ == "__main__":
    # Default is dry-run mode for safety
    asyncio.run(archive_not_relevant(dry_run=True))

