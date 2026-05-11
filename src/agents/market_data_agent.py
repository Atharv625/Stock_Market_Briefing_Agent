"""Agent responsible for market-level and movers intelligence."""

from __future__ import annotations

import asyncio
from datetime import timezone
from typing import Dict

from src.collectors.market_collector import MarketDataCollector
from src.models.schemas import MarketSummary, StockMove
from src.utils.config import SECTOR_TICKERS
from src.utils.logger import AgentLogger

logger = AgentLogger("market_data_agent")

# Valid report types — keep in sync with models/schemas.py ReportType Literal
_VALID_REPORT_TYPES = {"pre_market", "midday", "closing", "deep_analysis"}


class MarketDataAgent:
    def __init__(self) -> None:
        self.collector = MarketDataCollector()

    async def _get_sector_performance(self) -> Dict[str, float]:
        """Fetch live sector index % changes in parallel."""
        async def _fetch_one(name: str, symbol: str) -> tuple[str, float]:
            try:
                snap = await self.collector.get_index_snapshot(name, symbol)
                return name, snap.change_percent
            except Exception as exc:
                logger.warning("sector_fetch_failed", sector=name, error=str(exc))
                return name, 0.0

        tasks = [_fetch_one(name, sym) for name, sym in SECTOR_TICKERS.items()]
        pairs = await asyncio.gather(*tasks)
        return {name: pct for name, pct in pairs}

    async def build_market_summary(
        self, report_type: str
    ) -> tuple[MarketSummary, list[StockMove], list[StockMove], dict]:
        # Validate before Pydantic sees it — gives a clear error instead of a cryptic validation dump
        if report_type not in _VALID_REPORT_TYPES:
            logger.warning(
                "invalid_report_type",
                received=report_type,
                fallback="closing",
            )
            report_type = "closing"

        indices, moves, sector_perf, macro = await asyncio.gather(
            self.collector.get_indices(),
            self.collector.get_nifty_constituents_moves(),
            self._get_sector_performance(),
            self.collector.get_macro_indicators(),
        )

        gainers = sorted(moves, key=lambda m: m.change_percent, reverse=True)[:5]
        losers = sorted(moves, key=lambda m: m.change_percent)[:5]
        breadth = await self.collector.get_market_breadth(moves)

        summary = MarketSummary(
            timestamp=self.collector.now_utc().astimezone(timezone.utc),
            report_type=report_type,  # type: ignore[arg-type]
            indices=indices,
            sector_performance=sector_perf,       # ✅ now populated
            market_breadth=breadth,
            fii_dii_activity={},                   # requires NSE/SEBI data feed
            macro_indicators=macro,
            global_market_impact={},               # future: US/EU indices
        )
        highs_lows = {
            "gap_up": [
                m for m in moves
                if m.open_price and m.previous_close and m.open_price > m.previous_close * 1.01
            ][:5],
            "gap_down": [
                m for m in moves
                if m.open_price and m.previous_close and m.open_price < m.previous_close * 0.99
            ][:5],
            "volume_spikes": sorted(moves, key=lambda m: m.volume or 0, reverse=True)[:5],
        }
        return summary, gainers, losers, highs_lows
