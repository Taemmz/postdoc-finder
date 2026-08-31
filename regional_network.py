import sqlite3
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.scrapers import (
    scrape_mlu_halle,
    scrape_uni_leipzig,
    scrape_tu_dresden,
    scrape_uni_jena,
    scrape_ovgu_magdeburg,
)
from app.scrapers_haw import (
    scrape_eah_jena,
    scrape_h2_magdeburg,
    scrape_htwk_leipzig,
    scrape_hs_merseburg,
)

# --- DATABASE SETUP ---
DB_FILE = "opportunities.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seen_jobs (
            url TEXT PRIMARY KEY,
            title TEXT,
            organization TEXT,
            location TEXT,
            score INTEGER,
            seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# --- SCORING ENGINE ---

CRITERIA = {
    "domains": ([
        "hochschuldidaktik", "didaktik", "lehrinnovation", "qualitätsmanagement lehre",
        "educational psychology", "pädagogische psychologie", "erziehungswissenschaft",
        "curriculum", "wissenschaftsmanagement", "inklusion", "heterogenität", "schulentwicklung"
    ], 45),
    "methods": ([
        "qualitative forschung", "qualitative methods", "grounded theory", "inhaltsanalyse",
        "interview", "mixed methods", "evaluation", "bildungsforschung"
    ], 25),
    "future_tech": ([
        "künstliche intelligenz", "artificial intelligence", "ki in der lehre", "digitalisierung", "edtech"
    ], 15),
    "seniority": ([
        "e 13", "e13", "e 14", "tv-l", "postdoc", "postdoktorand", "research associate"
    ], 15)
}

def score_job(job: Dict[str, Any]) -> int:
    search_text = f"{job['title']} {job.get('organization', '')} {job.get('raw_text', '')}".lower()
    score = 0
    for keywords, weight in CRITERIA.values():
        if any(kw in search_text for kw in keywords):
            score += weight
    return min(score, 100)

# --- TELEGRAM DISPATCH ---

def notify(job: Dict[str, Any]):
    token = os.getenv("TELEGRAM_POSTDOC_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_POSTDOC_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print(f"🔔 [MATCH {job['score']}%] {job['title']} @ {job['organization']} ({job['location']})")
        return
    
    text = (
        f"🎯 *New Academic Opportunity ({job['score']}%)*\n\n"
        f"📌 *Role:* {job['title']}\n"
        f"🏛 *Employer:* {job['organization']}\n"
        f"📍 *Location:* {job['location']}\n"
        f"📅 *Deadline:* {job['deadline']}\n"
        f"💰 *Grade:* {job['pay_grade']}\n\n"
        f"🔗 [View Vacancy]({job['url']})"
    )
    try:
        httpx.post(f"https://api.telegram.org/bot{token}/sendMessage", json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception as e:
        print(f"Failed to dispatch alert: {e}")

# --- EXECUTION ---

def run():
    init_db()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    print("=" * 70)
    print("🚀 Fetching vacancies across 9 Regional Universities & HAWs...")
    print("   [Halle, Leipzig, Dresden, Jena, Magdeburg, Merseburg]")
    print("=" * 70)
    all_jobs = []
    
    halle_jobs = scrape_mlu_halle()
    print(f"  [MLU Halle] Extracted: {len(halle_jobs)}")
    all_jobs.extend(halle_jobs)

    leipzig_jobs = scrape_uni_leipzig()
    print(f"  [Uni Leipzig] Extracted: {len(leipzig_jobs)}")
    all_jobs.extend(leipzig_jobs)

    dresden_jobs = scrape_tu_dresden()
    print(f"  [TU Dresden] Extracted: {len(dresden_jobs)}")
    all_jobs.extend(dresden_jobs)

    jena_jobs = scrape_uni_jena()
    print(f"  [Uni Jena] Extracted: {len(jena_jobs)}")
    all_jobs.extend(jena_jobs)

    ovgu_jobs = scrape_ovgu_magdeburg()
    print(f"  [OVGU Magdeburg] Extracted: {len(ovgu_jobs)}")
    all_jobs.extend(ovgu_jobs)

    # ── Applied Sciences & Specialist Academies (HAWs) ────────────────────────
    eah_jobs = scrape_eah_jena()
    print(f"  [EAH Jena] Extracted: {len(eah_jobs)}")
    all_jobs.extend(eah_jobs)

    h2_jobs = scrape_h2_magdeburg()
    print(f"  [HS Magdeburg-Stendal] Extracted: {len(h2_jobs)}")
    all_jobs.extend(h2_jobs)

    htwk_jobs = scrape_htwk_leipzig()
    print(f"  [HTWK Leipzig] Extracted: {len(htwk_jobs)}")
    all_jobs.extend(htwk_jobs)

    merseburg_jobs = scrape_hs_merseburg()
    print(f"  [HS Merseburg] Extracted: {len(merseburg_jobs)}")
    all_jobs.extend(merseburg_jobs)

    new_matches = 0
    print("\n🔍 Scoring vacancies and checking local database...")
    for job in all_jobs:
        url = job.get("url")
        if not url: continue

        cur.execute("SELECT 1 FROM seen_jobs WHERE url = ?", (url,))
        if cur.fetchone():
            continue

        score = score_job(job)
        job["score"] = score

        cur.execute(
            "INSERT INTO seen_jobs (url, title, organization, location, score) VALUES (?, ?, ?, ?, ?)",
            (url, job["title"], job["organization"], job["location"], score)
        )
        conn.commit()

        if score >= 45:
            notify(job)
            new_matches += 1

    conn.close()
    print(f"\n✅ Finished! Extracted {len(all_jobs)} regional vacancies across 9 universities & HAWs.")
    print(f"   Found and processed {new_matches} matching opportunities (>= 45%).")

if __name__ == "__main__":
    run()
