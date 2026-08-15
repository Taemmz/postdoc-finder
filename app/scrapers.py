"""
scrapers.py — All source scrapers (mirrors the full n8n query sets).
Covers: Academic Boards, LinkedIn, XING, ResearchGate, Twitter/X,
        Google News (SerpAPI), Reddit, Facebook, Exa AI,
        North America/ANZ Boards, Academics.de SSR, EURAXESS SSR,
        UniversityPositions SSR, RSS Bund.de, RSS HigherEdJobs,
        RSS AcademicKeys Social Sciences, RSS AcademicKeys Education.
"""

import asyncio
import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List

from app.config import settings
from app.models import RawVacancy

# ---------------------------------------------------------------------------
# Common browser-like headers to avoid 403s on SSR sites
# ---------------------------------------------------------------------------
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ---------------------------------------------------------------------------
# Query definitions (ported from n8n Build-Query nodes)
# ---------------------------------------------------------------------------

ACADEMIC_BOARD_QUERIES = [
    # Trusted job boards
    ("site:academics.de (postdoc OR \"wissenschaftliche mitarbeiter\")", "de", "de"),
    ("site:euraxess.ec.europa.eu/jobs postdoc", "us", "en"),
    ("site:universitypositions.eu (postdoc OR \"research fellow\" OR \"research associate\")", "us", "en"),
    ("site:psychjob.eu (postdoc OR \"wissenschaftliche mitarbeiter\" OR postdoktorand)", "de", "de"),
    ("site:academicpositions.com postdoctoral researcher", "us", "en"),
    ("site:scholarshipdb.net Germany (postdoc OR \"research associate\")", "us", "en"),
    ("site:timeshighereducation.com/unijobs (postdoc OR \"research fellow\")", "gb", "en"),
    ("site:academictransfer.com (postdoc OR researcher)", "nl", "en"),
    ("site:service.bund.de/IMPORTE/Stellenangebote (postdoc OR \"wissenschaftliche mitarbeiter\" OR \"tv-l\")", "de", "de"),
    ("site:inomics.com (postdoc OR postdoctoral)", "us", "en"),
    ("site:evifa.de (postdoc OR \"wissenschaftliche mitarbeiter\")", "de", "de"),
    # German university pages
    ("site:tum.de Postdoctoral education", "de", "de"),
    ("site:jobs.tu-berlin.de postdoc", "de", "de"),
    ("site:uni-leipzig.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:hu-berlin.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:lmu.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:uni-koeln.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:uni-stuttgart.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:uni-hamburg.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:uni-heidelberg.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:uni-mannheim.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:uni-tuebingen.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:charite.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:kit.edu postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:rwth-aachen.de postdoc OR \"wissenschaftliche mitarbeiter\"", "de", "de"),
    ("site:mpg.de postdoc OR postdoctoral", "de", "de"),
    ("site:helmholtz.de postdoc OR postdoctoral", "de", "de"),
]

LINKEDIN_QUERIES = [
    "site:linkedin.com/jobs Postdoctoral Researcher \"graduate employability\"",
    "site:linkedin.com/jobs Research Fellow \"labour market\"",
    "site:linkedin.com/jobs Research Associate psychometrics",
    "site:linkedin.com/jobs (Postdoctoral OR Research Fellow) \"programme evaluation\"",
    "site:linkedin.com/jobs (Postdoc OR Research Associate) \"organisational development\"",
]

XING_QUERIES = [
    "site:xing.com/jobs (postdoc OR postdoctoral OR \"wissenschaftliche mitarbeiter\") (employability OR \"arbeitsmarkt\" OR \"organisationsentwicklung\")",
    "site:xing.com/jobs (postdoc OR \"wissenschaftliche mitarbeiter\") \"wissenschaftliche mitarbeiterin\"",
]

RESEARCHGATE_QUERIES = [
    "site:researchgate.net/jobs (postdoc OR postdoctoral OR \"wissenschaftliche mitarbeiter\") (employability OR \"labour market\" OR \"organisational development\")",
    "site:researchgate.net/jobs (postdoctoral OR research fellow) (workforce OR \"work psychology\" OR \"programme evaluation\")",
]

TWITTER_QUERIES = [
    "site:x.com (\"we are hiring\" OR \"applications are open\") (postdoc OR postdoctoral researcher) (employability OR workforce OR education)",
    "site:x.com (postdoctoral researcher OR research fellow) (psychometrics OR \"programme evaluation\" OR \"educational assessment\")",
    "site:x.com (postdoctoral fellow OR research associate) (\"organisational development\" OR \"work psychology\" OR \"workplace learning\")",
]

GOOGLE_NEWS_QUERIES = [
    "(research fellowship OR postdoctoral vacancy) \"applications open\" (employability OR \"labour market\")",
    "(Marie Curie OR ERC OR DAAD) postdoctoral fellowship (employability OR \"labour market\" OR workforce)",
]

REDDIT_QUERIES = [
    "site:reddit.com/r/AskAcademia (postdoc OR research fellow) (employability OR \"labour market\" OR \"workforce development\")",
    "site:reddit.com/r/PostDoc (\"postdoc opening\" OR \"postdoctoral opening\") (employability OR workforce OR \"labour market\")",
    "site:reddit.com/r/IOPsychology (postdoctoral OR research fellow) (\"organizational behavior\" OR \"organisational development\" OR \"work psychology\")",
]

FACEBOOK_QUERIES = [
    "site:facebook.com (postdoc position OR postdoctoral position) (employability OR \"labour market\" OR \"workforce development\")",
    "site:facebook.com/groups (postdoc opening OR research fellow position) (education OR \"social science\" OR workforce)",
    "site:facebook.com (postdoctoral researcher OR research fellow) (\"organisational development\" OR \"work psychology\" OR evaluation)",
]

EXA_QUERIES = [
    "Open postdoctoral or research fellow positions in graduate employability, labour market transitions, and workforce development at universities and research institutes, published in the last 30 days.",
    "Open postdoctoral researcher or research associate positions in programme evaluation, psychometrics, mixed methods, or educational assessment, published in the last 30 days.",
    "Open postdoctoral positions in organisational development, workplace learning, work psychology, or human resource development, published in the last 30 days.",
    "Open postdoctoral and research fellow positions in higher education research, graduate outcomes, or education policy at German or European universities, published in the last 30 days.",
]

NA_ANZ_QUERIES = [
    ("site:universityaffairs.ca (postdoctoral OR \"research associate\")", "ca", "en"),
    ("site:higheredjobs.com postdoctoral (employability OR \"labour market\")", "us", "en"),
    ("site:academicjobs.ca postdoctoral", "ca", "en"),
    ("site:jobs.ac.uk (Canada OR Australia OR \"New Zealand\") postdoctoral", "gb", "en"),
    ("(site:unimelb.edu.au OR site:sydney.edu.au OR site:anu.edu.au) postdoctoral (employability OR \"organisational development\" OR workforce)", "au", "en"),
]

RSS_FEEDS = [
    ("RSS Bund.de", "https://www.service.bund.de/Content/Globals/Functions/RSSFeed/RSSGenerator_Stellen.xml"),
    ("RSS HigherEdJobs", "https://www.higheredjobs.com/rss/categoryFeed.cfm?catID=68"),
    ("RSS AcademicKeys SocSci", "https://socialsciences.academickeys.com/rss"),
    ("RSS AcademicKeys Education", "https://education.academickeys.com/rss"),
]


# ---------------------------------------------------------------------------
# Serper search helper
# ---------------------------------------------------------------------------

async def _serper_search(
    client: httpx.AsyncClient,
    source: str,
    query: str,
    gl: str = "us",
    hl: str = "en",
    tbs: str = "qdr:m",
) -> List[RawVacancy]:
    """POST one query to Serper and return organic results as RawVacancy items."""
    try:
        res = await client.post(
            "https://google.serper.dev/search",
            headers={
                "X-API-KEY": settings.SERPER_API_KEY,
                "Content-Type": "application/json",
            },
            json={"q": query, "num": 10, "gl": gl, "hl": hl, "tbs": tbs},
            timeout=20.0,
        )
        data = res.json()
        results = []
        for r in data.get("organic", []):
            results.append(
                RawVacancy(
                    source=source,
                    title=r.get("title", ""),
                    link=r.get("link", ""),
                    snippet=r.get("snippet", ""),
                )
            )
        return results
    except Exception:
        return []


async def _serpapi_news_search(
    client: httpx.AsyncClient,
    query: str,
) -> List[RawVacancy]:
    """GET one Google News query from SerpAPI."""
    try:
        res = await client.get(
            "https://serpapi.com/search",
            params={
                "engine": "google_news",
                "q": query,
                "num": 10,
                "hl": "en",
                "gl": "us",
                "tbs": "qdr:w",
                "api_key": settings.SERPAPI_API_KEY,
            },
            timeout=20.0,
        )
        data = res.json()
        results = []
        for r in data.get("news_results", []):
            results.append(
                RawVacancy(
                    source="Google News",
                    title=r.get("title", ""),
                    link=r.get("link", ""),
                    snippet=r.get("snippet", ""),
                )
            )
        return results
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Serper source functions
# ---------------------------------------------------------------------------

async def fetch_academic_boards(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [
        _serper_search(client, "Academic Boards", q, gl=gl, hl=hl, tbs="qdr:w")
        for q, gl, hl in ACADEMIC_BOARD_QUERIES
    ]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_linkedin(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [_serper_search(client, "LinkedIn", q, tbs="qdr:w") for q in LINKEDIN_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_xing(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [_serper_search(client, "XING", q, gl="de", hl="de", tbs="qdr:m") for q in XING_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_researchgate(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [_serper_search(client, "ResearchGate", q, gl="de", hl="en", tbs="qdr:m") for q in RESEARCHGATE_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_twitter(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [_serper_search(client, "Twitter/X", q, tbs="qdr:m") for q in TWITTER_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_google_news(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [_serpapi_news_search(client, q) for q in GOOGLE_NEWS_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_reddit(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [_serper_search(client, "Reddit", q, gl="de", hl="en", tbs="qdr:m") for q in REDDIT_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_facebook(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [_serper_search(client, "Facebook", q, tbs="qdr:m") for q in FACEBOOK_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_na_anz(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [
        _serper_search(client, "North America/ANZ Boards", q, gl=gl, hl=hl, tbs="qdr:m")
        for q, gl, hl in NA_ANZ_QUERIES
    ]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


# ---------------------------------------------------------------------------
# Exa AI
# ---------------------------------------------------------------------------

async def fetch_exa(client: httpx.AsyncClient) -> List[RawVacancy]:
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")
    results = []
    for q in EXA_QUERIES:
        try:
            res = await client.post(
                "https://api.exa.ai/search",
                headers={
                    "x-api-key": settings.EXA_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "query": q,
                    "type": "auto",
                    "numResults": 10,
                    "startPublishedDate": start_date,
                    "contents": {
                        "highlights": {
                            "maxCharacters": 500,
                            "highlightsPerUrl": 2,
                            "query": "postdoctoral position deadline apply employability labour market",
                        }
                    },
                },
                timeout=20.0,
            )
            for r in res.json().get("results", []):
                snippet = " ".join(r.get("highlights", []))
                results.append(
                    RawVacancy(
                        source="Exa Search",
                        title=r.get("title", ""),
                        link=r.get("url", ""),
                        snippet=snippet,
                    )
                )
        except Exception:
            continue
    return results


# ---------------------------------------------------------------------------
# RSS Feeds
# ---------------------------------------------------------------------------

async def fetch_rss(client: httpx.AsyncClient, source: str, url: str) -> List[RawVacancy]:
    try:
        res = await client.get(url, headers=HEADERS, timeout=20.0)
        feed = feedparser.parse(res.text)
        return [
            RawVacancy(
                source=source,
                title=e.get("title", ""),
                link=e.get("link", ""),
                snippet=e.get("description", "") or e.get("summary", ""),
                query_type="rss_feed",
            )
            for e in feed.entries
            if e.get("link")
        ]
    except Exception:
        return []


async def fetch_all_rss(client: httpx.AsyncClient) -> List[RawVacancy]:
    tasks = [fetch_rss(client, src, url) for src, url in RSS_FEEDS]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


# ---------------------------------------------------------------------------
# SSR scrapers (direct HTML)
# ---------------------------------------------------------------------------

async def fetch_ssr_academics(client: httpx.AsyncClient) -> List[RawVacancy]:
    results = []
    queries = ["Postdoc", "Wissenschaftliche+Mitarbeiter", "Postdoktorand"]
    for q in queries:
        try:
            res = await client.get(
                f"https://www.academics.de/stellenanzeigen?q={q}",
                headers=HEADERS,
                timeout=20.0,
            )
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.select("a.job-link, h2 a, article a"):
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if not title or not href:
                    continue
                full_link = href if href.startswith("http") else f"https://www.academics.de{href}"
                results.append(
                    RawVacancy(
                        source="Academics.de SSR",
                        title=title,
                        link=full_link,
                        query_type="ssr_html",
                    )
                )
        except Exception:
            continue
    return results


async def fetch_ssr_euraxess(client: httpx.AsyncClient) -> List[RawVacancy]:
    try:
        res = await client.get(
            "https://euraxess.ec.europa.eu/jobs/search?f%5B0%5D=keywords%3Apostdoc",
            headers=HEADERS,
            timeout=20.0,
        )
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for a in soup.select(".field--name-title a, .node__title a"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or not href:
                continue
            full_link = href if href.startswith("http") else f"https://euraxess.ec.europa.eu{href}"
            results.append(
                RawVacancy(
                    source="EURAXESS SSR",
                    title=title,
                    link=full_link,
                    query_type="ssr_html",
                )
            )
        return results
    except Exception:
        return []


async def fetch_ssr_universitypositions(client: httpx.AsyncClient) -> List[RawVacancy]:
    try:
        res = await client.get(
            "https://universitypositions.eu/jobs?category=postdoc",
            headers=HEADERS,
            timeout=20.0,
        )
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for h3 in soup.select("h3"):
            title = h3.get_text(strip=True)
            a = h3.find("a") or (h3.find_parent("a"))
            href = a.get("href", "") if a else ""
            if not title or not href:
                continue
            full_link = href if href.startswith("http") else f"https://universitypositions.eu{href}"
            results.append(
                RawVacancy(
                    source="UniversityPositions SSR",
                    title=title,
                    link=full_link,
                    query_type="ssr_html",
                )
            )
        return results
    except Exception:
        return []


# ---------------------------------------------------------------------------
# Master entrypoint — runs all 17 sources concurrently
# ---------------------------------------------------------------------------

async def scrape_all_sources() -> List[RawVacancy]:
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_academic_boards(client),
            fetch_linkedin(client),
            fetch_xing(client),
            fetch_researchgate(client),
            fetch_twitter(client),
            fetch_google_news(client),
            fetch_reddit(client),
            fetch_facebook(client),
            fetch_exa(client),
            fetch_na_anz(client),
            fetch_all_rss(client),
            fetch_ssr_academics(client),
            fetch_ssr_euraxess(client),
            fetch_ssr_universitypositions(client),
        ]
        nested = await asyncio.gather(*tasks, return_exceptions=True)
        flat: List[RawVacancy] = []
        for batch in nested:
            if isinstance(batch, list):
                flat.extend(batch)
        print(f"  [scrapers] Total raw items collected: {len(flat)}")
        return flat
