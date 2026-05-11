from src.agents.sentiment_analyzer import SentimentAnalyzer
from src.models.schemas import NewsItem
from datetime import datetime, timezone


def test_sentiment_infer_bullish():
    analyzer = SentimentAnalyzer()
    news = [
        NewsItem(
            id="1",
            title="Large order win",
            source="x",
            url="https://example.com",
            published_at=datetime.now(timezone.utc),
            summary="Strong deal win",
            sentiment="bullish",
            importance_score=3,
        )
    ]
    assert analyzer.infer(advances=35, declines=15, news=news) == "bullish"
