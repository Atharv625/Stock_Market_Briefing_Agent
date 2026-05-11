"""News deduplication and rule-based classification helpers."""

from __future__ import annotations

from typing import List

from src.models.schemas import NewsItem

BULLISH_KEYWORDS = ["order win", "acquisition", "upgrade", "buyback", "record high", "deal win"]
BEARISH_KEYWORDS = ["downgrade", "fraud", "penalty", "stake sale", "delay", "default"]
HIGH_IMPORTANCE_KEYWORDS = ["merger", "acquisition", "guidance", "regulatory", "block deal", "results"]


def classify_news_items(items: List[NewsItem]) -> List[NewsItem]:
    """Annotate sentiment and importance with deterministic heuristics."""
    classified: List[NewsItem] = []
    for item in items:
        text = f"{item.title} {item.summary}".lower()
        sentiment = "neutral"
        if any(k in text for k in BULLISH_KEYWORDS):
            sentiment = "bullish"
        if any(k in text for k in BEARISH_KEYWORDS):
            sentiment = "bearish"
        importance = 1
        if any(k in text for k in HIGH_IMPORTANCE_KEYWORDS):
            importance = 4
        elif len(text) > 220:
            importance = 3
        item.sentiment = sentiment  # type: ignore[assignment]
        item.importance_score = importance
        item.category = infer_category(text)
        classified.append(item)
    return sorted(classified, key=lambda i: (i.importance_score, i.published_at), reverse=True)


def infer_category(text: str) -> str:
    if "result" in text or "earnings" in text:
        return "earnings"
    if "order" in text or "contract" in text:
        return "order_win"
    if "stake" in text or "insider" in text:
        return "holding_pattern"
    if "merger" in text or "acquisition" in text:
        return "mna"
    return "general"
