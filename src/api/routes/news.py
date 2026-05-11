"""News-specific API routes."""

from __future__ import annotations

from fastapi import APIRouter

from src.agents.news_intelligence_agent import NewsIntelligenceAgent

router = APIRouter(tags=["news"])
agent = NewsIntelligenceAgent()


@router.get("/news")
async def latest_news(limit: int = 20) -> list[dict]:
    items = await agent.get_ranked_news(limit=limit)
    return [i.model_dump() for i in items]
