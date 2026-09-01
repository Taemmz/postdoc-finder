"""scrapers_interamt.py — Interamt & Public Administration Vacancy Scraper.

Interamt is the primary portal mandated across German municipal, state,
and university administrations for public service positions (TV-L / TVöD / E 13–E 14).
"""

import re
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup


def scrape_interamt_html(soup_text: str) -> List[Dict[str, Any]]:
    """Parses Interamt table or list elements into structured job records."""
    soup = BeautifulSoup(soup_text, "html.parser")
    rows = soup.select("table tbody tr, .ia-eintrag, .ia-list-entry, [class*='result-row']")
    jobs: List[Dict[str, Any]] = []

    for row in rows:
        link_el = row.select_one("a[href*='stelle'], a[href*='id='], a[href]")
        if not link_el:
            continue

        full_text = row.get_text(" ", strip=True)
        title = link_el.get_text(strip=True) or (row.select_one("td:first-child") or row).get_text(strip=True)

        deadline_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", full_text)
        pay_grade_match = re.search(r"(?:E|EG|TV-L|TV-H|TVöD|BesGr)\s*(?:E\s*)?(?:13|14|15|A\s*13|A\s*14)", full_text, re.I)
        location_match = re.search(r"\b\d{5}\s+([A-Za-zäöüÄÖÜß\s\-]+)", full_text)

        if title and len(title) > 5:
            jobs.append({
                "title": title,
                "pay_grade": pay_grade_match.group(0) if pay_grade_match else "Check listing",
                "location": location_match.group(0) if location_match else "Germany",
                "deadline": deadline_match.group(1) if deadline_match else "Check listing",
                "url": requests.compat.urljoin("https://www.interamt.de/koop/app/", link_el.get("href", "")),
                "source": "Interamt.de",
            })

    return jobs


def scrape_interamt(query: str = "Wissenschaftsmanagement", max_results: int = 50) -> List[Dict[str, Any]]:
    """Queries Interamt's search service directly for academic and public administration positions."""
    url = "https://www.interamt.de/koop/app/trefferliste"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
    }
    payload = {
        "suchbegriff": query,
        "suchort": "",
        "umkreis": 0,
        "page": 1,
        "rows": max_results,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        if response.status_code != 200:
            return []
        data = response.json()
    except Exception:
        return scrape_interamt_html(response.text) if "response" in locals() and response else []

    jobs: List[Dict[str, Any]] = []
    entries = data.get("treffer", []) if isinstance(data, dict) else []
    for entry in entries:
        stelle_id = entry.get("id") or entry.get("stellennummer")
        title = entry.get("titel") or entry.get("stellenbezeichnung")
        if not title:
            continue
        jobs.append({
            "title": title.strip(),
            "organization": entry.get("arbeitgeber", "Public / Academic Body"),
            "location": entry.get("ort", "Germany"),
            "deadline": entry.get("frist"),
            "pay_grade": entry.get("besoldungsgruppe") or entry.get("entgeltgruppe"),
            "url": f"https://www.interamt.de/koop/app/stelle?id={stelle_id}" if stelle_id else "",
            "source": "Interamt.de",
        })
    return jobs
