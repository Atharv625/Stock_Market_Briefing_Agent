"""Earnings-specific API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query

from src.agents.earnings_analyzer_agent import EarningsAnalyzerAgent

router = APIRouter(tags=["earnings"])
agent = EarningsAnalyzerAgent()


@router.get("/earnings")
async def earnings_snapshot(tickers: str = Query(..., description="Comma separated Yahoo tickers")) -> list[dict]:
    parsed = [t.strip() for t in tickers.split(",") if t.strip()]
    items = await agent.analyze(parsed)
    return [i.model_dump() for i in items]
