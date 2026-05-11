"""Earnings data collection from Yahoo Finance fundamentals."""

from __future__ import annotations

import asyncio
from typing import Dict, List

import yfinance as yf

from src.models.schemas import EarningsSummary
from src.utils.logger import AgentLogger

logger = AgentLogger("earnings_collector")


class EarningsCollector:
    """Collects lightweight quarterly snapshot from Yahoo fundamentals."""

    async def fetch_quarterly_snapshots(self, tickers: List[str]) -> List[EarningsSummary]:
        results: List[EarningsSummary] = []
        tasks = [self._fetch_one(ticker) for ticker in tickers]
        for item in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(item, EarningsSummary):
                results.append(item)
        logger.info("earnings_snapshots_collected", count=len(results))
        return results

    async def _fetch_one(self, ticker: str) -> EarningsSummary:
        try:
            stock = yf.Ticker(ticker)
            info: Dict = await asyncio.to_thread(lambda: stock.info)

            # Yahoo returns an empty or minimal dict when a ticker is not found
            if not info or info.get("trailingPE") is None and info.get("revenueGrowth") is None:
                logger.warning("earnings_empty_info", ticker=ticker, hint="ticker may be delisted or unavailable")

            trailing_pe = float(info.get("trailingPE", 0.0) or 0.0)
            roe = float(info.get("returnOnEquity", 0.0) or 0.0)
            revenue_growth = float(info.get("revenueGrowth", 0.0) or 0.0) * 100.0
            margins = float(info.get("ebitdaMargins", 0.0) or 0.0) * 100.0
            debt_to_equity = float(info.get("debtToEquity", 0.0) or 0.0)

            return EarningsSummary(
                ticker=ticker,
                period="latest_quarter_estimate",
                headline_summary=f"{ticker} fundamentals snapshot extracted from public data.",
                metrics={
                    "revenue_growth_pct": round(revenue_growth, 2),
                    "ebitda_margin_pct": round(margins, 2),
                    "debt_to_equity": round(debt_to_equity, 2),
                    "roe_pct": round(roe * 100.0, 2) if roe else 0.0,
                    "trailing_pe": round(trailing_pe, 2),
                },
            )
        except Exception as exc:
            logger.warning("earnings_fetch_failed", ticker=ticker, error=str(exc))
            raise  # re-raise so asyncio.gather captures it as an exception, not a result
