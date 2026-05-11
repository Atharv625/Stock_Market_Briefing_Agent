"""Pydantic schemas used across API and agent layers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


SentimentLabel = Literal["bullish", "bearish", "neutral"]
ReportType = Literal["pre_market", "midday", "closing", "deep_analysis"]


class IndexSnapshot(BaseModel):
    name: str
    symbol: str
    last_price: float
    change: float
    change_percent: float


class MarketSummary(BaseModel):
    timestamp: datetime
    report_type: ReportType
    indices: List[IndexSnapshot]
    sector_performance: Dict[str, float] = Field(default_factory=dict)
    market_breadth: Dict[str, int] = Field(default_factory=dict)
    fii_dii_activity: Dict[str, float] = Field(default_factory=dict)
    macro_indicators: Dict[str, float] = Field(default_factory=dict)
    global_market_impact: Dict[str, float] = Field(default_factory=dict)


class StockMove(BaseModel):
    ticker: str
    company_name: str
    sector: Optional[str] = None
    last_price: float
    change_percent: float
    volume: Optional[int] = None
    open_price: Optional[float] = None
    previous_close: Optional[float] = None


class NewsItem(BaseModel):
    id: str
    ticker: Optional[str] = None
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str
    category: str = "general"
    importance_score: int = 1
    sentiment: SentimentLabel = "neutral"


class EarningsSummary(BaseModel):
    ticker: str
    period: str
    headline_summary: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    management_guidance: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    outlook: str = ""


class GeneratedReport(BaseModel):
    report_id: str
    generated_at: datetime
    report_type: ReportType
    market_summary: MarketSummary
    top_gainers: List[StockMove]
    top_losers: List[StockMove]
    key_highs_lows: Dict[str, List[StockMove]]
    key_news: List[NewsItem]
    earnings_highlights: List[EarningsSummary]
    market_sentiment: SentimentLabel
    llm_summary: str
