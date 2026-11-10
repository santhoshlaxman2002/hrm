from redis.asyncio import Redis


RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])

if current == 1 then
    redis.call("EXPIRE", KEYS[1], ARGV[1])
end

local ttl = redis.call("TTL", KEYS[1])

return {current, ttl}
"""


class RateLimiter:

    def __init__(self, redis: Redis):
        self.redis = redis

    async def is_allowed(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> tuple[bool, int, int]:

        result = await self.redis.eval(
            RATE_LIMIT_SCRIPT,
            1,
            key,
            window_seconds,
        )

        current_count = int(result[0])
        remaining_seconds = max(int(result[1]), 0)

        allowed = current_count <= limit

        return allowed, current_count, remaining_seconds