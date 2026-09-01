"""scrapers_karriere_bw.py — Baden-Württemberg State Career & University Vacancy Scraper.

Scrapes ministry, state agency, and university listings across Baden-Württemberg.
"""

import re
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup


def scrape_karriere_bw(query: str = "") -> List[Dict[str, Any]]:
    """Scrapes state vacancies and university notices from the Baden-Württemberg Career Portal."""
    url = "https://karriere.baden-wuerttemberg.de/de/startseite/stellenanzeigen"
    params = {"search": query} if query else {}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code != 200:
            return []
    except requests.RequestException as e:
        print(f"Error fetching Karriere BW: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    jobs: List[Dict[str, Any]] = []
    seen_urls = set()

    links = soup.select('a[href*="/einzelansicht/job/"], a[href*="/job/"], a[href*="stelle"]')

    for link in links:
        href = link.get("href", "")
        full_url = requests.compat.urljoin(url, href)

        if full_url in seen_urls:
            continue

        title = link.get_text(strip=True)
        card = link.find_parent(["article", "li", "div"]) or link
        card_text = card.get_text(" ", strip=True)

        # Fallback to heading if anchor text is a generic button label
        if not title or len(title) < 5 or "stelle" in title.lower() or "ansehen" in title.lower():
            heading = card.find(["h2", "h3", "h4", "strong"])
            if heading:
                title = heading.get_text(strip=True)

        if len(title) < 6 or "filter" in title.lower() or "stellenanzeigen" in title.lower():
            continue

        seen_urls.add(full_url)

        paygrade_match = re.search(
            r"(?:E|EG|TV-L|TV-H|BesGr|A)\s*(?:E\s*)?(?:13|14|15|A\s*13|A\s*14)",
            card_text,
            re.I,
        )
        deadline_match = re.search(r"\d{2}\.\d{2}\.\d{2,4}", card_text)

        lines = card.get_text("\n", strip=True).split("\n")
        org = lines[1] if len(lines) > 1 and lines[1] != title else "Baden-Württemberg State / University"

        jobs.append({
            "title": title,
            "organization": org,
            "location": "Baden-Württemberg, Germany",
            "deadline": deadline_match.group(0) if deadline_match else "Check listing",
            "pay_grade": paygrade_match.group(0) if paygrade_match else "TV-L",
            "url": full_url,
            "source": "Karriere BW",
            "raw_text": card_text,
        })

    return jobs
