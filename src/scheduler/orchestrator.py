"""Scheduler orchestration entrypoints for Lambda invocations."""

from __future__ import annotations

from typing import Any, Dict

from src.database.dynamodb_repo import DynamoRepository
from src.database.s3_store import S3ArchiveStore
from src.notifiers.telegram_notifier import TelegramNotifier
from src.summarizers.report_generator import DailyReportGenerator
from src.utils.config import get_settings
from src.utils.logger import AgentLogger

logger = AgentLogger("orchestrator")


class ReportOrchestrator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.generator = DailyReportGenerator()
        self.repo = DynamoRepository()
        self.s3_store = S3ArchiveStore()
        self.notifier = TelegramNotifier()

    async def run(self, report_type: str) -> Dict[str, Any]:
        report = await self.generator.generate(report_type=report_type)
        payload = report.model_dump(mode="json")

        self.repo.save_report(payload)
        self.repo.save_sentiment(report_type=report_type, sentiment=report.market_sentiment)
        if self.settings.enable_s3_cache:
            self.s3_store.put_report(payload)
        await self.notifier.send(report)
        logger.info("report_pipeline_completed", report_type=report_type, report_id=report.report_id)
        return payload
