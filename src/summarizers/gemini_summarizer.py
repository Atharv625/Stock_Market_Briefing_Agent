"""Gemini-specific summarizer adapter."""

from __future__ import annotations

from src.summarizers.llm_client import LLMClient


class GeminiSummarizer:
    def __init__(self) -> None:
        self.client = LLMClient()

    async def summarize(self, prompt: str) -> str:
        return await self.client.complete(prompt)
