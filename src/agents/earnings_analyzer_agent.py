"""Agent for quarterly performance summarization."""

from __future__ import annotations

from typing import List

from src.collectors.earnings_collector import EarningsCollector
from src.models.schemas import EarningsSummary
from src.parsers.earnings_parser import earnings_risk_flags


class EarningsAnalyzerAgent:
    def __init__(self) -> None:
        self.collector = EarningsCollector()

    async def analyze(self, tickers: List[str]) -> List[EarningsSummary]:
        snapshots = await self.collector.fetch_quarterly_snapshots(tickers=tickers)
        for snap in snapshots:
            metrics = snap.metrics
            snap.risks = earnings_risk_flags({k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))})
            rev = metrics.get("revenue_growth_pct", 0.0)
            margin = metrics.get("ebitda_margin_pct", 0.0)
            snap.headline_summary = (
                f"{snap.ticker}: Revenue growth {rev:.2f}%, EBITDA margin {margin:.2f}%, "
                f"Debt/Equity {metrics.get('debt_to_equity', 0.0):.2f}."
            )
            snap.outlook = "Stable to positive" if rev >= 0 else "Watch for slowdown"
        return snapshots
