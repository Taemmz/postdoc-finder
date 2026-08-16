"""
scrapers.py — Germany-only pivot.
Sources: German academic boards (Serper gl=de), Google News, Exa AI,
         RSS feeds (Bund.de, HigherEdJobs, AcademicKeys),
         SSR: academics.de, EURAXESS (Germany-filtered), psychjob.eu
"""

import asyncio
import feedparser
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List

from app.config import settings
from app.models import RawVacancy

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

GERMAN_ACADEMIC_QUERIES = [
    # ── Primary clearinghouses ────────────────────────────────────────────────
    ('site:academics.de (postdoc OR "wissenschaftlicher Mitarbeiter" OR "wissenschaftliche Mitarbeiterin" OR "research associate")', "de", "de"),
    ('site:academics.de (postdoc OR "wissenschaftliche Mitarbeiter") (arbeitsmarkt OR bildungsforschung OR employability OR evaluation)', "de", "de"),
    ('site:service.bund.de/IMPORTE/Stellenangebote ("wissenschaftliche Mitarbeiter" OR "postdoc" OR "TV-L E13")', "de", "de"),

    # ── Disciplinary clearinghouses ───────────────────────────────────────────
    # H-Soz-Kult: standard portal for German social science & humanities postdocs
    ('site:hsozkult.de/job (postdoc OR "wissenschaftliche Mitarbeiter" OR "research associate")', "de", "de"),
    ('site:hsozkult.de/job (arbeitsmarkt OR bildungsforschung OR employability OR evaluation OR hochschulforschung)', "de", "de"),
    # PsychJob.eu (DGPs portal): work, org, & educational psychology
    ('site:psychjob.eu (postdoc OR "wissenschaftliche Mitarbeiter" OR postdoktorand)', "de", "de"),
    # GESIS: social science infrastructure
    ('site:gesis.org (postdoc OR "wissenschaftliche")', "de", "de"),
    # WZB: labour & social research Berlin
    ('site:wzb.eu (postdoc OR "wissenschaftliche")', "de", "de"),
    # IAB: Germany's central labour market research institute
    ('site:iab.de (postdoc OR "wissenschaftliche" OR stellenangebot OR ausschreibung)', "de", "de"),
    # DZHW: higher education research
    ('site:dzhw.eu (postdoc OR "wissenschaftliche")', "de", "de"),
    # EVIFA: social science library network jobs
    ('site:evifa.de (postdoc OR "wissenschaftliche Mitarbeiter")', "de", "de"),

    # ── Multi-campus university job networks ──────────────────────────────────
    # Stellenwerk: official network for Hamburg, Cologne, Munich, Berlin, Würzburg
    ('site:stellenwerk.de (postdoc OR "wissenschaftliche Mitarbeiter" OR "wissenschaftlicher Mitarbeiter")', "de", "de"),
    ('site:stellenwerk.de (arbeitsmarkt OR bildungsforschung OR employability OR "work psychology" OR evaluation)', "de", "de"),
    # Deutscher Hochschulverband (DHV): academic & professorial openings
    ('site:hochschulverband.de (postdoc OR "wissenschaftliche Mitarbeiter" OR ausschreibungen)', "de", "de"),

    # ── International boards filtered to Germany ──────────────────────────────
    ('site:euraxess.ec.europa.eu/jobs Germany (postdoc OR "research fellow" OR "wissenschaftliche")', "de", "en"),
    ('site:universitypositions.eu Germany (postdoc OR "research associate")', "de", "en"),
    ('site:inomics.com Germany (postdoc OR postdoctoral OR researcher)', "de", "en"),

    # ── Professional networks (Germany-restricted) ────────────────────────────
    ('site:de.linkedin.com/jobs/view ("postdoc" OR "postdoctoral" OR "research associate" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:xing.com/jobs ("postdoc" OR "postdoctoral" OR "wissenschaftlicher Mitarbeiter" OR "wissenschaftliche Mitarbeiterin")', "de", "de"),

    # ── German university direct career pages ────────────────────────────────
    ('site:jobs.tu-berlin.de ("wissenschaftliche Mitarbeiter" OR postdoc)', "de", "de"),
    ('site:tum.de/die-tum/arbeiten-an-der-tum/stellenangebote', "de", "de"),
    ('site:lmu.de/de/die-lmu/arbeiten-an-der-lmu/stellenangebote ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:hu-berlin.de/de/ueberblick/karriere ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-leipzig.de/universitaet/arbeiten-an-der-universitaet-leipzig', "de", "de"),
    ('site:uni-koeln.de/universitaet/karriere ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-heidelberg.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-mannheim.de/universitaet/beschaeftigung ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-tuebingen.de/universitaet/karriere ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:stellenangebote.uni-stuttgart.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-hamburg.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-frankfurt.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-bonn.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-muenster.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-goettingen.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-bielefeld.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:rwth-aachen.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:kit.edu ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:charite.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:mpg.de (postdoc OR "research associate")', "de", "de"),
    ('site:helmholtz.de (postdoc OR "wissenschaftliche")', "de", "de"),

    # ── Broad German sweeps ───────────────────────────────────────────────────
    ('"wissenschaftlicher Mitarbeiter" (employability OR arbeitsmarkt OR bildungsforschung OR evaluation) site:.de', "de", "de"),
    ('"TV-L E13" OR "TV-L E14" (postdoc OR "wissenschaftliche Mitarbeiter") (bildung OR arbeitsmarkt OR evaluation) site:.de', "de", "de"),

    # ── Gender-inclusive title variants & city-specific portals ───────────────
    # German job boards use (m/w/d), (m/f/d/x), Wissenschaftliche*r suffixes
    ('site:psychjob.eu ("post-doktorandin" OR "postdoktorandin" OR "organisationale" OR "organisationspsychologie")', "de", "de"),
    ('site:evifa.de (postdoc OR "wissenschaftliche Mitarbeiter" OR "postdoktorand")', "de", "de"),
    ('site:academics.de/jobs ("wissenschaftliche Mitarbeiter" OR postdoc) (halle OR freiburg OR münchen OR berlin OR köln)', "de", "de"),
    ('site:academics.de/jobs ("wissenschaftliche Mitarbeiter" OR postdoc) (hamburg OR frankfurt OR bonn OR tübingen OR mannheim)', "de", "de"),
    ('site:xing.com/jobs ("wissenschaftliche Mitarbeiter" OR postdoc) "TV-L"', "de", "de"),
    # ScholarshipDB Germany aggregator (indexes Nature Careers & others scoped to Germany)
    ('site:scholarshipdb.net/jobs-in-Germany ("research associate" OR postdoc)', "de", "en"),
    # universitypositions.eu is already in queries above; add topic-scoped variant
    ('site:universitypositions.eu Germany (postdoc OR "wissenschaftliche Mitarbeiter") (labour OR arbeitsmarkt OR evaluation OR employability)', "de", "en"),
    # Freiburg, Halle, Regensburg — cities not covered by direct university scrapers
    ('"Freiburg" (postdoc OR "wissenschaftliche Mitarbeiter") (arbeitsmarkt OR bildung OR evaluation) site:.de', "de", "de"),
    ('"Halle" OR "Halle-Wittenberg" (postdoc OR "wissenschaftliche Mitarbeiter") site:.de', "de", "de"),

    # ── German university ATS (white-label recruiting platforms) ──────────────
    # Many German unis outsource their careers pages to these ATS providers.
    # The university name is encoded in the subdomain: uni-leipzig.b-ite.careers
    ('site:b-ite.careers (postdoc OR "wissenschaftliche Mitarbeiter" OR "research associate")', "de", "de"),
    ('site:dvinci-hr.com (postdoc OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:softgarden.io (postdoc OR "wissenschaftliche Mitarbeiter") Germany', "de", "en"),
    ('site:persis.de (postdoc OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    # interamt.de: German federal/state public sector vacancies (TV-L contracts)
    ('site:interamt.de (postdoc OR "wissenschaftliche Mitarbeiter" OR "TV-L E13" OR "TV-L E14")', "de", "de"),
]



GOOGLE_NEWS_QUERIES = [
    '(postdoc OR "wissenschaftlicher Mitarbeiter") Germany (employability OR "labour market" OR arbeitsmarkt OR evaluation)',
    '(DAAD OR DFG OR "Marie Curie") postdoctoral Germany (bildung OR workforce OR evaluation)',
]

EXA_QUERIES = [
    "Open postdoctoral researcher, research associate, or wissenschaftliche Mitarbeiter positions in Germany in employability, labour market, workforce development, or education research published in the last 30 days.",
    "Open postdoc or academic researcher vacancies at German universities or research institutes in psychometrics, programme evaluation, work psychology, or organisational development.",
    "Postdoctoral fellow or wissenschaftlicher Mitarbeiter jobs at German universities (TV-L E13 or TV-L E14) in higher education research, graduate employability, or transition to work.",
    "Open postdoctoral positions in Germany in bildungsforschung, hochschulforschung, arbeitsmarktforschung, or berufliche Bildung published in the last 30 days.",
]

RSS_FEEDS = [
    ("RSS Bund.de", "https://www.service.bund.de/Content/Globals/Functions/RSSFeed/RSSGenerator_Stellen.xml"),
    ("RSS HigherEdJobs", "https://www.higheredjobs.com/rss/categoryFeed.cfm?catID=68"),
    ("RSS AcademicKeys SocSci", "https://socialsciences.academickeys.com/rss"),
    ("RSS AcademicKeys Education", "https://education.academickeys.com/rss"),
]



async def _serper_search(client, source, query, gl="de", hl="de", tbs="qdr:m"):
    try:
        res = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": settings.SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "num": 10, "gl": gl, "hl": hl, "tbs": tbs},
            timeout=20.0,
        )
        return [RawVacancy(source=source, title=r.get("title",""), link=r.get("link",""), snippet=r.get("snippet","")) for r in res.json().get("organic", [])]
    except Exception:
        return []


async def _serpapi_news_search(client, query):
    try:
        res = await client.get(
            "https://serpapi.com/search",
            params={"engine":"google_news","q":query,"num":10,"hl":"de","gl":"de","tbs":"qdr:w","api_key":settings.SERPAPI_API_KEY},
            timeout=20.0,
        )
        return [RawVacancy(source="Google News", title=r.get("title",""), link=r.get("link",""), snippet=r.get("snippet","")) for r in res.json().get("news_results", [])]
    except Exception:
        return []


async def fetch_german_boards(client):
    tasks = [_serper_search(client, "German Academic Boards", q, gl=gl, hl=hl, tbs="qdr:m") for q, gl, hl in GERMAN_ACADEMIC_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_google_news(client):
    tasks = [_serpapi_news_search(client, q) for q in GOOGLE_NEWS_QUERIES]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_exa(client):
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000Z")
    results = []
    for q in EXA_QUERIES:
        try:
            res = await client.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": settings.EXA_API_KEY, "Content-Type": "application/json"},
                json={"query":q,"type":"auto","numResults":10,"startPublishedDate":start_date,
                      "contents":{"highlights":{"maxCharacters":500,"highlightsPerUrl":2,"query":"postdoctoral position Germany employability arbeitsmarkt deadline"}}},
                timeout=20.0,
            )
            for r in res.json().get("results", []):
                results.append(RawVacancy(source="Exa Search", title=r.get("title",""), link=r.get("url",""), snippet=" ".join(r.get("highlights",[]))))
        except Exception:
            continue
    return results


async def fetch_rss(client, source, url):
    try:
        res = await client.get(url, headers=HEADERS, timeout=20.0)
        feed = feedparser.parse(res.text)
        return [RawVacancy(source=source, title=e.get("title",""), link=e.get("link",""), snippet=e.get("description","") or e.get("summary",""), query_type="rss_feed") for e in feed.entries if e.get("link")]
    except Exception:
        return []


async def fetch_all_rss(client):
    tasks = [fetch_rss(client, src, url) for src, url in RSS_FEEDS]
    nested = await asyncio.gather(*tasks, return_exceptions=True)
    return [v for batch in nested if isinstance(batch, list) for v in batch]


async def fetch_ssr_academics(client):
    results = []
    for q in ["Postdoc", "Wissenschaftliche+Mitarbeiter", "Postdoktorand", "wissenschaftlicher+Mitarbeiter"]:
        try:
            res = await client.get(f"https://www.academics.de/stellenanzeigen?q={q}", headers=HEADERS, timeout=20.0)
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.select("a.job-link, h2 a, article a"):
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if title and href:
                    full = href if href.startswith("http") else f"https://www.academics.de{href}"
                    results.append(RawVacancy(source="Academics.de SSR", title=title, link=full, query_type="ssr_html"))
        except Exception:
            continue
    return results


async def fetch_ssr_euraxess(client):
    try:
        res = await client.get("https://euraxess.ec.europa.eu/jobs/search?f%5B0%5D=keywords%3Apostdoc&f%5B1%5D=country%3Agermany", headers=HEADERS, timeout=20.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for a in soup.select(".field--name-title a, .node__title a"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if title and href:
                full = href if href.startswith("http") else f"https://euraxess.ec.europa.eu{href}"
                results.append(RawVacancy(source="EURAXESS SSR", title=title, link=full, query_type="ssr_html"))
        return results
    except Exception:
        return []


async def fetch_ssr_psychjob(client):
    try:
        res = await client.get("https://www.psychjob.eu/jobs?q=postdoc", headers=HEADERS, timeout=20.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for a in soup.select("h2 a, .job-title a, article a"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if title and href:
                full = href if href.startswith("http") else f"https://www.psychjob.eu{href}"
                results.append(RawVacancy(source="PsychJob SSR", title=title, link=full, query_type="ssr_html"))
        return results
    except Exception:
        return []


async def fetch_ssr_hsozkult(client) -> List[RawVacancy]:
    """Scrape H-Soz-Kult — primary German social science & humanities job portal."""
    results = []
    urls = [
        "https://www.hsozkult.de/job/type/stellenangebote",
        "https://www.hsozkult.de/job/page/1?type=stellenangebote&q=postdoc",
        "https://www.hsozkult.de/job/page/1?type=stellenangebote&q=wissenschaftliche+Mitarbeiter",
    ]
    for url in urls:
        try:
            res = await client.get(url, headers=HEADERS, timeout=20.0)
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.select("h2 a, .title a, article a, .entry-title a"):
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if title and href:
                    full = href if href.startswith("http") else f"https://www.hsozkult.de{href}"
                    results.append(RawVacancy(source="H-Soz-Kult SSR", title=title, link=full, query_type="ssr_html"))
        except Exception:
            continue
    return results


async def fetch_ssr_stellenwerk(client) -> List[RawVacancy]:
    """Scrape Stellenwerk — official multi-campus German university job network."""
    results = []
    # Stellenwerk has campus sub-sites; scrape the central search
    urls = [
        "https://www.stellenwerk.de/jobboerse/?q=postdoc",
        "https://www.stellenwerk.de/jobboerse/?q=wissenschaftliche+Mitarbeiter",
    ]
    for url in urls:
        try:
            res = await client.get(url, headers=HEADERS, timeout=20.0)
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.select("h2 a, .job-title a, .stellenanzeige a, article a"):
                title = a.get_text(strip=True)
                href = a.get("href", "")
                if title and href:
                    full = href if href.startswith("http") else f"https://www.stellenwerk.de{href}"
                    results.append(RawVacancy(source="Stellenwerk SSR", title=title, link=full, query_type="ssr_html"))
        except Exception:
            continue
    return results


async def scrape_all_sources() -> List[RawVacancy]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [
            # ── Serper / API sources ───────────────────────────────────────────
            fetch_german_boards(client),      # ~42 Serper queries, gl=de hl=de
            fetch_google_news(client),        # 2 SerpAPI news queries, gl=de
            fetch_exa(client),                # 4 Exa semantic queries (Germany-scoped)
            fetch_all_rss(client),            # 4 RSS feeds
            # ── SSR aggregators ────────────────────────────────────────────────
            fetch_ssr_academics(client),      # academics.de direct HTML
            fetch_ssr_euraxess(client),       # EURAXESS Germany-filtered
            fetch_ssr_psychjob(client),       # psychjob.eu (DGPs portal)
            fetch_ssr_hsozkult(client),       # H-Soz-Kult (social science & humanities)
            fetch_ssr_stellenwerk(client),    # Stellenwerk (multi-campus network)
            # ── Direct university career pages (zero API cost) ─────────────────
            fetch_direct_lmu(client),
            fetch_direct_hu_berlin(client),
            fetch_direct_tu_berlin(client),
            fetch_direct_uni_leipzig(client),
            fetch_direct_uni_heidelberg(client),
            fetch_direct_uni_koeln(client),
        ]
        nested = await asyncio.gather(*tasks, return_exceptions=True)
        flat: List[RawVacancy] = []
        for batch in nested:
            if isinstance(batch, list):
                flat.extend(batch)
        print(f"  [scrapers] Total raw items collected: {len(flat)}")
        return flat


# ---------------------------------------------------------------------------
# Direct German university career page scrapers (zero API cost)
# ---------------------------------------------------------------------------

def _direct_uni(source: str, base_url: str) -> dict:
    """Shared config dict for direct university scrapers."""
    return {"source": source, "base": base_url}


async def fetch_direct_lmu(client: httpx.AsyncClient) -> List[RawVacancy]:
    """LMU München — arbeiten-an-der-lmu/stellenangebote."""
    url = "https://www.lmu.de/de/die-lmu/arbeiten-an-der-lmu/stellenangebote/index.html"
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for item in soup.select("article, .contenttable tr, .teaser-text, li.item"):
            a = item.select_one("a[href]")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a["href"]
            link = href if href.startswith("http") else f"https://www.lmu.de{href}"
            snippet = item.get_text(" ", strip=True)
            if title:
                results.append(RawVacancy(source="LMU München Direct", title=title, link=link, snippet=snippet, query_type="direct_uni_ssr"))
        return results
    except Exception:
        return []


async def fetch_direct_hu_berlin(client: httpx.AsyncClient) -> List[RawVacancy]:
    """HU Berlin — karriere/stellenausschreibungen."""
    url = "https://www.hu-berlin.de/de/ueberblick/karriere/stellenausschreibungen"
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for a in soup.select("a[href*='stellenausschreibungen'], .job-offer-item a, .news-list-item a"):
            title = a.get_text(strip=True)
            href = a["href"]
            link = href if href.startswith("http") else f"https://www.hu-berlin.de{href}"
            if title and len(title) > 10:
                results.append(RawVacancy(source="HU Berlin Direct", title=title, link=link, snippet=title, query_type="direct_uni_ssr"))
        return results
    except Exception:
        return []


async def fetch_direct_tu_berlin(client: httpx.AsyncClient) -> List[RawVacancy]:
    """TU Berlin — jobs.tu-berlin.de/stellenangebote."""
    url = "https://jobs.tu-berlin.de/stellenangebote"
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for row in soup.select(".views-row, .job-item, tr"):
            a = row.select_one("a[href]")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a["href"]
            link = href if href.startswith("http") else f"https://jobs.tu-berlin.de{href}"
            snippet = row.get_text(" ", strip=True)
            if title and len(title) > 10:
                results.append(RawVacancy(source="TU Berlin Direct", title=title, link=link, snippet=snippet, query_type="direct_uni_ssr"))
        return results
    except Exception:
        return []


async def fetch_direct_uni_leipzig(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Uni Leipzig — stellenausschreibungen page."""
    url = "https://www.uni-leipzig.de/universitaet/arbeiten-an-der-universitaet-leipzig/stellenausschreibungen"
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for a in soup.select("a[href*='ausschreibung'], a[href*='stellenangebot'], .element-job a, table.contenttable a"):
            title = a.get_text(strip=True)
            href = a["href"]
            link = href if href.startswith("http") else f"https://www.uni-leipzig.de{href}"
            if title and len(title) > 15:
                results.append(RawVacancy(source="Uni Leipzig Direct", title=title, link=link, snippet=title, query_type="direct_uni_ssr"))
        return results
    except Exception:
        return []


async def fetch_direct_uni_heidelberg(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Uni Heidelberg — beschaeftigung-ausbildung/stellenangebote."""
    url = "https://www.uni-heidelberg.de/de/beschaeftigung-ausbildung/stellenangebote"
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for item in soup.select(".news-list-item, article, li.item"):
            a = item.select_one("a[href]")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a["href"]
            link = href if href.startswith("http") else f"https://www.uni-heidelberg.de{href}"
            snippet = item.get_text(" ", strip=True)
            if title and len(title) > 10:
                results.append(RawVacancy(source="Uni Heidelberg Direct", title=title, link=link, snippet=snippet, query_type="direct_uni_ssr"))
        return results
    except Exception:
        return []


async def fetch_direct_uni_koeln(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Uni Köln — via stellenwerk-koeln.de (the official Cologne campus job board)."""
    url = "https://www.stellenwerk-koeln.de/stellenmarkt?q=wissenschaftliche+Mitarbeiter"
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for item in soup.select(".job-item, article, .job-title, li.item"):
            a = item.select_one("a[href]")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a["href"]
            link = href if href.startswith("http") else f"https://www.stellenwerk-koeln.de{href}"
            snippet = item.get_text(" ", strip=True)
            if title and len(title) > 10:
                results.append(RawVacancy(source="Uni Köln Direct", title=title, link=link, snippet=snippet, query_type="direct_uni_ssr"))
        return results
    except Exception:
        return []

