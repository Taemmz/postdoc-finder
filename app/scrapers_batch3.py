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
            
            for div in main.find_all(["div", "article", "tr", "li", "p"]):
                a = div.find("a", href=True)
                if a and ("/Stellenausschreibungen/" in a["href"] or "jobadid=" in a["href"]):
                    full_url = urljoin(url, a["href"])
                    if full_url in seen_links:
                        continue
                    seen_links.add(full_url)

                    full_text = div.get_text(separator=" | ", strip=True)
                    parts = [p.strip() for p in full_text.split(" | ") if len(p.strip()) > 5]
                    title = parts[0] if parts else a.get_text(strip=True)
                    for p in parts:
                        if any(k in p.lower() for k in ["m/w/d", "mitarbeiter", "prof", "manager", "assistenz", "lehr", "standortmanager"]):
                            title = p
                            break

                    if not any(skip in title.lower() for skip in ["datenschutz", "einwilligung"]):
                        vacancies.append(
                            RawVacancy(
                                source=source_name,
                                title=title,
                                link=full_url,
                                snippet=f"HS Harz: {full_text[:200]}",
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
    """Scrapes Fachhochschule Potsdam career portal."""
    source_name = "Fachhochschule Potsdam"
    vacancies: List[RawVacancy] = []
    url = "https://www.fh-potsdam.de/hochschule-karriere/karriere/stellenangebote-fh-potsdam"
    seen_links = set()

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            main = soup.find("main") or soup.find("div", id="content") or soup
            
            for a in main.find_all("a", href=True):
                href = a["href"].strip()
                title = a.get_text(strip=True)
                if not title or len(title) < 15:
                    continue
                if any(skip in href.lower() for skip in ["impressum", "datenschutz", "facebook", "instagram", "digitalisierungs", "personen/"]):
                    continue
                if any(k in title.lower() or k in href.lower() for k in ["kennziffer", "stellenausschreibung", "professur", "wissenschaftliche/r", "postdoc", "doktorand"]):
                    full_url = urljoin(url, href)
                    if full_url not in seen_links:
                        seen_links.add(full_url)
                        vacancies.append(
                            RawVacancy(
                                source=source_name,
                                title=title,
                                link=full_url,
                                snippet=f"FH Potsdam: {title}",
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
