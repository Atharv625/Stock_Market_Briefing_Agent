from src.summarizers.prompt_library import MARKET_SUMMARY_PROMPT


def test_fallback_summary():
    assert "Market Snapshot" in MARKET_SUMMARY_PROMPT
