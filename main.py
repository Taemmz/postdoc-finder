"""
main.py — Entrypoint for the SkillEdgeUp Post-Doc Finder.

Run manually:
    python main.py

Coolify scheduled task (Daily 08:00):
    cron: 0 8 * * *
    command: python main.py
"""

import asyncio
import httpx

from app.scrapers import scrape_all_sources
from app.processor import enrich_missing_deadlines, process_vacancies
from app.supabase_db import get_existing_links, insert_postdocs, log_activity
from app.telegram_bot import build_digest, send_pipeline_summary, send_telegram_alert


async def main() -> None:
    print("=" * 60)
    print("SkillEdgeUp Post-Doc Finder — starting run")
    print("=" * 60)

    # 1. Scrape all 18 sources concurrently
    print("\n[1/4] Scraping all sources...")
    raw_vacancies = await scrape_all_sources()
    print(f"      Raw items collected: {len(raw_vacancies)}")

    # 2. Filter, score, and deduplicate
    print("\n[2/4] Processing and scoring candidates...")
    candidates = process_vacancies(raw_vacancies)
    print(f"      Valid candidates after filtering: {len(candidates)}")

    # 2b. Lazy deep fetch for missing deadlines
    print("\n[2b/4] Enriching missing deadlines via deep fetch...")
    candidates = await enrich_missing_deadlines(candidates)
    print(f"      Candidates after deadline enrichment: {len(candidates)}")

    # 3. Deduplicate against Supabase, insert fresh records
    print("\n[3/4] Checking against Supabase and inserting new records...")
    async with httpx.AsyncClient() as client:
        existing_links = await get_existing_links(client)
        fresh_records = [c for c in candidates if c.link not in existing_links]
        print(f"      New records to insert: {len(fresh_records)}")

        if fresh_records:
            await insert_postdocs(client, fresh_records)
            await log_activity(client, len(fresh_records))

        # 4. Build and send clean Telegram summary
        print("\n[4/4] Sending Telegram summary card...")
        await send_pipeline_summary(
            client,
            raw_count=len(raw_vacancies),
            valid_count=len(candidates),
            inserted_count=len(fresh_records),
        )

    print("\n" + "=" * 60)
    print("Run complete.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
