import logging
from fastapi import status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request, call_next):
        path = request.url.path

        excluded_paths = [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]

        if any(path.startswith(item) for item in excluded_paths):
            return await call_next(request)

        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        if path.endswith("/auth/login"):
            limit = 5
            window = 60
        elif path.endswith("/auth/refresh"):
            limit=10
            window=60
        else:
            limit=100
            window=60

        redis = request.app.state.redis

        key = f"rate_limit:{client_ip}:{path}"

        try:
            limiter = RateLimiter(redis=redis)

            allowed, count, retry_after = (
                await limiter.is_allowed(
                    key=key,
                    limit=limit,
                    window_seconds=window
                )
            )
        except Exception:
            logger.exception("Redis rate limiter unavailable")
            return await call_next(request)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "details": "Too many requests. Please try again later."
                },
                headers={
                    "Retry-After": str(retry_after),
                }
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(limit - count, 0))

        return response