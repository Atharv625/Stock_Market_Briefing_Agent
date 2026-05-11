"""Thin LLM adapter supporting Gemini and OpenAI-compatible fallback."""

from __future__ import annotations

import json
from typing import Any, Dict

import google.generativeai as genai
import httpx
from google.api_core.exceptions import GoogleAPIError, InvalidArgument, PermissionDenied

from src.utils.config import get_settings
from src.utils.logger import AgentLogger
from src.utils.retry import with_async_retry

logger = AgentLogger("llm_client")

# Permanent errors that should NOT be retried — wrong key, quota hard-limit, etc.
_PERMANENT_ERRORS = (InvalidArgument, PermissionDenied)

# Transient errors worth retrying
_TRANSIENT_ERRORS = (GoogleAPIError, ConnectionError, TimeoutError)


class LLMClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        if self.settings.google_gemini_api_key:
            genai.configure(api_key=self.settings.google_gemini_api_key)

    @with_async_retry(max_attempts=3, min_wait=1, max_wait=8, exceptions=_TRANSIENT_ERRORS)
    async def complete(self, prompt: str) -> str:
        if not self.settings.google_gemini_api_key:
            logger.warning("llm_fallback_triggered", reason="no_api_key")
            return self._heuristic_fallback(prompt)
        try:
            model = genai.GenerativeModel(self.settings.gemini_model)
            response = await model.generate_content_async(prompt)
            text = response.text or ""
            if text:
                return text.strip()
            logger.warning("llm_empty_response")
            return self._heuristic_fallback(prompt)
        except _PERMANENT_ERRORS as exc:
            # Invalid key / quota hard-limit — retrying is pointless, fall back immediately
            logger.error("llm_permanent_error", error=str(exc), hint="Check GOOGLE_GEMINI_API_KEY in .env")
            return self._heuristic_fallback(prompt)

    @with_async_retry(max_attempts=2, min_wait=1, max_wait=4, exceptions=(httpx.HTTPError,))
    async def openai_compatible_complete(self, prompt: str, endpoint: str, api_key: str, model: str) -> str:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _heuristic_fallback(prompt: str) -> str:
        """Keeps system operational when LLM provider is unavailable."""
        clipped = prompt[:700].replace("\n", " ")
        return (
            "Automated market brief generated using fallback summarizer. "
            "Primary LLM was unavailable. Context snippet: "
            f"{clipped}"
        )

    @staticmethod
    def as_json(payload: Dict[str, Any]) -> str:
        return json.dumps(payload, default=str, ensure_ascii=True)
