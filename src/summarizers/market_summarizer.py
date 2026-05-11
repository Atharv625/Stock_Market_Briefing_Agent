"""Market summarizer helper."""

from __future__ import annotations

from src.summarizers.report_generator import DailyReportGenerator


class MarketSummarizer:
    def __init__(self) -> None:
        self.generator = DailyReportGenerator()

    async def generate_market_brief(self, report_type: str) -> str:
        report = await self.generator.generate(report_type=report_type)
        return report.llm_summary
