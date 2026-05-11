"""FastAPI routes for stock market intelligence APIs."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.agents.earnings_analyzer_agent import EarningsAnalyzerAgent
from src.agents.market_data_agent import MarketDataAgent
from src.agents.news_intelligence_agent import NewsIntelligenceAgent
from src.agents.sentiment_analyzer import SentimentAnalyzer
from src.models.schemas import SentimentLabel

router = APIRouter(tags=["market-intelligence"])

market_agent = MarketDataAgent()
news_agent = NewsIntelligenceAgent()
earnings_agent = EarningsAnalyzerAgent()
sentiment_agent = SentimentAnalyzer()


@router.get("/market-summary")
async def get_market_summary(report_type: str = "closing") -> dict:
    summary, gainers, losers, highs_lows = await market_agent.build_market_summary(report_type=report_type)
    return {
        "summary": summary.model_dump(),
        "top_gainers": [g.model_dump() for g in gainers],
        "top_losers": [l.model_dump() for l in losers],
        "key_highs_lows": {k: [x.model_dump() for x in v] for k, v in highs_lows.items()},
    }


@router.get("/top-gainers")
async def get_top_gainers() -> list[dict]:
    _, gainers, _, _ = await market_agent.build_market_summary(report_type="closing")
    return [x.model_dump() for x in gainers]


@router.get("/top-losers")
async def get_top_losers() -> list[dict]:
    _, _, losers, _ = await market_agent.build_market_summary(report_type="closing")
    return [x.model_dump() for x in losers]


@router.get("/company-news/{ticker}")
async def get_company_news(ticker: str) -> list[dict]:
    news = await news_agent.get_ranked_news(ticker=ticker, limit=15)
    return [x.model_dump() for x in news]


@router.get("/earnings-summary/{ticker}")
async def get_earnings_summary(ticker: str) -> dict:
    results = await earnings_agent.analyze([ticker])
    if not results:
        raise HTTPException(status_code=404, detail=f"No earnings snapshot found for {ticker}")
    return results[0].model_dump()


@router.get("/market-sentiment")
async def get_market_sentiment() -> dict:
    summary, _, _, _ = await market_agent.build_market_summary(report_type="closing")
    news = await news_agent.get_ranked_news(limit=20)
    label: SentimentLabel = sentiment_agent.infer(
        advances=summary.market_breadth.get("advances", 0),
        declines=summary.market_breadth.get("declines", 0),
        news=news[:10],
    )
    return {"sentiment": label, "breadth": summary.market_breadth}
