# SkillEdgeUp Post-Doc Finder 🔬

An automated post-doctoral vacancy aggregator for **Dr. Faloye**, targeting positions in graduate employability, labour market research, organisational development, and related fields — primarily at German and European universities.

Runs on a **Mon / Wed / Fri 08:00** cron schedule via Coolify, scrapes 17 sources concurrently, scores and deduplicates results, saves them to Supabase, and delivers a ranked digest via Telegram.

---

## Architecture

```
main.py
 ├── scrapers.py      → 17 concurrent sources (Serper, SerpAPI, Exa AI, RSS, SSR HTML)
 ├── processor.py     → Keyword scoring, deduplication, institution tier ranking
 ├── supabase_db.py   → Supabase REST API (fetch existing + bulk insert)
 └── telegram_bot.py  → Regional digest builder + Telegram delivery
```

## Sources Covered

| Category | Sources |
|---|---|
| Search (Serper) | Academic Boards (27 queries), LinkedIn, XING, ResearchGate, Twitter/X, Reddit, Facebook, North America/ANZ |
| Search (SerpAPI) | Google News |
| Semantic AI | Exa AI (4 queries) |
| RSS Feeds | Bund.de, HigherEdJobs, AcademicKeys Social Sciences, AcademicKeys Education |
| Direct HTML (SSR) | Academics.de, EURAXESS, UniversityPositions.eu |

## Scoring Logic

Each vacancy receives a **1–10 match score** based on:

- **Base score** (5–10): presence of core topic terms + vacancy signals + trusted domain
- **Institution bonus** (+1–2): Tier 1 (DZHW, IZA, WZB…) or Tier 2 (TU Berlin, LMU, Oxford…)
- **Negative discipline penalty** (−1 to −3): hard sciences not relevant to the role
- **Social source penalty** (−1): Reddit, Facebook, Twitter/X, ResearchGate
- **German language cap**: C1/C2 requirement caps score at 4

## Project Structure

```
postdoc-finder/
├── app/
│   ├── __init__.py
│   ├── config.py          # Pydantic-settings — all config from .env
│   ├── models.py          # RawVacancy + PostdocRecord schemas
│   ├── scrapers.py        # All 17 sources
│   ├── processor.py       # Full scoring & dedup engine
│   ├── supabase_db.py     # Supabase queries & inserts
│   └── telegram_bot.py    # Digest + Telegram delivery
├── main.py                # Entrypoint
├── Dockerfile             # Coolify-ready (Python 3.12-slim)
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Setup

### 1. Clone & create `.env`

```bash
git clone https://github.com/Taemmz/postdoc-finder.git
cd postdoc-finder
cp .env.example .env
# Fill in your values in .env
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run locally

```bash
python main.py
```

## Environment Variables

| Variable | Description |
|---|---|
| `SKILLEDGEUP_SUPABASE_PROJECT_REF` | Supabase project reference ID |
| `SKILLEDGEUP_SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `SERPER_API_KEY` | [Serper.dev](https://serper.dev) API key |
| `SERPAPI_API_KEY` | [SerpAPI](https://serpapi.com) key (Google News) |
| `EXA_API_KEY` | [Exa AI](https://exa.ai) API key |
| `TELEGRAM_POSTDOC_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_POSTDOC_CHAT_ID` | Telegram chat/channel ID |

## Deployment on Coolify

1. **New Resource → Application** → connect this GitHub repo
2. Coolify auto-detects the `Dockerfile`
3. In **Environment Variables**, paste all variables from `.env.example` with real values
4. In **Scheduled Tasks**, add:
   - **Schedule:** `0 8 * * 1,3,5`
   - **Command:** `python main.py`
   - **Timezone:** `Europe/Berlin`

## Supabase Table

The app writes to `skilledgeup_postdoc`. Required columns:

```sql
create table skilledgeup_postdoc (
  id              uuid primary key default gen_random_uuid(),
  institution     text not null,
  research_focus  text,
  link            text not null unique,
  deadline        date,
  match_score     int,
  german_required text,
  position_type   text default 'postdoc',
  employment_type text default 'full_time',
  status          text default 'new',
  research_data   jsonb,
  created_at      timestamptz default now()
);
```

---

*Built for SkillEdgeUp — automated research career intelligence.*
