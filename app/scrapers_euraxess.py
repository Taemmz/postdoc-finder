"""scrapers_euraxess.py — European Commission / EURAXESS Germany Research Vacancy Scraper.

Scrapes funded postdocs, research fellowships, and science management positions.
"""

import re
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup


def scrape_euraxess(query: str = "higher education", country: str = "Germany") -> List[Dict[str, Any]]:
    """Scrapes research, postdoctoral, and academic vacancies from EURAXESS."""
    url = f"https://euraxess.ec.europa.eu/jobs/search?keywords={query}&f%5B0%5D=country%3A{country.lower()}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return []
    except requests.RequestException as e:
        print(f"Error requesting EURAXESS: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs: List[Dict[str, Any]] = []
    seen_urls = set()

    cards = soup.select("article, .views-row, .node--type-job-offer, div[class*='job-card']")

    for card in cards:
        link_el = card.select_one("h2 a, h3 a, a[href*='/jobs/'], a[href*='node/']")
        if not link_el:
            continue

        title = link_el.get_text(strip=True)
        if len(title) < 6 or "newest" in title.lower() or "offers first" in title.lower():
            continue

        full_url = requests.compat.urljoin("https://euraxess.ec.europa.eu", link_el.get("href", ""))
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        card_text = card.get_text(" ", strip=True)

        deadline_match = re.search(
            r"(?:Deadline|Application Deadline|Valid until)[:\s]*([0-9]{1,2}[/\.\s][0-9]{1,2}[/\.\s][0-9]{4}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4})",
            card_text,
            re.I,
        )
        deadline = (
            deadline_match.group(1)
            if deadline_match
            else re.search(r"\d{2}[\./\-]\d{2}[\./\-]\d{4}", card_text)
        )
        if isinstance(deadline, re.Match):
            deadline = deadline.group(0)

        org_el = card.select_one(".field--name-field-organisation, .organisation, .institution, .field--name-field-company-name")
        org_name = org_el.get_text(strip=True) if org_el else "German Research Institute / University"

        jobs.append({
            "title": title,
            "organization": org_name,
            "location": country,
            "deadline": deadline if deadline else "Check listing",
            "url": full_url,
            "source": "EURAXESS Germany",
            "raw_text": card_text,
        })

    return jobs


def scrape_euraxess_api(query: str = "higher education", country: str = "DE", max_results: int = 50) -> List[Dict[str, Any]]:
    """Queries EURAXESS JSON endpoint for German postdoctoral fellowships and research management positions."""
    url = "https://euraxess.ec.europa.eu/api/jobs"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json",
    }
    params = {
        "keywords": query,
        "country": country,
        "rows": max_results,
        "page": 0,
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return []
        data = response.json()
    except Exception:
        return []

    jobs: List[Dict[str, Any]] = []
    items = data.get("results", []) if isinstance(data, dict) else data if isinstance(data, list) else []

    for item in items:
        title = item.get("title") or item.get("label")
        if not title:
            continue
        jobs.append({
            "title": title.strip(),
            "organization": item.get("organisation_name", "German Research Institution"),
            "location": item.get("city", "Germany"),
            "deadline": item.get("deadline"),
            "url": item.get("url", f"https://euraxess.ec.europa.eu/jobs/{item.get('id', '')}"),
            "source": "EURAXESS Germany (API)",
        })

    return jobs
