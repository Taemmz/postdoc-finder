"""
processor.py — Full port of the n8n "Filter, Score & Extract" node.
Handles: exclusion filtering, position/topic keyword matching,
         institution detection, deadline extraction, German language detection,
         tiered institution scoring, deduplication, and region classification.
"""

import re
from typing import List, Optional, Tuple

from app.models import PostdocRecord, RawVacancy

# ---------------------------------------------------------------------------
# Exclusion lists
# ---------------------------------------------------------------------------
EXCLUDE_TITLES = [
    "phd candidate", "doctoral researcher", "doctoral student",
    "doktorand", "doktorandin", "promotionsstelle", "phd programme",
    "hr generalist", "recruiter", "sales", "marketing", "customer service",
]
EXCLUDE_DESC = [
    "opportunity to pursue a doctorate", "doctoral qualification position",
    "doctorate expected", "promotion vorgesehen",
    "qualification position under wisszeitvg",
]

# ---------------------------------------------------------------------------
# Keyword banks
# ---------------------------------------------------------------------------
POSITION_TERMS = [
    "postdoc", "post-doc", "postdoctoral", "research fellow", "research associate",
    "academic researcher", "wissenschaftliche mitarbeiter", "wissenschaftlicher mitarbeiter",
    "wissenschaftliche mitarbeiterin", "postdoktorand", "postdoktorandin",
    "junior research group",
]
TOPIC_CORE = [
    "employability", "graduate employability", "labour market", "labor market",
    "workforce development", "organisational development", "organizational development",
    "arbeitsmarkt", "arbeitsmarktforschung", "beschäftigungsfähigkeit",
    "organisationsentwicklung",
]
TOPIC_ADJACENT = [
    "work psychology", "workplace learning", "human resource development",
    "capability development", "evaluation research", "programme evaluation",
    "program evaluation", "psychometrics", "educational assessment",
    "measurement and assessment", "mixed methods", "higher education research",
    "graduate outcomes", "education policy", "education-to-work",
    "assessment fairness", "labour market transitions", "skills development",
    "employment policy", "workforce capability", "organizational behavior",
    "organisational behaviour", "hochschulforschung", "bildungsforschung",
    "bildungspolitik", "evaluation", "programmevaluation", "kompetenzentwicklung",
    "personalentwicklung", "organisationspsychologie", "arbeitspsychologie",
    "berufliche bildung", "weiterbildung", "übergang studium beruf",
    "übergang hochschule beruf",
]
STRONG_VACANCY_SIGNALS = [
    "deadline", "closing date", "hiring", "vacancy", "opening",
    "position available", "join our team", "applications are open",
    "applications invited", "bewerbung", "bewerbungsfrist",
    "stellenausschreibung", "stellenangebot", "zu besetzen", "wir suchen",
]
WEAK_VACANCY_SIGNALS = ["apply", "application", "applications"]
VACANCY_SIGNALS = STRONG_VACANCY_SIGNALS + WEAK_VACANCY_SIGNALS

NEGATIVE_DISCIPLINES = [
    "chemistry", "chemical engineering", "biology", "molecular", "genetics",
    "genomics", "neuroscience", "physics", "astrophysics", "robotics",
    "mechanical engineering", "civil engineering", "electrical engineering",
    "materials science", "biomedical", "medicine", "clinical", "oncology",
    "pharmacology", "agriculture", "veterinary",
]

SOCIAL_SOURCES = {"Reddit", "Facebook", "Twitter/X", "ResearchGate"}
SOCIAL_SOURCE_PENALTY = 1

TRUSTED_JOB_DOMAINS = [
    "euraxess.ec.europa.eu", "academicpositions.com", "jobs.ac.uk",
    "academics.de", "linkedin.com/jobs", "universitypositions.eu",
    "jobs.chronicle.com", "higheredjobs.com", "careers.insidehighered.com",
    "psychjob.eu", "mpg.de", "leibniz-gemeinschaft.de", "helmholtz.de",
    "fraunhofer.de", "gesis.org", "bibb.de", "ifo.de", "zew.de",
    "service.bund.de", "inomics.com", "evifa.de", "xing.com/jobs",
    "researchgate.net/jobs", "charite.de", "kit.edu", "rwth-aachen.de",
    "academickeys.com",
]

# ---------------------------------------------------------------------------
# Institution tier patterns
# ---------------------------------------------------------------------------
TIER1_PATTERNS = [
    re.compile(p, re.I) for p in [
        r"\bdzhw\b", r"\biab\b", r"\biza\b", r"\bwzb\b", r"\bbibb\b",
        r"\bcedefop\b", r"\boecd\b", r"university of leipzig", r"uni-leipzig",
        r"leipzig university",
    ]
]
TIER2_PATTERNS = [
    re.compile(p, re.I) for p in [
        r"university of stuttgart", r"\btu berlin\b", r"technische universität berlin",
        r"\bhumboldt\b", r"\blmu\b", r"ludwig-maximilians", r"\bheidelberg\b",
        r"rwth aachen", r"freie universität berlin", r"university of cologne",
        r"universität zu köln", r"university of bonn", r"goethe university",
        r"university of frankfurt", r"university of freiburg",
        r"university of tübingen", r"universität tübingen", r"university of hamburg",
        r"technical university of munich", r"\btum münchen\b", r"university of mannheim",
        r"university of konstanz", r"university of duisburg-essen",
        r"university of erlangen", r"friedrich-alexander", r"university of göttingen",
        r"universität göttingen", r"university of kiel", r"christian-albrechts",
        r"university of mainz", r"university of marburg", r"university of münster",
        r"university of potsdam", r"bielefeld university", r"universität bielefeld",
        r"charité", r"karlsruhe institute of technology", r"\bkit\b",
        r"eth zurich", r"university of zurich", r"university of geneva",
        r"university of vienna", r"universität wien", r"university of copenhagen",
        r"university of helsinki", r"university of oslo", r"stockholm university",
        r"lund university", r"university of gothenburg", r"\boxford\b",
        r"\bcambridge\b", r"university college london", r"\bucl\b",
        r"london school of economics", r"king's college london",
        r"university of edinburgh", r"university of manchester",
        r"university of bristol", r"trinity college dublin",
        r"university college dublin", r"university of warwick", r"ku leuven",
        r"university of amsterdam", r"utrecht university",
        r"erasmus university rotterdam", r"university of groningen",
        r"sciences po", r"sorbonne",
    ]
]
TIER3_PATTERNS = [
    re.compile(p, re.I) for p in [
        r"university of toronto", r"mcgill university",
        r"university of british columbia", r"\bubc\b", r"university of waterloo",
        r"university of montreal", r"harvard", r"stanford", r"\bmit\b",
        r"university of michigan", r"australian national university",
        r"university of melbourne", r"university of sydney", r"university of auckland",
    ]
]

GERMAN_C_RE = re.compile(r"\b(c1|c2)\b", re.I)
GERMAN_B_RE = re.compile(r"\b(b1|b2)\b", re.I)
GERMAN_NONE_RE = re.compile(r"(no german required|german not required|english only)", re.I)

DEADLINE_PATTERNS = [
    re.compile(r"deadline[\s:]+([A-Za-z]+\s+\d{1,2},?\s*\d{4})", re.I),
    re.compile(r"(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s*\d{4}", re.I),
    re.compile(r"\d{1,2}\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}", re.I),
    re.compile(r"closing date[\s:]+([A-Za-z0-9\s,]+)", re.I),
    re.compile(r"apply by[\s:]+([A-Za-z]+\s+\d{1,2},?\s*\d{4})", re.I),
]

MONTHS = {
    "jan": 0, "january": 0, "feb": 1, "february": 1, "mar": 2, "march": 2,
    "apr": 3, "april": 3, "may": 4, "jun": 5, "june": 5, "jul": 6, "july": 6,
    "aug": 7, "august": 7, "sep": 8, "sept": 8, "september": 8,
    "oct": 9, "october": 9, "nov": 10, "november": 10, "dec": 11, "december": 11,
}

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _safe_str(v) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        return _safe_str(v[0]) if v else ""
    if isinstance(v, dict):
        return str(v.get("href", "") or next(iter(v.values()), ""))
    return str(v)


def guess_institution(title: str) -> str:
    parts = re.split(r"[-–|]", title)
    return parts[-1].strip() if len(parts) > 1 else title.strip()


def extract_position_title(title: str) -> str:
    parts = re.split(r"[-–|]", title)
    return parts[0].strip() if len(parts) > 1 else title.strip()


def normalize_dedup(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9äöüß\s]", " ", re.sub(r"\([^)]*\)", " ", text.lower()))).strip()


def build_canonical_key(title: str, institution: str) -> Optional[str]:
    norm_title = normalize_dedup(extract_position_title(title))
    norm_inst = normalize_dedup(institution)
    if len(norm_title.split()) < 4:
        return None
    if not norm_inst or institution == "Unknown — see listing":
        return None
    return f"{norm_title}|{norm_inst}"


def extract_deadline(text: str) -> Optional[str]:
    for pat in DEADLINE_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


def parse_deadline_iso(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    low = text.lower()
    m = re.search(r"([a-z]+)\s+(\d{1,2}),?\s*(\d{4})", low)
    if m and m.group(1) in MONTHS:
        try:
            from datetime import date
            d = date(int(m.group(3)), MONTHS[m.group(1)] + 1, int(m.group(2)))
            return d.isoformat()
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})\s+([a-z]+)\.?\s+(\d{4})", low)
    if m and m.group(2) in MONTHS:
        try:
            from datetime import date
            d = date(int(m.group(3)), MONTHS[m.group(2)] + 1, int(m.group(1)))
            return d.isoformat()
        except ValueError:
            pass
    return None


def detect_german(text: str) -> str:
    if GERMAN_C_RE.search(text):
        return "c1" if re.search(r"\bc1\b", text, re.I) else "c2"
    if GERMAN_B_RE.search(text):
        return "b1" if re.search(r"\bb1\b", text, re.I) else "b2"
    if GERMAN_NONE_RE.search(text):
        return "none"
    return "unknown"


def is_trusted_domain(url: str) -> bool:
    return any(d in url for d in TRUSTED_JOB_DOMAINS)


def _contains_exclude(text: str, terms: list) -> bool:
    low = text.lower()
    for term in terms:
        idx = low.find(term)
        if idx == -1:
            continue
        prefix = low[max(0, idx - 6) : idx]
        if re.search(r"post[\s-]?$", prefix):
            continue
        return True
    return False


def compute_institution_bonus(text: str, link: str) -> Tuple[int, int]:
    combined = f"{text} {link}"
    if any(p.search(combined) for p in TIER1_PATTERNS):
        return 2, 1
    if any(p.search(combined) for p in TIER2_PATTERNS):
        return 1, 2
    if any(p.search(combined) for p in TIER3_PATTERNS):
        return 0, 3
    return 0, 4


def compute_region(source: str, link: str, text: str, institution_tier: int) -> str:
    combined = f"{text} {link}".lower()
    german_signals = [".de", "germany", "deutschland", "tv-l", "tvöd"]
    global_board_sources = {
        "RSS HigherEdJobs", "RSS AcademicKeys SocSci", "RSS AcademicKeys Education"
    }
    if source == "North America/ANZ Boards":
        return "other"
    if institution_tier == 3:
        return "other"
    if any(s in combined for s in german_signals):
        return "germany"
    if institution_tier in (1, 2):
        return "europe"
    if source in global_board_sources:
        return "other"
    return "europe"


def passes_relevance_gate(
    source: str,
    has_position: bool,
    has_core: bool,
    has_adjacent: bool,
    trusted: bool,
    lower: str,
) -> bool:
    if not has_position:
        return False
    if not has_core and not has_adjacent:
        return False
    has_strong = any(t in lower for t in STRONG_VACANCY_SIGNALS)
    if source in SOCIAL_SOURCES:
        return has_strong
    return trusted or has_strong or any(t in lower for t in WEAK_VACANCY_SIGNALS)


# ---------------------------------------------------------------------------
# Main processor
# ---------------------------------------------------------------------------

def process_vacancies(raw_items: List[RawVacancy]) -> List[PostdocRecord]:
    seen_links: set = set()
    seen_canonical: set = set()
    results: List[PostdocRecord] = []

    for item in raw_items:
        clean_link = _safe_str(item.link).strip()
        if not clean_link or clean_link in seen_links:
            continue

        title = _safe_str(item.title)
        snippet = _safe_str(item.snippet)

        # Exclusion filters
        if _contains_exclude(title, EXCLUDE_TITLES):
            continue
        if _contains_exclude(snippet, EXCLUDE_DESC):
            continue

        text = f"{title} {snippet}"
        lower = text.lower()
        url = clean_link.lower()

        has_position = any(t in lower for t in POSITION_TERMS)
        has_core = any(t in lower for t in TOPIC_CORE)
        has_adjacent = any(t in lower for t in TOPIC_ADJACENT)
        trusted = is_trusted_domain(url)

        if not passes_relevance_gate(item.source, has_position, has_core, has_adjacent, trusted, lower):
            continue

        institution = guess_institution(title) or "Unknown — see listing"
        canonical = build_canonical_key(title, institution)
        if canonical and canonical in seen_canonical:
            continue

        # Base score
        has_strong = any(t in lower for t in STRONG_VACANCY_SIGNALS)
        if has_core and has_strong:
            base = 10
        elif has_core and trusted:
            base = 9
        elif has_core:
            base = 8
        elif has_adjacent and has_strong:
            base = 7
        elif has_adjacent and trusted:
            base = 6
        else:
            base = 5

        inst_bonus, inst_tier = compute_institution_bonus(text, clean_link)
        neg_hits = [d for d in NEGATIVE_DISCIPLINES if d in lower]
        neg_penalty = (-1 if has_core else -3) if neg_hits else 0
        social_penalty = SOCIAL_SOURCE_PENALTY if item.source in SOCIAL_SOURCES else 0

        score = max(1, min(10, base + inst_bonus + neg_penalty - social_penalty))

        german = detect_german(text)
        if german in ("c1", "c2"):
            score = min(score, 4)

        # Normalise relative links
        full_link = clean_link
        if clean_link.startswith("/"):
            if "universitypositions" in (item.source or "").lower():
                full_link = f"https://universitypositions.eu{clean_link}"
            elif "academics.de" in (item.source or "").lower():
                full_link = f"https://www.academics.de{clean_link}"
            elif "euraxess" in (item.source or "").lower():
                full_link = f"https://euraxess.ec.europa.eu{clean_link}"

        deadline_text = extract_deadline(text)
        region = compute_region(item.source, full_link, text, inst_tier)

        matched_terms = list({
            t for t in (POSITION_TERMS + TOPIC_CORE + TOPIC_ADJACENT + VACANCY_SIGNALS)
            if t in lower
        })

        seen_links.add(clean_link)
        if canonical:
            seen_canonical.add(canonical)

        results.append(
            PostdocRecord(
                institution=institution,
                research_focus=snippet[:300],
                link=full_link,
                deadline=parse_deadline_iso(deadline_text),
                match_score=score,
                german_required=german,
                research_data={
                    "source": item.source,
                    "query_type": item.query_type,
                    "title_raw": title,
                    "deadline_text": deadline_text,
                    "matched_terms": matched_terms,
                    "region_tier": region,
                    "live_verified": True,
                },
            )
        )

    return results
