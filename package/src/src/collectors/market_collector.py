"""Market data collection for Indian indices and Nifty 50 constituents."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, List

import math

import yfinance as yf

from src.models.schemas import IndexSnapshot, StockMove
from src.utils.config import INDEX_TICKERS, NIFTY_50_TICKERS
from src.utils.logger import AgentLogger
from src.utils.retry import with_async_retry

logger = AgentLogger("market_collector")


def _safe_int(val: object, default: int = 0) -> int:
    """Convert val to int safely — returns default for NaN, None, or non-numeric."""
    try:
        f = float(val)  # type: ignore[arg-type]
        return int(f) if not math.isnan(f) else default
    except (TypeError, ValueError):
        return default


class MarketDataCollector:
    """Collects market index snapshots and stock movers."""

    @with_async_retry(max_attempts=3, min_wait=1, max_wait=6)
    async def get_index_snapshot(self, name: str, symbol: str) -> IndexSnapshot:
        data = await asyncio.to_thread(yf.Ticker(symbol).history, period="5d", interval="1d")
        if data.empty:
            raise ValueError(f"No data for index {symbol}")
        row = data.iloc[-1]
        close_price = float(row["Close"])
        prev_close = float(data.iloc[-2]["Close"]) if len(data) > 1 else close_price
        change = close_price - prev_close
        pct = (change / prev_close * 100.0) if prev_close else 0.0
        return IndexSnapshot(
            name=name,
            symbol=symbol,
            last_price=round(close_price, 2),
            change=round(change, 2),
            change_percent=round(pct, 2),
        )

    async def get_indices(self) -> List[IndexSnapshot]:
        tasks = [self.get_index_snapshot(name, symbol) for name, symbol in INDEX_TICKERS.items()]
        snapshots = await asyncio.gather(*tasks, return_exceptions=True)
        valid = [s for s in snapshots if isinstance(s, IndexSnapshot)]
        logger.info("indices_collected", count=len(valid))
        return valid

    @with_async_retry(max_attempts=3, min_wait=1, max_wait=6)
    async def get_nifty_constituents_moves(self) -> List[StockMove]:
        frame = await asyncio.to_thread(yf.download, tickers=" ".join(NIFTY_50_TICKERS), period="2d", interval="1d", group_by="ticker", progress=False)
        moves: List[StockMove] = []
        for ticker in NIFTY_50_TICKERS:
            try:
                ticker_data = frame[ticker]
                if ticker_data.empty:
                    continue
                latest = ticker_data.iloc[-1]
                prev = ticker_data.iloc[-2] if len(ticker_data) > 1 else latest
                change = float(latest["Close"] - prev["Close"])
                pct = (change / float(prev["Close"]) * 100.0) if float(prev["Close"]) else 0.0
                moves.append(
                    StockMove(
                        ticker=ticker,
                        company_name=ticker.replace(".NS", ""),
                        last_price=round(float(latest["Close"]), 2),
                        change_percent=round(pct, 2),
                        volume=_safe_int(latest.get("Volume", 0)),  # NaN-safe
                        open_price=round(float(latest.get("Open", 0.0)), 2),
                        previous_close=round(float(prev.get("Close", 0.0)), 2),
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive for partial source failures
                logger.warning("constituent_parse_failed", ticker=ticker, error=str(exc))
        logger.info("nifty_constituents_collected", count=len(moves))
        return moves

    async def get_market_breadth(self, moves: List[StockMove]) -> Dict[str, int]:
        advances = sum(1 for m in moves if m.change_percent > 0)
        declines = sum(1 for m in moves if m.change_percent < 0)
        unchanged = len(moves) - advances - declines
        return {"advances": advances, "declines": declines, "unchanged": unchanged}

    async def get_macro_indicators(self) -> Dict[str, float]:
        symbols = {"usd_inr": "INR=X", "brent_crude": "BZ=F", "us_10y_yield": "^TNX"}
        metrics: Dict[str, float] = {}
        for key, symbol in symbols.items():
            data = await asyncio.to_thread(yf.Ticker(symbol).history, period="2d", interval="1d")
            if data.empty:
                continue
            metrics[key] = round(float(data.iloc[-1]["Close"]), 4)
        return metrics

    @staticmethod
    def now_utc() -> datetime:
        return datetime.now(timezone.utc)
