"""
processor.py — Full port of the n8n "Filter, Score & Extract" node.
Handles: exclusion filtering, position/topic keyword matching,
         institution detection, deadline extraction, German language detection,
         tiered institution scoring, deduplication, and region classification.
"""

import re
from datetime import date, datetime
from typing import List, Optional, Tuple

import httpx
from bs4 import BeautifulSoup

from app.models import PostdocRecord, RawVacancy

# ---------------------------------------------------------------------------
# Exclusion lists
# ---------------------------------------------------------------------------
EXCLUDE_TITLES = [
    "phd candidate", "doctoral researcher", "doctoral student",
    "doktorand", "doktorandin", "promotionsstelle", "phd programme",
    "hr generalist", "recruiter", "sales", "marketing", "customer service",
]
# NOTE: WissZeitVG removed — German postdoc contracts frequently cite this
# law without the role being doctoral-only. Keeping it caused valid drops.
EXCLUDE_DESC = [
    "opportunity to pursue a doctorate",
    "doctorate expected",
    "promotion vorgesehen",
]

# ---------------------------------------------------------------------------
# Keyword banks
# ---------------------------------------------------------------------------
POSITION_TERMS = [
    # English postdoc / staff researcher
    "postdoc", "post-doc", "postdoctoral", "postdoctoral researcher",
    "postdoctoral fellow", "research associate", "research assistant",
    "academic researcher", "senior researcher", "research fellow",
    # German postdoc / staff researcher
    "wissenschaftliche mitarbeiter", "wissenschaftlicher mitarbeiter",
    "wissenschaftliche mitarbeiterin", "postdoktorand", "postdoktorandin",
    "nachwuchswissenschaftler", "nachwuchswissenschaftlerin",
    "akademischer rat", "akademische rätin", "junior research group",
    "qualifikationsstelle", "akademische mitarbeiter",
    # German contract grades (strong signal of postdoc-level academic role)
    "tv-l e13", "tv-l e14", "tv-l 13", "tv-l 14", "tvöd e13", "tvöd e14",
    "wisszeitvg",
    # Professorships & junior faculty (W1/W2/W3, Juniorprofessur, Tenure Track)
    "professur", "professor", "professorin",
    "juniorprofessur", "juniorprofessor", "juniorprofessorin",
    "w1", "w2", "w3", "w1-professur", "w2-professur", "w3-professur",
    "tenure track", "tenure-track",
    "assistant professor", "associate professor",
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
    # Psychology sub-disciplines — W2-Professur titles use these directly
    "wirtschaftspsychologie", "gesundheitspsychologie", "sozialpsychologie",
    "pädagogische psychologie", "pädagogik", "erziehungswissenschaft",
    "personalpsychologie", "berufspsychologie",
]
STRONG_VACANCY_SIGNALS = [
    "deadline", "closing date", "hiring", "vacancy", "opening",
    "position available", "join our team", "applications are open",
    "applications invited", "bewerbung", "bewerbungsfrist",
    "stellenausschreibung", "stellenangebot", "zu besetzen", "wir suchen",
]
WEAK_VACANCY_SIGNALS = ["apply", "application", "applications"]
VACANCY_SIGNALS = STRONG_VACANCY_SIGNALS + WEAK_VACANCY_SIGNALS

# Soft penalty only (score reduction)
NEGATIVE_DISCIPLINES = [
    "genomics", "astrophysics", "robotics",
    "mechanical engineering", "civil engineering", "electrical engineering",
    "biomedical", "oncology", "pharmacology", "agriculture", "veterinary",
]

# Hard exclusion — immediate drop regardless of topic match
HARD_EXCLUSIONS = [
    "computational chemistry", "chemistry", "chemical engineering",
    "tooth enamel", "dentistry", "dental", "molecular biology",
    "nanotechnology", "materials science", "neuroscience",
    "physics", "biology", "genetics", "clinical trial", "medicine",
    # Veterinary / animal science — catches 'One Health, Tierhygiene' etc.
    "veterinary", "tierhygiene", "tierseuche", "one health", "tierschutz",
    "animal health", "livestock",
]

# Foreign location blacklist — instantly drops non-German positions
NON_GERMAN_LOCATIONS = [
    re.compile(p, re.I) for p in [
        r"\bindia\b", r"\bnagaland\b", r"\bsingapore\b", r"\bmalaysia\b",
        r"\bchina\b", r"\bjapan\b", r"\bbrazil\b", r"\bsouth africa\b",
        r"\bpakistan\b", r"\bbangladesh\b", r"\bnigeria\b", r"\bkenya\b",
        r"\bindonesia\b", r"\bphilippines\b", r"\bvietnam\b",
        r"\buk\b", r"\bunited kingdom\b", r"\blondon\b", r"\bleeds\b",
        r"\bmanchester\b", r"\bcambridge\b", r"\boxford\b", r"\bedinburgh\b",
        r"\bcanada\b", r"\btoronto\b", r"\baustralia\b", r"\bsydney\b",
        r"\bmelbourne\b", r"\bnew zealand\b", r"\busa\b", r"\bunited states\b",
        r"\bfrance\b", r"\bparis\b", r"\bnetherlands\b", r"\bamsterdam\b",
        r"\bswitzerland\b", r"\bzurich\b", r"\bbelgium\b", r"\bbrussels\b",
        r"\bsweden\b", r"\bdenmark\b", r"\bnorway\b", r"\bfinland\b",
    ]
]

# German geographic whitelist — at least one must be present
GERMAN_SIGNALS = [
    ".de/", "germany", "deutschland",
    # Major cities already in scrapers
    "berlin", "münchen", "munich", "hamburg", "köln", "cologne",
    "frankfurt", "stuttgart", "leipzig", "heidelberg", "mannheim",
    "tübingen", "düsseldorf", "bonn", "dresden", "hannover",
    "nürnberg", "kiel", "potsdam", "bielefeld", "münster", "göttingen",
    # Additional German cities appearing in listings (e.g. Halle, Freiburg)
    "freiburg", "halle", "halle-wittenberg", "regensburg", "würzburg",
    "jena", "marburg", "darmstadt", "erlangen", "augsburg", "konstanz",
    "rostock", "mainz", "kassel", "trier", "paderborn",
    "bamberg", "witten", "herdecke", "bochum", "giessen", "siegen",
    "braunschweig", "koblenz", "magdeburg", "halle saale",
    # Pay grades and legal frameworks → unambiguous Germany signals
    "tv-l", "tvöd", "e13", "e14", "wisszeitvg",
    # Academic language / institutional markers
    "universität", "hochschule", "wissenschaft",
    # Funding bodies and research orgs
    "dfg", "daad", "mpg.de", "helmholtz", "leibniz", "fraunhofer",
    "max-planck-institut", "mlu", "mpi",
    # Germany-only job portals — any URL on these is definitionally German
    "psychjob.eu", "academics.de", "hsozkult.de", "stellenwerk.de",
    "akademische-jobs.de", "hochschul-job.de",
]

# Regex to detect gender-inclusive German title variants found in URL slugs and
# mixed-format listings e.g. "Wissenschaftliche-r-Mitarbeiterin-Mitarbeiter-m-w-d",
# "Post-Doktorandin (m/f/d/x)", "Postdoc-Position-m-f-d-x"
GERMAN_POSITION_REGEX = re.compile(
    r"("
    # English postdoc: postdoc, post-doc
    r"post[-\s]?doc(?:torand(?:in)?)?|"
    # German: postdoktorand(in), post-doktorand(in)
    r"post[-\s]?doktorand(?:in)?|"
    # Wissenschaftliche(r/n) Mitarbeiter(in) — handles slug 'wissenschaftliche-r-mitarbeiterin'
    r"wissenschaftliche[-\s]?[rn]?[-\s]+mitarbeiter(?:in)?|"
    # Professorships: W1/W2/W3-Professur, Juniorprofessur, Professor(in)
    r"(?:w[123]|junior|tenure[-\s]?track)?[-\s]?professur|"
    r"(?:junior[-\s]?)?professor(?:in)?|"
    r"tenure[-\s]?track|"
    # Akademischer Rat / Rätin
    r"akademische[-\s]?[rn]?[-\s]+(?:rat|rätin|mitarbeiter(?:in)?)|"
    # Research roles (with optional hyphen between words)
    r"research[-\s]+(?:associate|fellow|assistant|scientist)|"
    # German-only academic terms
    r"nachwuchswissenschaftler(?:in)?|qualifikationsstelle|"
    # Pay grades — unambiguous postdoc signal in Germany (tvoed = umlaut-stripped tvöd)
    r"tv[-\s]?l[-\s]?e?1[34]|tv(?:\u00f6d|oed)[-\s]?e?1[34]"
    r")"
    # Optional gender suffix: (m/w/d), (m/f/d/x), -m-w-d etc.
    r"(?:[-\s]*\(?[mwdxf/]+\)?)?",
    re.IGNORECASE,
)

TRUSTED_JOB_DOMAINS = [
    # International boards
    "euraxess.ec.europa.eu", "academicpositions.com", "universitypositions.eu",
    "jobs.chronicle.com", "higheredjobs.com", "careers.insidehighered.com",
    "inomics.com",
    # German clearinghouses & discipline hubs
    "academics.de", "service.bund.de", "psychjob.eu", "evifa.de",
    "hsozkult.de",          # H-Soz-Kult: social science & humanities jobs
    "stellenwerk.de",       # Multi-campus university job network
    "hochschulverband.de",  # DHV: German academic association
    # German research institutes
    "mpg.de", "helmholtz.de", "leibniz-gemeinschaft.de", "fraunhofer.de",
    "gesis.org", "iab.de", "dzhw.eu", "wzb.eu",
    "bibb.de", "ifo.de", "zew.de",
    # German universities (domain-based)
    "charite.de", "kit.edu", "rwth-aachen.de",
    "lmu.de", "hu-berlin.de", "jobs.tu-berlin.de", "uni-leipzig.de",
    "uni-heidelberg.de", "stellenwerk-koeln.de",
    # Professional networks (Germany)
    "linkedin.com/jobs", "xing.com/jobs",
    # RSS aggregators
    "academickeys.com",
    # Germany-scoped aggregators
    "scholarshipdb.net",
    # German university ATS / white-label recruiting platforms
    # University name is encoded in subdomain: uni-leipzig.b-ite.careers
    "b-ite.careers", "dvinci-hr.com", "softgarden.io", "persis.de",
    "interamt.de",   # German federal/state public sector vacancies
    # Direct university scraper source names (matched against item.source)
    "LMU München Direct", "HU Berlin Direct", "TU Berlin Direct",
    "Uni Leipzig Direct", "Uni Heidelberg Direct", "Uni Köln Direct",
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

GERMAN_MONTHS_MAP = {
    "januar": 1, "jan": 1,
    "februar": 2, "feb": 2,
    "märz": 3, "maerz": 3, "mrz": 3,
    "april": 4, "apr": 4,
    "mai": 5,
    "juni": 6, "jun": 6,
    "juli": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "okt": 10,
    "november": 11, "nov": 11,
    "dezember": 12, "dez": 12,
}

ENGLISH_MONTHS_MAP = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3,
    "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6, "july": 7, "jul": 7,
    "august": 8, "aug": 8, "september": 9, "sep": 9, "october": 10, "oct": 10,
    "november": 11, "nov": 11, "december": 12, "dec": 12,
}

ALL_MONTHS = {**GERMAN_MONTHS_MAP, **ENGLISH_MONTHS_MAP}
_MONTHS_PATTERN = "|".join(ALL_MONTHS.keys())


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
    """Extract institution name from a job title string.
    Strips parenthetical fragments, rejects location noise, and removes
    trailing geographic qualifiers (e.g. ', Nagaland, India').
    """
    # Remove parenthetical suffixes e.g. '(2-year contract)'
    clean = re.sub(r"\([^)]*\)", "", title).strip()
    parts = re.split(r"[-–|]", clean)
    candidate = parts[-1].strip() if len(parts) > 1 else clean.strip()

    # Reject if fewer than 2 words or contains digits (likely an address/fragment)
    words = candidate.split()
    if len(words) < 2 or re.search(r"\d", candidate):
        return clean or title.strip()

    # Strip trailing 'City, Region, Country' geographic qualifiers
    candidate = re.sub(r",\s*[A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z]+$", "", candidate).strip()

    return candidate or title.strip()


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
    """Return the raw matched deadline string if a keyword-anchored date is found."""
    return parse_deadline_string(text)


def parse_deadline_string(text: Optional[str]) -> Optional[str]:
    """
    Parses dates in both German and English formats:
    - 31.10.2026, 31/10/2026, 31-10-2026
    - 15. Oktober 2026, Ende Oktober 2026
    - October 15, 2026 / 15 Oct 2026
    - Contextual phrases: Bewerbungsfrist bis, Einsendeschluss, Deadline, etc.
    """
    if not text:
        return None

    # Priority 1: Keyword-anchored dates (highest precision)
    # 1a. Anchored Numeric (e.g. Bewerbungsfrist: 15.09.2026, Deadline: 15/09/2026)
    anchored_num = re.search(
        r"(?:bewerbungsfrist|bewerbungsschluss|frist|einsendeschluss|deadline|closing\s*date|apply\s*by|applications?\s*due|bis\s*zum|bis)[:\s]+"
        r"([0-3]?[0-9])[./\-]([0-1]?[0-9])[./\-]((?:20)?[2-3][0-9])",
        text,
        re.IGNORECASE,
    )
    if anchored_num:
        day, month, year = anchored_num.groups()
        if len(year) == 2:
            year = f"20{year}"
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 1b. Anchored Textual (e.g. Bewerbungsfrist: 15. Oktober 2026, Deadline: 30 September 2027, Frist: Ende Oktober 2026)
    anchored_text = re.search(
        rf"(?:bewerbungsfrist|bewerbungsschluss|frist|einsendeschluss|deadline|closing\s*date|apply\s*by|applications?\s*due|ausschreibungsende|bis\s*zum|bis)[:\s]+"
        rf"(?:([0-3]?[0-9])\.?\s+|ende\s+)?({_MONTHS_PATTERN})\s+((?:20)?[2-3][0-9])",
        text,
        re.IGNORECASE,
    )
    if anchored_text:
        day_str, month_str, year_str = anchored_text.groups()
        month = ALL_MONTHS.get(month_str.lower(), 1)
        year = int(year_str) if len(year_str) == 4 else int(f"20{year_str}")
        day = int(day_str) if day_str else 28
        try:
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 1c. Anchored English Month first (e.g. Deadline: October 15, 2026)
    anchored_en = re.search(
        rf"(?:bewerbungsfrist|bewerbungsschluss|frist|einsendeschluss|deadline|closing\s*date|apply\s*by|applications?\s*due)[:\s]+"
        rf"({_MONTHS_PATTERN})\s+([0-3]?[0-9])(?:st|nd|rd|th)?,?\s+((?:20)?[2-3][0-9])",
        text,
        re.IGNORECASE,
    )
    if anchored_en:
        month_str, day_str, year_str = anchored_en.groups()
        month = ALL_MONTHS.get(month_str.lower(), 1)
        year = int(year_str) if len(year_str) == 4 else int(f"20{year_str}")
        day = int(day_str) if day_str else 1
        try:
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # Priority 2: Unanchored explicit dates with Day + Month + Year
    # 2a. Numeric standard DD.MM.YYYY
    num_match = re.search(
        r"\b([0-3]?[0-9])[./\-]([0-1]?[0-9])[./\-]((?:20)?[2-3][0-9])\b",
        text,
        re.IGNORECASE,
    )
    if num_match:
        day, month, year = num_match.groups()
        if len(year) == 2:
            year = f"20{year}"
        try:
            dt = datetime(int(year), int(month), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 2b. Textual DD. Month YYYY or Ende Month YYYY
    text_match = re.search(
        rf"\b(?:([0-3]?[0-9])\.?\s+|ende\s+)({_MONTHS_PATTERN})\s+((?:20)?[2-3][0-9])\b",
        text,
        re.IGNORECASE,
    )
    if text_match:
        day_str, month_str, year_str = text_match.groups()
        month = ALL_MONTHS.get(month_str.lower(), 1)
        year = int(year_str) if len(year_str) == 4 else int(f"20{year_str}")
        day = int(day_str) if day_str else 28
        try:
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 2c. Textual Month DD, YYYY
    text_match_en = re.search(
        rf"\b({_MONTHS_PATTERN})\s+([0-3]?[0-9])(?:st|nd|rd|th)?,?\s+((?:20)?[2-3][0-9])\b",
        text,
        re.IGNORECASE,
    )
    if text_match_en:
        month_str, day_str, year_str = text_match_en.groups()
        month = ALL_MONTHS.get(month_str.lower(), 1)
        year = int(year_str) if len(year_str) == 4 else int(f"20{year_str}")
        day = int(day_str) if day_str else 1
        try:
            dt = datetime(year, month, day)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return None


# Alias for backward compatibility
parse_deadline_iso = parse_deadline_string


def is_deadline_expired(deadline_iso: Optional[str]) -> bool:
    """Sole decision-maker for expiration.

    Guaranteed outcomes:
      None          → no keyword-anchored deadline found → rolling/open → False (keep)
      '2026-10-15'  → future deadline → False (keep)
      '2025-09-30'  → confirmed past deadline → True  (drop)
    """
    if not deadline_iso:
        return False   # No anchor found — cannot confirm expiry — keep listing
    from datetime import date
    return deadline_iso < date.today().isoformat()


def detect_german(text: str) -> str:
    if GERMAN_C_RE.search(text):
        return "c1" if re.search(r"\bc1\b", text, re.I) else "c2"
    if GERMAN_B_RE.search(text):
        return "b1" if re.search(r"\bb1\b", text, re.I) else "b2"
    if GERMAN_NONE_RE.search(text):
        return "none"
    return "unknown"


def is_trusted_domain(url: str, source: str = "") -> bool:
    """Return True if url or source name is in TRUSTED_JOB_DOMAINS."""
    return any(d in url or d in source for d in TRUSTED_JOB_DOMAINS)



def is_strictly_germany(link: str, text: str) -> bool:
    """Two-stage Germany gate:
    1. Reject if an explicit foreign location is present AND no .de domain/German city overrides it.
    2. Require at least one affirmative German signal in link or text.
    """
    combined = f"{link} {text}".lower()

    # Stage 1 — foreign location blacklist
    if any(pat.search(combined) for pat in NON_GERMAN_LOCATIONS):
        # Override allowed only if the link is .de OR text explicitly says Germany/Deutschland
        if not (".de/" in link.lower() or "germany" in combined or "deutschland" in combined):
            return False

    # Stage 2 — require at least one German signal
    return any(sig in combined for sig in GERMAN_SIGNALS)


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
    """Classify a listing into germany / europe / other.
    Signal check runs FIRST — a German city/paygrade/institution in the URL or
    text always wins, regardless of institution tier.
    Tier meanings from compute_institution_bonus: 1=top, 2=high, 3=lower, 4=unknown.
    """
    combined = f"{text} {link}".lower()
    global_board_sources = {
        "RSS HigherEdJobs", "RSS AcademicKeys SocSci", "RSS AcademicKeys Education"
    }
    if source == "North America/ANZ Boards":
        return "other"

    # German signals win unconditionally — city, paygrade, or institution in URL/text
    if any(s in combined for s in GERMAN_SIGNALS):
        return "germany"

    # No German signal found — fall back to tier/source heuristics
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

    # Professorship bypass: W1/W2/W3, Juniorprofessur, Tenure Track on a trusted
    # German portal are rare, high-value openings. Skip the topic gate for these
    # since the position type itself IS the relevance signal.
    PROF_TERMS = ["w1", "w2", "w3", "professur", "juniorprofessur", "tenure track", "tenure-track"]
    if trusted and any(p in lower for p in PROF_TERMS):
        return True

    if not has_core and not has_adjacent:
        return False
    has_strong = any(t in lower for t in STRONG_VACANCY_SIGNALS)
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

        # ── Guard 1: LinkedIn posts/shares are not job listings ──────────────
        if "linkedin.com" in clean_link and "/jobs/view/" not in clean_link:
            continue

        # ── Guard 1b: psychjob.eu — keep /job/ listings, drop /jobs/ category pages ─
        if "psychjob.eu" in clean_link and "/job/" not in clean_link:
            continue

        # ── Guard 1c: academics.de — keep /jobs/ listings, drop /stellenanzeigen/ browse
        if "academics.de" in clean_link and "/stellenanzeigen/" in clean_link:
            continue

        # ── Guard 1d: personal profile / team pages — not job listings ──────────
        _PROFILE_PATTERNS = ["/team/", "/mitarbeiter/", "/staff/", "/person/", "/people/", "~b"]
        if any(p in clean_link.lower() for p in _PROFILE_PATTERNS) and "/job" not in clean_link.lower():
            continue

        # ── Guard 1e: XING city/discipline search pages — not individual jobs ──
        # Valid XING job: /jobs/title-123456789 (numeric ID at end)
        # Noise:         /jobs/postdoc-jobs-in-berlin  (city/discipline search)
        import re as _re
        if "xing.com/jobs/" in clean_link and _re.search(r"-jobs-in-", clean_link, _re.I):
            continue

        # ── Guard 1f: Non-job pages from university domains ──────────────────
        # University websites contain "Professur" in menus, news, press releases.
        # Only keep pages whose URL path signals an actual vacancy.
        _JOB_PATH_SIGNALS = [
            "/job", "/stelle", "/career", "/vacancy", "/ausschreibung",
            "/posting", "/jobposting", "/stellen", "/wissenschaftliche",
            "/offene-stellen", "/open-positions", "/recruitment",
        ]
        _TRUSTED_PORTALS = [
            "academics.de", "psychjob.eu", "hsozkult.de", "stellenwerk",
            "akademische-jobs.de", "hochschul-job.de", "euraxess",
            "scholarshipdb.net", "universitypositions.eu", "inomics.com",
            "b-ite.careers", "dvinci-hr.com", "softgarden.io",
            "interamt.de", "service.bund.de", "evifa.de", "psychjob",
        ]
        _NON_JOB_SUFFIXES = [".pdf", ".php", "/", "/news", "/presse", "/aktuell"]
        is_trusted_portal = any(p in clean_link for p in _TRUSTED_PORTALS)
        has_job_path = any(s in clean_link.lower() for s in _JOB_PATH_SIGNALS)
        ends_with_noise = any(clean_link.lower().rstrip("/").endswith(s) for s in [".pdf", "pressemitteilungen", "promotion", "forschen", "startseite"])
        if not is_trusted_portal and not has_job_path:
            continue
        if ends_with_noise:
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

        # ── Guard 2: Hard science terms → immediate drop ───────────────────
        if any(term in lower for term in HARD_EXCLUSIONS):
            continue

        # ── Guard 3: Germany-only gate ─────────────────────────────────────
        if not is_strictly_germany(clean_link, text):
            continue

        # Match position terms: list check covers normal text; regex catches
        # hyphenated slug variants e.g. "wissenschaftliche-r-mitarbeiterin-m-w-d"
        has_position = (
            any(t in lower for t in POSITION_TERMS)
            or bool(GERMAN_POSITION_REGEX.search(lower))
        )
        has_core = any(t in lower for t in TOPIC_CORE)
        has_adjacent = any(t in lower for t in TOPIC_ADJACENT)
        trusted = is_trusted_domain(url, item.source or "")

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

        # Professorship bonus: W1/W2/W3 Professur or Juniorprofessur on a core/adjacent
        # topic is a rare, high-value opening — bump base score up
        PROFESSORSHIP_TERMS = ["w1", "w2", "w3", "professur", "juniorprofessur", "tenure track", "tenure-track"]
        if any(p in lower for p in PROFESSORSHIP_TERMS):
            base = max(base, 9 if has_core else 7)

        inst_bonus, inst_tier = compute_institution_bonus(text, clean_link)
        neg_hits = [d for d in NEGATIVE_DISCIPLINES if d in lower]
        neg_penalty = (-1 if has_core else -3) if neg_hits else 0

        score = max(1, min(10, base + inst_bonus + neg_penalty))

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

        # parse_deadline_iso scans the full text for a keyword-anchored date
        # and returns the real ISO string (past OR future) or None (no anchor).
        deadline_iso = parse_deadline_iso(text)

        # Drop only when an anchored deadline is confirmed past.
        # None → rolling/open position → always kept.
        if is_deadline_expired(deadline_iso):
            continue

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
                deadline=deadline_iso,
                match_score=score,
                german_required=german,
                research_data={
                    "source": item.source,
                    "query_type": item.query_type,
                    "title_raw": title,
                    "deadline_text": deadline_iso,
                    "matched_terms": matched_terms,
                    "region_tier": region,
                    "live_verified": True,
                },
            )
        )

    return results


async def enrich_missing_deadlines(
    candidates: List[PostdocRecord], max_fetches: int = 20
) -> List[PostdocRecord]:
    """
    Only fetches full pages for candidates missing a deadline date.
    Keeps network traffic low while solving the 150-char snippet truncation issue.
    """
    if not candidates:
        return candidates

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        fetched = 0
        for item in candidates:
            if not item.deadline and fetched < max_fetches:
                try:
                    resp = await client.get(
                        item.link,
                        headers={
                            "User-Agent": (
                                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/122.0.0.0 Safari/537.36"
                            ),
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        },
                    )
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")
                        for elem in soup(["script", "style", "noscript", "svg"]):
                            elem.decompose()
                        page_text = soup.get_text(separator=" ", strip=True)[:4000]
                        resolved_deadline = parse_deadline_string(page_text)
                        if resolved_deadline:
                            item.deadline = resolved_deadline
                            if isinstance(item.research_data, dict):
                                item.research_data["deadline_text"] = resolved_deadline
                    fetched += 1
                except Exception:
                    continue

    # Filter out any candidates whose newly resolved deadline is confirmed past
    active_candidates = [c for c in candidates if not is_deadline_expired(c.deadline)]
    return active_candidates
