"""purge_not_relevant.py - Purge rejected / not_relevant records from Supabase."""
import asyncio
import httpx
from collections import Counter
from app.config import settings

async def purge_not_relevant():
    headers = {
        "apikey": settings.SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {settings.SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY}",
        "Prefer": "return=representation",
    }
    base_url = f"https://{settings.SKILLEDGEUP_SUPABASE_PROJECT_REF}.supabase.co/rest/v1/skilledgeup_postdoc"

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.get(f"{base_url}?select=id,status", headers=headers)
        res.raise_for_status()
        counts = Counter(r["status"] for r in res.json())
        print("Current records in Supabase:", counts)

        if counts.get("not_relevant", 0) == 0:
            print("No 'not_relevant' records to purge.")
            return

        del_res = await client.delete(f"{base_url}?status=eq.not_relevant", headers=headers)
        del_res.raise_for_status()
        purged = len(del_res.json())
        print(f"Purged {purged} not_relevant records.")

        res2 = await client.get(f"{base_url}?select=id,status", headers=headers)
        res2.raise_for_status()
        print("Remaining records in Supabase:", Counter(r["status"] for r in res2.json()))

if __name__ == "__main__":
    asyncio.run(purge_not_relevant())
