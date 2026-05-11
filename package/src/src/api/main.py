"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI

from src.api.routes.earnings import router as earnings_router
from src.api.routes.market import router as market_router
from src.api.routes.news import router as news_router
from src.utils.logger import setup_logging

setup_logging()
app = FastAPI(title="AI Stock Market Intelligence Agent", version="1.0.0")
app.include_router(market_router)
app.include_router(news_router)
app.include_router(earnings_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
