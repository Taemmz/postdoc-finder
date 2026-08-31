"""
scrapers.py — Germany-only pivot.
Sources: German academic boards (Serper gl=de), Google News, Exa AI,
         RSS feeds (Bund.de, HigherEdJobs, AcademicKeys),
         SSR: academics.de, EURAXESS (Germany-filtered), psychjob.eu
"""

import asyncio
import feedparser
import httpx
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.config import settings
from app.models import RawVacancy
from app.scrapers_haw import (
    fetch_direct_eah_jena,
    fetch_direct_h2_magdeburg,
    fetch_direct_htwk_leipzig,
    fetch_direct_hs_merseburg,
)

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

    # ── Higher Education Innovation & Science Management ──────────────────────
    ('site:academics.de ("Lehrinnovation" OR "Hochschuldidaktik" OR "Prorektorat Lehre" OR "Wissenschaftsmanagement")', "de", "de"),
    ('site:academics.de ("Akademische*r Mitarbeiter*in" OR "Wissenschaftliche*r Mitarbeiter*in") AND ("TV-L E 13" OR "TV-L E 14" OR "E 13") -W2 -W3 -Professur', "de", "de"),
    ('("Stiftung Innovation in der Hochschullehre" OR "StIL" OR "Lehrwerkstatt" OR "Campus im Dialog") AND ("Mitarbeiter" OR "Koordinator") site:.de', "de", "de"),
    ('("Projektkoordinator" OR "Projektmanager") AND ("Prorektorat" OR "Hochschulentwicklung" OR "Qualitätsentwicklung") AND ("TV-L" OR "TV-H") -Student -HiWi site:.de', "de", "de"),
    ('site:service.bund.de/IMPORTE/Stellenangebote ("Wissenschaftsmanagement" OR "Qualitätsentwicklung" OR "Bildungsforschung" OR "Lehrinnovation")', "de", "de"),
    ('("Wissenschaftsmanager" OR "Dekanatsreferent" OR "Studiengangskoordinator" OR "Lehrinnovation") ("TV-L E13" OR "TV-L E14") site:.de', "de", "de"),
    ('("Stiftung Innovation in der Hochschullehre" OR "Learning Analytics" OR "Lehr-Lernforschung" OR "Transformative Hochschullehre") (Postdoc OR "wissenschaftliche Mitarbeiter" OR "akademische Mitarbeiter") site:.de', "de", "de"),

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

    # ── Pädagogische Hochschulen & Teacher Education Universities ─────────────
    ('site:stellenangebote.ph-freiburg.de OR site:ph-heidelberg.de OR site:ph-karlsruhe.de OR site:ph-ludwigsburg.de', "de", "de"),
    ('("Pädagogische Hochschule" OR "PH Freiburg" OR "PH Heidelberg") ("Projektkoordination" OR "Lehrinnovation" OR "wissenschaftliche Mitarbeiter" OR "TV-L")', "de", "de"),
    ('site:karriere.baden-wuerttemberg.de ("wissenschaftliche Mitarbeiter" OR "Postdoc" OR "TV-L E13" OR "TV-L E14")', "de", "de"),

    # ── German university ATS (white-label recruiting platforms) ──────────────
    # Many German unis outsource their careers pages to these ATS providers.
    # The university name is encoded in the subdomain: uni-leipzig.b-ite.careers
    ('site:b-ite.careers (postdoc OR "wissenschaftliche Mitarbeiter" OR "research associate")', "de", "de"),
    ('site:dvinci-hr.com (postdoc OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    ('site:softgarden.io (postdoc OR "wissenschaftliche Mitarbeiter") Germany', "de", "en"),
    ('site:persis.de (postdoc OR "wissenschaftliche Mitarbeiter")', "de", "de"),
    # interamt.de: German federal/state public sector vacancies (TV-L contracts)
    ('site:interamt.de (postdoc OR "wissenschaftliche Mitarbeiter" OR "TV-L E13" OR "TV-L E14")', "de", "de"),

    # ── Professorships & Junior Faculty (W1/W2/W3, Juniorprofessur, Tenure Track) ──
    # These are missed by postdoc-only queries; added as a separate sweep.
    ('site:psychjob.eu (Professur OR Juniorprofessur OR W2 OR W3 OR "tenure track")', "de", "de"),
    ('site:academics.de/jobs (Professur OR Juniorprofessur OR "W2-Professur" OR "W3-Professur")', "de", "de"),
    ('site:hsozkult.de/job (Professur OR Juniorprofessur OR "tenure track")', "de", "de"),
    ('site:xing.com/jobs (Professur OR W2 OR W3 OR Juniorprofessur) (Wirtschaftspsychologie OR Bildungsforschung OR Arbeitsmarkt)', "de", "de"),
    ('site:service.bund.de/IMPORTE/Stellenangebote (Professur OR Juniorprofessur OR "tenure track" OR W2 OR W3)', "de", "de"),
    ('site:lmu.de (Professur OR W2 OR W3 OR Juniorprofessur)', "de", "de"),
    ('site:uni-mannheim.de (Professur OR Juniorprofessur OR "tenure track")', "de", "de"),
    ('site:uni-leipzig.de (Professur OR Juniorprofessur OR W2 OR W3)', "de", "de"),
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
    """Academics.de direct HTML — postdoc + professorship queries.

    Uses article/div.job-item/[data-qa='job-item'] card containers matching
    academics.de's actual DOM structure rather than generic anchor scans.
    """
    queries = [
        "Postdoc", "Wissenschaftliche+Mitarbeiter", "Postdoktorand",
        "wissenschaftlicher+Mitarbeiter", "Akademische+Mitarbeiter",
        "Lehrinnovation", "Hochschuldidaktik", "Transformative+Hochschullehre",
        "Campus+im+Dialog", "Wissenschaftsmanagement", "Qualitaetsentwicklung",
        # Professorship & discipline terms
        "Professur", "Juniorprofessur", "W2",
        "Wirtschaftspsychologie", "Arbeitsmarkt", "Bildungsforschung",
    ]
    urls = [
        f"https://www.academics.de/stellenanzeigen?q={q}" for q in queries
    ] + [
        "https://www.academics.de/stellenanzeigen/branche-wissenschaftsmanagement/Sg==",
        "https://www.academics.de/stellenanzeigen/branche-wissenschaftsmanagement/Sg==?offset=50",
    ]
    results = []
    seen_links: set = set()
    # Card-level selectors matching academics.de job listing DOM
    CARD_SEL = "article, div.job-item, [data-qa='job-item'], div[class*='job-card']"
    for url in urls:
        try:
            res = await client.get(url, headers=HEADERS, timeout=20.0)
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select(CARD_SEL)
            # Fallback: scan all job-path anchors if no cards found
            anchors = (
                [c.select_one("a[href*='/jobs/']") for c in cards]
                if cards
                else soup.select("a[href*='/jobs/']")
            )
            for a in anchors:
                if not a:
                    continue
                title = a.get_text(strip=True)
                href  = a.get("href", "")
                if not href or not title or len(title) < 10:
                    continue
                if "/stellenanzeigen/" in href or "page=" in href:
                    continue
                full = href if href.startswith("http") else f"https://www.academics.de{href}"
                if full in seen_links:
                    continue
                seen_links.add(full)
                # Rich snippet from the card container
                card = a.find_parent("article") or a.find_parent("div") or a.parent
                snippet = card.get_text(" ", strip=True)[:400] if card else title
                results.append(RawVacancy(
                    source="Academics.de SSR", title=title, link=full,
                    snippet=snippet, query_type="ssr_html",
                ))
        except Exception:
            continue
    return results


async def fetch_bund_rss(client: httpx.AsyncClient) -> List[RawVacancy]:
    """service.bund.de native XML RSS feed.

    Legally mandated portal for ALL German federal/state public sector vacancies,
    including W2/W3 professorships at state universities (TV-L contracts).
    Zero API cost — pure RSS/XML, no scraping needed.
    """
    url = "https://www.service.bund.de/Content/Globals/Functions/RSSFeed/RSSGenerator_Stellen.xml"
    try:
        import feedparser
        res = await client.get(url, headers=HEADERS, timeout=20.0)
        feed = feedparser.parse(res.text)
        results = []
        for entry in feed.entries:
            link  = entry.get("link", "")
            title = entry.get("title", "")
            snippet = entry.get("description", "") or entry.get("summary", "")
            if link and title:
                results.append(RawVacancy(
                    source="RSS Bund.de",
                    title=title,
                    link=link,
                    snippet=snippet[:400],
                    query_type="rss_feed",
                ))
        return results
    except Exception as e:
        print(f"  [bund_rss] Error: {e}")
        return []


async def fetch_ssr_euraxess(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes research, postdoctoral, and academic vacancies from EURAXESS Germany."""
    queries = ["postdoc", "higher+education", "educational+research"]
    results: List[RawVacancy] = []
    seen_urls: set = set()

    for q in queries:
        url = f"https://euraxess.ec.europa.eu/jobs/search?keywords={q}&f%5B0%5D=country%3Agermany"
        try:
            res = await client.get(url, headers=HEADERS, timeout=20.0)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select("article, .views-row, .node--type-job-offer, div[class*='job-card']")
            for card in cards:
                link_el = card.select_one("h2 a, h3 a, a[href*='/jobs/'], a[href*='node/']")
                if not link_el:
                    continue
                title = link_el.get_text(strip=True)
                if len(title) < 6 or "newest" in title.lower():
                    continue
                href = link_el.get("href", "")
                full = href if href.startswith("http") else f"https://euraxess.ec.europa.eu{href}"
                if full in seen_urls:
                    continue
                seen_urls.add(full)
                card_text = card.get_text(" ", strip=True)[:400]
                results.append(RawVacancy(
                    source="EURAXESS SSR",
                    title=title,
                    link=full,
                    snippet=card_text,
                    query_type="ssr_html",
                ))
        except Exception:
            continue
    return results


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


async def fetch_ssr_wissmanagement_online(client: httpx.AsyncClient, max_pages: int = 3) -> List[RawVacancy]:
    """Scrape Wissenschaftsmanagement Online — hub for higher education governance & innovation across multiple pages."""
    base_url = "https://www.wissenschaftsmanagement-online.de/kategorie/alle-themen/aktivitaeten"
    results = []
    seen: set = set()

    for page in range(max_pages):
        page_url = base_url if page == 0 else f"{base_url}?page={page}"
        try:
            res = await client.get(page_url, headers=HEADERS, timeout=20.0)
            if res.status_code != 200:
                break
            soup = BeautifulSoup(res.text, "html.parser")
            cards = soup.select("div.text")
            if not cards:
                break

            for card in cards:
                card_text = card.get_text(" ", strip=True)

                # Extract title link
                title_link = None
                for a in card.find_all("a", href=True):
                    href = a["href"]
                    text = a.get_text(strip=True)
                    if (
                        "/users/" not in href
                        and "/user/" not in href
                        and not text.lower().startswith("by ")
                        and not text.lower().startswith("von ")
                        and len(text) > 5
                    ):
                        title_link = a
                        break

                if not title_link:
                    continue

                full = title_link["href"] if title_link["href"].startswith("http") else f"https://www.wissenschaftsmanagement-online.de{title_link['href']}"
                if full in seen:
                    continue
                seen.add(full)

                results.append(RawVacancy(
                    source="WissManagement Online SSR",
                    title=title_link.get_text(strip=True),
                    link=full,
                    snippet=card_text[:400],
                    query_type="ssr_html",
                ))
        except Exception:
            break

    return results


async def scrape_all_sources() -> List[RawVacancy]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        tasks = [
            # ── Serper / API sources ───────────────────────────────────────────
            fetch_german_boards(client),      # 64 Serper queries (postdoc + professorship)
            fetch_google_news(client),        # 2 SerpAPI news queries, gl=de
            fetch_exa(client),                # 4 Exa semantic queries (Germany-scoped)
            fetch_all_rss(client),            # 4 RSS feeds
            fetch_bund_rss(client),           # service.bund.de XML — federal/state vacancies
            # ── SSR aggregators ────────────────────────────────────────────────
            fetch_ssr_academics(client),      # academics.de (postdoc + professorship queries + WissManagement hub)
            fetch_ssr_wissmanagement_online(client), # Wissenschaftsmanagement Online
            fetch_ssr_euraxess(client),       # EURAXESS Germany-filtered
            fetch_ssr_psychjob(client),       # psychjob.eu (DGPs portal) — category list
            fetch_ssr_hsozkult(client),       # H-Soz-Kult (social science & humanities)
            fetch_ssr_stellenwerk(client),    # Stellenwerk (multi-campus network)
            # ── Direct university career pages (zero API cost) ─────────────────
            fetch_direct_lmu(client),
            fetch_direct_hu_berlin(client),
            fetch_direct_tu_berlin(client),
            fetch_direct_uni_leipzig(client),
            fetch_direct_uni_heidelberg(client),
            fetch_direct_uni_koeln(client),
            fetch_direct_uni_muenster(client),
            fetch_direct_ph_freiburg(client),
            fetch_direct_karriere_bw(client),
            fetch_direct_mlu_halle(client),
            fetch_direct_tu_dresden(client),
            fetch_direct_uni_jena(client),
            fetch_direct_ovgu_magdeburg(client),
            # ── Universities of Applied Sciences (HAW / Fachhochschulen) ──────
            fetch_direct_eah_jena(client),
            fetch_direct_h2_magdeburg(client),
            fetch_direct_htwk_leipzig(client),
            fetch_direct_hs_merseburg(client),
            # ── PsychJob direct — extracts individual /job/ links from categories ─
            fetch_psychjob_direct(client),
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
        if res.status_code != 200:
            return []
        soup = BeautifulSoup(res.text, "html.parser")
        results: List[RawVacancy] = []
        seen_urls: set = set()
        items = soup.select(".news-list-item, .item, article, [class*='news-list'], [class*='teaser'], div.ce-div")
        for item in items:
            link_el = item.select_one("a[href*='newsdetail'], a[href*='artikel'], a[href*='stelle'], a[href*='.pdf'], a")
            if not link_el:
                continue
            heading_el = item.select_one("h2, h3, h4, .header, strong")
            title = heading_el.get_text(strip=True) if heading_el else ""
            if not title or len(title) < 5:
                raw_lines = [line.strip() for line in item.get_text("\n").split("\n") if line.strip()]
                title = next((l for l in raw_lines if not l.startswith("∙") and "mehr erfahren" not in l.lower() and len(l) > 5), raw_lines[0] if raw_lines else "")
            if not title or len(title) < 6 or "news filtern" in title.lower() or "stellenausschreibungen" in title.lower():
                continue
            href = link_el.get("href", "")
            full = href if href.startswith("http") else f"https://www.uni-leipzig.de{href}"
            if full in seen_urls:
                continue
            seen_urls.add(full)
            item_text = item.get_text(" ", strip=True)
            results.append(RawVacancy(
                source="Uni Leipzig Direct",
                title=title,
                link=full,
                snippet=item_text[:400],
                query_type="direct_uni_ssr",
            ))
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


async def fetch_direct_uni_muenster(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Uni Münster — direct vacancies listing."""
    url = "https://www.uni-muenster.de/Rektorat/Stellen/"
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        soup = BeautifulSoup(res.text, "html.parser")
        results = []
        for item in soup.select("article, .content-box, li, tr, div.teaser, .content a"):
            a = item if item.name == "a" else item.select_one("a[href]")
            if not a or not a.get("href"):
                continue
            title = a.get_text(strip=True)
            href = a["href"]
            link = href if href.startswith("http") else f"https://www.uni-muenster.de{href}"
            snippet = item.get_text(" ", strip=True) if item != a else title
            if title and len(title) > 10 and any(w in (title + snippet).lower() for w in ["wissenschaft", "postdoc", "stelle", "ausschreibung"]):
                results.append(RawVacancy(source="Uni Münster Direct", title=title, link=link, snippet=snippet, query_type="direct_uni_ssr"))
        return results
    except Exception:
        return []


async def fetch_psychjob_direct(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrape individual job listings from PsychJob category pages.

    psychjob.eu runs on Drupal — job rows sit inside .views-row containers.
    Employer/location metadata lives in .views-field-field-employer or .field-content.
    Covers postdoc, Wiss.Mitarbeiter, Professur, and Juniorprofessur categories.
    Fallback to direct a[href*='/job/'] scan if Drupal layout changes.
    """
    categories = [
        # German postdoc & researcher categories
        "https://www.psychjob.eu/de/jobs/arbeits-betriebs-und-organisationspsychologie",
        "https://www.psychjob.eu/de/jobs/lehre-forschung",
        "https://www.psychjob.eu/de/jobs/personalpsychologie",
        # Professorship & junior faculty
        "https://www.psychjob.eu/de/jobs/professur",
        "https://www.psychjob.eu/de/jobs/juniorprofessur",
        "https://www.psychjob.eu/de/jobs/wirtschaftspsychologie",
        # English-language category (catches bilingual listings)
        "https://www.psychjob.eu/en/jobs/work-organisational-psychology",
    ]
    seen: set = set()
    results: List[RawVacancy] = []
    for url in categories:
        try:
            res = await client.get(url, headers=HEADERS, timeout=15.0)
            soup = BeautifulSoup(res.text, "html.parser")

            # Primary: Drupal .views-row containers
            rows = soup.select(".views-row")
            if rows:
                for row in rows:
                    link_tag = row.select_one("a[href*='/job/']")
                    if not link_tag:
                        continue
                    href  = link_tag.get("href", "")
                    full  = href if href.startswith("http") else f"https://www.psychjob.eu{href}"
                    if full in seen:
                        continue
                    seen.add(full)
                    title = link_tag.get_text(strip=True)
                    # Employer/location from Drupal field containers
                    meta  = row.select_one(
                        ".views-field-field-employer, .views-field-field-location, .field-content, p"
                    )
                    meta_text = meta.get_text(" ", strip=True) if meta else ""
                    snippet = f"{title} — {meta_text}" if meta_text else title
                    if title and len(title) > 10:
                        results.append(RawVacancy(
                            source="PsychJob Direct",
                            title=title,
                            link=full,
                            snippet=snippet[:400],
                            query_type="direct_uni_ssr",
                        ))
            else:
                # Fallback: flat anchor scan (handles layout changes)
                for a in soup.select("a[href*='/job/']"):
                    href = a.get("href", "")
                    full = href if href.startswith("http") else f"https://www.psychjob.eu{href}"
                    if full in seen:
                        continue
                    seen.add(full)
                    title = a.get_text(strip=True)
                    parent = a.find_parent(["li", "article", "div"])
                    snippet = parent.get_text(" ", strip=True) if parent else title
                    if title and len(title) > 10:
                        results.append(RawVacancy(
                            source="PsychJob Direct",
                            title=title,
                            link=full,
                            snippet=snippet[:400],
                            query_type="direct_uni_ssr",
                        ))
        except Exception:
            continue
    return results


async def fetch_direct_ph_freiburg(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes academic, teaching innovation, and scientific coordinator
    vacancies directly from Pädagogische Hochschule Freiburg Rexx portal.
    """
    url = "https://stellenangebote.ph-freiburg.de/stellenangebote.html"
    results: List[RawVacancy] = []
    seen: set = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            rows = soup.select("table tbody tr, .job-item, .stellen-item, tr")
            for row in rows:
                link_el = row.find("a", href=True)
                if not link_el:
                    continue
                title = link_el.get_text(strip=True)
                href = link_el["href"]
                if (
                    len(title) < 6
                    or "view job" in title.lower()
                    or "stellenbezeichnung" in title.lower()
                    or "order[" in href
                    or "order%5b" in href.lower()
                ):
                    continue
                full = href if href.startswith("http") else f"https://stellenangebote.ph-freiburg.de/{href.lstrip('/')}"
                if full in seen:
                    continue
                seen.add(full)
                snippet = row.get_text(" ", strip=True)[:400]
                results.append(RawVacancy(
                    source="PH Freiburg Direct",
                    title=title,
                    link=full,
                    snippet=snippet,
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


async def fetch_direct_karriere_bw(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes state university and public service notices from Karriere Baden-Württemberg."""
    url = "https://karriere.baden-wuerttemberg.de/de/startseite/stellenanzeigen"
    results: List[RawVacancy] = []
    seen: set = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            links = soup.select('a[href*="/einzelansicht/job/"], a[href*="/job/"]')
            for link in links:
                href = link.get("href", "")
                full = href if href.startswith("http") else f"https://karriere.baden-wuerttemberg.de{href}"
                if full in seen:
                    continue
                title = link.get_text(strip=True)
                card = link.find_parent(["article", "li", "div"]) or link
                if not title or len(title) < 5 or "stelle" in title.lower() or "ansehen" in title.lower():
                    heading = card.find(["h2", "h3", "h4", "strong"])
                    if heading:
                        title = heading.get_text(strip=True)
                if len(title) < 6:
                    continue
                seen.add(full)
                snippet = card.get_text(" ", strip=True)[:400]
                results.append(RawVacancy(
                    source="Karriere BW Direct",
                    title=title,
                    link=full,
                    snippet=snippet,
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


async def fetch_direct_mlu_halle(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes academic and postdoctoral vacancies from Martin-Luther-Universität Halle-Wittenberg."""
    url = "https://personal.verwaltung.uni-halle.de/jobs/wissmi/"
    results: List[RawVacancy] = []
    seen: set = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=lambda h: h and "/Ausschr/" in h):
                container = a.find_parent("div")
                if not container:
                    continue
                text = container.get_text(" ", strip=True)
                pdf_url = a["href"]
                if pdf_url in seen:
                    continue
                seen.add(pdf_url)
                
                title = "Wissenschaftliche*r Mitarbeiter*in"
                title_m = re.search(r"(Wiss\.\s*Mitarbeiter[^\n\[]+|Research\s+Associate[^\n\[]+|Akademische[^\n\[]+)", text, re.I)
                if title_m:
                    title = title_m.group(1).strip()
                
                results.append(RawVacancy(
                    source="MLU Halle Direct",
                    title=title,
                    link=pdf_url,
                    snippet=text[:400],
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


async def fetch_direct_tu_dresden(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes academic, postdoctoral, and research staff vacancies from TU Dresden."""
    url = "https://www.verw.tu-dresden.de/StellAus/stellen.asp?kat=2&lang=de"
    results: List[RawVacancy] = []
    seen: set = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=lambda h: h and "stelle.asp" in h):
                parent = a.find_parent(["li", "div", "p"]) or a.parent
                text = parent.get_text(" ", strip=True)
                title = a.get_text(strip=True)
                href = a["href"]
                full_url = href if href.startswith("http") else requests.compat.urljoin(url, href) if 'requests' in globals() else f"https://www.verw.tu-dresden.de/StellAus/{href.lstrip('/')}"
                if full_url in seen:
                    continue
                seen.add(full_url)
                
                results.append(RawVacancy(
                    source="TU Dresden Direct",
                    title=title,
                    link=full_url,
                    snippet=text[:400],
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


async def fetch_direct_uni_jena(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes academic staff, postdoc, and scientific coordinator vacancies from Uni Jena."""
    url = "https://www.uni-jena.de/122166/stellenangebote"
    results: List[RawVacancy] = []
    seen: set = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=lambda h: h and "jobs.uni-jena.de/jobposting/" in h):
                href = a["href"].split("?")[0]
                if href in seen:
                    continue
                seen.add(href)
                title = a.get_text(strip=True)
                if not title or len(title) < 5 or "teilen" in title.lower():
                    continue
                container = a.find_parent(["div", "li", "tr", "article"]) or a
                text = container.get_text(" ", strip=True)
                results.append(RawVacancy(
                    source="Uni Jena Direct",
                    title=title,
                    link=href,
                    snippet=text[:400],
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


async def fetch_direct_ovgu_magdeburg(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes scientific staff and postdoc vacancies from Otto-von-Guericke-Universität Magdeburg."""
    url = "https://www.ovgu.de/Karriere_wissenschaftlichesPersonal.html"
    results: List[RawVacancy] = []
    seen: set = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=lambda h: h and "b-ite.careers/jobposting/" in h):
                href = a["href"].split("?")[0]
                if href in seen:
                    continue
                seen.add(href)
                title = a.get_text(strip=True)
                container = a.find_parent(["div", "li", "p", "article"]) or a
                text = container.get_text(" ", strip=True)
                results.append(RawVacancy(
                    source="OVGU Magdeburg Direct",
                    title=title,
                    link=href,
                    snippet=text[:400],
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


# ---------------------------------------------------------------------------
# Synchronous helper methods for the 5 regional universities
# ---------------------------------------------------------------------------

def scrape_mlu_halle() -> List[Dict[str, Any]]:
    """Synchronous scraper for MLU Halle."""
    import requests
    url = "https://personal.verwaltung.uni-halle.de/jobs/wissmi/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200: return []
    except Exception: return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs = []
    for p in soup.find_all(["p", "div"]):
        text = p.get_text(" ", strip=True)
        if not ("Reg. No." in text or "Reg.-Nr." in text or "Research Associate" in text or "Wissenschaftliche" in text):
            continue
        link = p.find("a", href=True)
        full_url = requests.compat.urljoin(url, link["href"]) if link else url
        deadline_match = re.search(r"(?:accepted until|Bewerbungen bis|Frist:?)\s*([A-Za-z0-9\.,\s]+2026|[0-9]{2}\.[0-9]{2}\.[0-9]{2,4})", text, re.I)
        reg_match = re.search(r"Reg\.\s*(?:No\.|Nr\.)\s*([0-9\/\-A-Za-z]+)", text)
        lines = [l.strip() for l in p.get_text("\n").split("\n") if l.strip()]
        title = next((l for l in lines if any(k in l.lower() for k in ["research associate", "wissenschaftliche", "postdoc", "akademische"])), lines[0] if lines else "Academic Position")
        if len(title) >= 6:
            jobs.append({
                "title": title,
                "ref_no": reg_match.group(1) if reg_match else "N/A",
                "organization": "Martin-Luther-Universität Halle-Wittenberg",
                "location": "Halle (Saale), Germany",
                "deadline": deadline_match.group(1).strip() if deadline_match else "Check notice",
                "pay_grade": "TV-L E 13",
                "url": full_url,
                "source": "MLU Halle Portal",
                "raw_text": text
            })
    return jobs


def scrape_uni_leipzig() -> List[Dict[str, Any]]:
    """Synchronous scraper for Universität Leipzig."""
    import requests
    url = "https://www.uni-leipzig.de/universitaet/arbeiten-an-der-universitaet-leipzig/stellenausschreibungen"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200: return []
    except Exception: return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs, seen = [], set()
    for item in soup.select(".news-list-item, .item, article, [class*='news-list'], div.ce-div"):
        link = item.select_one("a[href*='newsdetail'], a[href*='artikel'], a[href*='stelle'], a")
        if not link: continue
        full_url = requests.compat.urljoin(url, link.get("href", ""))
        if full_url in seen: continue
        seen.add(full_url)
        heading = item.select_one("h2, h3, h4, .header, strong")
        title = heading.get_text(strip=True) if heading else link.get_text(strip=True)
        if len(title) < 6 or "stellenausschreibungen" in title.lower(): continue
        text = item.get_text(" ", strip=True)
        date_match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
        jobs.append({
            "title": title,
            "ref_no": "N/A",
            "organization": "Universität Leipzig",
            "location": "Leipzig, Germany (22 min commute)",
            "deadline": date_match.group(0) if date_match else "Current notice",
            "pay_grade": "TV-L E 13",
            "url": full_url,
            "source": "Uni Leipzig Portal",
            "raw_text": text
        })
    return jobs


def scrape_uni_jena() -> List[Dict[str, Any]]:
    """Synchronous scraper for Uni Jena."""
    import requests
    url = "https://www.uni-jena.de/122166/stellenangebote"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200: return []
    except Exception: return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs, seen = [], set()
    for link in soup.select("a[href]"):
        title = link.get_text(strip=True)
        full_url = requests.compat.urljoin(url, link.get("href", ""))
        if len(title) < 10 or full_url in seen: continue
        container = link.find_parent(["div", "li", "tr", "article"]) or link
        text = container.get_text(" ", strip=True)
        if not any(k in (title + " " + text).lower() for k in ["wissenschaft", "postdoc", "research", "akademisch", "lehrstuhl", "professur"]):
            continue
        seen.add(full_url)
        deadline_match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
        jobs.append({
            "title": title,
            "ref_no": "N/A",
            "organization": "Friedrich-Schiller-Universität Jena",
            "location": "Jena, Germany (45 min commute)",
            "deadline": deadline_match.group(0) if deadline_match else "Check listing",
            "pay_grade": "TV-L E 13",
            "url": full_url,
            "source": "Uni Jena Portal",
            "raw_text": text
        })
    return jobs


def scrape_ovgu_magdeburg() -> List[Dict[str, Any]]:
    """Synchronous scraper for OVGU Magdeburg."""
    import requests
    url = "https://www.ovgu.de/Karriere_WissenschaftlichesPersonal.html"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200: return []
    except Exception: return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs, seen = [], set()
    for link in soup.select("a[href]"):
        text = link.get_text(" ", strip=True)
        if not ("Research Associate" in text or "Wissenschaftliche" in text or "Postdoc" in text or "Ref. No." in text):
            continue
        full_url = requests.compat.urljoin(url, link.get("href", ""))
        if full_url in seen: continue
        seen.add(full_url)
        title_match = re.search(r"^(.*?)(?:Faculty|Department|Application|$)", text, re.I)
        title = title_match.group(1).strip() if title_match else text.split("\n")[0]
        ref_match = re.search(r"Ref\.\s*(?:No\.|Nr\.)\s*[:\s]*([0-9\/\-_A-Za-z]+)", text)
        deadline_match = re.search(r"Application deadline:\s*([A-Za-z0-9\s,]+2026)", text, re.I)
        jobs.append({
            "title": title,
            "ref_no": ref_match.group(1) if ref_match else "N/A",
            "organization": "Otto-von-Guericke-Universität Magdeburg",
            "location": "Magdeburg, Germany (50 min commute)",
            "deadline": deadline_match.group(1).strip() if deadline_match else "Check listing",
            "pay_grade": "TV-L E 13",
            "url": full_url,
            "source": "OVGU Magdeburg Portal",
            "raw_text": text
        })
    return jobs


def scrape_tu_dresden() -> List[Dict[str, Any]]:
    """Synchronous scraper for TU Dresden."""
    import requests
    url = "https://www.verw.tu-dresden.de/StellAus/stellen.asp?kat=2&lang=de"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200: return []
    except Exception: return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs, seen = [], set()
    for li in soup.select("li:has(a), p:has(a)"):
        link = li.find("a", href=True)
        if not link: continue
        full_url = requests.compat.urljoin(url, link["href"])
        if full_url in seen: continue
        seen.add(full_url)
        title = link.get_text(strip=True)
        if len(title) < 8 or "back to overview" in title.lower(): continue
        text = li.get_text(" ", strip=True)
        deadline_match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
        pay_match = re.search(r"(?:E|EG|TV-L|BesGr)\s*(?:E\s*)?(?:13|14|15|A\s*13|A\s*14)", text, re.I)
        jobs.append({
            "title": title,
            "ref_no": "N/A",
            "organization": "Technische Universität Dresden",
            "location": "Dresden, Germany (1h 25m commute)",
            "deadline": deadline_match.group(0) if deadline_match else "Check listing",
            "pay_grade": pay_match.group(0) if pay_match else "TV-L E 13",
            "url": full_url,
            "source": "TU Dresden Admin Portal",
            "raw_text": text
        })
    return jobs


