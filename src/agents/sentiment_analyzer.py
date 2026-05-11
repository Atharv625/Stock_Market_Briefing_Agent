"""Sentiment computation from structured market signals."""

from __future__ import annotations

from typing import Iterable

from src.models.schemas import NewsItem, SentimentLabel


class SentimentAnalyzer:
    """Combines market breadth and news tone into a simple label."""

    def infer(self, advances: int, declines: int, news: Iterable[NewsItem]) -> SentimentLabel:
        score = 0
        score += 2 if advances > declines else -2 if declines > advances else 0
        for item in news:
            if item.sentiment == "bullish":
                score += item.importance_score
            elif item.sentiment == "bearish":
                score -= item.importance_score
        if score >= 4:
            return "bullish"
        if score <= -4:
            return "bearish"
        return "neutral"
