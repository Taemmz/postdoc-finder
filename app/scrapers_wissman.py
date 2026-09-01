"""scrapers_wissman.py — Scraper for Wissenschaftsmanagement Online.

Extracts higher education management, academic coordination, and university
administration vacancies directly from Drupal views and node containers.
"""

import re
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup


def scrape_wissenschaftsmanagement_online() -> List[Dict[str, Any]]:
    """Scrapes higher education & science management leads from Wissenschaftsmanagement Online."""
    url = "https://www.wissenschaftsmanagement-online.de/kategorie/alle-themen/aktivitaeten"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
    except Exception as e:
        print(f"  [wissman] Connection error: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    leads: List[Dict[str, Any]] = []
    seen_urls = set()

    for item in soup.select(".views-row, .node-stellenanzeige, div[class*='views-field-title']"):
        link_el = item.select_one("a[href]")
        if not link_el:
            continue

        title = link_el.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
        if not title or len(title) < 8 or "uebersicht" in title.lower():
            continue

        full_url = requests.compat.urljoin(url, link_el.get("href"))
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        snippet = item.get_text(" ", strip=True).replace("\xad", "").replace("\u200b", "")

        # Extract deadline if present
        deadline_match = re.search(
            r"(?:Application deadline|Bewerbungsfrist|Frist)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            snippet,
            re.I,
        )
        deadline = deadline_match.group(1) if deadline_match else "Check listing"

        # Extract location if present
        location_match = re.search(r"Location:\s*([^\n,|]+)", snippet, re.I)
        location = location_match.group(1).strip() if location_match else "Germany"

        leads.append({
            "title": title,
            "url": full_url,
            "snippet": snippet,
            "deadline": deadline,
            "location": location,
            "source": "Wissenschaftsmanagement Online",
        })

    return leads
