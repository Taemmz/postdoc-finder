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

    for card in soup.select("div.text"):
        card_text = card.get_text(" ", strip=True).replace("\xad", "").replace("\u200b", "")

        # Filter out opinion/editorial articles without job metadata
        if not any(
            kw in card_text
            for kw in ["Location:", "Application deadline:", "Bewerbungsfrist:"]
        ):
            continue

        # Extract the job title anchor (skip author links and user profiles)
        title_link = None
        for a in card.find_all("a", href=True):
            text = a.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
            href = a["href"]
            if (
                "/users/" not in href
                and "/user/" not in href
                and not text.lower().startswith("by ")
                and len(text) > 5
            ):
                title_link = a
                break

        if not title_link:
            continue

        job_url = requests.compat.urljoin(url, title_link["href"])
        if job_url in seen_urls:
            continue
        seen_urls.add(job_url)

        title = title_link.get_text(strip=True).replace("\xad", "").replace("\u200b", "")

        deadline_match = re.search(
            r"(?:Application deadline|Bewerbungsfrist|Frist)[:\s]*(\d{1,2}[./]\d{1,2}[./]\d{2,4})",
            card_text,
            re.I,
        )
        location_match = re.search(r"Location:\s*([^,\n|]+)", card_text, re.I)

        leads.append({
            "title": title,
            "organization": "Wissenschaftsmanagement Online",
            "location": (
                location_match.group(1).strip() if location_match else "Germany"
            ),
            "deadline": deadline_match.group(1) if deadline_match else "Check listing",
            "url": job_url,
            "source": "Wissenschaftsmanagement Online",
            "snippet": card_text[:400],
        })

    return leads
