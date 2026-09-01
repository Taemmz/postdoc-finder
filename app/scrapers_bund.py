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
    seen_urls = set()

    for item in soup.select("table tbody tr, .result-list > li, [class*='result']"):
        link_el = item.select_one("a[href*='node.html'], a[href*='/Stellen/'], a[href*='nn='], a[href]")
        if not link_el:
            continue

        rel_href = link_el.get("href", "")
        full_url = requests.compat.urljoin(base_url, rel_href)
        if full_url in seen_urls:
            continue

        first_cell = item.select_one("td:first-child, .title-wrapper") or item
        lines = [l.strip() for l in first_cell.get_text("\n", strip=True).split("\n") if l.strip()]

        title = ""
        institution = "Public Body / University"
        deadline = None

        for i, line in enumerate(lines):
            l_low = line.lower()
            if "stellenbezeichnung" in l_low and i + 1 < len(lines):
                title = lines[i + 1].replace("\xad", "").replace("\u200b", "").strip()
            elif "arbeitgeber" in l_low and i + 1 < len(lines):
                institution = lines[i + 1].replace("\xad", "").replace("\u200b", "").strip()
            elif "bewerbungsfrist" in l_low and i + 1 < len(lines):
                deadline = lines[i + 1].strip()

        if not title:
            # Fallback if label markers are absent
            clean_lines = [
                l for l in lines
                if not l.lower().startswith(("stellenbezeichnung", "stellenangebot", "job title", "arbeitgeber"))
            ]
            title = clean_lines[0].replace("\xad", "").replace("\u200b", "") if clean_lines else link_el.get_text(strip=True)
            if len(clean_lines) > 1 and institution == "Public Body / University":
                institution = clean_lines[1].replace("\xad", "").replace("\u200b", "")

        if len(title) < 6:
            continue

        seen_urls.add(full_url)
        item_text = item.get_text(" ", strip=True).replace("\xad", "").replace("\u200b", "")

        # Extract pay grade if present
        pay_match = re.search(
            r"(?:E|EG|TV-L|TV-H|TVöD|BesGr|W|A)\s*(?:E\s*)?(?:10|11|12|13|14|15|A\s*13|A\s*14)",
            item_text,
            re.I,
        )

        jobs.append({
            "title": title,
            "organization": institution,
            "location": "Germany",
            "deadline": deadline if deadline else "Check listing",
            "pay_grade": pay_match.group(0) if pay_match else "TVöD / TV-L",
            "url": full_url,
            "source": "Service.bund.de",
            "raw_text": item_text,
        })

    return jobs


def scrape_all_bund_academic_tracks(max_pages: int = 1) -> List[Dict[str, Any]]:
    """Runs all 4 primary academic, higher ed governance, and postdoc queries on Service.bund.de."""
    queries = [
        "Wissenschaftsmanagement",
        "Hochschuldidaktik",
        "Postdoktorand",
        "Wissenschaftliche Mitarbeiterin",
    ]
    aggregated = []
    seen = set()
    for q in queries:
        vacancies = scrape_service_bund(query=q)
        for v in vacancies:
            u = v.get("url", "").split("?")[0]
            if u and u not in seen:
                seen.add(u)
                aggregated.append(v)
    return aggregated


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
