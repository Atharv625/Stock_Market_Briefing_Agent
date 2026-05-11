"""Agent for collecting and ranking market-moving news."""

from __future__ import annotations

from typing import List, Optional

from src.collectors.news_collector import NewsCollector
from src.models.schemas import NewsItem
from src.parsers.news_parser import classify_news_items


class NewsIntelligenceAgent:
    def __init__(self) -> None:
        self.collector = NewsCollector()

    async def get_ranked_news(self, ticker: Optional[str] = None, limit: int = 20) -> List[NewsItem]:
        items = await self.collector.fetch_latest_news(limit=limit * 2)
        parsed = classify_news_items(items)
        if ticker:
            ticker_upper = ticker.upper()
            parsed = [item for item in parsed if ticker_upper in item.title.upper() or ticker_upper in item.summary.upper()]
        return parsed[:limit]
