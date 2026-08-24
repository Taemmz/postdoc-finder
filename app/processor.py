"""
processor.py — Full port of the n8n "Filter, Score & Extract" node.
Handles: exclusion filtering, position/topic keyword matching,
         institution detection, deadline extraction, German language detection,
         tiered institution scoring, deduplication, and region classification.
"""

import re
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

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

# Disallow senior professorships (W2, W3, full chair / Lehrstuhl)
SENIOR_CHAIR_BLOCKLIST = [
    r"\bw3\b",
    r"\bw2\b",
    r"\bw2/w3\b",
    r"\bw3/w2\b",
    r"\buniversity\s+professor\b",
    r"\buniv\.-prof\b",
    r"\blehrstuhlinhaber",
    r"\bordentliche[r]?\s+professor",
    r"\btenured\s+full\s+professor\b",
]

SENIOR_CHAIR_REGEX = re.compile("|".join(SENIOR_CHAIR_BLOCKLIST), re.IGNORECASE)

# Block hard-gated psychology tracks that require a primary Psychology B.Sc./M.Sc.
PURE_PSYCH_BLOCKLIST = [
    r"\bpersönlichkeitspsychologie\b",
    r"\bpersonality\s+psychology\b",
    r"\bpsychologische\s+diagnostik\b",
    r"\bpsychological\s+diagnostics\b",
    r"\bklinische\s+psychologie\b",
    r"\bclinical\s+psychology\b",
    r"\bpsychotherapie\b",
    r"\bpsychotherapy\b",
    r"\bapprobation\b",
]

PURE_PSYCH_REGEX = re.compile("|".join(PURE_PSYCH_BLOCKLIST), re.IGNORECASE)

# Hard gate on Pre-Doc / PhD / Dissertation pursuit listings
PRE_DOC_BLOCKLIST = [
    r"within\s+the\s+framework\s+of\s+a\s+doctorate",
    r"academic\s+qualification\s+within\s+the\s+framework\s+of\s+a\s+doctorate",
    r"interest\s+in\s+pursuing\s+a\s+doctorate",
    r"pursuing\s+a\s+doctorate",
    r"attractive\s+phd\s+position",
    r"phd\s+position\s+in",
    r"opportunity\s+to\s+pursue\s+a\s+doctorate",
    r"im\s+rahmen\s+einer\s+promotion",
    r"gelegenheit\s+zur\s+promotion",
    r"wissenschaftliche\s+weiterqualifikation\s+\(promotion\)",
    r"streben\s+sie\s+eine\s+promotion\s+an",
    r"promotion\s+vorgesehen",
    r"promotionsabsicht",
    r"promotionsvorhaben",
    r"promotionsstelle",
    r"(?<!post)\bdoktorand(?:in)?\b",
    r"(?<!post)\bdoctoral\s+(?:researcher|student|candidate)\b",
    r"\bphd\s+candidate\b",
    r"even\s+if\s+you\s+have\s+not\s+yet\s+completed\s+your\s+studies",
    r"studium\s+noch\s+nicht\s+abgeschlossen",
    r"\b(?:50|65|70|75)\s*%\s*(?:tv[-\s]?l|tvöd)\b",
]
PRE_DOC_REGEX = re.compile("|".join(PRE_DOC_BLOCKLIST), re.IGNORECASE)

POSTDOC_AFFIRMATIVE = [
    r"\bpostdoc(?:torand(?:in)?)?\b",
    r"\bpost-doc\b",
    r"\bpostdoctoral\b",
    r"abgeschlossene\s+promotion",
    r"promotion\s+vorausgesetzt",
    r"phd\s+required",
    r"completed\s+phd",
    r"habilitation",
    r"\bw1\b",
    r"\bjuniorprofessur\b",
    r"100\s*%\s*(?:tv[-\s]?l|tvöd)",
]
POSTDOC_AFFIRMATIVE_REGEX = re.compile("|".join(POSTDOC_AFFIRMATIVE), re.IGNORECASE)

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
    # Junior Professorships & early faculty (W1, Juniorprofessur, Tenure Track)
    "juniorprofessur", "juniorprofessor", "juniorprofessorin",
    "w1", "w1-professur",
    "tenure track", "tenure-track",
    "assistant professor",
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
    # Psychology sub-disciplines
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
    # Chemistry / Material Science
    "computational chemistry", "chemistry", "chemical engineering",
    "tooth enamel", "dentistry", "dental", "molecular biology",
    "nanotechnology", "materials science", "materials",
    # Hard Physics / Atmospheric / Tropical / Climate Physics
    "tropical dynamics", "tropical", "meteorology", "meteorologie",
    "geophysics", "geophysik", "astronomy", "astronomie", "astrophysics",
    "quantum", "fluid mechanics", "strömungsmechanik", "stroemungsmechanik",
    "atmospheric", "atmosphäre", "atmosphaere", "oceanography", "ozeanographie",
    "climatology", "geology", "geowissenschaften", "thermodynamics",
    "plasma physics", "optics", "particle physics", "solid state physics",
    "kondensierte materie", "hydrodynamics", "physics", "systemsimulation",
    "technische mechanik", "regelungs-technik", "regelungs\xadtechnik",
    # Life sciences & Clinical medicine
    "biology", "genetics", "clinical trial", "medicine", "oncology", "pharmacology",
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
    # Junior professorships: W1-Professur, Juniorprofessur, Tenure Track
    r"(?:w1|junior|tenure[-\s]?track)?[-\s]?professur|"
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

# Phrases indicating contract duration or appointment start dates (NOT application deadlines)
DURATION_IGNORE_PATTERNS = [
    r"limited\s+to\s+(?:a\s+term\s+ending)?",
    r"term\s+ending",
    r"befristet\s+(?:bis\s+zum|bis)",
    r"vertragslaufzeit\s+bis",
    r"laufzeit\s+bis",
    r"starting\s+(?:on|from)",
    r"beginn\s+zum",
    r"beginn\s+ab",
    r"einstellung\s+zum",
    r"zum\s+(?:nächstmöglichen\s+zeitpunkt|frühestmöglichen\s+zeitpunkt)",
]

# Explicit application anchors (Highest Priority for Deadline Detection)
APPLICATION_ANCHOR_PATTERNS = [
    r"application(?:s)?\s+by",
    r"apply\s+by",
    r"closing\s+date",
    r"deadline",
    r"bewerbungsfrist\s+(?:bis\s+zum|bis)?",
    r"bewerbungsschluss\s+(?:bis\s+zum|bis)?",
    r"einsendeschluss\s+(?:bis\s+zum|bis)?",
    r"bewerbungen\s+bis\s+(?:zum)?",
    r"frist\s+(?:bis\s+zum|bis)?",
    r"ausschreibungsende",
]

APPLICATION_ANCHOR_REGEX = re.compile(
    rf"(?:{'|'.join(APPLICATION_ANCHOR_PATTERNS)})[:\s]*",
    re.IGNORECASE,
)

GERMAN_CITIES = [
    "Aachen", "Augsburg", "Bamberg", "Bayreuth", "Berlin", "Bielefeld", "Bochum", "Bonn",
    "Braunschweig", "Bremen", "Chemnitz", "Clausthal", "Cologne", "Köln", "Darmstadt",
    "Dortmund", "Dresden", "Duisburg", "Düsseldorf", "Erlangen", "Essen", "Frankfurt",
    "Freiberg", "Freiburg", "Gießen", "Giessen", "Göttingen", "Goettingen", "Greifswald",
    "Hagen", "Halle", "Hamburg", "Hannover", "Heidelberg", "Ilmenau", "Jena", "Kaiserslautern",
    "Karlsruhe", "Kassel", "Kiel", "Koblenz", "Konstanz", "Leipzig", "Lübeck", "Luebeck",
    "Magdeburg", "Mainz", "Mannheim", "Marburg", "Munich", "München", "Münster", "Muenster",
    "Nürnberg", "Nuernberg", "Oldenburg", "Osnabrück", "Paderborn", "Passau", "Potsdam",
    "Regensburg", "Rostock", "Saarbrücken", "Siegen", "Stuttgart", "Trier", "Tübingen",
    "Tuebingen", "Ulm", "Vechta", "Weimar", "Witten", "Würzburg", "Wuerzburg", "Wuppertal"
]

INSTITUTION_PATTERNS = [
    (r"(?:university\s+of|universit[äa]t\s+(?:zu\s+)?|uni\s+)([A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)", r"Universität \1"),
    (r"(?:freie\s+universit[äa]t|fu|free\s+university\s+of)\s+berlin", "Freie Universität Berlin"),
    (r"(?:humboldt-universit[äa]t|hu|humboldt\s+university)\s+(?:zu\s+)?berlin", "Humboldt-Universität zu Berlin"),
    (r"(?:technische\s+universit[äa]t|technical\s+university\s+of|tu)\s+([A-ZÄÖÜ][a-zäöüß]+)", r"TU \1"),
    (r"(?:ludwig-maximilians-universit[äa]t|lmu)\s*(?:m[üu]nchen)?", "LMU München"),
    (r"(?:technische\s+universit[äa]t\s+m[üu]nchen|tum)\b", "TU München"),
    (r"(?:rwth\s+aachen|rheinisch-westf[äa]lische\s+technische\s+hochschule)", "RWTH Aachen"),
    (r"(?:karlsruher\s+institut\s+f[üu]r\s+technologie|kit|karlsruhe\s+institute\s+of\s+technology)\b", "Karlsruhe Institute of Technology (KIT)"),
    (r"(?:hochschule)\s+([A-ZÄÖÜ][a-zäöüß]+(?:-[A-ZÄÖÜ][a-zäöüß]+)?)", r"Hochschule \1"),
    (r"\bdzhw\b", "Deutsches Zentrum für Hochschul- und Wissenschaftsforschung (DZHW)"),
    (r"\biab\b", "Institut für Arbeitsmarkt- und Berufsforschung (IAB)"),
    (r"\bwzb\b", "Wissenschaftszentrum Berlin für Sozialforschung (WZB)"),
    (r"\bbibb\b", "Bundesinstitut für Berufsbildung (BIBB)"),
    (r"\bgesis\b", "GESIS – Leibniz-Institut für Sozialwissenschaften"),
    (r"\bifo\b", "ifo Institut – Leibniz-Institut für Wirtschaftsforschung"),
    (r"\bzew\b", "ZEW – Leibniz-Zentrum für Europäische Wirtschaftsforschung"),
    (r"max-planck-institut[a-zäöü\s-]*|max\s+planck\s+institute", "Max-Planck-Institut"),
    (r"fraunhofer-institut[a-zäöü\s-]*|fraunhofer\s+institute", "Fraunhofer-Institut"),
    (r"helmholtz-zentrum[a-zäöü\s-]*|helmholtz\s+centre", "Helmholtz-Zentrum"),
    (r"charit[ée]", "Charité – Universitätsmedizin Berlin"),
]

DEPT_PATTERNS = [
    r"(?:institut\s+f[üu]r|department\s+of|fachbereich|fakult[äa]t\s+f[üu]r|chair\s+of|lehrstuhl\s+f[üu]r)\s+([A-Za-zÄÖÜäöüß\s,-]+?)(?=\.|\band\b|\bwith\b|\bat\b|,|\n|$)",
    r"(?:arbeits-\s+und\s+organisationspsychologie|arbeitsmarkt-?\s*und\s+berufsforschung|erziehungswissenschaft|hochschulforschung|bildungsforschung|psychometrie|wirtschaftspsychologie)",
]

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


def extract_city(text: str) -> Optional[str]:
    for city in GERMAN_CITIES:
        if re.search(rf"\b{city}\b", text, re.IGNORECASE):
            return city.replace("Munich", "München").replace("Cologne", "Köln")
    return None


def extract_department(title: str, text: str = "") -> Optional[str]:
    combined = f"{title} {text}"
    for pat in DEPT_PATTERNS:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            val = m.group(0).strip().rstrip(" ,.-")
            if 3 < len(val) < 60:
                return val
    return None


def guess_institution(title: str, text: str = "", url: str = "") -> str:
    """Extract clean institution name from title, text, or url."""
    combined = f"{title} {text} {url}"
    for pat, repl in INSTITUTION_PATTERNS:
        m = re.search(pat, combined, re.IGNORECASE)
        if m:
            if r"\1" in repl:
                city_or_name = m.group(1).strip()
                city_clean = extract_city(city_or_name) or city_or_name
                return repl.replace(r"\1", city_clean)
            return repl

    city = extract_city(combined)
    if city:
        return f"Universität {city}"

    clean = re.sub(r"\([^)]*\)", "", title).strip()
    parts = re.split(r"[-–|,]", clean)
    candidate = parts[-1].strip() if len(parts) > 1 else clean.strip()
    candidate = re.sub(r"\d+", "", candidate).strip()
    return candidate if len(candidate.split()) >= 2 else (clean or title.strip())


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


def clean_context(text: str) -> str:
    """Strips contract duration and start date clauses so they don't pollute date matching."""
    cleaned = text
    for pattern in DURATION_IGNORE_PATTERNS:
        cleaned = re.sub(
            rf"{pattern}\s+[A-Za-z0-9\.\s,]+?(?=\.|\band\b|\bwith\b|\bor\b|\bdeadline\b|\bapply\b|\bbewerbung\b|$)",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
    return cleaned


def is_plausible_deadline(dt: datetime) -> bool:
    """Sanity check: An application deadline must not be > 1 year in the future
    (dates 2-4 years ahead are contract terms or grant durations).
    """
    now = datetime.now()
    max_future = now + timedelta(days=365)
    min_past = now - timedelta(days=90)
    return min_past <= dt <= max_future


def parse_deadline_string(text: Optional[str]) -> Optional[str]:
    """Parses application deadlines in German and English formats, ignoring contract duration dates."""
    if not text:
        return None

    # Step 1: Check for explicit application anchors first (highest confidence)
    anchor_matches = list(APPLICATION_ANCHOR_REGEX.finditer(text))
    for m in anchor_matches:
        start_idx = m.end()
        snippet = text[start_idx : start_idx + 50]

        # Numeric DD.MM.YYYY
        num_m = re.search(r"([0-3]?[0-9])[./\-]([0-1]?[0-9])[./\-]((?:20)?[2-3][0-9])", snippet)
        if num_m:
            d, mo, yr = num_m.groups()
            yr = f"20{yr}" if len(yr) == 2 else yr
            try:
                dt = datetime(int(yr), int(mo), int(d))
                if is_plausible_deadline(dt):
                    return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

        # Textual Month (DD. Month YYYY or Month DD, YYYY or Ende Month YYYY)
        text_m = re.search(
            rf"(?:([0-3]?[0-9])\.?\s+|ende\s+)?({_MONTHS_PATTERN})\s+([0-3]?[0-9])?,?\s*((?:20)?[2-3][0-9])",
            snippet,
            re.IGNORECASE,
        )
        if text_m:
            d1, mo_str, d2, yr_str = text_m.groups()
            day = int(d1 or d2 or 28)
            month = ALL_MONTHS[mo_str.lower()]
            year = int(yr_str) if len(yr_str) == 4 else int(f"20{yr_str}")
            try:
                dt = datetime(year, month, day)
                if is_plausible_deadline(dt):
                    return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass

    # Step 2: Fallback to general date regex on cleaned text (duration clauses stripped)
    sanitized = clean_context(text)

    # General Numeric DD.MM.YYYY
    num_match = re.search(r"\b([0-3]?[0-9])[./\-]([0-1]?[0-9])[./\-]((?:20)?[2-3][0-9])\b", sanitized)
    if num_match:
        d, mo, yr = num_match.groups()
        yr = f"20{yr}" if len(yr) == 2 else yr
        try:
            dt = datetime(int(yr), int(mo), int(d))
            if is_plausible_deadline(dt):
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # General Textual DD. Month YYYY or Ende Month YYYY
    text_match = re.search(
        rf"\b(?:([0-3]?[0-9])\.?\s+|ende\s+)({_MONTHS_PATTERN})\s+((?:20)?[2-3][0-9])\b",
        sanitized,
        re.IGNORECASE,
    )
    if text_match:
        d_str, mo_str, yr_str = text_match.groups()
        day = int(d_str) if d_str else 28
        month = ALL_MONTHS[mo_str.lower()]
        year = int(yr_str) if len(yr_str) == 4 else int(f"20{yr_str}")
        try:
            dt = datetime(year, month, day)
            if is_plausible_deadline(dt):
                return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    # General Textual Month DD, YYYY
    text_match_en = re.search(
        rf"\b({_MONTHS_PATTERN})\s+([0-3]?[0-9])(?:st|nd|rd|th)?,?\s+((?:20)?[2-3][0-9])\b",
        sanitized,
        re.IGNORECASE,
    )
    if text_match_en:
        mo_str, d_str, yr_str = text_match_en.groups()
        day = int(d_str) if d_str else 1
        month = ALL_MONTHS[mo_str.lower()]
        year = int(yr_str) if len(yr_str) == 4 else int(f"20{yr_str}")
        try:
            dt = datetime(year, month, day)
            if is_plausible_deadline(dt):
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
    """Classify a listing into germany / europe / other."""
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


def passes_qualification_gates(title: str, text: str) -> Tuple[bool, str]:
    full_corpus = f"{title} {text}".lower()

    # Gate 1: Check for W2/W3 senior chair blocklist
    if SENIOR_CHAIR_REGEX.search(title):
        return False, "Excluded: Senior Professorship (W2/W3 / Tenured Chair)"

    # Gate 2: Check for pure psychology requirements
    if PURE_PSYCH_REGEX.search(full_corpus):
        return False, "Excluded: Requires formal Psychology degree / Clinical Approbation"

    # Gate 3: Check for Pre-Doc / PhD pursuit positions
    if PRE_DOC_REGEX.search(full_corpus):
        if re.search(r"within\s+the\s+framework\s+of\s+a\s+doctorate|im\s+rahmen\s+einer\s+promotion|pursuing\s+a\s+doctorate|promotionsstelle|\bphd\s+candidate\b|(?<!post)\bdoktorand", full_corpus, re.I):
            return False, "Excluded: Pre-Doctoral / PhD candidate role"
        if not POSTDOC_AFFIRMATIVE_REGEX.search(title):
            return False, "Excluded: Pre-Doctoral / PhD pursuit position"

    return True, "Passed"


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

    # Professorship bypass: W1, Juniorprofessur, Tenure Track on a trusted
    # German portal are rare, high-value openings. Skip the topic gate for these
    # since the position type itself IS the relevance signal.
    PROF_TERMS = ["w1", "juniorprofessur", "juniorprofessor", "tenure track", "tenure-track"]
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

        # Qualification gates: Senior Chair (W2/W3) & Pure/Clinical Psychology
        passes_qual, _ = passes_qualification_gates(title, text)
        if not passes_qual:
            continue

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

        # Normalise relative links
        full_link = clean_link
        if clean_link.startswith("/"):
            if "universitypositions" in (item.source or "").lower():
                full_link = f"https://universitypositions.eu{clean_link}"
            elif "academics.de" in (item.source or "").lower():
                full_link = f"https://www.academics.de{clean_link}"
            elif "euraxess" in (item.source or "").lower():
                full_link = f"https://euraxess.ec.europa.eu{clean_link}"

        institution = guess_institution(title, snippet, full_link) or "Unknown — see listing"
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

        # Junior Professorship bonus: W1 Professur or Juniorprofessur on a core/adjacent
        # topic is a rare, high-value opening — bump base score up
        PROFESSORSHIP_TERMS = ["w1", "juniorprofessur", "juniorprofessor", "tenure track", "tenure-track"]
        if any(p in lower for p in PROFESSORSHIP_TERMS):
            base = max(base, 9 if has_core else 7)

        inst_bonus, inst_tier = compute_institution_bonus(text, clean_link)
        neg_hits = [d for d in NEGATIVE_DISCIPLINES if d in lower]
        neg_penalty = (-1 if has_core else -3) if neg_hits else 0

        score = max(1, min(10, base + inst_bonus + neg_penalty))

        german = detect_german(text)
        if german in ("c1", "c2"):
            score = min(score, 4)

        # parse_deadline_iso scans the full text for a keyword-anchored date
        # and returns the real ISO string (past OR future) or None (no anchor).
        deadline_iso = parse_deadline_iso(text)

        # Drop only when an anchored deadline is confirmed past.
        # None → rolling/open position → always kept.
        if is_deadline_expired(deadline_iso):
            continue

        region = compute_region(item.source, full_link, text, inst_tier)
        city = extract_city(f"{title} {snippet} {full_link}")
        department = extract_department(title, snippet)
        country = "Germany" if region == "germany" else ("Europe" if region == "europe" else "Other")

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
                department=department,
                research_focus=snippet[:300],
                country=country,
                city=city,
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
