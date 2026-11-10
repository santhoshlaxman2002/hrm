import asyncio
import pytest
from src.core.rate_limiter import RateLimiter


@pytest.mark.asyncio
async def test_allows_requests_within_limit(fake_redis):
    limiter = RateLimiter(fake_redis)

    for _ in range(5):
        allowed, count, ttl = await limiter.is_allowed(
            key="test:user:1",
            limit=5,
            window_seconds=60
        )

        assert allowed is True

    assert count == 5
    assert ttl > 0

@pytest.mark.asyncio
async def test_rejects_requests_after_limit(fake_redis):
    limiter = RateLimiter(fake_redis)

    for _ in range(5):
        await limiter.is_allowed(
            key="test:user:2",
            limit=5,
            window_seconds=60,
        )

    allowed, count, ttl = await limiter.is_allowed(
        key="test:user:2",
        limit=5,
        window_seconds=60,
    )

    assert allowed is False
    assert count == 6
    assert ttl > 0

@pytest.mark.asyncio
async def test_concurrent_requests_respect_limit(fake_redis):
    limiter = RateLimiter(fake_redis)

    async def make_request():
        return await limiter.is_allowed(
            key="test:concurrent:user",
            limit=5,
            window_seconds=60,
        )

    results = await asyncio.gather(
        *[make_request() for _ in range(20)]
    )

    allowed_count = sum(
        1 for result in results if result[0]
    )

    rejected_count = sum(
        1 for result in results if not result[0]
    )

    assert allowed_count == 5
    assert rejected_count == 15