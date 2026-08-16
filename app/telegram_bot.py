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


def build_digest(records: List[PostdocRecord]) -> str:
    today = datetime.now().strftime("%d %b %Y")
    header = f"🔬 *SkillEdgeUp Post-Doc Finder* — {today}\n"

    if not records:
        return header + "\nNo new opportunities found this run."

    region_order = ["germany", "europe", "other"]
    region_labels = {
        "germany": "🇩🇪 GERMANY (Primary)",
        "europe": "🇪🇺 EUROPE (Secondary)",
        "other": "🌍 CANADA / US / ANZ (Tertiary)",
    }

    # Group by region → source
    grouped: dict = {r: {} for r in region_order}
    for rec in records:
        region = rec.research_data.get("region_tier", "other")
        if region not in grouped:
            region = "other"
        src = rec.research_data.get("source", "Web")
        grouped[region].setdefault(src, []).append(rec)

    msg = header + f"{len(records)} new opportunit{'y' if len(records) == 1 else 'ies'} found\n"

    for region in region_order:
        sources = grouped[region]
        region_count = sum(len(v) for v in sources.values())
        if region_count == 0:
            continue
        msg += f"\n═══ {region_labels[region]} ({region_count}) ═══\n"
        for source, items in sources.items():
            msg += f"\n📌 *{source}* ({len(items)})\n"
            for i, r in enumerate(items, 1):
                stars = score_to_stars(r.match_score)
                deadline = r.research_data.get("deadline_text")
                deadline_flag = f" | ⏰ {deadline}" if deadline else ""
                german = r.german_required
                german_flag = (
                    f" | 🇩🇪 {german.upper()} required"
                    if german in ("c1", "c2")
                    else ""
                )
                msg += (
                    f"{i}. {stars} {r.institution} — {r.match_score}/10"
                    f"{deadline_flag}{german_flag}\n{r.link}\n"
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
