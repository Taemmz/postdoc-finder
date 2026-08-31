import re
from typing import Any, Dict, List, Union

PROFILE_CRITERIA = {
    "core_domains": {
        "keywords": [
            "hochschuldidaktik", "lehrinnovation", "lehr- und lernforschung",
            "transformative hochschullehre", "curriculum development", "curriculumentwicklung",
            "qualitaetsmanagement lehre", "educational psychology", "paedagogische psychologie",
            "pädagogische psychologie", "erziehungswissenschaft", "studienqualitaet",
            "wissenschaftsmanagement", "dekanat", "forschungskoordination", "prorektorat lehre",
            "prorektorat", "berufliche bildung", "tvet", "service learning", "campus im dialog",
            "didaktik", "paedagogik", "pädagogik", "inklusion", "heterogenitaet",
            "heterogenität", "schulentwicklung", "bildungsforschung", "bildungssystem"
        ],
        "weight": 40
    },
    "methodology": {
        "keywords": [
            "qualitative forschung", "qualitative methods", "grounded theory",
            "inhaltsanalyse", "interview", "empirische bildungsforschung",
            "mixed methods", "evaluation", "projektevaluation", "wirkungsanalyse",
            "kompetenzmessung", "educational assessment", "psychometrie"
        ],
        "weight": 25
    },
    "future_topics": {
        "keywords": [
            "kuenstliche intelligenz", "artificial intelligence", "ki in der lehre",
            "digitalisierung in der lehre", "generative ki", "prompt", "edtech",
            "future skills", "futures literacy", "digitale lehrformate"
        ],
        "weight": 20
    },
    "pay_and_contract": {
        "keywords": [
            "e 13", "e13", "tv-l e 13", "tv-l 13", "tv-l e13", "e 14", "tv-l e 14", "tv-l 14",
            "postdoc", "postdoktorand", "akademische/r rat", "akademische/r mitarbeiter",
            "akademischer mitarbeiter", "tv-h e 13", "tvoed e 13", "wissenschaftliche/r mitarbeiter"
        ],
        "weight": 15
    }
}


def calculate_match_score(job: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    if isinstance(job, dict):
        title = job.get("title", "")
        organization = job.get("organization", "")
        pay_grade = job.get("pay_grade", "")
        raw_text = job.get("raw_text", "") or job.get("snippet", "")
        url = job.get("url", "") or job.get("link", "")
        deadline = job.get("deadline", "")
    else:
        title = getattr(job, "title", "") or getattr(job, "research_focus", "")
        organization = getattr(job, "institution", "") or getattr(job, "department", "")
        source = getattr(job, "source", "")
        pay_grade = ""
        raw_text = getattr(job, "snippet", "")
        url = getattr(job, "link", "")
        deadline = getattr(job, "deadline", "")
        if not organization:
            from app.processor import guess_institution
            organization = guess_institution(title, raw_text, url) or source.replace("Direct", "").strip() or "German Institution"

    searchable_text = f"{title} {organization} {pay_grade} {raw_text}".lower()
    total_score = 0.0
    matched_highlights = []
    category_scores = {}

    for category, spec in PROFILE_CRITERIA.items():
        matches = [kw for kw in spec["keywords"] if kw in searchable_text]
        if matches:
            ratio = min(len(matches) / 2.0, 1.0)
            score = spec["weight"] * ratio
            total_score += score
            matched_highlights.extend(matches)
            category_scores[category] = round(score, 1)
        else:
            category_scores[category] = 0.0

    percentage = int(round(min(total_score, 100.0)))
    ten_point = round(min(10.0, max(1.0, percentage / 10.0)), 1)

    if percentage >= 70:
        rec = "HIGH MATCH - Priority Apply"
    elif percentage >= 45:
        rec = "MODERATE MATCH - Review Details"
    else:
        rec = "LOW MATCH"

    res = {
        "title": title,
        "organization": organization,
        "url": url,
        "deadline": deadline,
        "match_percentage": percentage,
        "match_score": ten_point,
        "recommendation": rec,
        "matched_keywords": list(dict.fromkeys(matched_highlights)),
        "category_scores": category_scores,
    }
    if isinstance(job, dict):
        res = {**job, **res}
    return res
