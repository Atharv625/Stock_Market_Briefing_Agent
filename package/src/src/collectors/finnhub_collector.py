"""Finnhub collector for company news and insider trends."""

from __future__ import annotations

from datetime import date
from typing import List

import httpx

from src.utils.config import get_settings


class FinnhubCollector:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.base_url = "https://finnhub.io/api/v1"

    async def company_news(self, symbol: str, from_date: date, to_date: date) -> List[dict]:
        if not self.settings.finnhub_api_key:
            return []
        params = {
            "symbol": symbol,
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "token": self.settings.finnhub_api_key,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(f"{self.base_url}/company-news", params=params)
            resp.raise_for_status()
            return resp.json()
