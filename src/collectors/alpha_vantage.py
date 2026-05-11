"""Alpha Vantage collector (optional enrichment)."""

from __future__ import annotations

from typing import Dict

import httpx

from src.utils.config import get_settings


class AlphaVantageCollector:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def quote(self, symbol: str) -> Dict:
        if not self.settings.alpha_vantage_api_key:
            return {}
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": self.settings.alpha_vantage_api_key,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get("https://www.alphavantage.co/query", params=params)
            resp.raise_for_status()
            return resp.json()
