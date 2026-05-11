"""Telegram message delivery with retry and markdown formatting."""

from __future__ import annotations

import re

import httpx

from src.models.schemas import GeneratedReport
from src.utils.config import get_settings
from src.utils.retry import with_async_retry

# Telegram sendMessage hard limit
_TELEGRAM_MAX_CHARS = 4096

# Characters that break Telegram MarkdownV1 when inside plain text
_MD_SPECIAL = re.compile(r"([_*`\[])")


def _escape(text: str) -> str:
    """Escape Markdown special chars in dynamic content (tickers, titles, etc.)."""
    return _MD_SPECIAL.sub(r"\\\1", text)


class TelegramNotifier:
    def __init__(self) -> None:
        self.settings = get_settings()

    def render_message(self, report: GeneratedReport) -> str:
        nifty = next((x for x in report.market_summary.indices if x.name == "nifty_50"), None)
        sensex = next((x for x in report.market_summary.indices if x.name == "sensex"), None)

        gainers = "\n".join(
            [f"- {_escape(x.company_name)}: {x.change_percent:+.2f}%" for x in report.top_gainers[:3]]
        ) or "_None_"
        losers = "\n".join(
            [f"- {_escape(x.company_name)}: {x.change_percent:+.2f}%" for x in report.top_losers[:3]]
        ) or "_None_"
        headlines = "\n".join(
            [f"- {_escape(n.title)}" for n in report.key_news[:5]]
        ) or "_No headlines_"
        earnings = "\n".join(
            [f"- {_escape(e.headline_summary)}" for e in report.earnings_highlights[:3]]
        ) or "_No earnings data_"

        nifty_line = f"Nifty 50: {nifty.change_percent:+.2f}% ({nifty.last_price:,.0f})\n" if nifty else "Nifty 50: N/A\n"
        sensex_line = f"Sensex: {sensex.change:+.2f} pts ({sensex.last_price:,.0f})\n\n" if sensex else "Sensex: N/A\n\n"

        # Build static sections first, then fill remaining space with LLM summary
        header = (
            f"📈 *{report.report_type.upper().replace('_', ' ')} MARKET BRIEF*\n\n"
            + nifty_line
            + sensex_line
            + "*Top Gainers:*\n"
            + f"{gainers}\n\n"
            + "*Top Losers:*\n"
            + f"{losers}\n\n"
            + "*Key News:*\n"
            + f"{headlines}\n\n"
            + "*Quarterly Highlights:*\n"
            + f"{earnings}\n\n"
            + f"*Market Sentiment:* {report.market_sentiment.capitalize()}\n\n"
        )

        # Use all remaining characters for the LLM summary instead of hard-coding 900
        remaining = _TELEGRAM_MAX_CHARS - len(header) - 3  # 3 chars for "..." safety margin
        llm_text = report.llm_summary[:max(remaining, 0)]
        if len(report.llm_summary) > remaining:
            llm_text = llm_text.rstrip() + "…"

        return header + llm_text

    @with_async_retry(max_attempts=3, min_wait=1, max_wait=8, exceptions=(httpx.HTTPError,))
    async def send(self, report: GeneratedReport) -> None:
        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            return
        message = self.render_message(report)
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.settings.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
