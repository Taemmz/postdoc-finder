"""
cross_reference_hrk_matrix.py — Audit & Align HRK National Registry with Regional Matrix.
Compares:
1. data/hrk_institutions.json (269 national institutions)
2. docs/GERMAN_UNIVERSITIES_REGIONAL_EXPANSION_MATRIX.md (100-institution regional priority list)
Outputs structured cross-reference audit table and backlog insights.
"""

import json
import os
import re
import sys
from typing import Dict, List, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

HRK_JSON_PATH = "data/hrk_institutions.json"
MATRIX_MD_PATH = "docs/GERMAN_UNIVERSITIES_REGIONAL_EXPANSION_MATRIX.md"


def load_hrk_registry() -> List[Dict]:
    with open(HRK_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("institutions", [])


def load_matrix_entries() -> List[Dict]:
    entries = []
    with open(MATRIX_MD_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if line.strip().startswith("|") and not line.strip().startswith("| :") and not line.strip().startswith("| Status") and not line.strip().startswith("| Expansion Tier") and not line.strip().startswith("| **TOTALS**"):
            cols = [c.strip() for c in line.strip().split("|")[1:-1]]
            if len(cols) >= 6:
                status_raw = cols[0]
                inst_raw = cols[1].replace("**", "").strip()
                inst_type = cols[2] if len(cols) > 2 else ""
                city_state = cols[3] if len(cols) > 3 else ""
                scraper_or_url = cols[4] if len(cols) > 4 else ""
                
                is_active = "ACTIVE" in status_raw
                is_queued = "Queued" in status_raw or "⏳" in status_raw

                entries.append({
                    "name": inst_raw,
                    "is_active": is_active,
                    "is_queued": is_queued,
                    "type": inst_type,
                    "location": city_state,
                    "current_ref": scraper_or_url
                })
    return entries


def normalize_name(name: str) -> str:
    n = name.lower()
    for drop in [
        "universität", "hochschule", "technische", "fachhochschule", "technologie",
        "für angewandte wissenschaften", "applied sciences", "pädagogische",
        "otto-von-guericke", "martin-luther", "friedrich-schiller", "georg-august",
        "humboldt", "freie", "ludwig-maximilians", "julius-maximilians", "johann wolfgang",
        "albert-ludwigs", "eberhard karls", "ruhr-", "heinrich-heine", "bergische",
        "westfälische wilhelms", "johannes gutenberg", "justus-liebig", "philipps",
        "christian-albrechts", "gottfried wilhelm leibniz", "carl von ossietzky",
        "ernst-moritz-arndt", "bauhaus", "tu ", "rwth ", "th ", "hs ", "fh ", "eah ", "htwk ", "h2 "
    ]:
        n = n.replace(drop, " ")
    n = re.sub(r"[^a-z0-9äöüß]", " ", n)
    return " ".join(n.split())


def run_audit():
    hrk_list = load_hrk_registry()
    matrix_entries = load_matrix_entries()

    print("=" * 95)
    print("HRK NATIONAL REGISTRY VS. REGIONAL EXPANSION MATRIX AUDIT (Batch 3B)")
    print("=" * 95)
    print(f"Total HRK National Institutions:       {len(hrk_list)}")
    print(f"Total Regional Matrix Target Entities:  {len(matrix_entries)}")

    matched_active = []
    matched_queued = []
    unmatched_matrix = []
    
    hrk_matched_names = set()

    for m in matrix_entries:
        m_norm = normalize_name(m["name"])
        matched_hrk = None

        for h in hrk_list:
            h_norm = normalize_name(h["institution_name"])
            if m_norm and h_norm and (m_norm == h_norm or m_norm in h_norm or h_norm in m_norm):
                matched_hrk = h
                break

        if matched_hrk:
            hrk_matched_names.add(matched_hrk["institution_name"])
            if m["is_active"]:
                matched_active.append((m, matched_hrk))
            else:
                matched_queued.append((m, matched_hrk))
        else:
            unmatched_matrix.append(m)

    unmapped_hrk = [h for h in hrk_list if h["institution_name"] not in hrk_matched_names]

    print("\n" + "-" * 95)
    print("📊 AUDIT BREAKDOWN")
    print("-" * 95)
    print(f"1. Matrix Active Institutions Matched in HRK:  {len(matched_active):>3}")
    print(f"2. Matrix Queued Institutions Matched in HRK:  {len(matched_queued):>3}")
    print(f"3. Matrix Entities Not directly in HRK:        {len(unmatched_matrix):>3} (e.g. non-uni research institutes: DIPF, DZHW, DIE, STIL)")
    print(f"4. HRK National Expansion Backlog (Unmapped):   {len(unmapped_hrk):>3} (available for future batches beyond the 100)")
    print("-" * 95)

    print("\n🎯 SAMPLE OF MATCHED QUEUED INSTITUTIONS WITH AUTHORITATIVE HRK VACANCY URLS:")
    print("-" * 95)
    print(f"{'Matrix Institution':<32} | {'State':<18} | {'HRK Official Vacancy URL'}")
    print("-" * 95)
    for m, h in matched_queued[:12]:
        print(f"{m['name'][:32]:<32} | {h['state'][:18]:<18} | {h['vacancy_url']}")

    print("\n📦 SAMPLE OF NATIONAL EXPANSION BACKLOG (FROM HRK UNIVERSE):")
    print("-" * 95)
    print(f"{'Institution Name':<45} | {'Type':<30} | {'State'}")
    print("-" * 95)
    for h in unmapped_hrk[:10]:
        print(f"{h['institution_name'][:45]:<45} | {h['institution_type'][:30]:<30} | {h['state']}")

    return {
        "matched_active": len(matched_active),
        "matched_queued": len(matched_queued),
        "unmatched_matrix": len(unmatched_matrix),
        "unmapped_hrk": len(unmapped_hrk)
    }

if __name__ == "__main__":
    run_audit()
