import os
import httpx
from typing import Dict, Any

try:
    from app.config import settings
    DEFAULT_TOKEN = settings.TELEGRAM_POSTDOC_BOT_TOKEN
    DEFAULT_CHAT_ID = settings.TELEGRAM_POSTDOC_CHAT_ID
except Exception:
    DEFAULT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    DEFAULT_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or DEFAULT_TOKEN
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or DEFAULT_CHAT_ID


def send_telegram_alert(job: Dict[str, Any]) -> bool:
    """
    Sends structured alert card to Telegram channel/DM.
    """
    score = job.get("match_percentage", job.get("match_score", 0))
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN":
        print(f"[Alert Simulation] High Match: {job.get('title')} ({score}%)")
        return True

    text = (
        f"🎯 *New Academic Match: {score}%*\n\n"
        f"📌 *Role:* {job.get('title', 'N/A')}\n"
        f"🏛 *Employer:* {job.get('organization', 'German University / Research Institute')}\n"
        f"💰 *Grade:* {job.get('pay_grade', 'TV-L E 13 / Postdoc')}\n"
        f"📅 *Deadline:* {job.get('deadline', 'Check Listing')}\n"
        f"🔍 *Matched On:* {', '.join(job.get('matched_keywords', [])[:4])}\n\n"
        f"🔗 [View Official Listing]({job.get('url', '')})"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }

    try:
        res = httpx.post(url, json=payload, timeout=10)
        return res.status_code == 200
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        return False
