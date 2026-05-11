"""AWS Lambda handlers for scheduler-driven report generation."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from src.scheduler.orchestrator import ReportOrchestrator
from src.utils.config import get_settings
from src.utils.logger import setup_logging

setup_logging()
settings = get_settings()


def _run(report_type: str) -> Dict[str, Any]:
    orchestrator = ReportOrchestrator()
    return asyncio.run(orchestrator.run(report_type=report_type))


def scheduled_report_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    report_type = event.get("report_type", settings.default_report_type)
    payload = _run(report_type=report_type)
    return {"statusCode": 200, "report_id": payload["report_id"], "report_type": report_type}


def pre_market_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    return {"statusCode": 200, "payload": _run("pre_market")}


def midday_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    return {"statusCode": 200, "payload": _run("midday")}


def closing_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    return {"statusCode": 200, "payload": _run("closing")}


def deep_analysis_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    return {"statusCode": 200, "payload": _run("deep_analysis")}
