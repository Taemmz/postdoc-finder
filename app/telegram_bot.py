"""telegram_bot.py — Builds and dispatches the Telegram digest."""

import httpx
from datetime import datetime
from typing import List

from app.config import settings
from app.models import PostdocRecord


def score_to_stars(score: int) -> str:
    if score >= 9:
        return "⭐⭐⭐⭐⭐"
    if score >= 7:
        return "⭐⭐⭐⭐"
    if score >= 5:
        return "⭐⭐⭐"
    if score >= 3:
        return "⭐⭐"
    return "⭐"


def _deadline_display(deadline_iso: str | None) -> tuple[str, int]:
    """Return (display_string, sort_key) for a deadline ISO string.
    sort_key: 0 = most urgent, 9999 = no deadline found.
    """
    if not deadline_iso:
        return ("📅 Deadline: open / not stated", 9999)
    try:
        from datetime import date
        d = date.fromisoformat(deadline_iso)
        days_left = (d - date.today()).days
        formatted = d.strftime("%-d %b %Y") if hasattr(d, "strftime") else deadline_iso
        # Try Windows-compatible strftime
        try:
            formatted = d.strftime("%d %b %Y").lstrip("0")
        except Exception:
            formatted = deadline_iso
        if days_left <= 7:
            urgency = f"🔴 Deadline: {formatted}  ({days_left}d left — URGENT)"
        elif days_left <= 21:
            urgency = f"🟡 Deadline: {formatted}  ({days_left}d left)"
        else:
            urgency = f"🟢 Deadline: {formatted}  ({days_left}d left)"
        return (urgency, days_left)
    except Exception:
        return (f"📅 Deadline: {deadline_iso}", 9999)


def build_digest(records: List[PostdocRecord]) -> str:
    today = datetime.now().strftime("%d %b %Y")
    header = f"🔬 SkillEdgeUp Post-Doc Finder — {today}\n"

    if not records:
        return header + "\nNo new opportunities found this run."

    region_order = ["germany", "europe", "other"]
    region_labels = {
        "germany": "🇩🇪 GERMANY (Primary)",
        "europe": "🇪🇺 EUROPE (Secondary)",
        "other": "🌍 CANADA / US / ANZ (Tertiary)",
    }

    # Group by region
    grouped: dict = {r: [] for r in region_order}
    for rec in records:
        region = rec.research_data.get("region_tier", "other")
        if region not in grouped:
            region = "other"
        grouped[region].append(rec)

    # Sort within each region: most urgent deadline first, then by score desc
    for region in region_order:
        grouped[region].sort(
            key=lambda r: (
                _deadline_display(r.research_data.get("deadline_text"))[1],
                -r.match_score,
            )
        )

    total = len(records)
    msg = header + f"{total} new opportunit{'y' if total == 1 else 'ies'} found\n"

    for region in region_order:
        items = grouped[region]
        if not items:
            continue
        msg += f"\n{'='*3} {region_labels[region]} ({len(items)}) {'='*3}\n"
        for i, r in enumerate(items, 1):
            stars = score_to_stars(r.match_score)
            deadline_str, _ = _deadline_display(r.research_data.get("deadline_text"))
            german = r.german_required
            german_flag = (
                f"\n   🇩🇪 German {german.upper()} required"
                if german in ("c1", "c2")
                else ""
            )
            source = r.research_data.get("source", "Web")
            msg += (
                f"\n{i}. {stars} {r.match_score}/10 — {r.institution}\n"
                f"   {deadline_str}{german_flag}\n"
                f"   [{source}]\n"
                f"   {r.link}\n"
            )

    return msg



async def send_telegram_alert(client: httpx.AsyncClient, text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_POSTDOC_BOT_TOKEN}/sendMessage"

    # Split into <=4000 char chunks (Telegram message limit is 4096)
    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]

    for chunk in chunks:
        try:
            res = await client.post(
                url,
                json={
                    "chat_id": settings.TELEGRAM_POSTDOC_CHAT_ID,
                    "text": chunk,
                    "disable_web_page_preview": True,
                },
                timeout=15.0,
            )
            res.raise_for_status()
        except Exception as exc:
            print(f"  [telegram] Failed to send chunk — {exc}")
            return

    print(f"  [telegram] Digest sent successfully ({len(chunks)} message(s)).")
