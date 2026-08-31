"""
pipeline.py — Unified Multi-Source Runner & Matcher for Dr. Faloye.

Runs all local (MLU Halle, Leipzig, Dresden) and national scrapers concurrently,
evaluates opportunities against Dr. Faloye's profile, and outputs a ranked markdown table.
"""

import asyncio
import re
import sys
from datetime import datetime
from typing import List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.scrapers import scrape_all_sources
from app.matcher import calculate_match_score
from app.processor import is_deadline_expired, parse_deadline_iso


def get_commute_info(org: str, location: str, text: str) -> str:
    combined = f"{org} {location} {text}".lower()
    if "halle" in combined:
        return "0 min (Home Institution)"
    if "leipzig" in combined:
        return "22 min (S-Bahn S3/S5)"
    if "jena" in combined:
        return "45 min (Direct RE/ICE)"
    if "magdeburg" in combined:
        return "50 min (Direct RE/IC)"
    if "dresden" in combined:
        return "1h 25m (Direct IC/ICE)"
    if "freiburg" in combined:
        return "Baden-Württemberg (Target Region)"
    if "berlin" in combined:
        return "1h 15m (Direct ICE)"
    return "Germany (Nationwide)"


async def run_pipeline() -> List[Dict[str, Any]]:
    print("=" * 70)
    print("🚀 Starting Unified Regional & National Academic Pipeline")
    print("=" * 70)

    # 1. Scrape all verified sources concurrently
    print("\n[1/3] Collecting opportunities from all verified sources...")
    raw_items = await scrape_all_sources()
    print(f"      Total raw vacancies collected: {len(raw_items)}")

    # 2. Score and filter candidates
    print("\n[2/3] Scoring and matching against Dr. Faloye's profile...")
    qualified: List[Dict[str, Any]] = []
    seen_links = set()

    for item in raw_items:
        link = (item.link or "").split("?")[0].rstrip("/")
        if not link or link in seen_links:
            continue
        seen_links.add(link)

        # Evaluate against profile criteria
        scored = calculate_match_score(item)
        score_pct = scored["match_percentage"]

        # Only keep moderate and high matches (>= 45%)
        if score_pct < 45:
            continue

        # Check deadline status
        full_text = f"{item.title} {item.snippet}"
        deadline_iso = parse_deadline_iso(full_text)
        if is_deadline_expired(deadline_iso):
            continue

        commute = get_commute_info(scored.get("organization", ""), "", full_text)
        scored["commute"] = commute
        scored["deadline_iso"] = deadline_iso or "Open / Unstated"
        qualified.append(scored)

    # 3. Sort by match percentage descending
    qualified.sort(key=lambda x: -x["match_percentage"])
    print(f"      Total qualified opportunities: {len(qualified)}")

    # 4. Generate Markdown Table
    print("\n[3/3] Generating Ranked Match Table...\n")
    headers = ["Rank", "Match", "Title", "Institution / Commute", "Deadline", "Pay Grade", "Key Match Tags", "Official Link"]
    rows = []

    for idx, q in enumerate(qualified, 1):
        match_badge = f"**{q['match_percentage']}%**"
        title = q["title"][:50] + ("..." if len(q["title"]) > 50 else "")
        org_commute = f"**{q['organization'][:30]}**<br>_{q['commute']}_"
        deadline = q["deadline_iso"]
        pay = "TV-L E 13" if "13" in q.get("raw_text", "") else "TV-L / Postdoc"
        tags = ", ".join(q.get("matched_keywords", [])[:3])
        link = f"[Apply ↗]({q['url']})"
        rows.append(f"| {idx} | {match_badge} | {title} | {org_commute} | {deadline} | {pay} | `{tags}` | {link} |")

    table_md = "| " + " | ".join(headers) + " |\n"
    table_md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    table_md += "\n".join(rows)

    print(table_md)

    # Save output report
    with open("ranked_opportunities.md", "w", encoding="utf-8") as f:
        f.write("# SkillEdgeUp Post-Doc & Academic Ranked Opportunities\n\n")
        f.write(f"Generated: {datetime.now().strftime('%d %b %Y, %H:%M CET')}\n\n")
        f.write(table_md)
    print("\n✅ Ranked opportunities saved to 'ranked_opportunities.md'")

    return qualified


if __name__ == "__main__":
    asyncio.run(run_pipeline())
