"""Parser utilities for shaping quarterly metrics for reporting."""

from __future__ import annotations

from typing import Dict


def format_metric_change(current: float, baseline: float) -> str:
    """Return percentage change string with sign and basis points where relevant."""
    if baseline == 0:
        return "N/A"
    pct = ((current - baseline) / baseline) * 100.0
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.2f}%"


def earnings_risk_flags(metrics: Dict[str, float]) -> list[str]:
    """Generate simple risk flags from key metrics."""
    risks: list[str] = []
    if metrics.get("debt_to_equity", 0.0) > 120:
        risks.append("Leverage remains elevated")
    if metrics.get("ebitda_margin_pct", 0.0) < 10:
        risks.append("EBITDA margin profile is weak")
    if metrics.get("revenue_growth_pct", 0.0) < 0:
        risks.append("Revenue contraction observed")
    return risks
