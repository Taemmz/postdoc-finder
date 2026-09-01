import hashlib
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def normalize_url(url: str) -> str:
    """Strips tracking, pagination, session IDs, and trailing slashes."""
    if not url:
        return ""
    clean = re.sub(r";jsessionid=[^?#]+", "", url.strip())
    parsed = urlparse(clean)

    ignored_params = {
        "sid",
        "session",
        "sessionid",
        "jsessionid",
        "pk_campaign",
        "pk_kwd",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "ref",
        "src",
        "searchresult",
        "templatequerystring",
        "nn",
        "type",
    }
    query_dict = parse_qs(parsed.query)
    clean_query = {k: v for k, v in query_dict.items() if k.lower() not in ignored_params}

    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc.lower(),
        parsed.path.rstrip("/"),
        "",
        urlencode(clean_query, doseq=True),
        "",
    ))
    return clean_url


def is_valid_title(title: str, organization: str = "") -> bool:
    """Rejects low-quality placeholders and navigation text."""
    if not title or len(title.strip()) < 8:
        return False

    t_lower = title.strip().lower()
    org_lower = (organization or "").strip().lower()

    # Reject if title is just the institution name
    if org_lower and (
        t_lower == org_lower
        or t_lower in org_lower
        or (org_lower in t_lower and len(t_lower) < len(org_lower) + 5)
    ):
        return False

    # Reject incomplete sentence fragments or generic UI elements
    invalid_exact = [
        "hochschule und",
        "hochschule für",
        "hochschule hochschule",
        "stellenangebote",
        "job postings",
        "karriere",
        "uebersicht",
        "read all",
        "further links",
        "view latest",
        "zurück zur übersicht",
        "zurueck zur uebersicht",
    ]
    if any(t_lower == inv or t_lower.startswith(inv) for inv in invalid_exact):
        return False

    return True


def generate_fingerprint(title: str, organization: str, deadline: str = "") -> str:
    """Creates a normalized unique content hash to detect cross-portal duplicates."""
    clean_title = re.sub(r"[^\w\s]", "", (title or "").lower()).strip()
    clean_title = re.sub(r"\s+", " ", clean_title)

    clean_org = re.sub(r"[^\w\s]", "", (organization or "").lower()).strip()
    clean_deadline = (deadline or "").strip()

    composite = f"{clean_title}|{clean_org}|{clean_deadline}"
    return hashlib.sha256(composite.encode("utf-8")).hexdigest()
