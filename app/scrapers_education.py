"""scrapers_education.py — Specialized scrapers for Pedagogical Universities (Pädagogische Hochschulen)
and German Educational Science & Higher Education Research Institutes.

Monitored Institutions:
  1. DIPF Leibniz Institute for Educational Research and Information (Frankfurt/Berlin)
  2. DZHW German Centre for Higher Education Research and Science Studies (Hannover/Berlin)
  3. DIE Bonn — Leibniz Institute for Adult Education & Lifelong Learning
  4. Stiftung Innovation in der Hochschullehre (StIL)
  5. PH Ludwigsburg (Pädagogische Hochschule Ludwigsburg)
  6. PH Karlsruhe (Pädagogische Hochschule Karlsruhe)
  7. PH Heidelberg (Pädagogische Hochschule Heidelberg)
  8. Wissenschaftsmanagement Online (WIM'O)
"""

import re
import asyncio
from typing import List, Set
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.models import RawVacancy

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
}


async def fetch_dipf_vacancies(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes academic and research management postings from DIPF Leibniz Institute."""
    url = "https://www.dipf.de/de/dipf-aktuell/stellenangebote"
    results: List[RawVacancy] = []
    seen: Set[str] = set()
    try:
        res = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for h in soup.find_all(["h2", "h3", "h4"]):
                a = h.find("a", href=True)
                if not a:
                    continue
                title = a.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
                href = a["href"]
                full_url = urljoin(url, href)
                if full_url in seen or len(title) < 6:
                    continue
                seen.add(full_url)
                parent = h.find_parent(["article", "div", "li"]) or h
                snippet = parent.get_text(" ", strip=True)[:400].replace("\xad", "").replace("\u200b", "")
                results.append(
                    RawVacancy(
                        source="DIPF Leibniz Institut",
                        title=title,
                        link=full_url,
                        snippet=snippet,
                        query_type="education_institute_ssr",
                    )
                )
    except Exception as e:
        print(f"  [dipf] Warning: {e}")
    return results


async def fetch_dzhw_vacancies(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes higher education & science research postings from DZHW."""
    url = "https://www.dzhw.eu/gmbh/karriere"
    results: List[RawVacancy] = []
    seen: Set[str] = set()
    try:
        res = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                title = a.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
                if any(w in href.lower() or w in title.lower() for w in ["stelle", "job", "ausschreibung", "pdf"]):
                    full_url = urljoin(url, href)
                    if full_url in seen or len(title) < 6 or "uebersicht" in title.lower():
                        continue
                    seen.add(full_url)
                    parent = a.find_parent(["li", "p", "div"]) or a
                    snippet = parent.get_text(" ", strip=True)[:400]
                    results.append(
                        RawVacancy(
                            source="DZHW Hochschulforschung",
                            title=title,
                            link=full_url,
                            snippet=snippet,
                            query_type="education_institute_ssr",
                        )
                    )
    except Exception as e:
        print(f"  [dzhw] Warning: {e}")
    return results


async def fetch_die_bonn_vacancies(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes adult education & TVET research postings from DIE Bonn."""
    url = "https://www.die-bonn.de/karriere"
    results: List[RawVacancy] = []
    seen: Set[str] = set()
    try:
        res = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                title = a.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
                if any(w in href.lower() or w in title.lower() for w in ["stelle", "job", "ausschreibung", ".pdf"]):
                    full_url = urljoin(url, href)
                    if full_url in seen or len(title) < 6:
                        continue
                    seen.add(full_url)
                    parent = a.find_parent(["li", "p", "div"]) or a
                    snippet = parent.get_text(" ", strip=True)[:400]
                    results.append(
                        RawVacancy(
                            source="DIE Bonn Institut",
                            title=title,
                            link=full_url,
                            snippet=snippet,
                            query_type="education_institute_ssr",
                        )
                    )
    except Exception as e:
        print(f"  [die_bonn] Warning: {e}")
    return results


async def fetch_stil_vacancies(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes higher education teaching innovation funding notices from Stiftung Innovation in der Hochschullehre."""
    url = "https://stiftung-hochschullehre.de/ueber-uns/offene-stellen/"
    results: List[RawVacancy] = []
    seen: Set[str] = set()
    try:
        res = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for item in soup.select("article, .job-item, .stellenangebot, .elementor-widget-container"):
                a = item.select_one("a[href]")
                if not a:
                    continue
                title = a.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
                if len(title) < 6 or "uebersicht" in title.lower():
                    heading = item.find(["h2", "h3", "h4", "strong"])
                    if heading:
                        title = heading.get_text(strip=True)
                full_url = urljoin(url, a["href"])
                if full_url in seen or len(title) < 6:
                    continue
                seen.add(full_url)
                snippet = item.get_text(" ", strip=True)[:400]
                results.append(
                    RawVacancy(
                        source="Stiftung Innovation Hochschullehre",
                        title=title,
                        link=full_url,
                        snippet=snippet,
                        query_type="education_institute_ssr",
                    )
                )
    except Exception as e:
        print(f"  [stil] Warning: {e}")
    return results


async def fetch_ph_ludwigsburg_vacancies(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes academic postings from PH Ludwigsburg."""
    url = "https://www.ph-ludwigsburg.de/hochschule/verwaltung/personalangelegenheiten/stellenangebote"
    results: List[RawVacancy] = []
    seen: Set[str] = set()
    try:
        res = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                title = a.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
                href = a["href"]
                if any(w in title.lower() or w in href.lower() for w in ["akademisch", "wissenschaft", "didaktik", "lehre", "stelle", "ausschreibung"]):
                    full_url = urljoin(url, href)
                    if full_url in seen or len(title) < 6 or "uebersicht" in title.lower():
                        continue
                    seen.add(full_url)
                    parent = a.find_parent(["li", "p", "div", "tr"]) or a
                    snippet = parent.get_text(" ", strip=True)[:400]
                    results.append(
                        RawVacancy(
                            source="PH Ludwigsburg Direct",
                            title=title,
                            link=full_url,
                            snippet=snippet,
                            query_type="ph_direct_ssr",
                        )
                    )
    except Exception as e:
        print(f"  [ph_ludwigsburg] Warning: {e}")
    return results


async def fetch_ph_karlsruhe_vacancies(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes academic postings from PH Karlsruhe."""
    url = "https://www.ph-karlsruhe.de/hochschule/karriere-und-stellenangebote"
    results: List[RawVacancy] = []
    seen: Set[str] = set()
    try:
        res = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                title = a.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
                href = a["href"]
                if any(w in title.lower() or w in href.lower() for w in ["akademisch", "wissenschaft", "didaktik", "lehre", "stelle", "ausschreibung", "pdf"]):
                    full_url = urljoin(url, href)
                    if full_url in seen or len(title) < 6:
                        continue
                    seen.add(full_url)
                    parent = a.find_parent(["li", "p", "div", "tr"]) or a
                    snippet = parent.get_text(" ", strip=True)[:400]
                    results.append(
                        RawVacancy(
                            source="PH Karlsruhe Direct",
                            title=title,
                            link=full_url,
                            snippet=snippet,
                            query_type="ph_direct_ssr",
                        )
                    )
    except Exception as e:
        print(f"  [ph_karlsruhe] Warning: {e}")
    return results


async def fetch_wissman_online_vacancies(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Scrapes higher education & science management listings from Wissenschaftsmanagement Online."""
    url = "https://www.wissenschaftsmanagement-online.de/kategorie/alle-themen/aktivitaeten"
    results: List[RawVacancy] = []
    seen: Set[str] = set()
    try:
        res = await client.get(url, headers=HEADERS, follow_redirects=True, timeout=12.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.select("article a[href], .views-row a[href], h2 a[href], h3 a[href]"):
                title = a.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
                href = a["href"]
                if len(title) > 10 and any(k in title.lower() for k in ["lehr", "professur", "mitarbeiter", "koordinator", "referent", "leitung", "management"]):
                    full_url = urljoin(url, href)
                    if full_url in seen:
                        continue
                    seen.add(full_url)
                    parent = a.find_parent(["article", "li", "div"]) or a
                    snippet = parent.get_text(" ", strip=True)[:400]
                    results.append(
                        RawVacancy(
                            source="Wissenschaftsmanagement Online",
                            title=title,
                            link=full_url,
                            snippet=snippet,
                            query_type="science_management_hub",
                        )
                    )
    except Exception as e:
        print(f"  [wissman_online] Warning: {e}")
    return results


async def scrape_education_institutes() -> List[RawVacancy]:
    """Aggregates all pedagogical universities and education research institute scrapers concurrently."""
    async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
        tasks = [
            fetch_dipf_vacancies(client),
            fetch_dzhw_vacancies(client),
            fetch_die_bonn_vacancies(client),
            fetch_stil_vacancies(client),
            fetch_ph_ludwigsburg_vacancies(client),
            fetch_ph_karlsruhe_vacancies(client),
            fetch_wissman_online_vacancies(client),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        all_vacancies: List[RawVacancy] = []
        for r in results:
            if isinstance(r, list):
                all_vacancies.extend(r)
        return all_vacancies
