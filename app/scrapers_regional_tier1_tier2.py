"""
scrapers_regional_tier1_tier2.py — Direct scrapers for Tier 1 & Tier 2 Regional Expansion:
- Universität Erfurt (B-ite / ATS)
- Bauhaus-Universität Weimar (Central Academic Gazette)
- Universität Potsdam (Dezernat 3 Academic Staff)
- Universität Hildesheim (Teacher Education / Didactics Hub)
"""

import re
from typing import Any, Dict, List
from urllib.parse import urljoin
import httpx
import requests
from bs4 import BeautifulSoup
from app.models import RawVacancy
from app.telemetry import record_telemetry

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8",
}


# ---------------------------------------------------------------------------
# 1. Universität Erfurt (B-ite ATS & Direct Portal)
# ---------------------------------------------------------------------------
def scrape_uni_erfurt() -> List[Dict[str, Any]]:
    """Synchronous scraper for Universität Erfurt."""
    url = "https://jobs.uni-erfurt.de/"
    jobs = []
    seen = set()
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return []
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/jobposting/" in href:
                title = a.get_text(strip=True)
                if len(title) < 8 or any(x in title.lower() for x in ["impressum", "datenschutz", "zurück"]):
                    continue
                full_url = urljoin(url, href)
                if full_url in seen:
                    continue
                seen.add(full_url)
                parent = a.find_parent(["tr", "li", "div", "p"]) or a
                text = parent.get_text(" ", strip=True)
                deadline = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
                pay = re.search(r"(?:E|EG|TV-L|BesGr|W)\s*(?:E\s*)?(?:10|11|12|13|14|15|A\s*13)", text, re.I)
                jobs.append({
                    "title": title,
                    "organization": "Universität Erfurt",
                    "location": "Erfurt, Germany (50 min commute)",
                    "deadline": deadline.group(0) if deadline else "Check listing",
                    "pay_grade": pay.group(0) if pay else "TV-L E 13",
                    "url": full_url,
                    "source": "Uni Erfurt Portal",
                    "raw_text": f"{title} Universität Erfurt {text}",
                })
    except Exception:
        pass
    return jobs


async def fetch_direct_uni_erfurt(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Async scraper for Universität Erfurt."""
    url = "https://jobs.uni-erfurt.de/"
    results = []
    seen = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "/jobposting/" in href:
                    title = a.get_text(strip=True)
                    if len(title) < 8 or any(x in title.lower() for x in ["impressum", "datenschutz", "zurück"]):
                        continue
                    full_url = urljoin(url, href)
                    if full_url in seen:
                        continue
                    seen.add(full_url)
                    parent = a.find_parent(["tr", "li", "div", "p"]) or a
                    text = parent.get_text(" ", strip=True)
                    results.append(RawVacancy(
                        source="Uni Erfurt Direct",
                        title=title,
                        link=full_url,
                        snippet=f"{title} Universität Erfurt {text}"[:500],
                        query_type="direct_uni_ssr",
                    ))
    except Exception as e:
        record_telemetry("Uni Erfurt Direct", pages=1, raw=0, mode="SINGLE_PAGE", completeness="FAILED", error=str(e))
        return []
    record_telemetry("Uni Erfurt Direct", pages=1, raw=len(results), mode="SINGLE_PAGE", completeness="COMPLETE")
    return results


# ---------------------------------------------------------------------------
# 2. Bauhaus-Universität Weimar (Central Academic Gazette)
# ---------------------------------------------------------------------------
def scrape_uni_weimar() -> List[Dict[str, Any]]:
    """Synchronous scraper for Bauhaus-Universität Weimar."""
    url = "https://www.uni-weimar.de/de/universitaet/aktuell/stellenausschreibungen/"
    jobs = []
    seen = set()
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return []
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if any(term in href for term in ["m-wp-", "a-u-wp-", "k-g-kwp-", "b-u-wp-", "stellenausschreibungen/"]):
                title = a.get_text(strip=True)
                if len(title) < 4 or any(x in title.lower() for x in ["stellenausschreibungen", "zurück", "menü", "aktuell", "impressum", "datenschutz"]):
                    continue
                full_url = urljoin(url, href)
                if full_url in seen:
                    continue
                seen.add(full_url)
                parent = a.find_parent(["tr", "li", "div", "p"]) or a
                text = parent.get_text(" ", strip=True)
                deadline = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
                pay = re.search(r"(?:E|EG|TV-L|BesGr|W)\s*(?:E\s*)?(?:10|11|12|13|14|15|A\s*13)", text, re.I)
                jobs.append({
                    "title": f"Wissenschaftliche Stelle: {title}",
                    "organization": "Bauhaus-Universität Weimar",
                    "location": "Weimar, Germany (50 min commute)",
                    "deadline": deadline.group(0) if deadline else "Check listing",
                    "pay_grade": pay.group(0) if pay else "TV-L E 13",
                    "url": full_url,
                    "source": "Bauhaus-Uni Weimar Portal",
                    "raw_text": f"{title} Bauhaus-Universität Weimar {text}",
                })
    except Exception:
        pass
    return jobs


async def fetch_direct_uni_weimar(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Async scraper for Bauhaus-Universität Weimar."""
    url = "https://www.uni-weimar.de/de/universitaet/aktuell/stellenausschreibungen/"
    results = []
    seen = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if any(term in href for term in ["m-wp-", "a-u-wp-", "k-g-kwp-", "b-u-wp-", "stellenausschreibungen/"]):
                    title = a.get_text(strip=True)
                    if len(title) < 4 or any(x in title.lower() for x in ["stellenausschreibungen", "zurück", "menü", "aktuell", "impressum", "datenschutz"]):
                        continue
                    full_url = urljoin(url, href)
                    if full_url in seen:
                        continue
                    seen.add(full_url)
                    parent = a.find_parent(["tr", "li", "div", "p"]) or a
                    text = parent.get_text(" ", strip=True)
                    results.append(RawVacancy(
                        source="Bauhaus Weimar Direct",
                        title=f"Wissenschaftliche Stelle: {title}",
                        link=full_url,
                        snippet=f"{title} Bauhaus-Universität Weimar {text}"[:500],
                        query_type="direct_uni_ssr",
                    ))
    except Exception as e:
        record_telemetry("Bauhaus Weimar Direct", pages=1, raw=0, mode="SINGLE_PAGE", completeness="FAILED", error=str(e))
        return []
    record_telemetry("Bauhaus Weimar Direct", pages=1, raw=len(results), mode="SINGLE_PAGE", completeness="COMPLETE")
    return results


# ---------------------------------------------------------------------------
# 3. Universität Potsdam (Dezernat 3 Academic Staff)
# ---------------------------------------------------------------------------
def scrape_uni_potsdam() -> List[Dict[str, Any]]:
    """Synchronous scraper for Universität Potsdam."""
    url = "https://www.uni-potsdam.de/de/verwaltung/dezernat3/stellenausschreibungen/befristete-stellen-fuer-akademisches-personal"
    jobs = []
    seen = set()
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        if res.status_code != 200:
            return []
        soup = BeautifulSoup(res.text, "html.parser")
        for a in soup.select("a[href*='.pdf']"):
            href = a["href"]
            if not any(k in href for k in ["Dezernat3", "Ausschreibungen", "akadPersonal"]):
                continue
            title = a.get_text(strip=True)
            if len(title) < 8 or any(x in title.lower() for x in ["zurück", "impressum", "datenschutz"]):
                continue
            full_url = urljoin(url, href)
            if full_url in seen:
                continue
            seen.add(full_url)
            parent = a.find_parent(["tr", "li", "p", "div"]) or a
            text = parent.get_text(" ", strip=True)
            deadline = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
            pay = re.search(r"(?:E|EG|TV-L|BesGr|W)\s*(?:E\s*)?(?:10|11|12|13|14|15|A\s*13)", text, re.I)
            jobs.append({
                "title": title,
                "organization": "Universität Potsdam",
                "location": "Potsdam, Germany (60 min ICE)",
                "deadline": deadline.group(0) if deadline else "Check listing",
                "pay_grade": pay.group(0) if pay else "TV-L E 13",
                "url": full_url,
                "source": "Uni Potsdam Portal",
                "raw_text": f"{title} Universität Potsdam {text}",
            })
    except Exception:
        pass
    return jobs


async def fetch_direct_uni_potsdam(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Async scraper for Universität Potsdam."""
    url = "https://www.uni-potsdam.de/de/verwaltung/dezernat3/stellenausschreibungen/befristete-stellen-fuer-akademisches-personal"
    results = []
    seen = set()
    try:
        res = await client.get(url, headers=HEADERS, timeout=15.0)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.select("a[href*='.pdf']"):
                href = a["href"]
                if not any(k in href for k in ["Dezernat3", "Ausschreibungen", "akadPersonal"]):
                    continue
                title = a.get_text(strip=True)
                if len(title) < 8 or any(x in title.lower() for x in ["zurück", "impressum", "datenschutz"]):
                    continue
                full_url = urljoin(url, href)
                if full_url in seen:
                    continue
                seen.add(full_url)
                parent = a.find_parent(["tr", "li", "p", "div"]) or a
                text = parent.get_text(" ", strip=True)
                results.append(RawVacancy(
                    source="Uni Potsdam Direct",
                    title=title,
                    link=full_url,
                    snippet=f"{title} Universität Potsdam {text}"[:500],
                    query_type="direct_uni_ssr",
                ))
    except Exception as e:
        record_telemetry("Uni Potsdam Direct", pages=1, raw=0, mode="SINGLE_PAGE", completeness="FAILED", error=str(e))
        return []
    record_telemetry("Uni Potsdam Direct", pages=1, raw=len(results), mode="SINGLE_PAGE", completeness="COMPLETE")
    return results


# ---------------------------------------------------------------------------
# 4. Universität Hildesheim (Teacher Education / Didactics Hub)
# ---------------------------------------------------------------------------
def scrape_uni_hildesheim() -> List[Dict[str, Any]]:
    """Synchronous scraper for Universität Hildesheim."""
    urls = [
        "https://www.uni-hildesheim.de/universitaet/karriere-weiterbildung/stellenangebote/wissenschaftliche-mitarbeiterinnen/",
        "https://www.uni-hildesheim.de/universitaet/karriere-weiterbildung/stellenangebote/professuren/",
    ]
    jobs = []
    seen = set()
    for url in urls:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code != 200:
                continue
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.select("a[href*='.pdf'], a[href*='stelle']"):
                href = a["href"]
                title = a.get_text(strip=True)
                if not href.lower().endswith(".pdf") and not any(k in href for k in ["stelle", "job", "ausschreibung"]):
                    continue
                if len(title) < 8 or any(x in title.lower() for x in ["stellenangebote", "impressum", "datenschutz", "zurück", "anlaufstellen", "präsidium", "interne"]):
                    continue
                full_url = urljoin(url, href)
                if full_url in seen:
                    continue
                seen.add(full_url)
                parent = a.find_parent(["tr", "li", "p", "div", "article"]) or a
                text = parent.get_text(" ", strip=True)
                deadline = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", text)
                pay = re.search(r"(?:E|EG|TV-L|BesGr|W)\s*(?:E\s*)?(?:10|11|12|13|14|15|A\s*13)", text, re.I)
                jobs.append({
                    "title": title,
                    "organization": "Universität Hildesheim",
                    "location": "Hildesheim, Germany (1h 15m commute)",
                    "deadline": deadline.group(0) if deadline else "Check listing",
                    "pay_grade": pay.group(0) if pay else "TV-L E 13",
                    "url": full_url,
                    "source": "Uni Hildesheim Portal",
                    "raw_text": f"{title} Universität Hildesheim {text}",
                })
        except Exception:
            pass
    return jobs


async def fetch_direct_uni_hildesheim(client: httpx.AsyncClient) -> List[RawVacancy]:
    """Async scraper for Universität Hildesheim with multi-category inspection."""
    urls = [
        "https://www.uni-hildesheim.de/universitaet/karriere-weiterbildung/stellenangebote/wissenschaftliche-mitarbeiterinnen/",
        "https://www.uni-hildesheim.de/universitaet/karriere-weiterbildung/stellenangebote/professuren/",
    ]
    results = []
    seen = set()
    pages_traversed = 0
    try:
        for url in urls:
            pages_traversed += 1
            res = await client.get(url, headers=HEADERS, timeout=15.0)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                for a in soup.select("a[href*='.pdf'], a[href*='stelle']"):
                    href = a["href"]
                    title = a.get_text(strip=True)
                    if not href.lower().endswith(".pdf") and not any(k in href for k in ["stelle", "job", "ausschreibung"]):
                        continue
                    if len(title) < 8 or any(x in title.lower() for x in ["stellenangebote", "impressum", "datenschutz", "zurück", "anlaufstellen", "präsidium", "interne"]):
                        continue
                    full_url = urljoin(url, href)
                    if full_url in seen:
                        continue
                    seen.add(full_url)
                    parent = a.find_parent(["tr", "li", "p", "div", "article"]) or a
                    text = parent.get_text(" ", strip=True)
                    results.append(RawVacancy(
                        source="Uni Hildesheim Direct",
                        title=title,
                        link=full_url,
                        snippet=f"{title} Universität Hildesheim {text}"[:500],
                        query_type="direct_uni_ssr",
                    ))
    except Exception as e:
        record_telemetry("Uni Hildesheim Direct", pages=pages_traversed, raw=0, mode="MULTI_CATEGORY", completeness="FAILED", error=str(e))
        return []
    record_telemetry("Uni Hildesheim Direct", pages=pages_traversed, raw=len(results), mode="MULTI_CATEGORY", completeness="COMPLETE")
    return results
