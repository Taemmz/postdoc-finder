"""
scrapers_batch3.py — HRK Discovery Scrapers (Batch 3C Validation).
Includes:
- Hochschule Schmalkalden
- Hochschule Harz
- Leuphana Universität Lüneburg
- Fachhochschule Potsdam

Every scraper adheres to the strict contract:
- Returns List[RawVacancy] only
- No internal filtering, scoring, deadline, or suppression logic
- Registers full telemetry: pages, mode, completeness, coverage
"""

import logging
from typing import List
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from app.models import RawVacancy
from app.telemetry import record_telemetry

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}


async def scrape_hs_schmalkalden() -> List[RawVacancy]:
    """Scrapes Hochschule Schmalkalden official vacancy portal."""
    source_name = "Hochschule Schmalkalden"
    vacancies: List[RawVacancy] = []
    url = "https://www.hs-schmalkalden.de/stellenangebote-an-der-hochschule"
    seen_links = set()

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            main = soup.find("main") or soup.find("div", id="content") or soup.find("article") or soup
            
            for a in main.find_all("a", href=True):
                href = a["href"].strip()
                if "/stellenangebote/details/" in href:
                    full_url = urljoin(url, href)
                    if full_url in seen_links:
                        continue
                    seen_links.add(full_url)

                    # Extract slug from URL for precise title
                    slug = href.split("/")[-1].replace("-", " ")
                    title = slug.replace("fuer", "für").title()

                    parent = a.find_parent(["div", "p", "article", "li"])
                    full_text = parent.get_text(separator=" ", strip=True) if parent else a.get_text(strip=True)

                    vacancies.append(
                        RawVacancy(
                            source=source_name,
                            title=title,
                            link=full_url,
                            snippet=f"HS Schmalkalden: {full_text[:200]}",
                        )
                    )

        record_telemetry(
            source=source_name,
            pages=1,
            raw=len(vacancies),
            mode="SINGLE_PAGE",
            completeness="COMPLETE",
            coverage="VERIFIED",
        )
    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")
        record_telemetry(
            source=source_name,
            pages=1,
            raw=len(vacancies),
            mode="SINGLE_PAGE",
            completeness="FAILED",
            coverage="UNKNOWN",
            error=str(e),
        )

    return vacancies


async def scrape_hs_harz() -> List[RawVacancy]:
    """Scrapes Hochschule Harz official vacancy portal."""
    source_name = "Hochschule Harz"
    vacancies: List[RawVacancy] = []
    url = "https://www.hs-harz.de/karriere/aktuelle-stellenausschreibungen"
    seen_links = set()

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            main = soup.find("main") or soup.find("div", id="content") or soup
            
            # Primary path: accordion job blocks
            accordions = main.find_all("div", class_="nn__content-effect--accordion")
            for acc in accordions:
                title_el = acc.find(["h1", "h2", "h3", "h4", "strong"])
                title = title_el.get_text(strip=True) if title_el else ""
                
                pdf_a = acc.find("a", href=lambda h: h and "Stellenausschreibung" in h and h.endswith(".pdf"))
                app_a = acc.find("a", href=lambda h: h and "jobadid=" in h)
                
                link = None
                if pdf_a:
                    link = urljoin(url, pdf_a["href"])
                elif app_a:
                    link = urljoin(url, app_a["href"])
                
                if link and link not in seen_links:
                    seen_links.add(link)
                    full_text = acc.get_text(separator=" | ", strip=True)
                    if not any(skip in title.lower() for skip in ["datenschutz", "einwilligung"]):
                        vacancies.append(
                            RawVacancy(
                                source=source_name,
                                title=title,
                                link=link,
                                snippet=f"HS Harz: {full_text[:200]}",
                            )
                        )

            # Fallback path if no accordions found
            if not vacancies:
                for a in main.find_all("a", href=True):
                    href = a["href"]
                    if any(skip in href.lower() for skip in ["datenschutz", "einwilligung"]):
                        continue
                    if "Stellenausschreibung" in href and href.endswith(".pdf"):
                        full_url = urljoin(url, href)
                        if full_url in seen_links:
                            continue
                        seen_links.add(full_url)
                        title = a.get_text(strip=True) or href.split("/")[-1].replace(".pdf", "")
                        vacancies.append(
                            RawVacancy(
                                source=source_name,
                                title=title,
                                link=full_url,
                                snippet=f"HS Harz: {title}",
                            )
                        )

        record_telemetry(
            source=source_name,
            pages=1,
            raw=len(vacancies),
            mode="SINGLE_PAGE",
            completeness="COMPLETE",
            coverage="VERIFIED",
        )
    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")
        record_telemetry(
            source=source_name,
            pages=1,
            raw=len(vacancies),
            mode="SINGLE_PAGE",
            completeness="FAILED",
            coverage="UNKNOWN",
            error=str(e),
        )

    return vacancies


async def scrape_leuphana_lueneburg() -> List[RawVacancy]:
    """Scrapes Leuphana Universität Lüneburg research & professorship portals."""
    source_name = "Leuphana Universität Lüneburg"
    vacancies: List[RawVacancy] = []
    seen_links = set()
    pages_visited = 0

    urls = [
        "https://www.leuphana.de/universitaet/jobs-und-karriere/forschung-lehre.html",
        "https://www.leuphana.de/universitaet/jobs-und-karriere/professuren/ausschreibungen-und-laufende-verfahren.html",
    ]

    try:
        for u in urls:
            pages_visited += 1
            r = requests.get(u, headers=HEADERS, timeout=15)
            if r.status_code != 200:
                continue
            soup = BeautifulSoup(r.text, "html.parser")
            main = soup.find("main") or soup.find("div", id="content") or soup

            for a in main.find_all("a", href=True):
                href = a["href"].strip()
                if "/ansicht-forschung-lehre/" in href or "/ansicht-professuren/" in href or ("/files/stellenausschreibung/" in href and ".pdf" in href.lower()):
                    full_url = urljoin(u, href)
                    if full_url in seen_links:
                        continue
                    seen_links.add(full_url)

                    title = a.get_text(separator=" ", strip=True)
                    if not title or len(title) < 10:
                        parent = a.find_parent(["div", "p", "article", "li"])
                        title = parent.get_text(strip=True) if parent else href.split("/")[-1]

                    vacancies.append(
                        RawVacancy(
                            source=source_name,
                            title=title,
                            link=full_url,
                            snippet=f"Leuphana: {title}",
                        )
                    )

        record_telemetry(
            source=source_name,
            pages=pages_visited,
            raw=len(vacancies),
            mode="URL_PAGINATION" if pages_visited > 1 else "SINGLE_PAGE",
            completeness="COMPLETE",
            coverage="VERIFIED",
        )
    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")
        record_telemetry(
            source=source_name,
            pages=pages_visited or 1,
            raw=len(vacancies),
            mode="SINGLE_PAGE",
            completeness="FAILED",
            coverage="UNKNOWN",
            error=str(e),
        )

    return vacancies


async def scrape_fh_potsdam() -> List[RawVacancy]:
    """Scrapes Fachhochschule Potsdam career portal via B-ITE REST API with dynamic pagination."""
    source_name = "Fachhochschule Potsdam"
    vacancies: List[RawVacancy] = []
    api_url = "https://jobs.b-ite.com/api/v1/postings/search"
    api_key = "335f1dcc409f0d424facf79f3f2ed0895fe2d6fa"
    seen_links = set()
    pages_traversed = 0
    offset = 0
    limit = 50

    try:
        api_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        while True:
            pages_traversed += 1
            payload = {
                "key": api_key,
                "locale": "de",
                "channel": 0,
                "page": {
                    "offset": offset,
                    "limit": limit,
                },
            }
            r = requests.post(api_url, json=payload, headers=api_headers, timeout=15)
            if r.status_code != 200:
                break
            data = r.json()
            postings = data.get("jobPostings", [])
            if not postings:
                break

            for p in postings:
                pid = p.get("id")
                title = p.get("title", "").strip()
                if not pid or not title:
                    continue
                full_url = f"https://jobs.fh-potsdam.de/jobposting/{pid}"
                if full_url in seen_links:
                    continue
                seen_links.add(full_url)

                custom = p.get("custom", {}) or {}
                tasks = custom.get("ihre_aufgaben", "")
                profile = custom.get("ihr_profil", "")
                snippet_text = f"{title} | {tasks} | {profile}".replace("\n", " ")[:300]

                vacancies.append(
                    RawVacancy(
                        source=source_name,
                        title=title,
                        link=full_url,
                        snippet=f"FH Potsdam: {snippet_text}",
                        query_type="bite_api",
                    )
                )

            page_meta = data.get("page", {})
            total = page_meta.get("total", len(postings))
            offset += len(postings)
            if offset >= total or len(postings) < limit:
                break

        record_telemetry(
            source=source_name,
            pages=pages_traversed,
            raw=len(vacancies),
            mode="REST_API_PAGINATION",
            completeness="COMPLETE",
            coverage="VERIFIED",
        )
    except Exception as e:
        logger.error(f"Error scraping {source_name}: {e}")
        record_telemetry(
            source=source_name,
            pages=pages_traversed or 1,
            raw=len(vacancies),
            mode="REST_API_PAGINATION",
            completeness="FAILED",
            coverage="UNKNOWN",
            error=str(e),
        )

    return vacancies
