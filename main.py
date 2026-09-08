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

from app.dedup import generate_canonical_key, generate_fingerprint, normalize_url
from app.processor import enrich_missing_deadlines, process_vacancies, sanitize_job_url
from app.scrapers import scrape_all_sources
from app.supabase_db import get_existing_signatures, insert_postdocs, log_activity
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

    # 3. Deduplicate against Supabase, insert fresh records (Permanent Suppression)
    print("\n[3/4] Checking against historical Supabase memory (all statuses)...")
    async with httpx.AsyncClient() as client:
        existing_links, existing_fps, existing_canonicals = await get_existing_signatures(client)
        fresh_records = []
        seen_links_this_run = set()
        seen_canonicals_this_run = set()

        for c in candidates:
            clean_url = sanitize_job_url(c.link)
            norm_url = normalize_url(c.link)
            c.link = clean_url

            title = c.research_focus
            org = c.institution
            deadline = c.deadline or ""

            fp_with_deadline = generate_fingerprint(title, org, deadline)
            fp_no_deadline = generate_fingerprint(title, org, "")
            canonical_key = generate_canonical_key(title, org)

            # Layer 1: In-run deduplication
            if clean_url in seen_links_this_run or canonical_key in seen_canonicals_this_run:
                continue

            # Layer 2: Historical Supabase suppression (regardless of status: new, interested, applied, rejected, not_relevant)
            if (
                clean_url in existing_links
                or (norm_url and norm_url in existing_links)
                or fp_with_deadline in existing_fps
                or fp_no_deadline in existing_fps
                or canonical_key in existing_canonicals
            ):
                continue

            seen_links_this_run.add(clean_url)
            if norm_url:
                seen_links_this_run.add(norm_url)
            seen_canonicals_this_run.add(canonical_key)
            fresh_records.append(c)

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
