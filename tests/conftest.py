import fakeredis
from fastapi import FastAPI
import pytest

from src.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
async def fake_redis():
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    yield redis

    await redis.aclose()

@pytest.fixture
def test_app(fake_redis):
    app = FastAPI()

    app.state.redis = fake_redis
    app.add_middleware(RateLimitMiddleware)

    @app.get("/api/v1/employees")
    async def get_employees():
        return {"message": "Employees retrieved successfully"}

    @app.post("/api/v1/auth/login")
    async def login():
        return {"message": "Login endpoint"}

    @app.post("/api/v1/auth/refresh")
    async def refresh():
        return {"message": "Refresh endpoint"}

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    return app