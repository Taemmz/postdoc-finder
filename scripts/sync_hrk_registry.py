"""
sync_hrk_registry.py — National German Higher Education Institution Registry Synchronizer.
Harvests authoritative vacancy endpoints directly from the Hochschulrektorenkonferenz (HRK).
Saves structured ground-truth registry to data/hrk_institutions.json.
"""

import json
import os
import re
import ssl
import sys
import urllib.request
from datetime import date
from typing import Dict, List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# Ensure UTF-8 stdout
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

HRK_URLS = [
    "https://www.hrk.de/mitglieder/stellenanzeigen-der-hochschulen/",
    "https://www.hrk.de/hrk/stellenanzeigen/stellenanzeigen-der-hochschulen/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

STATE_CITY_MAP = {
    "aachen": ("Nordrhein-Westfalen", "Aachen"),
    "aalen": ("Baden-Württemberg", "Aalen"),
    "albstadt": ("Baden-Württemberg", "Albstadt"),
    "amberg": ("Bayern", "Amberg"),
    "weiden": ("Bayern", "Weiden"),
    "ansbach": ("Bayern", "Ansbach"),
    "aschaffenburg": ("Bayern", "Aschaffenburg"),
    "augsburg": ("Bayern", "Augsburg"),
    "bamberg": ("Bayern", "Bamberg"),
    "bayreuth": ("Bayern", "Bayreuth"),
    "berlin": ("Berlin", "Berlin"),
    "bielefeld": ("Nordrhein-Westfalen", "Bielefeld"),
    "bingen": ("Rheinland-Pfalz", "Bingen"),
    "bochum": ("Nordrhein-Westfalen", "Bochum"),
    "bonn": ("Nordrhein-Westfalen", "Bonn"),
    "brandenburg": ("Brandenburg", "Brandenburg"),
    "braunschweig": ("Niedersachsen", "Braunschweig"),
    "bremen": ("Bremen", "Bremen"),
    "bremerhaven": ("Bremen", "Bremerhaven"),
    "chemnitz": ("Sachsen", "Chemnitz"),
    "clausthal": ("Niedersachsen", "Clausthal-Zellerfeld"),
    "coburg": ("Bayern", "Coburg"),
    "cottbus": ("Brandenburg", "Cottbus"),
    "darmstadt": ("Hessen", "Darmstadt"),
    "deggendorf": ("Bayern", "Deggendorf"),
    "dortmund": ("Nordrhein-Westfalen", "Dortmund"),
    "dresden": ("Sachsen", "Dresden"),
    "duisburg": ("Nordrhein-Westfalen", "Duisburg"),
    "essen": ("Nordrhein-Westfalen", "Essen"),
    "düsseldorf": ("Nordrhein-Westfalen", "Düsseldorf"),
    "eberswalde": ("Brandenburg", "Eberswalde"),
    "eichstätt": ("Bayern", "Eichstätt"),
    "ingolstadt": ("Bayern", "Ingolstadt"),
    "emden": ("Niedersachsen", "Emden"),
    "leer": ("Niedersachsen", "Leer"),
    "erfurt": ("Thüringen", "Erfurt"),
    "erlangen": ("Bayern", "Erlangen"),
    "nürnberg": ("Bayern", "Nürnberg"),
    "flensburg": ("Schleswig-Holstein", "Flensburg"),
    "frankfurt": ("Hessen", "Frankfurt am Main"),
    "oder": ("Brandenburg", "Frankfurt (Oder)"),
    "freiberg": ("Sachsen", "Freiberg"),
    "freiburg": ("Baden-Württemberg", "Freiburg im Breisgau"),
    "fulda": ("Hessen", "Fulda"),
    "furtwangen": ("Baden-Württemberg", "Furtwangen"),
    "geisenheim": ("Hessen", "Geisenheim"),
    "gelsenkirchen": ("Nordrhein-Westfalen", "Gelsenkirchen"),
    "bocholt": ("Nordrhein-Westfalen", "Bocholt"),
    "recklinghausen": ("Nordrhein-Westfalen", "Recklinghausen"),
    "giessen": ("Hessen", "Gießen"),
    "gießen": ("Hessen", "Gießen"),
    "göttingen": ("Niedersachsen", "Göttingen"),
    "goettingen": ("Niedersachsen", "Göttingen"),
    "greifswald": ("Mecklenburg-Vorpommern", "Greifswald"),
    "hagen": ("Nordrhein-Westfalen", "Hagen"),
    "halle": ("Sachsen-Anhalt", "Halle (Saale)"),
    "hamburg": ("Hamburg", "Hamburg"),
    "hamm": ("Nordrhein-Westfalen", "Hamm"),
    "lippstadt": ("Nordrhein-Westfalen", "Lippstadt"),
    "hannover": ("Niedersachsen", "Hannover"),
    "harz": ("Sachsen-Anhalt", "Wernigerode"),
    "heidelberg": ("Baden-Württemberg", "Heidelberg"),
    "heilbronn": ("Baden-Württemberg", "Heilbronn"),
    "hildesheim": ("Niedersachsen", "Hildesheim"),
    "hof": ("Bayern", "Hof"),
    "hohenheim": ("Baden-Württemberg", "Stuttgart"),
    "ilmenau": ("Thüringen", "Ilmenau"),
    "jena": ("Thüringen", "Jena"),
    "kaiserslautern": ("Rheinland-Pfalz", "Kaiserslautern"),
    "karlsruhe": ("Baden-Württemberg", "Karlsruhe"),
    "kassel": ("Hessen", "Kassel"),
    "kehl": ("Baden-Württemberg", "Kehl"),
    "kempten": ("Bayern", "Kempten"),
    "kiel": ("Schleswig-Holstein", "Kiel"),
    "koblenz": ("Rheinland-Pfalz", "Koblenz"),
    "köln": ("Nordrhein-Westfalen", "Köln"),
    "koeln": ("Nordrhein-Westfalen", "Köln"),
    "konstanz": ("Baden-Württemberg", "Konstanz"),
    "landshut": ("Bayern", "Landshut"),
    "leipzig": ("Sachsen", "Leipzig"),
    "lübeck": ("Schleswig-Holstein", "Lübeck"),
    "luebeck": ("Schleswig-Holstein", "Lübeck"),
    "ludwigsburg": ("Baden-Württemberg", "Ludwigsburg"),
    "ludwigshafen": ("Rheinland-Pfalz", "Ludwigshafen"),
    "lüneburg": ("Niedersachsen", "Lüneburg"),
    "lueneburg": ("Niedersachsen", "Lüneburg"),
    "magdeburg": ("Sachsen-Anhalt", "Magdeburg"),
    "mainz": ("Rheinland-Pfalz", "Mainz"),
    "mannheim": ("Baden-Württemberg", "Mannheim"),
    "marburg": ("Hessen", "Marburg"),
    "merseburg": ("Sachsen-Anhalt", "Merseburg"),
    "mittweida": ("Sachsen", "Mittweida"),
    "münchen": ("Bayern", "München"),
    "muenchen": ("Bayern", "München"),
    "münster": ("Nordrhein-Westfalen", "Münster"),
    "muenster": ("Nordrhein-Westfalen", "Münster"),
    "neubrandenburg": ("Mecklenburg-Vorpommern", "Neubrandenburg"),
    "nordhausen": ("Thüringen", "Nordhausen"),
    "nürtingen": ("Baden-Württemberg", "Nürtingen"),
    "geislingen": ("Baden-Württemberg", "Geislingen"),
    "offenburg": ("Baden-Württemberg", "Offenburg"),
    "oldenburg": ("Niedersachsen", "Oldenburg"),
    "osnabrück": ("Niedersachsen", "Osnabrück"),
    "osnabrueck": ("Niedersachsen", "Osnabrück"),
    "paderborn": ("Nordrhein-Westfalen", "Paderborn"),
    "passau": ("Bayern", "Passau"),
    "pforzheim": ("Baden-Württemberg", "Pforzheim"),
    "potsdam": ("Brandenburg", "Potsdam"),
    "ravensburg": ("Baden-Württemberg", "Ravensburg"),
    "weingarten": ("Baden-Württemberg", "Weingarten"),
    "regensburg": ("Bayern", "Regensburg"),
    "reutlingen": ("Baden-Württemberg", "Reutlingen"),
    "rostock": ("Mecklenburg-Vorpommern", "Rostock"),
    "rottenburg": ("Baden-Württemberg", "Rottenburg"),
    "saarbrücken": ("Saarland", "Saarbrücken"),
    "saarland": ("Saarland", "Saarbrücken"),
    "schmalkalden": ("Thüringen", "Schmalkalden"),
    "schwäbisch gmünd": ("Baden-Württemberg", "Schwäbisch Gmünd"),
    "siegen": ("Nordrhein-Westfalen", "Siegen"),
    "speyer": ("Rheinland-Pfalz", "Speyer"),
    "stralsund": ("Mecklenburg-Vorpommern", "Stralsund"),
    "stuttgart": ("Baden-Württemberg", "Stuttgart"),
    "trier": ("Rheinland-Pfalz", "Trier"),
    "trossingen": ("Baden-Württemberg", "Trossingen"),
    "tübingen": ("Baden-Württemberg", "Tübingen"),
    "tuebingen": ("Baden-Württemberg", "Tübingen"),
    "ulm": ("Baden-Württemberg", "Ulm"),
    "vechta": ("Niedersachsen", "Vechta"),
    "wedel": ("Schleswig-Holstein", "Wedel"),
    "weihenstephan": ("Bayern", "Freising"),
    "trizdorf": ("Bayern", "Weidenbach"),
    "weimar": ("Thüringen", "Weimar"),
    "wiesbaden": ("Hessen", "Wiesbaden"),
    "wilhelmshaven": ("Niedersachsen", "Wilhelmshaven"),
    "wismar": ("Mecklenburg-Vorpommern", "Wismar"),
    "worms": ("Rheinland-Pfalz", "Worms"),
    "wuppertal": ("Nordrhein-Westfalen", "Wuppertal"),
    "würzburg": ("Bayern", "Würzburg"),
    "wuerzburg": ("Bayern", "Würzburg"),
    "zittau": ("Sachsen", "Zittau"),
    "görlitz": ("Sachsen", "Görlitz"),
    "zwickau": ("Sachsen", "Zwickau"),
}


def classify_institution_type(name: str) -> str:
    """Classifies the German higher education institution type."""
    name_lower = name.lower()
    if "pädagogische hochschule" in name_lower or name_lower.startswith("ph "):
        return "Pädagogische Hochschule (PH)"
    elif any(k in name_lower for k in ["musik", "kunst", "film", "schauspiel", "theater", "gestaltung"]):
        return "Kunst- und Musikhochschule"
    elif any(k in name_lower for k in ["kirchliche", "theologische", "philosophisch-theologische"]):
        return "Kirchliche / Theologische Hochschule"
    elif any(k in name_lower for k in ["universität", "tu ", "technische universität", "fernuniversität", "medizinische hochschule"]):
        return "Universität / Technische Universität"
    elif any(k in name_lower for k in ["hochschule", "fachhochschule", "technische hochschule", "oth ", "dhbw", "applied sciences"]):
        return "Hochschule für Angewandte Wissenschaften (HAW/FH)"
    else:
        return "Sonstige Hochschule"


def infer_state_and_city(name: str, url: str) -> (Optional[str], Optional[str]):
    """Infers the federal state and city from institution name or url."""
    text = (name + " " + url).lower()
    for key, (state, city) in STATE_CITY_MAP.items():
        if re.search(rf"\b{re.escape(key)}\b", text):
            return state, city
    return "Deutschland (National)", None


def derive_base_url(vacancy_url: str) -> str:
    """Extracts root official domain from vacancy URL."""
    parsed = urlparse(vacancy_url)
    return f"{parsed.scheme}://{parsed.netloc}"


def fetch_hrk_directory() -> List[Dict]:
    """Fetches and parses the HRK member university vacancy directory."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    html_doc = None
    source_url_used = None

    for u in HRK_URLS:
        try:
            req = urllib.request.Request(u, headers=HEADERS)
            with urllib.request.urlopen(req, context=ctx, timeout=25) as response:
                html_doc = response.read().decode("utf-8", errors="ignore")
                source_url_used = u
                print(f"  [HRK Sync] Successfully fetched HRK directory from {u} ({len(html_doc):,} bytes)")
                break
        except Exception as e:
            print(f"  [HRK Sync] Warning: Failed fetching {u}: {e}")

    if not html_doc:
        raise RuntimeError("Failed to fetch HRK directory from all candidate endpoints.")

    soup = BeautifulSoup(html_doc, "html.parser")
    institutions: List[Dict] = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        name = a.get_text(separator=" ", strip=True)

        if not name or len(name) < 4:
            continue
        # Skip generic navigation links or external portal links
        if any(skip in href.lower() for skip in ["hrk.de", "hochschulkompass.de", "impressum", "datenschutz", "kontakt"]):
            continue
        if not href.startswith("http"):
            continue
        if href in seen_urls:
            continue

        # Skip known non-institution generic names
        if name.lower() in ["hochschulen", "studium", "promotion", "weiterbildung"]:
            continue

        seen_urls.add(href)
        inst_type = classify_institution_type(name)
        state, city = infer_state_and_city(name, href)
        base_url = derive_base_url(href)

        institutions.append({
            "institution_name": name,
            "institution_type": inst_type,
            "state": state,
            "city": city,
            "official_url": base_url,
            "vacancy_url": href,
            "hrk_source_url": source_url_used,
            "last_verified": str(date.today()),
        })

    # Sort alphabetically by name
    institutions.sort(key=lambda x: x["institution_name"].lower())
    return institutions


def sync_registry(output_file: str = "data/hrk_institutions.json") -> List[Dict]:
    """Synchronizes HRK directory and writes structured JSON."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    institutions = fetch_hrk_directory()

    registry_payload = {
        "metadata": {
            "source": "Hochschulrektorenkonferenz (HRK) - Stellenanzeigen der Mitgliedshochschulen",
            "source_urls": HRK_URLS,
            "total_institutions": len(institutions),
            "generated_date": str(date.today()),
            "description": "National authoritative registry of official German university and HAW vacancy portals."
        },
        "institutions": institutions
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(registry_payload, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Successfully synchronized {len(institutions)} institutions to {output_file}")
    return institutions


if __name__ == "__main__":
    print("=" * 80)
    print("HRK NATIONAL INSTITUTION REGISTRY SYNCHRONIZER (Batch 3A)")
    print("=" * 80)
    sync_registry()
