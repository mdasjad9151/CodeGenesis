"""Small Redis helpers. Redis is an optimization: if it is down, caching is skipped and
rate limits fail open, so the service keeps working on Postgres alone."""
import json
from datetime import datetime, timezone

import redis
from fastapi import HTTPException, status

from core.configs import ConfigLoader
from core.logging import logger

config = ConfigLoader()
_client = redis.Redis.from_url(config.redis_config()["url"], socket_timeout=1, socket_connect_timeout=1)


def get_json(key: str):
    try:
        value = _client.get(key)
        return json.loads(value) if value else None
    except redis.RedisError as e:
        logger.warning(f"Redis get failed ({key}): {e}")
        return None


def set_json(key: str, value, ttl_seconds: int) -> None:
    try:
        _client.set(key, json.dumps(value, default=str), ex=ttl_seconds)
    except redis.RedisError as e:
        logger.warning(f"Redis set failed ({key}): {e}")


def delete(key: str) -> None:
    try:
        _client.delete(key)
    except redis.RedisError as e:
        logger.warning(f"Redis delete failed ({key}): {e}")


def get_version(name: str) -> int:
    """Cache 'generation' number; bump it to invalidate every key built from it."""
    try:
        return int(_client.get(f"version:{name}") or 0)
    except redis.RedisError:
        return 0


def bump_version(name: str) -> None:
    try:
        _client.incr(f"version:{name}")
    except redis.RedisError as e:
        logger.warning(f"Redis incr failed (version:{name}): {e}")


def rate_limit(name: str, user_id: str, limit: int, window_seconds: int) -> None:
    """Fixed-window counter: at most `limit` calls per user per window. Raises 429 when exceeded."""
    window = int(datetime.now(timezone.utc).timestamp()) // window_seconds
    key = f"ratelimit:{name}:{user_id}:{window}"
    try:
        pipe = _client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        count = pipe.execute()[0]
    except redis.RedisError as e:
        logger.warning(f"Rate limit skipped, Redis unavailable: {e}")
        return
    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: max {limit} per {window_seconds}s",
            headers={"Retry-After": str(window_seconds - int(datetime.now(timezone.utc).timestamp()) % window_seconds)},
        )


def ping() -> bool:
    try:
        return bool(_client.ping())
    except redis.RedisError:
        return False
