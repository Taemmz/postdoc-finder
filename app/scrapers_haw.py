"""
scrapers_haw.py - Universities of Applied Sciences (HAWs / Fachhochschulen)
Direct scrapers for regional institutions around Halle (Saale):
  - Ernst-Abbe-Hochschule Jena (EAH)
  - Hochschule Magdeburg-Stendal (h2)
  - HTWK Leipzig (Leipzig University of Applied Sciences)
  - Hochschule Merseburg (Direct neighbor to Halle - 10 min train)
"""

import re
from typing import Any, Dict, List
import httpx
import requests
from bs4 import BeautifulSoup

from app.models import RawVacancy

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8",
}


# ===========================================================================
# 1. Ernst-Abbe-Hochschule Jena (EAH Jena)
# ===========================================================================

def scrape_eah_jena() -> List[Dict[str, Any]]:
    """Scrapes active staff and teaching vacancies from EAH Jena."""
    url = "https://www.eah-jena.de/hochschule/stellenangebote"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs, seen = [], set()
    for link in soup.select("a[href*='jobposting/'], a[href*='stellenangebot'], a[href*='.pdf']"):
        href = link.get("href", "")
        full_url = requests.compat.urljoin(url, href)
        title = link.get_text(strip=True)
        if (
            len(title) < 6
            or full_url in seen
            or "zurueck" in title.lower()
            or "datenschutz" in title.lower()
            or "inhalt" in title.lower()
            or title.lower() in ["stellenangebote", "karriere"]
            or full_url.rstrip("/").endswith("/stellenangebote")
        ):
            continue
        seen.add(full_url)

        parent = link.find_parent(["tr", "li", "div", "article", "p"]) or link
        text = parent.get_text(" ", strip=True)
        deadline_match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
        pay_match = re.search(r"(?:E|EG|TV-L|BesGr|W)\s*(?:E\s*)?(?:10|11|12|13|14|15|A\s*13)", text, re.I)

        jobs.append({
            "title": title,
            "organization": "Ernst-Abbe-Hochschule Jena",
            "location": "Jena, Germany (45 min commute)",
            "deadline": deadline_match.group(0) if deadline_match else "Check notice",
            "pay_grade": pay_match.group(0) if pay_match else "TV-L",
            "url": full_url,
            "source": "EAH Jena Portal",
            "raw_text": text,
        })
    return jobs


async def fetch_direct_eah_jena(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Async scraper for EAH Jena."""
    url = "https://www.eah-jena.de/hochschule/stellenangebote"
    results: List[RawVacancy] = []
    seen = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for link in soup.select("a[href*='jobposting/'], a[href*='stellenangebot'], a[href*='.pdf']"):
                full_url = requests.compat.urljoin(url, link.get("href", ""))
                title = link.get_text(strip=True)
                if (
                    len(title) < 6
                    or full_url in seen
                    or "zurueck" in title.lower()
                    or "datenschutz" in title.lower()
                    or "inhalt" in title.lower()
                    or title.lower() in ["stellenangebote", "karriere"]
                    or full_url.rstrip("/").endswith("/stellenangebote")
                ):
                    continue
                seen.add(full_url)
                parent = link.find_parent(["tr", "li", "div", "article", "p"]) or link
                text = parent.get_text(" ", strip=True)
                results.append(RawVacancy(
                    source="EAH Jena Direct",
                    title=title,
                    link=full_url,
                    snippet=text[:400],
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


# ===========================================================================
# 2. Hochschule Magdeburg-Stendal (h2)
# ===========================================================================

def scrape_h2_magdeburg() -> List[Dict[str, Any]]:
    """Scrapes active vacancies from Hochschule Magdeburg-Stendal."""
    url = "https://www.h2.de/hochschule/jobs-und-karriere/stellenangebote.html"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs, seen = [], set()
    for item in soup.select("table tbody tr, .job-item, article, li:has(a[href*='.pdf']), li:has(a[href*='stelle'])"):
        link = item.find("a", href=True) if item.name != "a" else item
        if not link:
            continue
        full_url = requests.compat.urljoin(url, link.get("href", ""))
        title = link.get_text(strip=True)

        if len(title) < 8 or full_url in seen or "stellenangebote" in title.lower():
            continue
        seen.add(full_url)

        text = item.get_text(" ", strip=True)
        deadline_match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
        pay_match = re.search(r"(?:E|EG|TV-L|BesGr|W)\s*(?:E\s*)?(?:10|11|12|13|14|15)", text, re.I)

        jobs.append({
            "title": title,
            "organization": "Hochschule Magdeburg-Stendal",
            "location": "Magdeburg, Germany (50 min commute)",
            "deadline": deadline_match.group(0) if deadline_match else "Check listing",
            "pay_grade": pay_match.group(0) if pay_match else "TV-L",
            "url": full_url,
            "source": "HS Magdeburg-Stendal Portal",
            "raw_text": text,
        })
    return jobs


async def fetch_direct_h2_magdeburg(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Async scraper for Hochschule Magdeburg-Stendal."""
    url = "https://www.h2.de/hochschule/jobs-und-karriere/stellenangebote.html"
    results: List[RawVacancy] = []
    seen = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for item in soup.select("table tbody tr, .job-item, article, li:has(a[href*='.pdf']), li:has(a[href*='stelle'])"):
                link = item.find("a", href=True) if item.name != "a" else item
                if not link:
                    continue
                full_url = requests.compat.urljoin(url, link.get("href", ""))
                title = link.get_text(strip=True)
                if len(title) < 8 or full_url in seen or "stellenangebote" in title.lower():
                    continue
                seen.add(full_url)
                text = item.get_text(" ", strip=True)
                results.append(RawVacancy(
                    source="HS Magdeburg-Stendal Direct",
                    title=title,
                    link=full_url,
                    snippet=text[:400],
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


# ===========================================================================
# 3. HTWK Leipzig (Leipzig University of Applied Sciences)
# ===========================================================================

def scrape_htwk_leipzig() -> List[Dict[str, Any]]:
    """Fetches vacancies from HTWK Leipzig via b-ite API."""
    url = "https://jobs.b-ite.com/api/v1/postings/search"
    payload = {
        "key": "07459439a8d6d2568ef5398202d2346d855c9e12",
        "locale": "de",
        "channel": 0
    }
    jobs = []
    try:
        res = requests.post(url, json=payload, headers=HEADERS, timeout=15)
        if res.status_code == 200:
            for p in res.json().get("jobPostings", []):
                title = p.get("title", "")
                posting_id = p.get("id", "")
                link = f"https://jobs.htwk-leipzig.de/jobposting/{posting_id}"
                ends_on = p.get("endsOn", "")
                deadline = ends_on[:10] if ends_on else "Check listing"
                jobs.append({
                    "title": title,
                    "organization": "HTWK Leipzig",
                    "location": "Leipzig, Germany (25 min commute)",
                    "deadline": deadline,
                    "pay_grade": "TV-L / W",
                    "url": link,
                    "source": "HTWK Leipzig Portal",
                    "raw_text": f"{title} HTWK Leipzig Bewerbungsfrist: {deadline}",
                })
    except Exception:
        pass
    return jobs


async def fetch_direct_htwk_leipzig(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Async scraper for HTWK Leipzig."""
    url = "https://jobs.b-ite.com/api/v1/postings/search"
    payload = {
        "key": "07459439a8d6d2568ef5398202d2346d855c9e12",
        "locale": "de",
        "channel": 0
    }
    results: List[RawVacancy] = []
    try:
        res = await client.post(url, json=payload, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            for p in res.json().get("jobPostings", []):
                title = p.get("title", "")
                posting_id = p.get("id", "")
                link = f"https://jobs.htwk-leipzig.de/jobposting/{posting_id}"
                ends_on = p.get("endsOn", "")
                deadline = ends_on[:10] if ends_on else ""
                snippet = f"{title} HTWK Leipzig Bewerbungsschluss: {deadline}"
                results.append(RawVacancy(
                    source="HTWK Leipzig Direct",
                    title=title,
                    link=link,
                    snippet=snippet,
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results


# ===========================================================================
# 4. Hochschule Merseburg (Direct Neighbor to Halle - 10 min train)
# ===========================================================================

def scrape_hs_merseburg() -> List[Dict[str, Any]]:
    """Scrapes vacancies from Hochschule Merseburg."""
    url = "https://www.hs-merseburg.de/hochschule/information/stellenausschreibungen/"
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs, seen = [], set()
    for link in soup.select("a[href*='neuigkeiten/details/'], a[href*='stellenangebote'], a[href*='.pdf']"):
        href = link.get("href", "")
        full_url = requests.compat.urljoin(url, href)
        title = link.get_text(strip=True)

        if len(title) < 8 or full_url in seen or "uebersicht" in title.lower() or "stellenangebote" in title.lower():
            continue
        seen.add(full_url)

        parent = link.find_parent(["tr", "li", "div", "article", "p"]) or link
        text = parent.get_text(" ", strip=True)
        deadline_match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
        pay_match = re.search(r"(?:E|EG|TV-L|BesGr)\s*(?:E\s*)?(?:10|11|12|13|14|15)", text, re.I)

        jobs.append({
            "title": title,
            "organization": "Hochschule Merseburg",
            "location": "Merseburg, Germany (10 min commute)",
            "deadline": deadline_match.group(0) if deadline_match else "Check listing",
            "pay_grade": pay_match.group(0) if pay_match else "TV-L",
            "url": full_url,
            "source": "HS Merseburg Portal",
            "raw_text": text,
        })
    return jobs


async def fetch_direct_hs_merseburg(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Async scraper for Hochschule Merseburg."""
    url = "https://www.hs-merseburg.de/hochschule/information/stellenausschreibungen/"
    results: List[RawVacancy] = []
    seen = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for link in soup.select("a[href*='neuigkeiten/details/'], a[href*='stellenangebote'], a[href*='.pdf']"):
                full_url = requests.compat.urljoin(url, link.get("href", ""))
                title = link.get_text(strip=True)
                if len(title) < 8 or full_url in seen or "uebersicht" in title.lower() or "stellenangebote" in title.lower():
                    continue
                seen.add(full_url)
                parent = link.find_parent(["tr", "li", "div", "article", "p"]) or link
                text = parent.get_text(" ", strip=True)
                results.append(RawVacancy(
                    source="HS Merseburg Direct",
                    title=title,
                    link=full_url,
                    snippet=text[:400],
                    query_type="direct_uni_ssr",
                ))
    except Exception:
        pass
    return results
