import re
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup


def scrape_service_bund(query: str = "Wissenschaft") -> List[Dict[str, Any]]:
    """Scrapes academic and public service jobs from service.bund.de using a persistent session."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
            " like Gecko) Chrome/128.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8",
    })

    # Step 1: Establish session cookies by visiting the main portal
    base_url = "https://www.service.bund.de"
    search_url = f"{base_url}/Content/DE/Stellen/Suche/Formular.html"

    try:
        init_res = session.get(search_url, timeout=15)
        if init_res.status_code != 200:
            return []
    except requests.RequestException as e:
        print(f"Error connecting to service.bund.de: {e}")
        return []

    # Step 2: Fetch search results
    params = {
        "nn": "4641482",
        "cl2Categories_Ort": "",
        "resourceId": "4641484",
        "input_": "4641482",
        "pageLocale": "de",
        "templateQueryString": query,
        "submit": "Finden",
    }

    try:
        res = session.get(search_url, params=params, timeout=15)
        if res.status_code != 200:
            return []
    except requests.RequestException:
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    jobs: List[Dict[str, Any]] = []
    seen_titles = set()

    # Search result items are in list elements with class 'result-item' or table rows
    for item in soup.select("li.result-item, div.result-item, tr.result, .result-list > li"):
        link_el = item.select_one("a[href]")
        if not link_el:
            continue

        title = link_el.get_text(strip=True).replace("\xad", "").replace("\u200b", "")
        if len(title) < 8 or title in seen_titles:
            continue
        seen_titles.add(title)

        rel_href = link_el.get("href", "")
        full_url = requests.compat.urljoin(base_url, rel_href)
        item_text = item.get_text(" ", strip=True).replace("\xad", "").replace("\u200b", "")

        # Extract Deadline, Employer, Location
        deadline_match = re.search(r"\b\d{2}\.\d{2}\.\d{4}\b", item_text)
        pay_match = re.search(
            r"(?:E|EG|TV-L|TVöD|BesGr|W|A)\s*(?:E\s*)?(?:10|11|12|13|14|15|A\s*13)",
            item_text,
            re.I,
        )

        # Institution name typically follows the title or is in a specific span
        org_el = item.select_one(".institution, .author, .source, p")
        org_name = org_el.get_text(strip=True) if org_el else "Public Institution"

        jobs.append({
            "title": title,
            "organization": org_name,
            "location": "Germany",
            "deadline": (
                deadline_match.group(0) if deadline_match else "Check listing"
            ),
            "pay_grade": pay_match.group(0) if pay_match else "TVöD / TV-L",
            "url": full_url,
            "source": "Service.bund.de",
            "raw_text": item_text,
        })

    return jobs


def is_valid_tender_page(response_text: str) -> bool:
    """Detects expired or 404 job notices."""
    invalid_phrases = [
        "The requested job offer is no longer current",
        "has not yet been published",
        "Die gewünschte Seite existiert nicht",
        "Stellenausschreibung ist abgelaufen",
        "404 Not Found",
    ]
    return not any(phrase in response_text for phrase in invalid_phrases)
