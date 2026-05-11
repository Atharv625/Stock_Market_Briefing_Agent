"""News collection from public RSS feeds for Indian markets."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime, timezone
from typing import List

import feedparser

from src.models.schemas import NewsItem
from src.utils.logger import AgentLogger

logger = AgentLogger("news_collector")

RSS_SOURCES = [
    ("EconomicTimes", "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms"),
    ("Moneycontrol", "https://www.moneycontrol.com/rss/business.xml"),
    ("LiveMint", "https://www.livemint.com/rss/markets"),
]


class NewsCollector:
    """Fetches market related RSS items and normalizes them."""

    async def _fetch_feed(self, source: str, url: str, per_source: int) -> List[NewsItem]:
        """Fetch one RSS feed in a thread so it does not block the async event loop."""
        feed = await asyncio.to_thread(feedparser.parse, url)
        items: List[NewsItem] = []
        for entry in feed.entries[:per_source]:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", "").strip()
            if not title or not link:
                continue
            # sha256 gives better collision resistance than md5 for stored IDs
            digest = hashlib.sha256(f"{title}|{link}".encode()).hexdigest()[:32]
            published = self._parse_published(entry)
            items.append(
                NewsItem(
                    id=digest,
                    title=title,
                    source=source,
                    url=link,
                    summary=summary,
                    published_at=published,
                )
            )
        return items

    async def fetch_latest_news(self, limit: int = 40) -> List[NewsItem]:
        per_source = limit // max(len(RSS_SOURCES), 1)
        # Fetch all feeds concurrently — none of these block the event loop anymore
        tasks = [self._fetch_feed(source, url, per_source) for source, url in RSS_SOURCES]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

        all_items: List[NewsItem] = []
        for batch in batches:
            if isinstance(batch, list):
                all_items.extend(batch)
            else:
                logger.warning("rss_feed_failed", error=str(batch))

        deduped = {item.id: item for item in all_items}
        results = sorted(deduped.values(), key=lambda i: i.published_at, reverse=True)[:limit]
        logger.info("news_items_collected", count=len(results))
        return results

    @staticmethod
    def _parse_published(entry: feedparser.FeedParserDict) -> datetime:
        published = entry.get("published_parsed")
        if published:
            return datetime(*published[:6], tzinfo=timezone.utc)
        return datetime.now(timezone.utc)
