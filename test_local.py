"""
test_local.py — Step-by-step local testing for the Post-Doc Finder.

Run individual tests with:
    python test_local.py env         → check all env vars are loaded
    python test_local.py serper      → fire one Serper query, print results
    python test_local.py exa         → fire one Exa query, print results
    python test_local.py rss         → fetch one RSS feed
    python test_local.py process     → run full scoring on 3 mock vacancies
    python test_local.py supabase    → fetch existing links from Supabase
    python test_local.py telegram    → send a test message to your Telegram chat
    python test_local.py full        → run the FULL pipeline (all 17 sources)
"""

import asyncio
import sys
import httpx

# ──────────────────────────────────────────────────────────────
# TEST: env
# ──────────────────────────────────────────────────────────────
def test_env():
    print("\n🔧 Testing environment variables...\n")
    try:
        from app.config import settings
        print(f"  ✅ SUPABASE_PROJECT_REF  : {settings.SKILLEDGEUP_SUPABASE_PROJECT_REF}")
        print(f"  ✅ SUPABASE_KEY          : ...{settings.SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY[-8:]}")
        print(f"  ✅ SERPER_API_KEY        : ...{settings.SERPER_API_KEY[-6:]}")
        print(f"  ✅ SERPAPI_API_KEY       : ...{settings.SERPAPI_API_KEY[-6:]}")
        print(f"  ✅ EXA_API_KEY           : ...{settings.EXA_API_KEY[-6:]}")
        print(f"  ✅ TELEGRAM_BOT_TOKEN    : ...{settings.TELEGRAM_POSTDOC_BOT_TOKEN[-8:]}")
        print(f"  ✅ TELEGRAM_CHAT_ID      : {settings.TELEGRAM_POSTDOC_CHAT_ID}")
        print("\n✅ All environment variables loaded successfully.")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        print("   → Make sure your .env file exists and all variables are filled in.")


# ──────────────────────────────────────────────────────────────
# TEST: serper
# ──────────────────────────────────────────────────────────────
async def test_serper():
    print("\n🔍 Testing Serper API (1 query)...\n")
    from app.config import settings
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
                json={"q": "site:euraxess.ec.europa.eu/jobs postdoc", "num": 5, "gl": "us", "hl": "en"},
                timeout=15.0,
            )
            data = res.json()
            results = data.get("organic", [])
            print(f"  Status: {res.status_code}")
            print(f"  Results returned: {len(results)}")
            for r in results[:3]:
                print(f"\n  📌 {r.get('title', 'N/A')}")
                print(f"     {r.get('link', 'N/A')}")
            print("\n✅ Serper is working." if results else "\n⚠️  Serper returned 0 results (check API key or quota).")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")


# ──────────────────────────────────────────────────────────────
# TEST: exa
# ──────────────────────────────────────────────────────────────
async def test_exa():
    print("\n🔍 Testing Exa AI (1 query)...\n")
    from app.config import settings
    from datetime import datetime, timedelta
    try:
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")
        async with httpx.AsyncClient() as client:
            res = await client.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": settings.EXA_API_KEY, "Content-Type": "application/json"},
                json={
                    "query": "Open postdoctoral positions in graduate employability or labour market research",
                    "numResults": 5,
                    "startPublishedDate": start_date,
                    "contents": {"highlights": {"maxCharacters": 200}},
                },
                timeout=15.0,
            )
            data = res.json()
            results = data.get("results", [])
            print(f"  Status: {res.status_code}")
            print(f"  Results returned: {len(results)}")
            for r in results[:3]:
                print(f"\n  📌 {r.get('title', 'N/A')}")
                print(f"     {r.get('url', 'N/A')}")
            print("\n✅ Exa is working." if results else "\n⚠️  Exa returned 0 results.")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")


# ──────────────────────────────────────────────────────────────
# TEST: rss
# ──────────────────────────────────────────────────────────────
async def test_rss():
    print("\n📡 Testing RSS feed (HigherEdJobs)...\n")
    import feedparser
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(
                "https://www.higheredjobs.com/rss/categoryFeed.cfm?catID=68",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=15.0,
            )
            feed = feedparser.parse(res.text)
            print(f"  Feed title   : {feed.feed.get('title', 'N/A')}")
            print(f"  Entries found: {len(feed.entries)}")
            for e in feed.entries[:3]:
                print(f"\n  📌 {e.get('title', 'N/A')}")
                print(f"     {e.get('link', 'N/A')}")
            print("\n✅ RSS is working." if feed.entries else "\n⚠️  RSS returned 0 entries.")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")


# ──────────────────────────────────────────────────────────────
# TEST: process
# ──────────────────────────────────────────────────────────────
def test_process():
    print("\n⚙️  Testing processor with mock vacancies...\n")
    from app.models import RawVacancy
    from app.processor import process_vacancies

    mocks = [
        RawVacancy(
            source="Academic Boards",
            title="Postdoctoral Researcher in Graduate Employability — University of Leipzig",
            link="https://uni-leipzig.de/jobs/postdoc-employability",
            snippet="We are hiring a postdoctoral researcher to join our labour market transitions project. Applications are open. Deadline: 30 September 2025.",
        ),
        RawVacancy(
            source="Reddit",
            title="PhD candidate wanted at TU Berlin",
            link="https://reddit.com/r/AskAcademia/phd-candidate-tu-berlin",
            snippet="Doctoral position in mechanical engineering available.",
        ),
        RawVacancy(
            source="RSS HigherEdJobs",
            title="Research Fellow in Workforce Development — Humboldt University Berlin",
            link="https://hu-berlin.de/jobs/research-fellow-workforce",
            snippet="Open position for research fellow. Closing date: 15 October 2025. No German required.",
        ),
    ]

    results = process_vacancies(mocks)
    print(f"  Input : {len(mocks)} raw vacancies")
    print(f"  Output: {len(results)} scored records\n")
    for r in results:
        print(f"  ✅ {r.institution}")
        print(f"     Score        : {r.match_score}/10")
        print(f"     German       : {r.german_required}")
        print(f"     Region       : {r.research_data.get('region_tier')}")
        print(f"     Deadline ISO : {r.deadline}")
        print(f"     Matched      : {r.research_data.get('matched_terms', [])[:5]}")
        print()

    print("✅ Processor working correctly." if results else "⚠️  No records passed the filter — check keyword logic.")


# ──────────────────────────────────────────────────────────────
# TEST: supabase
# ──────────────────────────────────────────────────────────────
async def test_supabase():
    print("\n🗄️  Testing Supabase connection (fetch existing links)...\n")
    from app.supabase_db import get_existing_links
    try:
        async with httpx.AsyncClient() as client:
            links = await get_existing_links(client)
            print(f"  Existing links in DB: {len(links)}")
            for l in list(links)[:5]:
                print(f"    → {l}")
            print("\n✅ Supabase connection working.")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")


# ──────────────────────────────────────────────────────────────
# TEST: telegram
# ──────────────────────────────────────────────────────────────
async def test_telegram():
    print("\n📱 Sending test message to Telegram...\n")
    from app.config import settings
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_POSTDOC_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": settings.TELEGRAM_POSTDOC_CHAT_ID,
                    "text": "SkillEdgeUp Post-Doc Finder - Test message\n\nYour bot is connected and working correctly!\n\nThis was triggered by test_local.py",
                },
                timeout=15.0,
            )
            r.raise_for_status()
            print("✅ Check your Telegram chat for the test message.")
    except Exception as e:
        print(f"\n❌ FAILED: {e}")


# ──────────────────────────────────────────────────────────────
# TEST: full pipeline
# ──────────────────────────────────────────────────────────────
async def test_full():
    print("\n🚀 Running FULL pipeline (this will hit all APIs — takes ~30–60s)...\n")
    import main as m
    await m.main()


# ──────────────────────────────────────────────────────────────
# TEST: dryrun — scrape + score + show all results + send Telegram
#               but DO NOT insert to Supabase (safe to repeat)
# ──────────────────────────────────────────────────────────────
async def test_dryrun():
    print("\n🧪 DRY RUN — scrape all sources, score, preview results, send Telegram digest")
    print("   (nothing will be inserted into Supabase)\n")

    from app.scrapers import scrape_all_sources
    from app.processor import process_vacancies
    from app.telegram_bot import build_digest, send_telegram_alert

    # 1. Scrape
    print("[1/3] Scraping all sources...")
    raw = await scrape_all_sources()
    print(f"      Raw items: {len(raw)}")

    # 2. Process
    print("\n[2/3] Scoring and filtering...")
    candidates = process_vacancies(raw)
    print(f"      Passed filter: {len(candidates)} records\n")

    if not candidates:
        print("  No results passed the filter. Try running again or check your API keys.")
        return

    # 3. Print full detail in terminal
    region_order = ["germany", "europe", "other"]
    grouped: dict = {r: [] for r in region_order}
    for c in candidates:
        region = c.research_data.get("region_tier", "other")
        grouped.setdefault(region, []).append(c)

    region_labels = {"germany": "GERMANY", "europe": "EUROPE", "other": "OTHER (NA/ANZ)"}
    stars_map = lambda s: round(s / 2) * "*"

    print("=" * 70)
    print(f"  SCORED RESULTS — {len(candidates)} total")
    print("=" * 70)

    for region in region_order:
        records = grouped[region]
        if not records:
            continue
        print(f"\n  [{region_labels[region]}] — {len(records)} record(s)")
        print("  " + "-" * 66)
        for i, r in enumerate(sorted(records, key=lambda x: -x.match_score), 1):
            src  = r.research_data.get('source', '?')
            terms = ', '.join(r.research_data.get('matched_terms', [])[:4])
            print(f"  {i:>2}. [{r.match_score}/10] {r.institution}")
            print(f"       Source   : {src}")
            print(f"       German   : {r.german_required}")
            print(f"       Deadline : {r.deadline or 'not found'}")
            print(f"       Matched  : {terms}")
            print(f"       Link     : {r.link}")
            print()

    # 4. Send real Telegram digest (using ALL candidates, not just new ones)
    print("[3/3] Sending digest to Telegram...")
    async with httpx.AsyncClient() as client:
        digest = build_digest(candidates)
        await send_telegram_alert(client, digest)

    print("\nDry run complete. Check your Telegram for the full digest.")
    print("NOTE: Nothing was written to Supabase — run 'full' to do a real insert.")


# ──────────────────────────────────────────────────────────────
# Router
# ──────────────────────────────────────────────────────────────
COMMANDS = {
    "env": (test_env, False),
    "serper": (test_serper, True),
    "exa": (test_exa, True),
    "rss": (test_rss, True),
    "process": (test_process, False),
    "supabase": (test_supabase, True),
    "telegram": (test_telegram, True),
    "full": (test_full, True),
    "dryrun": (test_dryrun, True),
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "env"
    if cmd not in COMMANDS:
        print(f"Unknown command '{cmd}'. Choose from: {', '.join(COMMANDS)}")
        sys.exit(1)

    fn, is_async = COMMANDS[cmd]
    if is_async:
        asyncio.run(fn())
    else:
        fn()
