"""
src/utils/cache.py
==================
Two-tier caching strategy:
  Tier 1 — In-memory LRU cache (fast, ephemeral)
  Tier 2 — S3-backed persistent cache (durable, cross-invocation)

S3 cache is only used when ENABLE_S3_CACHE=true in config.
"""

import json
import time
import hashlib
from typing import Any, Optional
from cachetools import TTLCache
from src.utils.logger import get_logger
from src.utils.config import get_settings

logger = get_logger(__name__)
settings = get_settings()

# In-memory TTL cache: max 256 items, TTL = 30 minutes
_memory_cache: TTLCache = TTLCache(maxsize=256, ttl=1800)


def _make_cache_key(namespace: str, key: str) -> str:
    """Generate a consistent, safe cache key."""
    raw = f"{namespace}:{key}"
    return hashlib.md5(raw.encode()).hexdigest()


# ---- Tier 1: In-Memory Cache ----

def get_from_memory(namespace: str, key: str) -> Optional[Any]:
    """Retrieve a value from the in-memory cache."""
    cache_key = _make_cache_key(namespace, key)
    value = _memory_cache.get(cache_key)
    if value is not None:
        logger.debug("memory_cache_hit", namespace=namespace, key=key)
    return value


def set_in_memory(namespace: str, key: str, value: Any) -> None:
    """Store a value in the in-memory cache."""
    cache_key = _make_cache_key(namespace, key)
    _memory_cache[cache_key] = value
    logger.debug("memory_cache_set", namespace=namespace, key=key)


# ---- Tier 2: S3-Backed Cache ----

def get_from_s3(namespace: str, key: str) -> Optional[Any]:
    """
    Retrieve a cached value from S3.
    Returns None if not found, expired, or S3 is disabled.
    """
    if not settings.enable_s3_cache:
        return None
    try:
        import boto3
        s3 = boto3.client("s3", region_name=settings.aws_region)
        s3_key = f"cache/{namespace}/{_make_cache_key(namespace, key)}.json"
        response = s3.get_object(Bucket=settings.s3_cache_bucket, Key=s3_key)
        payload = json.loads(response["Body"].read())
        if payload.get("expires_at", 0) < time.time():
            logger.debug("s3_cache_expired", namespace=namespace, key=key)
            return None
        logger.debug("s3_cache_hit", namespace=namespace, key=key)
        return payload["data"]
    except Exception as e:
        logger.warning("s3_cache_miss", namespace=namespace, key=key, error=str(e))
        return None


def set_in_s3(namespace: str, key: str, value: Any, ttl_seconds: int = 3600) -> None:
    """Store a value in S3 cache with a TTL."""
    if not settings.enable_s3_cache:
        return
    try:
        import boto3
        s3 = boto3.client("s3", region_name=settings.aws_region)
        s3_key = f"cache/{namespace}/{_make_cache_key(namespace, key)}.json"
        payload = json.dumps({
            "data": value,
            "expires_at": time.time() + ttl_seconds,
            "created_at": time.time(),
        })
        s3.put_object(
            Bucket=settings.s3_cache_bucket,
            Key=s3_key,
            Body=payload,
            ContentType="application/json",
        )
        logger.debug("s3_cache_set", namespace=namespace, key=key, ttl=ttl_seconds)
    except Exception as e:
        logger.warning("s3_cache_write_failed", error=str(e))


# ---- Unified Cache Interface ----

def get_cached(namespace: str, key: str) -> Optional[Any]:
    """Try memory cache first, then S3."""
    value = get_from_memory(namespace, key)
    if value is not None:
        return value
    return get_from_s3(namespace, key)


def set_cached(namespace: str, key: str, value: Any, ttl_seconds: int = 3600) -> None:
    """Write to both memory and S3 cache."""
    set_in_memory(namespace, key, value)
    set_in_s3(namespace, key, value, ttl_seconds)
