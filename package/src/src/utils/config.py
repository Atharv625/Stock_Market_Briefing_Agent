"""
src/utils/config.py
===================
Centralized configuration management.
Loads from .env file locally, AWS Secrets Manager in production.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    All fields have sensible defaults for local development.
    """

    # --- AI Configuration ---
    google_gemini_api_key: str = Field(default="", env="GOOGLE_GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")

    # --- Telegram Configuration ---
    telegram_bot_token: str = Field(default="", env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", env="TELEGRAM_CHAT_ID")

    # --- Data Source API Keys ---
    finnhub_api_key: str = Field(default="", env="FINNHUB_API_KEY")
    alpha_vantage_api_key: str = Field(default="", env="ALPHA_VANTAGE_API_KEY")

    # --- AWS Configuration ---
    aws_region: str = Field(default="ap-south-1", env="AWS_REGION")
    aws_access_key_id: Optional[str] = Field(default=None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(default=None, env="AWS_SECRET_ACCESS_KEY")

    # --- DynamoDB Table Names ---
    dynamodb_market_table: str = Field(default="stock-agent-market-data", env="DYNAMODB_MARKET_TABLE")
    dynamodb_news_table: str = Field(default="stock-agent-news-items", env="DYNAMODB_NEWS_TABLE")
    dynamodb_earnings_table: str = Field(default="stock-agent-earnings-reports", env="DYNAMODB_EARNINGS_TABLE")
    dynamodb_reports_table: str = Field(default="stock-agent-generated-reports", env="DYNAMODB_REPORTS_TABLE")
    dynamodb_sentiment_table: str = Field(default="stock-agent-sentiment-history", env="DYNAMODB_SENTIMENT_TABLE")

    # --- S3 ---
    s3_cache_bucket: str = Field(default="stock-agent-cache", env="S3_CACHE_BUCKET")

    # --- Feature Flags ---
    enable_dynamodb: bool = Field(default=False, env="ENABLE_DYNAMODB")
    enable_s3_cache: bool = Field(default=False, env="ENABLE_S3_CACHE")

    # --- App Settings ---
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    default_report_type: str = Field(default="closing", env="DEFAULT_REPORT_TYPE")

    # --- Rate Limits ---
    finnhub_calls_per_minute: int = Field(default=60, env="FINNHUB_CALLS_PER_MINUTE")
    alpha_vantage_calls_per_minute: int = Field(default=5, env="ALPHA_VANTAGE_CALLS_PER_MINUTE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns a cached singleton settings instance."""
    return Settings()


# ---- Nifty 50 Universe ----
NIFTY_50_TICKERS = [
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "BHARTIARTL.NS", "ICICIBANK.NS",
    "INFY.NS", "SBIN.NS", "LICI.NS", "HINDUNILVR.NS", "ITC.NS",
    "BAJFINANCE.NS", "KOTAKBANK.NS", "LT.NS", "HCLTECH.NS", "MARUTI.NS",
    "AXISBANK.NS", "ASIANPAINT.NS", "SUNPHARMA.NS", "TITAN.NS", "NTPC.NS",
    "POWERGRID.NS", "ONGC.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "WIPRO.NS",
    "M&M.NS", "BAJAJFINSV.NS", "ADANIENT.NS", "ADANIPORTS.NS", "TATAMOTORS.NS",
    "JSWSTEEL.NS", "TATASTEEL.NS", "COALINDIA.NS", "HINDALCO.NS", "APOLLOHOSP.NS",
    "CIPLA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS",
    "BPCL.NS", "HEROMOTOCO.NS", "INDUSINDBK.NS", "SBILIFE.NS", "TECHM.NS",
    "TRENT.NS", "SHRIRAMFIN.NS", "BEL.NS", "BAJAJ-AUTO.NS", "BRITANNIA.NS"
]

# ---- Index Tickers ----
INDEX_TICKERS = {
    "nifty_50": "^NSEI",
    "sensex": "^BSESN",
    "bank_nifty": "^NSEBANK",
    "midcap": "^NSEMDCP50",
    "india_vix": "^INDIAVIX",
}

# ---- Sector Mapping ----
SECTOR_TICKERS = {
    "IT": "^CNXIT",
    "Bank": "^NSEBANK",
    "Auto": "^CNXAUTO",
    "Pharma": "^CNXPHARMA",
    "FMCG": "^CNXFMCG",
    "Metal": "^CNXMETAL",
    "Realty": "^CNXREALTY",
    "Energy": "^CNXENERGY",
}

# ---- Report Schedule Types ----
REPORT_TYPES = {
    "pre_market": "8AM Pre-Market Report",
    "midday": "1PM Midday Report",
    "closing": "4PM Closing Report",
    "deep_analysis": "8PM Deep Analysis Report",
}
