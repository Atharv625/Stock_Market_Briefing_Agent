"""Earnings summary formatter."""

from __future__ import annotations

from typing import List

from src.models.schemas import EarningsSummary


def summarize_earnings(items: List[EarningsSummary]) -> str:
    return "\n".join([f"- {item.headline_summary}" for item in items[:5]])
