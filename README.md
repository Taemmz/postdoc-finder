# SkillEdgeUp Post-Doc Finder 🔬

An automated post-doctoral vacancy aggregator for **Dr. Faloye**, targeting positions in Empirical Educational Research (*Empirische Bildungsforschung*), Higher Education Innovation, Learning Analytics, Educational Evaluation & Quality Development, Science Management (*Wissenschaftsmanagement*), Academic Governance, and Labour Market Research — primarily at German universities and research institutes.

Runs on a **Daily 08:00 UTC** cron schedule via Coolify, scrapes 18 sources concurrently (including direct university portals), scores and deduplicates results, saves them to Supabase, and delivers a ranked digest via Telegram.

---

## Architecture

```
main.py
 ├── scrapers.py      → 18 concurrent sources (Serper, SerpAPI, Exa AI, RSS, Direct SSR HTML)
 ├── processor.py     → Keyword scoring, deduplication, institution tier ranking & hard gates
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
| Direct Portals (SSR) | Uni Münster Vacancies, Academics.de, EURAXESS, UniversityPositions.eu, PsychJob.eu |

## Scoring Logic & Quality Gates

Each vacancy passes strict pre-filters and receives a **1–10 match score**:

- **Hard Pre-Filters (Dropped before scoring):**
  - **Dead / Soft-404 placeholder listings** (*"This job ad isn't available"*, *"Über diesen Job"*, text < 80 chars)
  - **Non-German locations** (Austria, UK, Switzerland, USA, etc.)
  - **Off-target domains** (Physics, Tropical Dynamics, Engineering, IT / Computer Science, Pure Macro/Micro Economics)
  - **Senior chairs** (W2/W3 Professorships and tenured chairs requiring Habilitation)
  - **Pure/Clinical psychology** (Clinical Approbation, Psychotherapy)
  - **Pre-doc / PhD positions** ($\le 75\%$ TV-L 13 requiring dissertation completion)

- **Match Scoring:**
  - **Base score** (5–10): presence of core topic terms (*Empirische Bildungsforschung, Wissenschaftsmanagement, Hochschulforschung, Evaluation, Labour Market, Learning Analytics*) + vacancy signals
  - **Target Core Requirement**: Scores $\ge 7/10$ require a Target Core match.
  - **Institution bonus** (+1–2): Tier 1 (DZHW, IZA, WZB, DIPF, BIBB…) or Tier 2 (Uni Münster, TU Berlin, LMU, Uni Leipzig, Uni Bamberg…)
  - **German language cap**: C1/C2 requirement caps score at 4

## Project Structure

```
postdoc-finder/
├── app/
│   ├── __init__.py
│   ├── config.py          # Pydantic-settings — all config from .env
│   ├── models.py          # RawVacancy + PostdocRecord schemas
│   ├── scrapers.py        # All 18 sources (including direct Uni portals)
│   ├── processor.py       # Full scoring, dedup & hard exclusion engine
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
   - **Task Name:** `germany-postdoc-scraper`
   - **Schedule:** `0 8 * * *`
   - **Command:** `python main.py`
   - **Timezone:** `Europe/Berlin`

## Supabase Table

The app writes to `skilledgeup_postdoc`. Required columns:

```sql
create table skilledgeup_postdoc (
  id              uuid primary key default gen_random_uuid(),
  institution     text not null,
  department      text,
  research_focus  text,
  country         text default 'Germany',
  city            text,
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
