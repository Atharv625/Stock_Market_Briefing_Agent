"""Build full daily intelligence report using all agents."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from typing import List

from src.agents.earnings_analyzer_agent import EarningsAnalyzerAgent
from src.agents.market_data_agent import MarketDataAgent
from src.agents.news_intelligence_agent import NewsIntelligenceAgent
from src.agents.sentiment_analyzer import SentimentAnalyzer
from src.models.schemas import GeneratedReport, NewsItem
from src.summarizers.llm_client import LLMClient
from src.summarizers.prompt_library import MARKET_SUMMARY_PROMPT

# Fallback watchlist used when there are fewer than 3 gainers (e.g. full red day)
_EARNINGS_FALLBACK_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
]


class DailyReportGenerator:
    def __init__(self) -> None:
        self.market_agent = MarketDataAgent()
        self.news_agent = NewsIntelligenceAgent()
        self.earnings_agent = EarningsAnalyzerAgent()
        self.sentiment = SentimentAnalyzer()
        self.llm = LLMClient()

    async def generate(self, report_type: str = "closing") -> GeneratedReport:
        # Run all three I/O-heavy fetches concurrently for maximum speed
        (market_summary, gainers, losers, highs_lows), key_news = await asyncio.gather(
            self.market_agent.build_market_summary(report_type=report_type),
            self.news_agent.get_ranked_news(limit=12),
        )

        # Build earnings tickers: top gainers first, pad with fallback watchlist if needed
        earnings_tickers = [g.ticker for g in gainers[:3]]
        if len(earnings_tickers) < 3:
            seen = set(earnings_tickers)
            for fb in _EARNINGS_FALLBACK_TICKERS:
                if fb not in seen:
                    earnings_tickers.append(fb)
                    seen.add(fb)
                if len(earnings_tickers) >= 3:
                    break

        earnings = await self.earnings_agent.analyze(earnings_tickers)

        sentiment = self.sentiment.infer(
            advances=market_summary.market_breadth.get("advances", 0),
            declines=market_summary.market_breadth.get("declines", 0),
            news=key_news[:8],
        )
        prompt = MARKET_SUMMARY_PROMPT.format(
            report_type=report_type,
            market_summary_json=self.llm.as_json(market_summary.model_dump()),
            gainers_json=self.llm.as_json([g.model_dump() for g in gainers]),
            losers_json=self.llm.as_json([l.model_dump() for l in losers]),
            news_json=self.llm.as_json([n.model_dump() for n in key_news[:10]]),
            earnings_json=self.llm.as_json([e.model_dump() for e in earnings]),
            sentiment_label=sentiment,
        )
        llm_summary = await self.llm.complete(prompt)
        return GeneratedReport(
            report_id=str(uuid.uuid4()),
            generated_at=datetime.now(timezone.utc),
            report_type=report_type,  # type: ignore[arg-type]
            market_summary=market_summary,
            top_gainers=gainers,
            top_losers=losers,
            key_highs_lows=highs_lows,
            key_news=key_news,
            earnings_highlights=earnings,
            market_sentiment=sentiment,
            llm_summary=llm_summary,
        )
