"""NSE collector placeholder for breadth/FII-DII extensions."""

from __future__ import annotations

from typing import Dict


class NSECollector:
    async def get_market_breadth(self) -> Dict[str, int]:
        return {"advances": 0, "declines": 0, "unchanged": 0}

    async def get_fii_dii_activity(self) -> Dict[str, float]:
        return {"fii_net": 0.0, "dii_net": 0.0}
