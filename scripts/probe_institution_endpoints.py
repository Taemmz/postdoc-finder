"""
probe_institution_endpoints.py — Non-Invasive Vacancy Endpoint & Architecture Classifier.
Probes official vacancy URLs from the HRK registry to discover:
- Architecture (HTML_TABLE, HTML_CARDS, PDF_DIRECTORY, API_PAGE, CMS_REXX, CMS_DVINCI, INTERAMT_REDIRECT)
- Pagination Support (SINGLE_PAGE, URL_PAGINATION, UNKNOWN)
- Coverage Quality (VERIFIED, PARTIAL, AGGREGATOR_COVERED)
- Action Recommendation (READY_FOR_SCRAPER, ROUTE_TO_EXISTING_AGGREGATOR, BLOCKED)
"""

import json
import os
import re
import ssl
import sys
import urllib.request
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}


def probe_endpoint(name: str, url: str) -> Dict:
    """Non-invasively probes an institution's vacancy endpoint."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    res = {
        "institution": name,
        "original_url": url,
        "final_url": url,
        "status_code": 0,
        "architecture": "UNKNOWN",
        "pagination": "SINGLE_PAGE",
        "coverage": "UNKNOWN",
        "action": "INVESTIGATE",
        "sample_vacancies": [],
        "detected_links_count": 0,
        "error": None
    }

    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
            res["status_code"] = response.getcode()
            res["final_url"] = response.geturl()
            html = response.read().decode("utf-8", errors="ignore")

        soup = BeautifulSoup(html, "html.parser")
        final_url_lower = res["final_url"].lower()
        html_lower = html.lower()

        # Check for State Portal or Third-Party Aggregator Redirects
        if "karriere.baden-wuerttemberg.de" in final_url_lower or "karriere-bw" in final_url_lower:
            res["architecture"] = "STATE_PORTAL_BW"
            res["coverage"] = "AGGREGATOR_COVERED"
            res["action"] = "ROUTE_TO_EXISTING_AGGREGATOR"
            return res
        elif "interamt.de" in final_url_lower:
            res["architecture"] = "INTERAMT_REDIRECT"
            res["coverage"] = "AGGREGATOR_COVERED"
            res["action"] = "ROUTE_TO_EXISTING_AGGREGATOR"
            return res
        elif "stellenwerk" in final_url_lower:
            res["architecture"] = "STELLENWERK_PORTAL"
            res["coverage"] = "VERIFIED"
            res["action"] = "READY_FOR_SCRAPER"

        # Check for ATS / CMS Signatures
        if "rexx" in html_lower or "rexx-systems" in final_url_lower or "jobportal" in final_url_lower:
            res["architecture"] = "CMS_REXX"
        elif "dvinci" in html_lower or "d-vinci" in final_url_lower:
            res["architecture"] = "CMS_DVINCI"
        elif "successfactors" in html_lower or "sap" in final_url_lower:
            res["architecture"] = "SAP_SUCCESSFACTORS"
        elif "typo3" in html_lower or "tx_" in html_lower:
            res["architecture"] = "TYPO3_PORTAL"

        # Inspect Links and Structure
        academic_links = []
        pdf_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            text = a.get_text(separator=" ", strip=True)
            if not text or len(text) < 12:
                continue
            if any(skip in href.lower() for skip in ["impressum", "datenschutz", "facebook", "linkedin", "instagram", "login"]):
                continue

            full_link = urljoin(res["final_url"], href)
            if any(k in text.lower() or k in href.lower() for k in ["wiss", "mitarbeiter", "prof", "kennziffer", "doktor", "postdoc", "stelle", "lehrkraft"]):
                academic_links.append({"title": text[:80], "link": full_link})
            if ".pdf" in href.lower() or "download" in href.lower():
                pdf_links.append({"title": text[:80], "link": full_link})

        # Check for Pagination Elements
        if re.search(r"(\?|&)(page|p|pageNo|offset)=\d+", html) or soup.find(class_=lambda c: c and any(p in c.lower() for p in ["pagination", "pager", "seiten"])):
            res["pagination"] = "URL_PAGINATION"

        res["detected_links_count"] = len(academic_links)
        res["sample_vacancies"] = academic_links[:5]

        if academic_links:
            res["coverage"] = "VERIFIED"
            res["action"] = "READY_FOR_SCRAPER"
            if res["architecture"] == "UNKNOWN":
                res["architecture"] = "HTML_CARDS" if soup.find_all("article") else "HTML_LIST"
        elif pdf_links:
            res["architecture"] = "PDF_DIRECTORY"
            res["coverage"] = "VERIFIED"
            res["action"] = "READY_FOR_SCRAPER"
            res["sample_vacancies"] = pdf_links[:5]
        elif "keine stellen" in html_lower or "keine offenen stellen" in html_lower or "derzeit keine" in html_lower:
            res["coverage"] = "VERIFIED"
            res["action"] = "READY_FOR_SCRAPER"
            res["architecture"] = "EMPTY_JOBBOARD"
        else:
            res["coverage"] = "PARTIAL"
            res["action"] = "INVESTIGATE"

    except Exception as e:
        res["error"] = str(e)
        res["action"] = "BLOCKED"

    return res


def probe_batch(targets: List[Dict]) -> List[Dict]:
    """Probes a batch of target institutions."""
    results = []
    print(f"Probing {len(targets)} institutions...")
    for t in targets:
        name = t.get("institution_name") or t.get("name")
        url = t.get("vacancy_url") or t.get("url")
        print(f"  -> Probing {name[:40]} ({url[:50]}...)")
        info = probe_endpoint(name, url)
        results.append(info)
        print(f"     Status: {info['status_code']} | Arch: {info['architecture']} | Action: {info['action']} | Found: {info['detected_links_count']} items")
    return results


if __name__ == "__main__":
    test_sample = [
        {"name": "Hochschule Schmalkalden", "url": "https://www.hs-schmalkalden.de/stellenangebote-an-der-hochschule"},
        {"name": "Hochschule Harz", "url": "https://www.hs-harz.de/karriere/aktuelle-stellenausschreibungen"},
        {"name": "Leuphana Universität Lüneburg", "url": "https://www.leuphana.de/universitaet/jobs-und-karriere.html"},
        {"name": "Fachhochschule Potsdam", "url": "https://www.fh-potsdam.de/hochschule-karriere/karriere/stellenangebote-fh-potsdam"}
    ]
    probe_batch(test_sample)
