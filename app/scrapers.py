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
    ('site:academics.de (postdoc OR "wissenschaftlicher Mitarbeiter" OR "wissenschaftliche Mitarbeiterin" OR "research associate")', "de", "de"),
    ('site:service.bund.de/IMPORTE/Stellenangebote ("wissenschaftliche Mitarbeiter" OR "postdoc" OR "TV-L E13")', "de", "de"),
    ('site:euraxess.ec.europa.eu/jobs Germany (postdoc OR "research fellow" OR "wissenschaftliche")', "de", "en"),
    ('site:universitypositions.eu Germany (postdoc OR "research associate")', "de", "en"),
    ('site:inomics.com Germany (postdoc OR postdoctoral OR researcher)', "de", "en"),
    ('site:psychjob.eu (postdoc OR "wissenschaftliche Mitarbeiter" OR postdoktorand)', "de", "de"),
    ('site:gesis.org (postdoc OR "wissenschaftliche")', "de", "de"),
    ('site:wzb.eu (postdoc OR "wissenschaftliche")', "de", "de"),
    ('site:iab.de (postdoc OR "wissenschaftliche")', "de", "de"),
    ('site:dzhw.eu (postdoc OR "wissenschaftliche")', "de", "de"),
    ('site:evifa.de (postdoc OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:de.linkedin.com/jobs/view ("postdoc" OR "postdoctoral" OR "research associate" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:xing.com/jobs ("postdoc" OR "postdoctoral" OR "wissenschaftlicher Mitarbeiter" OR "wissenschaftliche Mitarbeiterin")', "de", "de"),
    ('site:tum.de ("postdoc" OR "wissenschaftlicher Mitarbeiter" OR "research fellow")', "de", "de"),
    ('site:lmu.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:hu-berlin.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:jobs.tu-berlin.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-leipzig.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-koeln.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-heidelberg.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-mannheim.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-tuebingen.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-hamburg.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:uni-stuttgart.de ("postdoc" OR "wissenschaftliche Mitarbeiter")', "de", "de"),
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
    ('"wissenschaftlicher Mitarbeiter" (employability OR arbeitsmarkt OR bildungsforschung OR evaluation) site:.de', "de", "de"),
    ('"TV-L E13" OR "TV-L E14" (postdoc OR "wissenschaftliche Mitarbeiter") (bildung OR arbeitsmarkt OR evaluation) site:.de', "de", "de"),
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


async def scrape_all_sources() -> List[RawVacancy]:
    async with httpx.AsyncClient() as client:
        tasks = [
            fetch_german_boards(client),
            fetch_google_news(client),
            fetch_exa(client),
            fetch_all_rss(client),
            fetch_ssr_academics(client),
            fetch_ssr_euraxess(client),
            fetch_ssr_psychjob(client),
        ]
        nested = await asyncio.gather(*tasks, return_exceptions=True)
        flat: List[RawVacancy] = []
        for batch in nested:
            if isinstance(batch, list):
                flat.extend(batch)
        print(f"  [scrapers] Total raw items collected: {len(flat)}")
        return flat
