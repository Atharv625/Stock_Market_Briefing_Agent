"""Market parser utilities."""

from __future__ import annotations

from typing import Dict, List

from src.models.schemas import StockMove


def sector_performance_from_moves(moves: List[StockMove]) -> Dict[str, float]:
    grouped: Dict[str, list[float]] = {}
    for move in moves:
        sector = move.sector or "Unknown"
        grouped.setdefault(sector, []).append(move.change_percent)
    return {sector: round(sum(vals) / len(vals), 2) for sector, vals in grouped.items() if vals}
