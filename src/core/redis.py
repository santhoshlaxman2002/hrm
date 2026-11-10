from redis.asyncio import Redis
from src.core.settings import get_settings

settings = get_settings()

async def create_redis_client() -> Redis:
    redis_client = Redis.from_url(
        settings.REDIS_URL.get_secret_value(),
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
        health_check_interval=30,
    )

    await redis_client.ping()

    return redis_client